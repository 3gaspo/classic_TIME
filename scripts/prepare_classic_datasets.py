"""Materialize shared classic CSV panels as TIME-compatible saved Arrow datasets."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
from datasets import Dataset as HFDataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from timebench.evaluation.dataset_builder import dataframes_to_generator  # noqa: E402
from timebench.paths import data_root, dataset_storage_root  # noqa: E402


PROJECT_SCOPE = "classic_tsf"
PORTABLE_KEYS = {
    "date_col",
    "target_cols",
    "drop_users",
    "aggr",
    "aggr_period",
    "missing_values",
}


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    frequency: str

    @property
    def key(self) -> str:
        return f"{self.name}/{self.frequency}"


DATASETS = (
    DatasetSpec("electricity", "H"),
    DatasetSpec("traffic", "H"),
    DatasetSpec("solar", "H"),
    DatasetSpec("weather", "H"),
    DatasetSpec("exchange_rate", "D"),
    DatasetSpec("ETTh1", "H"),
    DatasetSpec("ETTh2", "H"),
    DatasetSpec("ETTm1", "15T"),
    DatasetSpec("ETTm2", "15T"),
)


def _config_options(config_path: Path) -> tuple[dict[str, Any], list[str]]:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError(f"dataset config must contain an object: {config_path}")

    options = {
        key: value
        for key, value in raw.items()
        if key in PORTABLE_KEYS and not key.startswith("_")
    }
    scoped = raw.get(PROJECT_SCOPE) or {}
    if not isinstance(scoped, Mapping):
        raise ValueError(f"{PROJECT_SCOPE!r} config must be an object: {config_path}")
    for key, value in scoped.items():
        if key in PORTABLE_KEYS and value is not None:
            options[key] = value
    options.setdefault("missing_values", "zero")
    options.setdefault("drop_users", [])
    return options, sorted(key for key, value in options.items() if value is not None)


def _drop_target_columns(frame: pd.DataFrame, drop_users: list[Any]) -> pd.DataFrame:
    columns = list(frame.columns)
    drop_names: set[str] = set()
    for value in drop_users:
        if isinstance(value, str) and not value.lstrip("-").isdigit():
            if value not in columns:
                raise KeyError(f"drop_users column {value!r} is absent")
            drop_names.add(value)
            continue
        index = int(value)
        if index < 0 or index >= len(columns):
            raise IndexError(f"drop_users index {index} is outside {len(columns)} targets")
        drop_names.add(str(columns[index]))
    return frame[[column for column in columns if str(column) not in drop_names]]


def _load_panel(csv_path: Path, options: Mapping[str, Any]) -> tuple[pd.DataFrame, int]:
    frame = pd.read_csv(csv_path)
    date_col = str(options.get("date_col") or frame.columns[0])
    if date_col not in frame:
        raise KeyError(f"date column {date_col!r} is absent from {csv_path}")
    timestamps = pd.to_datetime(frame.pop(date_col), errors="raise")
    if timestamps.isna().any() or timestamps.duplicated().any():
        raise ValueError(f"timestamps must be finite and unique: {csv_path}")
    frame.index = pd.DatetimeIndex(timestamps)
    frame = frame.sort_index()

    target_cols = options.get("target_cols")
    if target_cols is not None:
        requested = [str(column) for column in target_cols]
        missing = [column for column in requested if column not in frame]
        if missing:
            raise KeyError(f"target columns are absent from {csv_path}: {missing}")
        frame = frame[requested]
    frame = _drop_target_columns(frame, list(options.get("drop_users") or []))
    if frame.shape[1] == 0:
        raise ValueError(f"no target columns remain: {csv_path}")

    values = frame.to_numpy(dtype=float)
    infinite_count = int(np.isinf(values).sum())
    if infinite_count:
        raise ValueError(f"{csv_path} contains {infinite_count} infinite values")

    aggregation = options.get("aggr")
    if aggregation:
        period = str(options.get("aggr_period") or "h")
        if aggregation not in {"sum", "mean"}:
            raise ValueError(f"unsupported aggregation {aggregation!r}")
        frame = getattr(frame.resample(period), str(aggregation))()

    missing_policy = str(options.get("missing_values") or "zero").lower()
    if missing_policy not in {"zero", "error"}:
        raise ValueError("missing_values must be 'zero' or 'error'")
    missing_count = int(frame.isna().sum().sum())
    if missing_count and missing_policy == "error":
        raise ValueError(f"{csv_path} contains {missing_count} missing values")
    if missing_count:
        frame = frame.fillna(0.0)
    if np.isinf(frame.to_numpy(dtype=float)).any():
        raise ValueError(f"{csv_path} contains infinite values after aggregation")
    return frame.astype(np.float32), missing_count


def _prepare_one(
    spec: DatasetSpec,
    source_root: Path,
    destination_root: Path,
    overwrite: bool,
) -> dict[str, Any]:
    source_dir = source_root / spec.name
    csv_path = source_dir / f"{spec.name}.csv"
    config_path = source_dir / "config.json"
    if not csv_path.is_file() or not config_path.is_file():
        raise FileNotFoundError(f"expected {csv_path} and {config_path}")

    output_path = destination_root / spec.name / spec.frequency
    if output_path.exists():
        if not overwrite:
            raise FileExistsError(f"destination already exists: {output_path}")
        resolved_output = output_path.resolve()
        resolved_root = destination_root.resolve()
        if resolved_output == resolved_root or resolved_root not in resolved_output.parents:
            raise ValueError(f"refusing to replace destination outside {resolved_root}")
        shutil.rmtree(resolved_output)

    options, applied_keys = _config_options(config_path)
    print(f"{spec.key}: config={config_path} applied_keys={applied_keys}")
    frame, missing_count = _load_panel(csv_path, options)
    generator, features = dataframes_to_generator(
        frame,
        freq=spec.frequency,
        to_univariate=False,
        csv_names=[spec.name],
    )
    dataset = HFDataset.from_generator(generator, features=features)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.save_to_disk(output_path)
    print(f"{spec.key}: saved {frame.shape[0]} timestamps x {frame.shape[1]} targets")
    return {
        "dataset": spec.key,
        "source_csv": str(csv_path.resolve()),
        "source_config": str(config_path.resolve()),
        "output": str(output_path.resolve()),
        "timestamps": int(frame.shape[0]),
        "targets": int(frame.shape[1]),
        "missing_values_replaced": missing_count,
        "applied_config_keys": applied_keys,
        "effective_options": options,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=data_root(),
        help="Shared root containing one source directory per classic dataset.",
    )
    parser.add_argument(
        "--destination-root",
        type=Path,
        default=dataset_storage_root(),
        help="Shared TIME saved-Arrow root to create.",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=[spec.name for spec in DATASETS],
        help="Optional subset; the default prepares every configured classic dataset.",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    source_root = args.source_root.expanduser().resolve()
    destination_root = args.destination_root.expanduser().resolve()
    selected = set(args.datasets or [spec.name for spec in DATASETS])
    destination_root.mkdir(parents=True, exist_ok=True)
    records = [
        _prepare_one(spec, source_root, destination_root, args.overwrite)
        for spec in DATASETS
        if spec.name in selected
    ]
    catalog_path = destination_root / "catalog.json"
    catalog_path.write_text(
        json.dumps({"version": 1, "datasets": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"catalog: {catalog_path}")


if __name__ == "__main__":
    main()
