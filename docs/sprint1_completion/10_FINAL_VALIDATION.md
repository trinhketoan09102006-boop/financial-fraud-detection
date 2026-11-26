# Final Sprint 1 validation

## Environments

| Environment | Python | pandas | PyArrow | pytest |
|---|---:|---:|---:|---:|
| Toan | 3.13.7 | 2.2.3 | 22.0.0 | 9.2.0 |
| Tu compatibility venv | 3.11.9 | 3.1.1 | 26.0.1 | 9.2.0 |

## Tests and checks

| Check | Python 3.11 / pandas 3.1 / Arrow 26 | Python 3.13 / pandas 2.2 / Arrow 22 |
|---|---|---|
| Reported mock test (`-vv -s`) | PASS, 1 test | PASS, 1 test |
| Full `python -m pytest -q -rs` | PASS, 18 passed, 0 skipped | PASS, 18 passed, 0 skipped |
| `python -m compileall -q src tests` | PASS | PASS |
| `python -m pip check` | PASS | PASS |
| Contract-backed Parquet round-trip | PASS | PASS |

The Toan environment emits one third-party AnyIO `PytestRemovedIn10Warning`; the Tu compatibility environment emits no test warnings. Full logs are `11_full_suite_py311_final.txt` and `11_full_suite_py313_final.txt`; targeted logs are `11_mock_test_py311_verbose.txt` and `11_mock_test_py313_verbose.txt`.

## Arrow schema and values

- Contract source remains `configs/data_schema.yaml`.
- The shared converter loads every field type/nullability from that YAML file.
- Normalized output is validated against all 25 contract fields. Train, validation, test, and split manifest use Arrow `string` for textual fields under both environments.
- `trans_num`, `cc_num`, timestamp values, fraud labels, row counts, and split assignments are preserved. Full-data integration passes in both environments.
- Mock conversion is tested from object, pandas string, and Arrow-backed large_string input through Parquet readback.

The current split policy is `nearest_row_count`; hash remains `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`. No split policy/config/hash change was made.

## Cross-version numeric parsing note

A separate full-data comparison of Parquets produced by the two prior runtime combinations found identical IDs, card IDs, timestamps, labels, source labels, and split hash. CSV-to-float parsing differed in coordinate columns by at most `2.84e-14`; one derived `merchant_distance_km` value differed by `3.81e-6 km`. This is sub-ULP coordinate parsing/runtime variance, not introduced by the Arrow schema fix. Details are in `11_cross_version_data_comparison.json`.

## Git and data safety

- Branch remains `toan`; no commit, push, merge, reset, rebase, or LFS change was performed.
- Raw checksums and current split metadata were unchanged.
- Processed/split artifacts and both compatibility environments are Git-ignored; no large data or venv files are staged.
- Python 3.11.9 compatibility packages are isolated in `data/processed/.compat_tu_py311env`. The active Python 3.13 installation was not upgraded or downgraded.

See `11_CROSS_VERSION_ARROW_COMPATIBILITY.md` for the root cause, reproduction, and instructions for Tu to repeat the checks after pulling the reviewed branch.
