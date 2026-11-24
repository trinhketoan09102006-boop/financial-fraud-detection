# T04 — Reproducibility guide

## Prerequisites and provenance

Feature source was delivered locally in commit `af71e9d3a07180e92de7bbf19f72a37eb0d91fad`; the T03 documents and packaging scripts are pending Commit 2. Earlier base HEAD `0161186bdc1ac0eb0d88a7638dad67d1b9fbf029` alone does not contain the feature source. Obtain reviewed T01–T04 changes through an approved team handoff after the owner resolves Git/LFS. Raw/processed/splits/features are local artifacts; obtain authorized input data. A clone or external transfer was not tested during T04.

Validated local environment: Windows, Python 3.14.4, pandas 3.1.1, PyArrow 26.0.1, NumPy 2.5.5, pytest 9.2.0, isolated `.venv-clean`. `requirements.txt` is unpinned, therefore installing it alone does **not** guarantee this exact environment; the proposed freeze is preserved in `C:\Users\MSI\Documents\Codex\2026-11-22\files-pasted-by-the-user-task\desktop_preserved\fraud_final_fix_report\requirements-lock-proposed.txt`. That absolute path is local only; transfer/review it separately and ensure platform compatibility. No claim of cross-machine reproducibility until the team tests it. Metadata records versions, hashes and generated timestamp, not an input artifact absolute path.

## Windows commands after team-approved source delivery

```powershell
git clone https://github.com/trinhketoan09102006-boop/financial-fraud-detection.git
Set-Location financial-fraud-detection
# Obtain the approved feature source/tests on the intended branch via your team's process.
py -3.14 -m venv .venv-clean
.\.venv-clean\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-clean\Scripts\python.exe -m pip check
# Put authorized raw CSV files in data/raw, or obtain verified processed/split artifacts.
# Only if upstream artifacts are absent and raw data is authorized:
.\.venv-clean\Scripts\python.exe -m src.data.pipeline --stage all --cutoff-policy nearest_row_count
.\.venv-clean\Scripts\python.exe -c "import json; print(json.load(open('data/splits/split_metadata.json'))['split_hash'])"
# Confirm aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8.
# Preserve existing feature outputs; this CLI refuses a non-empty destination.
.\.venv-clean\Scripts\python.exe -m src.features.behavioral
.\.venv-clean\Scripts\python.exe -m src.features.validate_behavioral
.\.venv-clean\Scripts\python.exe -m pytest -q -rs
```

The upstream pipeline command writes generated outputs; use only when absent and reviewed. Do not use `--force` on shared data without preserving it. The feature CLI is real and supports `--output`; validation CLI supports `--directory` and `--metadata`. No full regeneration was run during T04. Feature builder and validator hard-code the approved split hash and expected row counts; a different split will fail until the contract is intentionally revised.

## Use with baseline

```python
import pandas as pd, yaml
from src.features.behavioral import FEATURES
from src.features.validate_behavioral import validate
validate('data/features/behavioral_v1')
config = yaml.safe_load(open('configs/base_features.yaml', encoding='utf-8'))
base = config['features']['numeric'] + config['features']['categorical']
for split in ('train', 'validation', 'test'):
    transactions = pd.read_parquet(f'data/splits/{split}.parquet')
    features = pd.read_parquet(f'data/features/behavioral_v1/{split}.parquet')
    joined = transactions.merge(features, on='trans_num', validate='one_to_one')
    assert len(joined) == len(transactions) == len(features)
    X, y, keys = joined[base + FEATURES], joined['is_fraud'], joined['trans_num']
    # Fit any preprocessing only on training X; retain keys for scores.
```

Metadata's input/output SHA-256 values verify the exact files from that run. Parquet serialization may differ with library versions; compare schema, keys, feature values with documented numeric tolerance, and semantic split hash rather than requiring cross-version byte equality. Current validator intentionally requires local metadata to match local bytes. History includes all earlier observed events across split boundaries; same timestamps are atomic and labels excluded. D01–D06 are approved in T01 documents.

## T03 reproducibility package — later update

`docs/trung/requirements-behavioral-v1-snapshot.txt` is a 121-package freeze snapshot of the validated Python 3.14.4 environment (pandas 3.1.1, PyArrow 26.0.1); it is a reference, not an official team lock, and a clean install on another machine has not been verified. Choose a suitable environment and review platform-specific pins before using `pip install -r docs/trung/requirements-behavioral-v1-snapshot.txt`; this may change packages in that environment. `requirements.txt` remains unchanged.

The packaged assessment and report scripts live beside the handoff documents in `docs/trung/`: the sandbox did not permit creation of the proposed repository-root `scripts/` parent. They derive the repository root from their location and read inputs from that repository. From the repo root, after dependencies and validated inputs are ready:

```powershell
.\.venv-clean\Scripts\python.exe docs/trung/t03_assess.py --help
.\.venv-clean\Scripts\python.exe docs/trung/t03_assess.py --output-dir results/features/t03_reproduction
.\.venv-clean\Scripts\python.exe docs/trung/t03_reports.py --assessment-dir results/features/t03_reproduction --output-dir results/features/t03_reproduction_reports
```

The first command that runs an assessment above processes all 1,852,394 rows; do not run it until intended. Both scripts refuse to overwrite their existing named outputs unless explicitly given `--overwrite`; preserve existing outputs before using that flag. Neither writes to `data/` or regenerates features. The report template contains historical narrative and is restricted to the previously reviewed artifact hashes and expected table shapes; its report log describes the historical T03 run, not a new execution. Report tables are trusted local assessment outputs: independently verify their provenance and values before publication. Run the two scripts in order on the same dataset. Other data, schema or split versions require separate review. Packaging was checked with syntax, imports, help and rendering existing aggregate tables to a workspace directory; the full assessment and cross-machine rebuild were not rerun.
