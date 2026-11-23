# Pending group decisions

## Resolved: DEC-S1-01 - temporal split boundary policy

Toan explicitly requested switching to `nearest_row_count` on 2026-11-23. This policy is active in this worktree's code defaults, config, generated artifacts, and reports.

- Current hash: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.
- Cutoff: `2020-03-06T07:16:43`.
- Current counts: train 1,037,340; validation 259,335; test 555,719.
- Exactly one transaction (`408a69cd781df5546489ecb28a2007ea`, `2020-03-06T07:15:17`) moved validation -> train relative to former hash `70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255`.
- Downstream feature/model/evaluation outputs must use one consistent split hash. This records the requester's decision; it does not claim broader project sign-off.

## DEC-S1-02 - Confirm source timezone and currency conventions

- **Issue:** Sparkov files do not declare timezone or currency.
- **Recommendation:** retain timezone-naive timestamps and source-relative amount units until a documented source decision exists.
- **Impact:** hour-of-day and amount units remain source-relative; do not convert or label as USD without evidence.
- **Status:** `PENDING`; no contract change made.

## DEC-S1-03 - Locate missing remaining-work input

- **Issue:** `TOAN_SPRINT1_REMAINING_WORK.md` was required by the task but is not present in the repository. It was not read or audited.
- **Action:** provide the approved file before claiming its checklist has been completed.
- **Status:** `BLOCKED` on missing document.

## DEC-S1-04 - Restore GitHub read access for remote verification

- **Issue:** safe fetch returned `Repository not found`; the configured URL may require credentials or may no longer identify the repository.
- **Impact:** local remote-tracking refs may be stale; no GitHub state is certified here.
- **Status:** `BLOCKED`; no remote mutation attempted.
