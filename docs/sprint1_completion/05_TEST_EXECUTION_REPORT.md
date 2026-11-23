# Test execution report

## Baseline before artifact generation

The worktree initially contained no processed/split Parquet artifacts. `python -m pytest -q -ra` therefore reported 12 passed, 1 skipped, 0 failed; the integration test skipped with the explicit reason that processed Parquet was missing. Log: `09_initial_pytest_baseline.txt`.

The previously supplied summary mentioned one failed test but omitted its name and traceback. A controlled Arrow fixture reproduced the contract failure (`large_string` where `string` was expected); its traceback is `09_arrow_schema_failure_reproduction.txt`. This is a reproduction of the reported failure mode, not a claim that it is the omitted historical test.

## Final suite after rebuild

After the full pipeline generated current `nearest_row_count` artifacts:

```powershell
python -m pytest -q -rs
```

```text
14 passed, 1 warning in about 21s
EXIT_CODE=0
SKIPPED=0
FAILED=0
```

The 14 tests include the full-data integration test, timestamp precision checks, split regression coverage, synthetic mock tests, and the Arrow `large_string` to contract `string` regression. Full log: `10_pytest_final.txt`.

The only warning is a third-party AnyIO `PytestRemovedIn10Warning` about the deprecated `_pytest.python.CallSpec2` alias. There were no failed or skipped tests in the final run.

## Other checks

| Check | Result |
|---|---|
| `python -m compileall -q src tests` | PASS |
| `python -m pip check` | PASS; no broken requirements |
| Contract schema read from processed Parquet | PASS; exact match across 25 fields |
| Raw-to-processed ID and `cc_num` comparison | PASS; 1,852,394 rows joined 1:1 and `cc_num` identical |
| Notebook | PASS; 2/2 code cells, exit 0, no cell errors |

Notebook log: `10_notebook_execution.txt`; validation summary: `10_notebook_validation.json`. The Windows ZeroMQ Proactor warning was non-fatal. The first launcher attempt could not create Jupyter config under the protected user profile; a rerun with config/runtime directories in the ignored repository staging folder completed successfully. Notebook source was not overwritten.
