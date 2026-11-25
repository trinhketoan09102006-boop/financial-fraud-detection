# T01 — Behavioral feature dictionary

> **APPROVED_FOR_T02:** Trung đã phê duyệt D01–D06 ngày 24/11/2026 trong yêu cầu S1-T02. Các dòng đề xuất hoặc chờ quyết định bên dưới là lịch sử T01; quyết định được duyệt trong yêu cầu T02 có hiệu lực.

**Status:** design proposal for Trung; no feature values have been generated. These ten names and missing-value rules are proposed, not yet team-approved. Inputs are the normalized `data/processed/transactions.parquet` contract. For anchor row `i`, let `c_i=cc_num_i`, `t_i=timestamp_i`, `a_i=amt_i`, and `H_i={j: cc_num_j=c_i and timestamp_j<t_i}`. The current row is excluded from history. For tied `(cc_num,timestamp)` rows, compute every feature from the identical pre-group state, then insert the entire group. No label, model prediction, `source_dataset`, split name, row index, or `trans_num` ordering enters any formula. `trans_num` is only an output join key and deterministic sort tie-breaker.

`timestamp` is Arrow `timestamp[ns]`, timezone-naive, parsed from `trans_date_trans_time`. `cc_num`, `merchant`, `category` are Arrow strings; `amt` is float64, finite and positive in the audited source. All historical statistics use only earlier observed transactions, even across temporal split boundaries. Intervals use nanosecond comparisons. Count windows are inclusive at the lower bound and exclusive at the anchor. `NaN` means undefined, not zero; downstream imputation belongs to a train-fitted model preprocessing step. Any current null `merchant` or `category` yields `NaN` for its novelty flag; null historical values are ignored for that category's seen set. No synthetic missing-value token is treated as a real merchant/category.

| ID | Feature | Group | Output | Window | Cold start |
|---|---|---|---|---|---|
| F01 | `txn_count_1h` | velocity | int32, transactions | `[t-1h,t)` | 0 |
| F02 | `txn_count_24h` | velocity | int32, transactions | `[t-24h,t)` | 0 |
| F03 | `txn_count_7d` | velocity | int32, transactions | `[t-7d,t)` | 0 |
| F04 | `hist_amt_mean` | amount | float64, source amount unit | all `H_i` | NaN |
| F05 | `hist_amt_std` | amount | float64, source amount unit | all `H_i` | NaN |
| F06 | `amt_ratio` | amount | float64, unitless | all `H_i` | NaN |
| F07 | `txn_recency` | temporal | float64, seconds | all `H_i` | NaN |
| F08 | `is_new_merchant` | novelty | float64, 0/1/NaN | all `H_i` | 1 when current value is valid |
| F09 | `is_new_category` | novelty | float64, 0/1/NaN | all `H_i` | 1 when current value is valid |
| F10 | `hour_deviation` | temporal | float64, hours in `[0,12]` | all `H_i` | NaN |

The `float64` novelty outputs encode a nullable indicator without a separate sentinel. If an implementation uses a nullable integer in memory, it must serialize values, nulls, and model inputs consistently. All count outputs must be checked for int32 overflow before cast; 1,852,394 total rows are below the limit in this dataset.

## F01 — `txn_count_1h`

- **Business meaning/input/formula:** recent card velocity. Input: `cc_num`, `timestamp`. `|{j in H_i: t_i - 1 hour <= t_j}|`.
- **Null/edge/same time:** required keys cannot be null; reject invalid keys or timestamps. At exactly one hour before anchor count the event; equal-time events do not count. Cold start 0. Multiple events in a historical timestamp group each count after that group has committed.
- **Leakage/test/complexity/integration:** never include anchor or later/equal events. Test `t-1h`, `t-1h-1ns`, and tied anchors. A per-card deque with an inclusive lower-bound eviction gives amortized O(1) per event, O(number of events within 1h) state; can share the 7d deque. Pass as numeric model input after keyed join.

## F02 — `txn_count_24h`

- **Business meaning/input/formula:** one-day card velocity. Input: `cc_num`, `timestamp`. `|{j in H_i: t_i - 24 hours <= t_j}|`.
- **Null/edge/same time:** same key validation and equal-time isolation as F01; exactly 24 hours old counts, older by 1 ns does not. Cold start 0. This is elapsed 24 hours, not local calendar day.
- **Leakage/test/complexity/integration:** future injection must leave earlier counts unchanged. Shared 7d deque and moving cursor: amortized O(1) per event, state O(events in 7d). Numeric feature; do not normalize using validation/test statistics.

## F03 — `txn_count_7d`

- **Business meaning/input/formula:** week-scale card velocity. Input: `cc_num`, `timestamp`. `|{j in H_i: t_i - 7 days <= t_j}|`.
- **Null/edge/same time:** 7 days means 168 elapsed hours, not calendar week. Exact lower boundary counts; same-timestamp batch does not. Cold start 0.
- **Leakage/test/complexity/integration:** reject any result dependent on equal/future records. Per-card deque: amortized O(1) insert/expire per event, O(events in last 7d) state. Numeric feature.

## F04 — `hist_amt_mean`

- **Business meaning/input/formula:** usual amount for the card. Input: `cc_num`, `timestamp`, historical `amt`. For `n=|H_i|>0`, `mu_i=(sum_{j in H_i} a_j)/n`.
- **Null/edge/same time:** no history -> NaN. Contract marks amount non-null; reject non-finite amount if contract violated. The current amount and tied-group amounts do not enter `mu_i`; zero and large amounts, if admitted by future data, remain literal values.
- **Leakage/test/complexity/integration:** first row NaN; next timestamp sees prior amount only; tied rows share mean. Running mean update O(1)/event, O(1)/card. Train-fitted missing imputation only.

## F05 — `hist_amt_std`

- **Business meaning/input/formula:** historical amount variability. Input: `cc_num`, `timestamp`, historical `amt`. Population deviation `sqrt(sum_{j in H_i}(a_j-mu_i)^2/n)` (`ddof=0`).
- **Null/edge/same time:** no history -> NaN; one historical event -> 0. Reject non-finite input; clamp tiny negative floating variance to zero. Tied anchors share the same pre-group statistic.
- **Leakage/test/complexity/integration:** compare two known amounts against population, not sample, deviation; future amount must not alter prior values. Welford `(n,mean,M2)` update O(1)/event, O(1)/card; numeric input with train-fitted missing handling.

## F06 — `amt_ratio`

- **Business meaning/input/formula:** size of current transaction relative to past mean. Input: current `amt`, `cc_num`, `timestamp`, F04. `a_i/mu_i` only when `n>0`, `mu_i` finite, and `mu_i != 0`.
- **Null/edge/same time:** no history or zero historical mean -> NaN; never use epsilon or infinity as an implicit substitute. Reject non-finite current amount. Tied anchors may have different numerators but share the same past denominator.
- **Leakage/test/complexity/integration:** test cold start, zero mean, and two tied anchors with different amounts. O(1) per event after F04; unitless numeric input. Source has positive amounts, but zero-mean behavior is defined for robustness.

## F07 — `txn_recency`

- **Business meaning/input/formula:** time since the last earlier card event. Input: `cc_num`, `timestamp`. `(t_i - max_{j in H_i} t_j).total_seconds()`.
- **Null/edge/same time:** no history -> NaN. Strictly positive for valid history; tied rows cannot produce zero recency by observing each other. Preserve subsecond precision from `timestamp[ns]`.
- **Leakage/test/complexity/integration:** test prior timestamp, tied timestamp, and a later injected event. Keep last committed timestamp per card: O(1)/event and O(1)/card. Numeric input; avoid treating missing as zero.

## F08 — `is_new_merchant`

- **Business meaning/input/formula:** unfamiliar merchant for the card. Input: current/historical `merchant`, `cc_num`, `timestamp`. If current merchant is non-null, `1[merchant_i not in {merchant_j: j in H_i, merchant_j non-null}]`.
- **Null/edge/same time:** current null -> NaN, even on cold start; historical null adds nothing. Valid current value on a new card -> 1. Empty string remains a distinct valid string unless upstream contract changes. Two tied transactions at the same new merchant both return 1.
- **Leakage/test/complexity/integration:** test repeated merchant at later time and tied new merchant; never consult global merchants from another card. Per-card seen set: expected O(1) lookup/update, total memory O(distinct card-merchant pairs). Nullable numeric 0/1/NaN; model imputation fit on train.

## F09 — `is_new_category`

- **Business meaning/input/formula:** unfamiliar spending category for the card. Input: current/historical `category`, `cc_num`, `timestamp`. If current category is non-null, `1[category_i not in {category_j: j in H_i, category_j non-null}]`.
- **Null/edge/same time:** current null -> NaN; historical null ignored; valid value with no history -> 1. A pair of tied first occurrences both return 1. Empty string is valid unless an upstream decision changes that interpretation.
- **Leakage/test/complexity/integration:** test first/repeated category and cross-card isolation. Expected O(1) per lookup/update, memory O(distinct card-category pairs). Nullable numeric model input.

## F10 — `hour_deviation`

- **Business meaning/input/formula:** shortest circular distance from the card's historical typical time of day. Input: `cc_num`, `timestamp`; use fractional hour `h=hour+minute/60+second/3600+microsecond/3.6e9+nanosecond/3.6e12` from the timezone-naive canonical timestamp. For each `j in H_i`, let `theta_j=2*pi*h_j/24`; maintain `C=sum cos(theta_j)`, `S=sum sin(theta_j)`. If `n>0` and `R=hypot(C,S)>epsilon*n`, historical circular mean angle is `theta_bar=atan2(S,C) mod 2*pi`, converted to hour `h_bar`. Output `min(|h_i-h_bar|,24-|h_i-h_bar|)` hours.
- **Null/edge/same time:** no history -> NaN. Nearly cancelling opposite-hour history (`R<=epsilon*n`) has no stable usual hour -> NaN; proposed `epsilon=1e-12`. 23:00 versus 00:00 is 1 hour, not 23. Tied anchors see identical `(C,S,n)` before group update.
- **Leakage/test/complexity/integration:** test 23:00/00:00, 23:00+01:00 mean near midnight, opposite-hour cancellation, and future injection. O(1) update/query per event, O(1)/card. Numeric `[0,12]`; no UTC conversion because source timezone is unknown. Definition and epsilon need Trung/team sign-off before T02.

## Shared acceptance checks

For all ten outputs: output exactly one row per unique input `trans_num`; neither `is_fraud` nor any label-derived statistic enters history; a future row cannot alter an earlier row; row order permutation cannot alter results; same-card equal-time rows share pre-group state; other cards never influence a card; history may continue across approved split boundaries. Inputs violating unique/non-null `trans_num`, non-null `cc_num`/`timestamp`, valid numeric `amt`, or one-to-one manifest coverage fail validation rather than silently changing semantics. All formulas are independent of target labels.
