# T04 — Handoff readiness

T01 defined and approved 10 features; T02 implemented them and generated 1,852,394 rows; T03 quality assessment passed; T04 full-key join, model input shapes and artifact validation passed. Full regression: 23 passed, 0 failed, 0 skipped, 606 warnings. Baseline/imbalance/evaluation compatibility is interface-level because the corresponding team modules are absent. No training, sampling or evaluation was performed.

| Gate | Status |
|---|---|
| Feature artifacts and input integrity | PASS |
| One-to-one join, X/y split and baseline schema | PASS |
| Imbalance/evaluation actual module integration | PENDING — module absent |
| Past-only history and tie isolation | PASS on tests/data; deployment semantics pending |
| Reproduction guidance | Written; fresh cross-machine rebuild unverified |
| Git full inventory | BLOCKED — status/diff error |
| TECHNICAL_HANDOFF_READY | YES, for local interface use |
| GIT_HANDOFF_READY | NO |

**Decision: CONDITIONAL GO.** Team lead needs to approve generated artifact ignore/metadata sharing policy and deployment event availability/late arrivals. Toàn reviews the fixture; Git/LFS needs normal-terminal inspection. Clone at baseline HEAD alone does not contain current feature code. No stage, commit or push.

## Deliverable inventory

| Path | Purpose | Owner | Generated/Source | Proposed Git action | Review required |
|---|---|---|---|---|---|
| src/features/behavioral.py | Feature builder / validator | Trung | Source | Review and commit | Trung |
| src/features/validate_behavioral.py | Feature builder / validator | Trung | Source | Review and commit | Trung |
| tests/test_behavioral_features.py | Behavioral regression | Trung | Source | Review and commit | Trung |
| docs/trung/S1_T01_DESIGN_AUDIT.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T01_FEATURE_CONTRACT_AND_ARCHITECTURE.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T01_FEATURE_DICTIONARY.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T01_OPEN_SOURCE_FEATURE_REVIEW.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T02_FEATURE_OUTPUT_VALIDATION.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T02_HANDOFF_GUIDE.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T02_IMPLEMENTATION_REPORT.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T02_TEST_REPORT.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T03_EXECUTION_LOG.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T03_FEATURE_QUALITY_REPORT.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T03_INTEGRATION_READINESS.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T04_GIT_AND_ARTIFACT_AUDIT.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T04_INTEGRATION_AUDIT.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| docs/trung/S1_T04_REPRODUCIBILITY_GUIDE.md | Design, quality or handoff report | Trung | Documentation | Review and commit | Trung/team |
| data/features/behavioral_v1/metadata.json | Feature data / provenance | Trung | Generated | Keep Parquet out; metadata policy decision | Team lead |
| data/features/behavioral_v1/test.parquet | Feature data / provenance | Trung | Generated | Keep Parquet out; metadata policy decision | Team lead |
| data/features/behavioral_v1/train.parquet | Feature data / provenance | Trung | Generated | Keep Parquet out; metadata policy decision | Team lead |
| data/features/behavioral_v1/validation.parquet | Feature data / provenance | Trung | Generated | Keep Parquet out; metadata policy decision | Team lead |
| results/features/behavioral_v1/assessment_summary.json | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/distribution_comparison.png | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/feature_statistics.csv | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/missing_rate.png | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/novelty_rate.png | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/novelty_rates.csv | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/train_fraud_comparison.csv | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/train_pearson.csv | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/train_pearson_heatmap.png | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/train_spearman.csv | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| results/features/behavioral_v1/velocity_median.png | Quality evidence | Trung | Generated | Decide if shared through Git or artifact channel | Team lead |
| tests/test_mock_data.py | Existing fixture fix | Toàn | Existing tracked change | Do not stage with Trung work | Toàn |
| docs/data_manifest.json and results/eda/* | DE audit/EDA output | Toàn | Existing output | Separate review | Toàn |
| data/raw/fraudTrain.csv and fraudTest.csv | Source data / LFS | Toàn/team | Existing tracked LFS | Do not stage | Team lead |
| Codex workspace t03_assess.py, t03_reports.py, t04_smoke.py | Assessment/smoke scripts | Trung | Workspace source | Review and decide delivery | Trung |

| docs/trung/S1_T04_HANDOFF_READINESS.md | Final acceptance and inventory | Trung | Documentation | Review and commit | Trung/team |

The earlier `PRE_SPRINT1_ENVIRONMENT_CHECK.md` is prior environment evidence, not part of T01–T04 source; decide separately whether to publish. Full existing tracked change inventory cannot be certified until Git status works.



## T05 update — later evidence

Trung reports that in a normal Windows PowerShell session `git status --short`, `git lfs ls-files`, and `git lfs status` succeeded, the staged-name list was empty, and both LFS OIDs matched local file hashes. This is user-supplied evidence; it was not independently reproduced in the Codex sandbox, where `git status` still reports `fatal: this operation must be run in a work tree`. The exact sandbox cause remains undetermined. The narrow `/data/features/behavioral_v1/*.parquet` rule was subsequently added to `.gitignore`; current `git ls-files --others --exclude-standard data/features/behavioral_v1` lists only runtime `metadata.json`. The previous T04 statement that all three Parquet files were unignored describes the earlier check. Toàn fixture review, cross-machine reproducibility, actual Tùng/Khoa integration and deployment policy remain pending.
