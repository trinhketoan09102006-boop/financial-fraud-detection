# Data audit

Full-file audit of `fraudTrain.csv` and `fraudTest.csv`. No direct identifiers or raw values are reported.

Canonical event time is `trans_date_trans_time`, parsed as timezone-naive `timestamp`. Full-file checks verify `unix_time` exactly reconstructs this field only after adding seven calendar years; it is excluded from normalized data. See warning code `UNIX_TIME_STALE_BY_7_CALENDAR_YEARS`.

## File inventory

| File | Rows | Columns | Size (bytes) | SHA-256 |
|---|---:|---:|---:|---|
| `fraudTrain.csv` | 1,296,675 | 23 | 351,238,196 | `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d` |
| `fraudTest.csv` | 555,719 | 23 | 150,354,339 | `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0` |

## Findings

| Status | Check | Detail |
|---|---|---|
| **PASS** | `schema_match` | Both files have the same columns. |
| **PASS** | `reference_rows:fraudTrain.csv` | Observed 1,296,675; reference 1,296,675. |
| **PASS** | `transaction_id_integrity:fraudTrain.csv` | Duplicate IDs=0; missing/blank IDs=0. |
| **PASS** | `label_domain:fraudTrain.csv` | Invalid/missing labels=0. |
| **PASS** | `timestamp_parse:fraudTrain.csv` | Unparseable timestamps=0. |
| **WARNING** | `card_number_format:fraudTrain.csv` | Missing, non-digit, or shorter than 12-digit identifiers=6,111; values are preserved as strings and not used as model inputs. |
| **WARNING** | `source_timestamp_order:fraudTrain.csv` | Timestamp decreases in original row order=1; the preprocessor sorts by parsed timestamp. |
| **PASS** | `reference_rows:fraudTest.csv` | Observed 555,719; reference 555,719. |
| **PASS** | `transaction_id_integrity:fraudTest.csv` | Duplicate IDs=0; missing/blank IDs=0. |
| **PASS** | `label_domain:fraudTest.csv` | Invalid/missing labels=0. |
| **PASS** | `timestamp_parse:fraudTest.csv` | Unparseable timestamps=0. |
| **WARNING** | `card_number_format:fraudTest.csv` | Missing, non-digit, or shorter than 12-digit identifiers=2,708; values are preserved as strings and not used as model inputs. |
| **PASS** | `source_timestamp_order:fraudTest.csv` | Timestamp decreases in original row order=0; the preprocessor sorts by parsed timestamp. |
| **PASS** | `cross_file_transaction_ids` | Shared transaction IDs=0. |
| **PASS** | `test_after_train` | train max=2020-06-21T12:13:37; test min=2020-06-21T12:14:25; strict ordering=True. |
| **WARNING** | `UNIX_TIME_STALE_BY_7_CALENDAR_YEARS` | All 1,852,394 records reconstruct exactly when unix_time (seconds since epoch, interpreted UTC) is advanced by seven calendar years. Excluded from normalized data; raw CSVs remain unchanged. Offset seconds observed: 220,838,400 to 220,924,800. |
| **PASS** | `cross_file_card_overlap` | Shared cards=901; card overlap alone is not leakage when prior history is used temporally. |

## Quality summary: `fraudTrain.csv`

- Target counts: `{'0': 1289169, '1': 7506}`
- Duplicate complete rows: 0
- Duplicate transaction IDs: 0
- Card identifiers outside the 12-19 digit PAN-like range: 6,111 (preserved as strings; synthetic IDs may not be actual PANs)
- Canonical text timestamp range: 2019-01-01T00:00:18 to 2020-06-21T12:13:37
- Source timestamp decreases in row order: 1
- Adjacent equal timestamps: 21,852
- Unix epoch timestamp range: 2012-01-01T00:00:18+00:00 to 2013-06-21T12:13:37+00:00
- `trans_date_trans_time` minus `unix_time` offsets (seconds): `{'220924800': 372364, '220838400': 924311}`
- Rows reconstructed exactly after adding seven calendar years to UTC unix_time: 1,296,675/1,296,675
- unix_time decreases in source order: 0
- Negative/zero/invalid amounts: 0/0/0
- Invalid coordinates: 0
- Invalid or future DOB: 0/0
- Missing values by column: `{'Unnamed: 0': 0, 'trans_date_trans_time': 0, 'cc_num': 0, 'merchant': 0, 'category': 0, 'amt': 0, 'first': 0, 'last': 0, 'gender': 0, 'street': 0, 'city': 0, 'state': 0, 'zip': 0, 'lat': 0, 'long': 0, 'city_pop': 0, 'job': 0, 'dob': 0, 'trans_num': 0, 'unix_time': 0, 'merch_lat': 0, 'merch_long': 0, 'is_fraud': 0}`
- Blank strings by column: `{}`

## Quality summary: `fraudTest.csv`

- Target counts: `{'0': 553574, '1': 2145}`
- Duplicate complete rows: 0
- Duplicate transaction IDs: 0
- Card identifiers outside the 12-19 digit PAN-like range: 2,708 (preserved as strings; synthetic IDs may not be actual PANs)
- Canonical text timestamp range: 2020-06-21T12:14:25 to 2020-12-31T23:59:34
- Source timestamp decreases in row order: 0
- Adjacent equal timestamps: 10,959
- Unix epoch timestamp range: 2013-06-21T12:14:25+00:00 to 2013-12-31T23:59:34+00:00
- `trans_date_trans_time` minus `unix_time` offsets (seconds): `{'220924800': 555719}`
- Rows reconstructed exactly after adding seven calendar years to UTC unix_time: 555,719/555,719
- unix_time decreases in source order: 0
- Negative/zero/invalid amounts: 0/0/0
- Invalid coordinates: 0
- Invalid or future DOB: 0/0
- Missing values by column: `{'Unnamed: 0': 0, 'trans_date_trans_time': 0, 'cc_num': 0, 'merchant': 0, 'category': 0, 'amt': 0, 'first': 0, 'last': 0, 'gender': 0, 'street': 0, 'city': 0, 'state': 0, 'zip': 0, 'lat': 0, 'long': 0, 'city_pop': 0, 'job': 0, 'dob': 0, 'trans_num': 0, 'unix_time': 0, 'merch_lat': 0, 'merch_long': 0, 'is_fraud': 0}`
- Blank strings by column: `{}`
