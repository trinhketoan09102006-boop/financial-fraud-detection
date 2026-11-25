# S1-T03 — Feature Quality Assessment

## Executive summary

**COMPLETE, conditional handoff.** Direct inspection of all 1,852,394 rows shows artifact integrity, schema, one-to-one manifest coverage and the requested behavioral invariants pass. Ten feature definitions remain unchanged. Git status remains unavailable in this environment, so repository handoff is conditional. This is descriptive analysis, not model performance or feature selection.

## Integrity

All four files exist; SHA-256 of each Parquet matches metadata, processed/manifest input checksums match metadata, feature version and order match T01, and split hash matches config, metadata, and independently calculated manifest. Three Arrow count fields are int32, seven other features float64, ID Arrow string; no target/card/source/split predictor occurs. IDs are non-null/unique and exactly cover each manifest split, counts train 1,037,340, validation 259,335, test 555,719. No source or feature artifact was written by assessment. Full hashes and run details are in the execution log.

## Statistics and distribution

Complete per-feature/per-split statistics including valid/missing counts and rates, infinities, min/max, mean, median, sample standard deviation (ddof=1), P01/P05/P25/P75/P95/P99, zero fraction of all rows and unique non-null counts are in `results/features/behavioral_v1/feature_statistics.csv`. Zero rate uses all rows as denominator, with missing included in denominator. The table below shows summary values; units remain as specified by T01.

| split | feature | mean | median | p95 | p99 | missing_rate | zero_rate_all_rows |
|---|---|---|---|---|---|---|---|
| train | txn_count_1h | 0.1926 | 0 | 1 | 2 | 0 | 0.8339 |
| train | txn_count_24h | 3.941 | 3 | 10 | 14 | 0 | 0.08457 |
| train | txn_count_7d | 25.42 | 23 | 53 | 72 | 0 | 0.001165 |
| train | hist_amt_mean | 70.4 | 65.01 | 98.76 | 116.5 | 0.0009293 | 0 |
| train | hist_amt_std | 129.6 | 111.6 | 263.9 | 488.3 | 0.0009293 | 0.0009293 |
| train | amt_ratio | 1.025 | 0.6658 | 2.716 | 7.488 | 0.0009293 | 0 |
| train | txn_recency | 3.247e+04 | 1.64e+04 | 1.146e+05 | 2.346e+05 | 0.0009293 | 0 |
| train | is_new_merchant | 0.4264 | 0 | 1 | 1 | 0 | 0.5736 |
| train | is_new_category | 0.01253 | 0 | 0 | 1 | 0 | 0.9875 |
| train | hour_deviation | 5.204 | 4.748 | 11.18 | 11.83 | 0.0009293 | 0 |
| validation | txn_count_1h | 0.1772 | 0 | 1 | 2 | 0 | 0.8447 |
| validation | txn_count_24h | 3.658 | 3 | 9 | 12 | 0 | 0.08173 |
| validation | txn_count_7d | 23.83 | 23 | 44 | 52 | 0 | 0.0002275 |
| validation | hist_amt_mean | 70.33 | 65.15 | 96.2 | 102.5 | 7.326e-05 | 0 |
| validation | hist_amt_std | 139.9 | 121.1 | 266.5 | 423.3 | 7.326e-05 | 7.326e-05 |
| validation | amt_ratio | 1.007 | 0.6746 | 2.631 | 7.316 | 7.326e-05 | 0 |
| validation | txn_recency | 3.254e+04 | 1.719e+04 | 1.125e+05 | 2.26e+05 | 7.326e-05 | 0 |
| validation | is_new_merchant | 0.1416 | 0 | 1 | 1 | 0 | 0.8584 |
| validation | is_new_category | 0.0003663 | 0 | 0 | 0 | 0 | 0.9996 |
| validation | hour_deviation | 5.186 | 4.72 | 11.17 | 11.83 | 7.326e-05 | 0 |
| test | txn_count_1h | 0.2244 | 0 | 1 | 2 | 0 | 0.8101 |
| test | txn_count_24h | 4.639 | 4 | 11 | 16 | 0 | 0.06167 |
| test | txn_count_7d | 29.75 | 27 | 61 | 80 | 0 | 8.997e-05 |
| test | hist_amt_mean | 70.05 | 64.65 | 96.02 | 101.2 | 2.879e-05 | 0 |
| test | hist_amt_std | 141.8 | 124.9 | 263.4 | 401.7 | 2.879e-05 | 2.879e-05 |
| test | amt_ratio | 0.9949 | 0.6685 | 2.584 | 6.818 | 2.879e-05 | 0 |
| test | txn_recency | 2.734e+04 | 1.388e+04 | 9.598e+04 | 1.943e+05 | 2.879e-05 | 0 |
| test | is_new_merchant | 0.09043 | 0 | 1 | 1 | 0 | 0.9096 |
| test | is_new_category | 0.0001494 | 0 | 0 | 0 | 0 | 0.9999 |
| test | hour_deviation | 5.184 | 4.719 | 11.17 | 11.83 | 2.879e-05 | 0 |

Novelty rates (denominator all rows):

| split | feature | rate_0 | rate_1 | rate_nan |
|---|---|---|---|---|
| train | is_new_merchant | 0.5736 | 0.4264 | 0 |
| train | is_new_category | 0.9875 | 0.01253 | 0 |
| validation | is_new_merchant | 0.8584 | 0.1416 | 0 |
| validation | is_new_category | 0.9996 | 0.0003663 | 0 |
| test | is_new_merchant | 0.9096 | 0.09043 | 0 |
| test | is_new_category | 0.9999 | 0.0001494 | 0 |

Merchant novelty falls from 42.64% train to 14.16% validation and 9.04% test, consistent with growing observed history as a possible contributor; no causal attribution is established. Median 7-day counts are 23, 23 and 27; median ratio is 0.666, 0.675 and 0.669. Train-derived P99 clipping is used only for comparable chart display, not to change data or fit preprocessing. These are descriptive time-split differences; no arbitrary drift threshold, PSI, or test-driven selection is used.

## Missing and behavioral plausibility

All 999 cards have one earliest event: 999 cold-start rows. Each of mean, std, ratio, recency and hour deviation has exactly 999 missing values, all on those earliest rows; zero missing in non-cold rows. This directly supports cold-start as their observed cause in this dataset; it does not establish that other undefined cases cannot occur in future data. Production merchant/category inputs have no nulls, novelty outputs are 0/1 without missing. Amounts are positive. There are zero infinities, negative counts/amount mean/std/ratio, nonpositive defined recencies, out-of-range hours, or count-order violations. Counts are int32. There are zero cold-start violations for count, history, recency or novelty.

All **44** tied card/timestamp groups (88 rows) were checked: counts, historical mean/std, recency and hour deviation have the same pre-group values, including matching NaN; zero violating groups. Ratio and novelty can depend on the current transaction and were not required to be equal. Existing T02 synthetic tests also address future injection, ties, card isolation and label independence; this data inspection does not establish online availability or parity.

## Correlation — train only

Pearson and Spearman use pairwise complete observations; NaNs are not imputed. Full 10×10 matrices are `train_pearson.csv` and `train_spearman.csv`. There are no pairs with |r| >= 0.9 in either matrix (this is a descriptive flag, not a selection rule). Pearson/Spearman respectively: 1h vs 24h 0.342/0.308; 24h vs 7d 0.703/0.686; historical mean vs std 0.313/0.372; historical mean vs ratio -0.032/-0.001; std vs ratio -0.034/-0.107; merchant vs category novelty 0.131/0.131. No feature is removed.

## Fraud relevance — train labels only

Train has 1,031,372 normal and 5,968 fraud rows; feature calculation did not access labels. Detailed descriptive comparisons are in `train_fraud_comparison.csv`. The table shows means and medians; differences may be affected by skew, time and limited fraud sample. No validation/test labels were read for this section.

| label | feature | rows | mean | median |
|---|---|---|---|---|
| 0 | txn_count_1h | 1031372 | 0.1899 | 0 |
| 0 | txn_count_24h | 1031372 | 3.939 | 3 |
| 0 | txn_count_7d | 1031372 | 25.46 | 23 |
| 0 | hist_amt_mean | 1031372 | 70.13 | 64.99 |
| 0 | hist_amt_std | 1031372 | 129.4 | 111.6 |
| 0 | amt_ratio | 1031372 | 0.9907 | 0.6624 |
| 0 | txn_recency | 1031372 | 3.254e+04 | 1.646e+04 |
| 0 | is_new_merchant | 1031372 | 0.4256 | 0 |
| 0 | is_new_category | 1031372 | 0.01224 | 0 |
| 0 | hour_deviation | 1031372 | 5.203 | 4.743 |
| 1 | txn_count_1h | 5968 | 0.6709 | 0 |
| 1 | txn_count_24h | 5968 | 4.258 | 4 |
| 1 | txn_count_7d | 5968 | 18.63 | 17 |
| 1 | hist_amt_mean | 5968 | 117.3 | 72.13 |
| 1 | hist_amt_std | 5968 | 157 | 125.2 |
| 1 | amt_ratio | 5968 | 6.938 | 5.164 |
| 1 | txn_recency | 5968 | 2.132e+04 | 4790 |
| 1 | is_new_merchant | 5968 | 0.5729 | 1 |
| 1 | is_new_category | 5968 | 0.062 | 0 |
| 1 | hour_deviation | 5968 | 5.436 | 5.356 |

For example, median amount ratio is 0.662 for normal and 5.164 for fraud; merchant novelty fraction is 42.56% vs 57.29%. These are observational associations on train and do not prove improvements in PR-AUC or recall. Small fraud subgroups, including novel category fraud events, warrant caution; no threshold is fitted.

## Limits

Sparkov is simulated, timestamp timezone and amount currency are unspecified. Cross-split history assumes preceding non-target events are observable at scoring time. Review Git/LFS and unreviewed Toàn fixture before handoff. Output visuals: five PNGs in `results/features/behavioral_v1/`; `distribution_comparison.png` clips at train P99 for display.
