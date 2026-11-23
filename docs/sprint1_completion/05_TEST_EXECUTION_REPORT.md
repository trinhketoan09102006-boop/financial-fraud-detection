# Test execution report

## Full suite on the nearest-row-count data

The full raw-to-split pipeline was regenerated in the current `sprint1-completion` worktree before testing. Then:

```text
python -m pytest -q -rs
13 passed, 1 warning in 21.32s
EXIT_CODE=0
SKIPPED=0
```

The only warning is a third-party `PytestRemovedIn10Warning` from the installed AnyIO pytest plugin (`CallSpec2` is deprecated). The integration test read the generated artifacts and checked source hashes, row counts, `unix_time` reconstruction, schema exclusions, split chronology, ID disjointness, timestamp-group atomicity, manifest hash, and the current `nearest_row_count` hash.

Pytest log: `sprint1_completion_evidence_20261122\pytest_nearest_row_count_20261123.log`.

## Other checks

| Check | Result |
|---|---|
| `python -m compileall -q src tests` | PASS |
| `python -m pip check` | PASS; no broken requirements |
| Parse repository JSON/YAML files | PASS |
| Mock fixture tests | PASS; 300 deterministic synthetic records, schema field/type match |
| Timestamp-unit regression (`s`, `ms`, `us`, `ns`) | PASS |
| Notebook code cells | 2/2 executed; no error outputs |
| Notebook process | exit code 0 |

The notebook was separately executed after the new split was generated. It produced ten charts using only the training split. The execution log and executed notebook are outside the repository under `sprint1_completion_evidence_20261122/`: `notebook_nearest_row_count_20261123.log` and `01_data_understanding_nearest_row_count_executed.ipynb`. A non-fatal Windows ZeroMQ/Proactor event-loop warning appeared after execution.

These results are from the current feature worktree with local ignored processed/split Parquet artifacts present. The artifacts and logs are verification evidence, not Git-tracked handoff files. Earlier 13-pass results from the external validation project used the former split baseline; this run specifically verifies the new split.
