# Cross-version test execution report

## Environments

| Environment | Python | pandas | PyArrow | pytest |
|---|---:|---:|---:|---:|
| A (existing Toan environment) | 3.13.7 | 2.2.3 | 22.0.0 | 9.2.0 |
| B (isolated Tu-compatible environment) | 3.11.9 | 3.1.1 | 26.0.1 | 9.2.0 |

Environment B was created in an isolated virtual environment. The active Python 3.13 environment was not changed.

## Results

| Check | Environment A | Environment B |
|---|---|---|
| Reported mock test `test_mock_data_is_synthetic_temporal_and_covers_each_split` | PASS | PASS |
| Full `pytest -q -rs` suite | 18 passed, 0 failed, 0 skipped | 18 passed, 0 failed, 0 skipped |
| `python -m compileall -q src tests` | PASS | PASS |
| `python -m pip check` | PASS | PASS |
| Contract Arrow schema after Parquet round-trip | PASS | PASS |

Logs: `11_mock_test_py313_verbose.txt`, `11_mock_test_py311_verbose.txt`, `11_full_suite_py313_final.txt`, and `11_full_suite_py311_final.txt`. The exact failing test was also run separately in both environments; it passed in each.

Environment A emitted one third-party AnyIO `PytestRemovedIn10Warning` concerning a deprecated pytest alias. Environment B completed without warnings. No test was skipped in either final full-suite run.

An earlier full-suite attempt in Environment B failed collection because optional plotting packages were not installed in that isolated environment. The dependencies were installed into that venv, after which the full suite passed. The initial attempt is retained in `11_full_suite_py311_initial_dependency_gap.txt`; it is not the final result.

## Schema regression coverage

The regression tests exercise Python object strings, pandas `string`, and Arrow-backed `large_string` inputs. They confirm that the declared YAML contract drives the Arrow schema and that Parquet readback preserves Arrow `string` for contract text fields. The split writer is covered as well, including its extra `split` text column.

No split policy or hash changed: policy `nearest_row_count`, hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.

## Interpretation

The original assertion tested pandas-to-Arrow type inference, which varies by library version. Serialization now explicitly applies the YAML contract at the Parquet boundary. The test validates the actual contract-backed output and round-trip schema rather than relying on inference. No commit or push was made.
