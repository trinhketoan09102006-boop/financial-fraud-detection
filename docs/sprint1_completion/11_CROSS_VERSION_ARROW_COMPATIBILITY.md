# Cross-version Arrow schema compatibility

## Summary

The reported mock test failure is reproducible on the exact Tu versions. The generated values are valid; direct pandas-to-Arrow inference changes the Arrow width for strings across library versions. A contract-driven converter now controls serialization for normalized data, mocks, and splits.

## Environments and reproduction

| Environment | Python | pandas | PyArrow |
|---|---:|---:|---:|
| A (Toan) | 3.13.7 | 2.2.3 | 22.0.0 |
| B (Tu) | 3.11.9 | 3.1.1 | 26.0.1 |

Actual generator output on B:

```text
pandas trans_num dtype: string
pa.Table.from_pandas(...).trans_num: large_string
contract Arrow table trans_num: string
Parquet readback trans_num: string
```

On A, direct inference happens to return `string`. Both environments return `string` when conversion follows the YAML contract. The reproduction logs are `11_root_cause_reproduction_py311.txt` and `11_root_cause_reproduction_py313.txt`.

## Implementation

- `src/data/arrow_schema.py` reads type and nullability declarations from `configs/data_schema.yaml`.
- `dataframe_to_arrow_table(frame, strict=True)` requires the exact normalized field set and constructs the declared schema.
- Non-strict conversion is used for temporal split Parquets; known fields retain contract types and additional `large_string` fields such as manifest `split` are narrowed to `string`.
- `src/data/preprocess.py` and `src/data/split.py` use the shared converter at their Parquet write boundaries.
- Tests validate the mock through a contract-backed Parquet write/read, and exercise object, pandas string, and Arrow-backed large_string input. Integration tests also inspect normalized/split/manifest Parquet schemas.

No contract, identifier, timestamp, label, row count, or split logic was changed.

## Validation results

| Result | Environment A | Environment B |
|---|---|---|
| Reported test | PASS | PASS |
| Full pytest suite | 18 passed, 0 skipped | 18 passed, 0 skipped |
| Compileall | PASS | PASS |
| pip check | PASS | PASS |
| Parquet contract round-trip | PASS | PASS |

The official split remains `nearest_row_count`, hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.

Cross-version full-data comparison preserved `trans_num`, `cc_num`, timestamps, labels, and split assignments exactly. Only coordinate parser binary rounding differed by at most `2.84e-14`; one derived distance differed by `3.81e-6 km`. This was present between the two pandas CSV parsers and is documented in `11_cross_version_data_comparison.json`.

## Repeat on Tu's machine

After Toan's reviewed change is pushed, Tu can run from the repository root:

```powershell
python -m pytest tests/test_mock_data.py::test_mock_data_is_synthetic_temporal_and_covers_each_split -vv -s
python -m pytest -q -rs
python -m compileall -q src tests
python -m pip check
```

Use Python 3.11.9, pandas 3.1.1, and PyArrow 26.0.1. The first command should pass and the full suite should report 18 passed with no skips. The regression itself additionally constructs Arrow-backed `large_string` values, so it continues to exercise the backend that triggered the original report.

## Remaining notes

No dependencies in `requirements.txt` were changed; PyYAML was already declared. No commit or push was performed. `READY_FOR_TU` is yes based on running this exact Python/pandas/PyArrow combination in an isolated venv; Tu should still repeat the commands after pulling.
