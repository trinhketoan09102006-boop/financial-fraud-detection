# Mock transaction data

These 300 rows are synthetic and generated with NumPy seed `2026`. They contain no records copied from the Sparkov CSVs and are for interface and pipeline tests only; they do not represent model performance.

        `mock_transactions.csv` follows the normalized transaction schema. `mock_split_manifest.csv` maps each unique `trans_num` to one time-ordered split. The default fixture spans more than seven days per split for 1h/24h/7d history tests and includes both labels, tied timestamps, unseen cards, new merchants/categories, a large amount, and nullable fields.
