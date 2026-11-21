# Temporal split report

Canonical time field: `timestamp`, parsed from `trans_date_trans_time` as timezone-naive. `unix_time` is excluded from normalized data after the full audit verified its exact seven-calendar-year stale offset.

- Requested train fraction of original training file: 80.0%.
- Timestamp cutoff (first validation timestamp): 2020-03-06T07:15:17.
- Stable split hash: `70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255`.
- Raw SHA-256: `{'fraudTrain.csv': 'fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d', 'fraudTest.csv': '12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0'}`.
- No random or stratified splitting; same-timestamp groups stay together.
- fraudTest.csv is preserved wholly as test because its timestamps follow fraudTrain.csv.

| Split | Rows | Normal | Fraud | Fraud rate | Cards | Min timestamp | Max timestamp |
|---|---:|---:|---:|---:|---:|---|---|
| train | 1,037,339 | 1,031,371 | 5,968 | 0.5753% | 964 | 2019-01-01T00:00:18 | 2020-03-06T07:14:37 |
| validation | 259,336 | 257,798 | 1,538 | 0.5931% | 927 | 2020-03-06T07:15:17 | 2020-06-21T12:13:37 |
| test | 555,719 | 553,574 | 2,145 | 0.3860% | 924 | 2020-06-21T12:14:25 | 2020-12-31T23:59:34 |

The 80/20 boundary is chosen at the nearest whole timestamp group, so counts can differ slightly from the row-based target. Card overlap across splits is expected and permits use of observed prior history; transaction IDs remain disjoint.

The split hash is unchanged from the earlier provisional split (`70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255`), because canonical timestamp boundaries and transaction-to-split assignments did not change after excluding `unix_time`.
