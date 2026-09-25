# Classic TIME Template

Classic TIME Template is the reusable layer for supervised experiments on the
established long-term forecasting datasets. It derives from Improved TIME and
adds preparation and loading of classic panels through TIME's saved-Arrow
schema. Experiment repositories such as
[`classic_tsf`](https://github.com/3gaspo/classic_tsf) inherit this layer and
the generic Improved TIME cluster/artifact toolchain. They own their model
grids, experiment-specific launchers, results, and conclusions.
The inherited runtime logs explicit cgroup availability in each compute-node
snapshot and records the device actually selected by learned and CPU-only
stages. Reusable plotting is headless and moves dense labels to an external
legend.

The dataset scope is Electricity, Traffic, Solar-Energy, Weather, Exchange
Rate, ETTh1, ETTh2, ETTm1, and ETTm2. PEMS is intentionally excluded.

## Current status

Dataset conversion and loading are implemented. The shared supervised split,
training-window, horizon, target-mode, objective, and seed contracts have not
yet been selected. Consequently, the catalog is preparation-ready but not a
runnable forecasting grid, and this template claims no experimental result.

## Dataset preparation

The shared source layout is:

```text
datasets/
  electricity/electricity.csv
  traffic/traffic.csv
  solar/solar.csv
  weather/weather.csv
  exchange_rate/exchange_rate.csv
  ETTh1/ETTh1.csv
  ETTh2/ETTh2.csv
  ETTm1/ETTm1.csv
  ETTm2/ETTm2.csv
```

Prepare the nine panels into `datasets/classic_datasets/` with:

```bash
PYTHONPATH=src uv run --no-sync python scripts/prepare_classic_datasets.py
```

The command discovers each adjacent `config.json`, applies portable fields and
the existing `classic_tsf` override object, and writes one multivariate
saved-Arrow dataset per panel plus `classic_datasets/catalog.json` provenance.
Supported source settings include timestamp/target selection, exclusions,
aggregation, and the `zero|error` missing-value policy. Infinite values are
rejected. Solar is aggregated to hourly sums and Weather to hourly means
through their shared configurations.

For `drop_users`, omission or `null` inherits the preceding value, `[]` keeps
all CSV columns, and a non-empty list replaces it. Exclusions are applied only
during CSV preparation and never again by saved-Arrow consumers. Existing
prepared datasets are preserved unless `--overwrite` is explicit.

## Runtime paths

Within this workspace, `TIME_DATASET` defaults to the shared
`datasets/classic_datasets/` root and `TIME_METADATA` to
`datasets/classic_tsf_metadata/`. Standalone checkouts resolve the same names
below their configured `TIME_DATA_ROOT`. Weights, outputs, and logs remain
project-scoped and ignored.

The inherited schema-1 lifecycle recognizes `computed` task artifacts between
computation and a separate finalizer. Outer launch interruption preserves that
state, while reports and downstream consumers continue to require
`completed`. Cache dependencies use compact producer references. The inherited
validation helper requires finite support in both context and future; future
classic selectors must define their own no-validation default.

The catalog at
[`src/timebench/config/datasets.yaml`](src/timebench/config/datasets.yaml)
contains the nine dataset/frequency keys but deliberately omits split lengths
and terms. This prevents TIME's three `short|medium|long` labels from silently
replacing the conventional `96/192/336/720` supervised horizons.

## Source tree

```text
scripts/prepare_classic_datasets.py  CSV/config to TIME saved-Arrow front
src/timebench/config/                classic dataset catalog
src/timebench/evaluation/            inherited dataset/window/metric contracts
src/timebench/pipeline/              inherited task lifecycle contracts
src/timebench/feature/               inherited dataset diagnostics/features
slurm/, src/slurm/                    inherited generic cluster execution
src/tests/                            common and classic preparation checks
datasets/, weights/                   ignored input placeholders
outputs/, logs/                       ignored artifact placeholders
```

See [architecture](docs/architecture.md),
[dataset format](docs/DATASET_FORMAT.md),
[experiment catalog](docs/experiment_catalog.md), and
[method overview](latex/method_overview.tex).

The inherited TIME code remains under Apache-2.0. Dataset licenses remain
those of their original providers and must be reviewed before redistribution.
