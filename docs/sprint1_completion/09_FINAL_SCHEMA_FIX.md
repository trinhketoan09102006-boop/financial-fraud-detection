# Final Arrow schema fix

## Reported failure and reproduction

Tu reported `test_mock_data_is_synthetic_temporal_and_covers_each_split` failing for `trans_num`, expecting Arrow `string` but receiving `large_string` on Python 3.11.9 / pandas 3.1.1 / PyArrow 26.0.1.

The failure was reproduced with the actual mock generator in that environment:

- generator DataFrame dtype: pandas `string`
- direct `pa.Table.from_pandas(data, preserve_index=False)`: `trans_num` is `large_string`
- contract conversion: `trans_num` is `string`
- Parquet schema after readback: `trans_num` is `string`

The earlier test asserted the backend's direct inference rather than serializing through the declared contract. The mock generator itself returns correct identifiers and writes CSV; it does not create Arrow/Parquet output. Separately, full-data staging showed that the split writer also inferred `large_string` on the new environment. That was a real serialization defect and is fixed at the shared writer boundary.

Logs: `11_root_cause_reproduction_py311.txt`, `11_root_cause_reproduction_py313.txt`, and `11_mock_test_py311_verbose.txt`.

## Root cause and fix

Pandas 3.1.1 with PyArrow 26.0.1 maps pandas `StringDtype` to Arrow `large_string` during uninstructed DataFrame conversion. The prior string cast in preprocessing used a hard-coded column list, and the test bypassed that writer. The split writer also called `DataFrame.to_parquet` without an explicit schema conversion.

Added `src/data/arrow_schema.py`. `load_contract_arrow_schema()` reads field types and nullability from `configs/data_schema.yaml`. `dataframe_to_arrow_table()` applies that schema to normalized and mock frames; in non-strict mode it applies contract types to known fields and safely narrows additional `large_string` columns (including the split label) to `string`. It does not coerce unrelated columns to strings.

Preprocessing and split serialization now share this helper. The data contract is unchanged. The mock test creates a contract Arrow table, writes Parquet, then validates the schema and values after reading it back.

## Regression coverage

Regression tests exercise `object`, pandas `string`, and Arrow-backed `large_string` text inputs. They check the in-memory Arrow table, every field in the Parquet round-trip, and preservation of text values including `trans_num` and `cc_num`. Split tests cover `trans_num` and the manifest's `split` field. Full-data integration checks string types in normalized, split, and manifest Parquets.

## Cross-version result

- Python 3.11.9 / pandas 3.1.1 / PyArrow 26.0.1: target test passes; full suite 18 passed, no skips.
- Python 3.13.7 / pandas 2.2.3 / PyArrow 22.0.0: target test passes; full suite 18 passed, no skips.
- Full normalized/split schema remains consistent with the YAML contract under both environments.

The split policy and official hash were not changed. See `11_CROSS_VERSION_ARROW_COMPATIBILITY.md` for exact commands, comparisons, and remaining numeric-parser caveat.
