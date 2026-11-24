# S1-T02 test report

Full suite before the last two new tests: `.venv-clean\Scripts\python.exe -m pytest -q -rs -p no:cacheprovider`: exit 0, **18 passed**, including 14 existing tests and four new tests; 604 existing Pandas4Warning deprecations. After adding two boundary/circular tests, targeted test file was rerun: **6 passed**, exit 0. The final complete 20-test suite was not rerun.

New tests compare hand-computed cold start, counts, population amount moments, ratios, recency, novelty, ties, card isolation, history across splits, future injection, label perturbation, permutations, duplicate ID, missing manifest, bad hash, invalid/null input, zero mean, seven-day nanosecond boundary, circular midnight and opposite-hour cancellation. Tests are synthetic. Full artifact keyed IDs, checksums, and Arrow schemas were checked separately. Additional dedicated tests for each 1h/24h outside-boundary and CLI metadata round-trip remain desirable before T02 acceptance.

## Final verification — 2026-11-24

Exact command `.\.venv-clean\Scripts\python.exe -m pytest -q -rs`: exit 0, **23 passed, 0 failed, 0 errors, 0 skipped**, 606 warnings, 66.72 seconds. This includes 14 legacy and 9 behavioral tests (three independently parameterized 1h/24h/7d boundary cases). Each boundary case checks one nanosecond outside, the inclusive lower bound, and two same-card events at anchor. Existing 604 pandas warnings remain; one new pandas duration warning and one sandbox pytest-cache warning are non-blocking. Integration test passed.

Separate validation CLI: `.\.venv-clean\Scripts\python.exe -m src.features.validate_behavioral` returned exit 0 on installed artifacts, including input/output checksums and manifest one-to-one coverage. A copied metadata fixture with a deliberately wrong split hash returned exit 1 and `ValueError: metadata split hash mismatch`. Prior unit tests also exercise invalid input, manifest and hash errors, equal timestamps, cross-card, future injection, changed labels, permutation, and cross-split history.
