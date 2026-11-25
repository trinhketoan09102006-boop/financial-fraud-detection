# S1-T03 — Execution log

Branch `trung/feature-engineering-s1`; HEAD `0161186bdc1ac0eb0d88a7638dad67d1b9fbf029`. `git status --short --branch --untracked-files=all` returned `fatal: this operation must be run in a work tree`; no clean-tree assertion is made.

Python 3.14.4; pandas 3.1.1; PyArrow 26.0.1. Command from repo root: `.\.venv-clean\Scripts\python.exe C:\Users\MSI\Documents\Codex\2026-11-22\files-pasted-by-the-user-task\t03_assess.py`. Script uses only read access to input files and writes assessment outputs. Runtime 79.76 s; peak Windows working set 1,668,427,776 bytes during assessment, not feature generation.

Input paths: `data/processed/transactions.parquet`, `data/splits/split_manifest.parquet`, split config/metadata; features `data/features/behavioral_v1/`. Split hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`. SHA-256:

- processed: `111d9d7e3d8c959728aafd3787701595285acbdf9c807433f5b718dcef637626`
- manifest: `86d8a6e44e01464a82540ba07ff0a1da8e1a44045c61a94436351f36f987fe96`
- metadata: `4fa810a1d2452ed3f5dbfdc0d01cf666b69e1c4a00939a514d66b25c4bc3fd11`
- train: `5184322dc4b88f73fa59a091406d34b746c253c93533f48427c2589c818d32b1`
- validation: `cb34d6e44f194eb927c460e4da78a349536a64b48a93271182093a69e12c8b63`
- test: `7bd3d66ac276e0837d94ad2596b9beb450606a2b809b1ed45d13c13c150e3093`

Outputs: `results/features/behavioral_v1/` contains `feature_statistics.csv`, `novelty_rates.csv`, `train_pearson.csv`, `train_spearman.csv`, `train_fraud_comparison.csv`, `assessment_summary.json` and five PNG charts. Reports are the three S1_T03 Markdown documents in `docs/trung/`.

Warnings/limits: Git status unavailable; input data timezone and currency unknown. Display plots clip continuous distributions at train P99. Correlations use pairwise complete train rows; no imputation. Fraud relevance joins only the pre-existing train labels. Files contain aggregate statistics; no feature regeneration or upstream overwrite occurred.
