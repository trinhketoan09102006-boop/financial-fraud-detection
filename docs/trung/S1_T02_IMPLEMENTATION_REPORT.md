# S1-T02 implementation report

> Finalization update: the initial blocked workspace-only state below is historical; installed artifacts passed verification as documented in the final section.

Trung approved D01–D06 on 2026-11-24. `src/features/behavioral.py` implements the ten T01 features with card/time group isolation, strict past-only histories, shared history across splits, deque windows, Welford moments, seen sets, and circular hour sums. The builder excludes target labels, validates key coverage and optional semantic split hash, and rejects production null merchant/category. CLI: `.\.venv-clean\Scripts\python.exe -m src.features.behavioral`.

Full dataset was computed successfully to `C:\Users\MSI\Documents\Codex\2026-11-22\files-pasted-by-the-user-task\behavioral_v1`, 140.53 seconds. The intended `data/features/behavioral_v1` destination is **blocked**: sandbox denied creating parent `data/features`, and the subsequent request for write permission to `data` was not granted. The first attempt finished computing but exited before writing; the second succeeded at the workspace location. No file in processed or splits was overwritten. Git status inspection failed with `fatal: this operation must be run in a work tree`; HEAD and branch were readable. Peak memory was not measured.

T02 remains **PARTIAL** until the outputs are placed at the approved repository path and all requested acceptance coverage is reviewed. No model training or additional features.

## Final verification — 2026-11-24

The four artifacts were verified in the workspace and copied to `data/features/behavioral_v1/` after write permission was granted. All four source/destination SHA-256 values matched immediately after copying. Metadata lacked an explicit null policy, so the original metadata remains backed up in the workspace and the installed metadata was augmented with `null_policy`; the builder now emits the same field on subsequent builds. Installed metadata SHA-256 after this intentional enrichment: `4fa810a1d2452ed3f5dbfdc0d01cf666b69e1c4a00939a514d66b25c4bc3fd11`; its output Parquet checksums are unchanged. No feature calculations were altered.

The original create failure was consistent with the sandbox permission boundary: `data` is a directory without read-only attribute; ACL gives `TRUNG\MSI` FullControl and `TRUNG\CodexSandboxUsers` ReadAndExecute. This session obtained scoped write access and created the requested path. Windows Controlled Folder Access could not be inspected (`Get-MpPreference` module failed to load); no conclusion is made about its configuration. Ownership is `TRUNG\MSI`, and no ACL or ownership was changed.

T02 implementation and local artifacts meet the requested verification checks. Git status remains unresolved: `fatal: this operation must be run in a work tree`. Check Git from a normal Windows terminal before staging anything. Source `.gitignore` contains no `data/features` or Parquet rule; global/exclude rules could not be verified because `git check-ignore` returned the same error. Treat feature Parquet as potentially unignored.
