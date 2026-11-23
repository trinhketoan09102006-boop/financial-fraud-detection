# Temporal split report

- Requested train fraction of original training file: 80.0%.
- Cutoff policy: `nearest_row_count`.
- Timestamp cutoff (first validation timestamp): 2020-03-06T07:16:43.
- Stable split hash: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.
- Raw SHA-256: `{'fraudTrain.csv': 'fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d', 'fraudTest.csv': '12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0'}`.
- No random or stratified splitting; same-timestamp groups stay together.
- fraudTest.csv is preserved wholly as test because its timestamps follow fraudTrain.csv.

| Split | Rows | Normal | Fraud | Fraud rate | Cards | Min timestamp | Max timestamp |
|---|---:|---:|---:|---:|---:|---|---|
| train | 1,037,340 | 1,031,372 | 5,968 | 0.5753% | 964 | 2019-01-01T00:00:18 | 2020-03-06T07:15:17 |
| validation | 259,335 | 257,797 | 1,538 | 0.5931% | 927 | 2020-03-06T07:16:43 | 2020-06-21T12:13:37 |
| test | 555,719 | 553,574 | 2,145 | 0.3860% | 924 | 2020-06-21T12:14:25 | 2020-12-31T23:59:34 |

The 80/20 boundary is chosen at the nearest whole timestamp group, so counts can differ slightly from the row-based target. Card overlap across splits is expected and permits use of observed prior history; transaction IDs remain disjoint.
