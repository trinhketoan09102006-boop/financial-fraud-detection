# S1-T02 handoff guide

The current generated files are in `C:\Users\MSI\Documents\Codex\2026-11-22\files-pasted-by-the-user-task\behavioral_v1`. The planned repository destination `data/features/behavioral_v1` awaits permission to create `data/features`.

Read `metadata.json` and verify split hash against `configs/split.yaml` and the SHA-256 for each Parquet. Read the matching split Parquet and join to `data/splits/{split}.parquet` by `trans_num` with `validate="one_to_one"`; check equal row counts and no unmatched IDs. Use feature columns in `metadata.feature_order`; remove `trans_num`, `cc_num`, target `is_fraud`, `split` and `source_dataset` from X. Obtain y separately from the data split. Undefined historical values are NaN; fit any imputer and encoder on train only, then apply the fitted transform to validation/test. Tùng applies sampling or class weights to train only.

To rebuild after fixing destination permissions, from repository root run `.\.venv-clean\Scripts\python.exe -m src.features.behavioral`. The command refuses a nonempty destination; preserve an existing artifact first. To use another empty destination, pass `--output <path>`. Track input/output checksums and the semantic split hash; source timestamps remain timezone-naive and amounts retain source units. Online late-event handling is a design requirement and is not implemented by this offline builder.

## Final verification update

The four artifacts are now installed at `data/features/behavioral_v1/`. Validate them before use with `.\.venv-clean\Scripts\python.exe -m src.features.validate_behavioral`; a mismatch exits nonzero. This command reads the installed metadata and current processed and split inputs; it does not regenerate features. Metadata now records the production rejection of null merchant/category and the undefined-history NaN policy. The workspace metadata remains the backup made before this metadata-only addition.

The repository `.gitignore` does not itself list `data/features/`; `git check-ignore` failed in this environment. Keep feature Parquet out of staging until ignore policy is verified. Git status also failed with `fatal: this operation must be run in a work tree`; perform status review in a normal Windows terminal. In addition to the two feature source files and behavioral test file, review T01/T02 documents, Toàn's pre-existing test fixture change, raw CSV LFS status, and earlier manifest/EDA changes before any commit.
