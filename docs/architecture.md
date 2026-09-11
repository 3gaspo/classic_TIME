# Architecture

Classic TIME Template adds one reusable preparation path to Improved TIME:

```text
shared datasets/<name>/<name>.csv + config.json
  -> scripts/prepare_classic_datasets.py
       timestamp and target selection
       configured exclusions and resampling
       post-aggregation missing-value policy
       TIME multivariate saved-Arrow conversion
  -> shared datasets/classic_datasets/<name>/<frequency>/
  -> timebench.evaluation.Dataset
       chronological partitions and windows once configured
```

`src/timebench/paths.py` owns the classic shared-data defaults,
`src/timebench/config/datasets.yaml` owns the dataset catalog, and
`src/timebench/evaluation/` retains the inherited loading and metric contracts.
The reusable supervised model, training, and sampling owners do not yet exist;
they will be introduced only after the shared protocol is selected.

This repository contains no cluster workflow or scientific result layer.
Direct children add their own models, launchers, reports, `outputs/`, and
`logs/` while receiving later Improved TIME changes transitively.
