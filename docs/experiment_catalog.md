# Experiment catalog

## Implemented preparation

- Question: can the nine classic non-PEMS panels be consumed through the same
  saved-Arrow schema and loader as TIME?
- Entry point: `scripts/prepare_classic_datasets.py`.
- Output: shared `classic_datasets/<dataset>/<frequency>/` data and catalog
  provenance.
- Status: implemented; no forecasting result is produced.

## Shared supervised contract

Chronological split borders, training-window sampling, context lengths,
prediction horizons, target representation, objective, and seed ownership
remain to be selected. These are template-level decisions because every small-
model child must compare methods on the same data contract.

## Downstream experiment families

`classic_tsf` is the first experiment child. It will host TimeTensors- and
RevIN-like studies using this storage/loading layer. PatchTST, DLinear, and
other baselines may be added to the shared training surface once their common
protocol is selected. None is currently implemented by this template.
