# S1-T03 — Integration readiness

**Verdict: CONDITIONAL GO.** Ten fixed feature names and order, exact Arrow types, checksums, split hash and ID coverage pass on all 1,852,394 rows. The approved output is `data/features/behavioral_v1/{train,validation,test}.parquet`, one row per `trans_num`, with metadata in the same directory. Canonical source is `data/processed/transactions.parquet`, split assignment `data/splits/split_manifest.parquet`.

Tú/Tùng: load matching split, validate checksum and split hash, join transaction labels and features by `trans_num` with one-to-one validation and equal coverage. Exclude ID, card, target, source metadata and split from X. Undefined history remains NaN; fit imputation/encoding/scaling only on train. Tùng samples or weights training only. Khoa keys scores with `trans_num`, records split, model, feature version and split hash. See `S1_T02_HANDOFF_GUIDE.md`.

Strict past-only and same-timestamp isolation pass artifact checks plus existing T02 synthetic leakage tests; no labels are used by feature generation. The observed-history policy assumes earlier validation/test non-target transactions are available when later events are scored; online replay, watermark and late-event behavior need operational validation. Source timezone/currency remain unspecified.

**Outstanding:** Git status and ignore resolution failed with `fatal: this operation must be run in a work tree`; `.gitignore` does not explicitly ignore `data/features`. Check before staging, review Toàn's existing test change and generated EDA/manifest, and resolve LFS status. No test split labels were used for feature selection or model training.
