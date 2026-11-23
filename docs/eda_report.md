# Exploratory data analysis report

## Scope and method

Detailed exploratory analysis uses only the temporal training split (1,037,340 transactions; 964 cards). Validation and test are not used to choose features. This analysis describes associations and distributions; it does not establish causal relationships or model performance.

## Target and imbalance

- Normal: 1,031,372; fraud: 5,968; fraud rate: 0.5753%.
- The low fraud prevalence means accuracy alone can look high while missed fraud remains substantial. Compare precision-recall, recall, precision, and cost-aware metrics in Khoa's evaluation.

## Transaction amounts

See `numeric_summary.csv`, `03_amount_distribution.png`, `04_log_amount_distribution.png`, and `05_amount_by_label.png`. Valid large amounts are preserved; amount outliers are not removed. Source currency is unspecified.

## Categories and time

Fraud rates include transaction and fraud counts in `fraud_rate_by_category.csv` to show uncertainty for small groups. Highest observed category rates in this training partition: `[{'category': 'shopping_net', 'transactions': 78025, 'fraud': 1370, 'fraud_rate': 0.01755847484780519}, {'category': 'misc_net', 'transactions': 50501, 'fraud': 737, 'fraud_rate': 0.014593770420387715}, {'category': 'grocery_pos', 'transactions': 98808, 'fraud': 1387, 'fraud_rate': 0.014037324912962513}, {'category': 'shopping_pos', 'transactions': 93330, 'fraud': 661, 'fraud_rate': 0.007082395799849994}, {'category': 'gas_transport', 'transactions': 105248, 'fraud': 493, 'fraud_rate': 0.004684174521131043}]`. Hour/day/month outputs are descriptive, based on timezone-naive source timestamps.

## Exploratory card-level summaries

`card_behavior_summary.csv` describes transaction, merchant, category, and inter-transaction gap counts within training only. These summaries are for feature discussion and are not added to the baseline table. History features should be produced causally by Trung with strict past-only and timestamp-batch semantics.

## Baseline suggestions and cautions

The agreed transaction-local candidates are amount, calendar fields, age at transaction, straight-line merchant distance, merchant, and category. Large valid amounts can be informative and are retained. Merchant distance is not physical travel distance. Spearman correlation in `spearman_correlation.csv` is a screening summary only; do not remove a feature automatically from correlation alone.

## Limitations

Sparkov is simulated data. The source does not declare timestamp timezone or currency, so hour-of-day and amount units are source-relative. Association by label is not causal evidence, and findings may not generalize to production transaction streams.

## Figures

Ten PNG charts are saved in `results/eda/` with counts, labels, and units where applicable.
