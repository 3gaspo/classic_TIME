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

This repository inherits Improved TIME's generic cluster, artifact, Seasonal
Naive, diagnostic, evaluation-grid, and reporting implementation but does not
execute it or own a scientific result layer. Direct children add their own
models, scientific schedules, experiment-specific launchers and reports,
`outputs/`, and `logs/` while receiving later Improved TIME changes
transitively.
