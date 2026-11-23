# Bug fix changelog

## `src/data/split.py` and `src/data/pipeline.py`

- **Issue:** the old splitter selected a timestamp whose cumulative count reached the target, then assigned rows with `timestamp < cutoff` to train. This excluded the entire cutoff timestamp group from train.
- **Reproduction:** ten timestamp groups of two rows each, target train size 16. The legacy cutoff was the eighth timestamp, so `< cutoff` produced 14 train rows. The new candidate boundary is the ninth timestamp and produces 16.
- **Change:** introduced `choose_timestamp_cutoff` and `cutoff_policy`. `nearest_row_count` is now the default in this worktree; `legacy` remains an explicit option for reproduction. The active policy selects a legal group boundary closest to the target without dividing equal timestamps.
- **Verification:** regression tests assert the 14-versus-16 behavior, strict chronology, no timestamp-group crossing, unique IDs, and one-to-one manifest coverage.
- **Downstream impact:** on Toan's instruction (2026-11-23), the full-data outputs now use `nearest_row_count`. One transaction moves from validation to train. Current hash: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`; counts are train 1,037,340, validation 259,335, test 555,719. This is the canonical split in this worktree.

## `src/data/audit.py`

- **Issue:** converting inferred datetime values directly to `int64` assumes the storage unit is nanoseconds. Pandas 3 can infer seconds, milliseconds, or microseconds.
- **Change:** normalize to nanoseconds with `Series.dt.as_unit("ns")` before integer conversion, then compute epoch seconds.
- **Verification:** parameterized regression check covers `datetime64[s]`, `[ms]`, `[us]`, and `[ns]`.
- **Environment limit:** these cases ran under pandas 2.2.3; pandas 3 was not installed here. Pandas documents the resolution-inference change in its [3.0 release notes](https://pandas.pydata.org/docs/whatsnew/v3.0.0.html).

## `src/data/preprocess.py`

- **Issue:** `pd.to_datetime` may preserve or infer a coarser unit, while the contract specifies nanosecond Parquet timestamps.
- **Change:** explicitly cast `timestamp` and `dob` to `datetime64[ns]`; preserve identifier and categorical string dtypes.
- **Verification:** Arrow schema regression asserts `timestamp[ns]`, no timezone, and `dob` at nanosecond precision.

## `src/data/generate_mock.py`

- **Issue:** the normalized mock included excluded `unix_time`, used an unapproved `source_dataset="mock"`, and relied on inferred dtypes.
- **Change:** removed `unix_time`, mapped synthetic train/validation to `fraudTrain` and synthetic test to `fraudTest`, and cast fields to contract dtypes.
- **Verification:** generated mock column set and Arrow field types are checked against `configs/data_schema.yaml`.
- **Checked-in fixture:** the prior `data/samples` CSV and README were copied to the external evidence backup before regeneration; the checked-in CSV/manifest are now generated with seed 2026 and covered by a repository-fixture regression test.

## `notebooks/01_data_understanding.ipynb`

- **Issue:** the notebook depended on the kernel's current directory for both data paths and imports. Execution from a notebook/output directory caused missing-artifact or `No module named src` failures.
- **Change:** search the current directory and its parents for the project root, then add that root to `sys.path`; document required pipeline artifacts and contract checks.
- **Verification:** executed from `notebooks/` with all cells successful and exit code 0. The earlier wrapper failure itself was not present as a stored historical log, so its exact original invocation cannot be independently confirmed.
