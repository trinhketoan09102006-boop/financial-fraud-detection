# Git and data safety

## Repository state

- Historical Sprint 1 audit snapshot: branch `toan`, HEAD `0515b4b3c87431e1dae39c50f012b211385442d6`; cached refs at that audit were `origin/toan=0515b4b3c87431e1dae39c50f012b211385442d6` and `origin/main=9648beb5ef87f1b1daf8feb5af4ac852fdd0e524`. No fetch was performed, so those remote refs were not verified as current.
- Current cross-version schema review: branch remains `toan`, HEAD is `ae0294f7890905101374f9f1f2a030703cffa71e`. Compatibility fix and report changes are in the uncommitted working tree; there are no staged files.
- A pre-existing linked worktree registration is marked `prunable`; it was not altered.
- No commit, push, merge, PR, fetch, reset, clean, stash, history rewrite, branch creation, or branch deletion was performed during this review.

## LFS and ignore rules

- `.gitattributes` applies LFS to `data/raw/*.csv`; mock CSV is not LFS-filtered.
- `git lfs ls-files` reports the two raw CSVs. `git lfs fsck` passed.
- Raw SHA-256 values before and after both full pipeline runs are unchanged: train `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d`; test `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`.
- `.gitignore` excludes `data/raw`, `data/processed`, and `data/splits` contents while preserving `.gitkeep` files. Generated Parquet files and the reproducibility snapshots are ignored and not Git-tracked.
- `git ls-files data/processed data/splits` contains only `.gitkeep` files.

No raw file, LFS tracking rule, remote ref, or Git history was modified.
