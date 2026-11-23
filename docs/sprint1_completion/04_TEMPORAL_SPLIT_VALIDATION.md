# Temporal split validation

## Current split (active in this worktree)

- Policy: `nearest_row_count`; test remains the full `fraudTest.csv` source.
- Cutoff / first validation timestamp: `2020-03-06T07:16:43`.
- Counts: train 1,037,340; validation 259,335; test 555,719.
- Fraud counts: train 5,968; validation 1,538; test 2,145.
- Strict chronology: train max `2020-03-06T07:15:17` < validation min `2020-03-06T07:16:43`; validation max `2020-06-21T12:13:37` < test min `2020-06-21T12:14:25`.
- Split hash: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.
- ID overlap: zero; every manifest ID maps one-to-one to exactly one split parquet. No timestamp group crosses splits.

## Policy change and historical baseline

The old cutoff selection counted through a timestamp group when choosing the cutoff, then assigned rows with `timestamp < cutoff` to train. That could omit the cutoff group from the requested train count. A 20-row fixture with ten equal-sized groups and target 16 produces 14 train rows with the legacy policy; the nearest legal boundary produces 16 while preserving chronology and timestamp-group atomicity.

The former baseline used cutoff `2020-03-06T07:15:17`, counts train 1,037,339 / validation 259,336 / test 555,719, and hash `70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255`. It is historical in this worktree. Toan requested the new policy on 2026-11-23, and code defaults, config, artifacts, and reports now use `nearest_row_count`.

Exactly one record changed membership: `trans_num=408a69cd781df5546489ecb28a2007ea`, timestamp `2020-03-06T07:15:17`, validation -> train. Test membership is unchanged. The resulting split hash is `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.

## Downstream requirements

Trung's feature rows, model training, and evaluation outputs must use the same current manifest/hash. Any artifacts built against `70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255` must not be mixed with this split. For history features, use only same-card events strictly earlier than the anchor; batch equal timestamps before updating state; never use labels in history; fit transforms on train only.
