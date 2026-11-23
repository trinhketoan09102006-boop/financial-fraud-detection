# Git and data safety

## Repository state

- Original project worktree: branch `toan`, HEAD `af693e0274ddfb9d7f4b57b13f6872b95680bfe9`, preserved separately.
- Work was isolated in branch `sprint1-completion`, based on local `main` at the same baseline. Changes remain uncommitted for review.
- No commit, push, merge, PR, reset, clean, stash, history rewrite, or branch deletion was performed.
- Configured remote: `https://github.com/trinhketoan09102006-boop/financial-fraud-detection.git`.
- Safe fetch returned `Repository not found`; GitHub state and remote branch freshness are unverified.

## LFS, ignore rules, and data

- Raw SHA-256 values before and after regeneration are unchanged: train `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d`; test `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`.
- Both raw CSVs remain Git LFS tracked. `.gitattributes` scope is `data/raw/*.csv`; mock and EDA summary CSVs are not covered.
- `.gitignore` excludes raw, processed, split, and artifact data while preserving `.gitkeep` files.
- Current generated Parquet files physically exist in `data/processed/` and `data/splits/`. They are ignored and untracked; only `.gitkeep` files in those folders are Git-tracked. Do not stage the Parquet files.
- Current split metadata and EDA outputs use `nearest_row_count`, hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.

These are local verification artifacts, not committed/shared deliverables. They can be regenerated with `python -m src.data.pipeline --stage all` when the raw inputs are available. No raw file, Git LFS tracking rule, or Git history was modified.
