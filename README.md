# Financial Fraud Detection

An educational project for financial fraud detection using transaction data, customer behavior, and machine learning on an imbalanced dataset. Sprint 1 establishes the data audit, normalized data contract, leakage-aware temporal split, EDA, and synthetic fixtures. It does not train models or rebalance the data.

## Repository layout

```text
src/data/       audit, preprocessing, split, EDA, mock generator, pipeline
src/features/   behavioral feature work (Trung)
src/models/     model work (Tú)
src/imbalance/  imbalance methods (Tùng)
src/evaluation/ evaluation (Khoa)
data/raw/       local source CSVs; not intended for Git
data/processed/ normalized Parquet, local and ignored
data/splits/    temporal split Parquet, local and ignored
data/samples/   small synthetic fixtures
configs/        schema, baseline features, split metadata
notebooks/      data understanding notebook
results/eda/    aggregate summaries and PNG figures
artifacts/      local model artifacts, ignored
docs/           data audit, contract, and handoff reports
tests/          unit tests
```

## Environment

Python 3.10+ is recommended. Create an isolated environment and install the declared dependencies:

```powershell
py -m venv .venv
..venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

## Source data

Use the Sparkov `fraudTrain.csv` and `fraudTest.csv` files. Place them at:

```text
data/raw/fraudTrain.csv
data/raw/fraudTest.csv
```

The pipeline does not download or alter source files. Confirm local checksums with:

```powershell
Get-FileHash data/raw/fraudTrain.csv -Algorithm SHA256
Get-FileHash data/raw/fraudTest.csv -Algorithm SHA256
```

Raw, processed, split, and model artifacts are excluded from new Git additions by `.gitignore`. Check `git ls-files data/raw` as well: ignore patterns do not remove files that Git already tracks.

## Run the data pipeline

Run from the repository root:

```powershell
python -m src.data.pipeline --stage audit
python -m src.data.pipeline --stage preprocess
python -m src.data.pipeline --stage split
python -m src.data.pipeline --stage eda
python -m src.data.pipeline --stage all
python -m src.data.pipeline --stage mock
```

Stages refuse to replace existing processed/split artifacts by default. Add `--force` only when intentionally rebuilding. Detailed EDA uses training rows only. The test file is preserved in full as test when its timestamps follow the training source.

## Tests

```powershell
python -m pytest -q
```

Tests use synthetic fixtures and do not train a model. The EDA notebook at `notebooks/01_data_understanding.ipynb` calls the same implementation as the CLI.

## Data contract and outputs

**Current readiness:** the data pipeline and model inputs pass full-data validation. The audit verifies that adding seven calendar years to UTC `unix_time` reproduces `trans_date_trans_time` on every row; `unix_time` is treated as a stale source field, excluded from normalized data, and retained only in unchanged raw CSVs. A Git handoff blocker remains because the raw CSVs are already LFS-tracked in the published `toan` branch; see `docs/DATA_READINESS_REPORT.md` before sharing or merging this work.

- `data/processed/transactions.parquet`: normalized transaction table; names and street addresses removed.
- `data/splits/{train,validation,test}.parquet`: train/validation derived from fraudTrain by time; fraudTest retained as test.
- `data/splits/split_manifest.parquet`: `trans_num` to split mapping.
- `configs/data_schema.yaml`, `configs/base_features.yaml`, `configs/split.yaml`: field, feature, and split contracts.
- `docs/DATA_CONTRACT.md`: join and leakage rules for the project team.
- `results/eda/`: aggregate tables and ten PNG figures; no direct identity fields.

All scores should be keyed by `trans_num`. The baseline excludes transaction/card IDs, target, timestamp metadata, and source-dataset metadata. Behavioral features must use only same-card events strictly before the current timestamp; equal-time events are processed as a group.

## Git collaboration

Work on the assigned feature branch. Do not commit raw, processed, split, or model files. Review `git status --short --branch` before handoff. Commit, push, and PR actions require explicit approval from the project owner.
