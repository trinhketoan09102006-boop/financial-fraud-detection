"""Training-only exploratory summaries and privacy-safe diagnostic charts."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .audit import ROOT, run_audit


def _group_rates(data: pd.DataFrame, field: str) -> pd.DataFrame:
    grouped = data.groupby(field, dropna=False, observed=True)["is_fraud"].agg(transactions="size", fraud="sum").reset_index()
    grouped["fraud_rate"] = grouped["fraud"] / grouped["transactions"]
    return grouped.sort_values(["fraud_rate", "transactions"], ascending=[False, False], kind="mergesort")


def run_eda(train_path: Path | None = None, output_dir: Path | None = None, report_path: Path | None = None, validate_audit: bool = True) -> dict:
    train_path = train_path or ROOT / "data" / "splits" / "train.parquet"
    output_dir = output_dir or ROOT / "results" / "eda"
    report_path = report_path or ROOT / "docs" / "eda_report.md"
    if validate_audit:
        audit = run_audit(output_root=ROOT)
        blockers = [item for item in audit["findings"] if item["status"] == "BLOCKER"]
        if blockers:
            raise RuntimeError(f"EDA stopped because audit reported BLOCKER findings: {blockers}")
    if not train_path.is_file():
        raise FileNotFoundError("Run the temporal split stage before EDA.")
    data = pd.read_parquet(train_path)
    if "split" in data and not data["split"].eq("train").all():
        raise ValueError("Detailed EDA is restricted to training data.")
    if data.empty:
        raise ValueError("Training data is empty.")
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams["figure.dpi"] = 120

    numeric = data.select_dtypes(include=["number"]).drop(columns=["is_fraud"], errors="ignore")
    numeric_summary = numeric.describe(percentiles=[.01, .05, .25, .50, .75, .95, .99]).T
    numeric_summary["skew"] = numeric.skew(numeric_only=True)
    numeric_summary.to_csv(output_dir / "numeric_summary.csv")
    for field in ("category", "merchant", "job", "gender", "state"):
        if field in data:
            table = _group_rates(data, field)
            table.to_csv(output_dir / f"fraud_rate_by_{field}.csv", index=False)
    calendar = data.assign(month_period=data["timestamp"].dt.to_period("M").astype(str)).groupby("month_period", observed=True)["is_fraud"].agg(transactions="size", fraud="sum").reset_index()
    calendar["fraud_rate"] = calendar["fraud"] / calendar["transactions"]
    calendar.to_csv(output_dir / "monthly_trend.csv", index=False)
    card_behavior = data.groupby("cc_num", observed=True).agg(transactions=("trans_num", "size"), unique_merchants=("merchant", "nunique"), unique_categories=("category", "nunique"), first_timestamp=("timestamp", "min"), last_timestamp=("timestamp", "max")).reset_index(drop=True)
    gaps = data.sort_values(["cc_num", "timestamp"], kind="mergesort").groupby("cc_num", observed=True)["timestamp"].diff().dt.total_seconds() / 3600
    card_behavior["median_intertransaction_hours"] = gaps.groupby(data.sort_values(["cc_num", "timestamp"], kind="mergesort")["cc_num"].reset_index(drop=True), observed=True).median().to_numpy()
    card_behavior.to_csv(output_dir / "card_behavior_summary.csv", index=False)
    corr = data[[c for c in ["amt", "hour", "day_of_week", "month", "age_at_transaction", "merchant_distance_km", "city_pop", "is_fraud"] if c in data]].corr(method="spearman")
    corr.to_csv(output_dir / "spearman_correlation.csv")

    def save(name: str) -> None:
        plt.tight_layout()
        plt.savefig(output_dir / f"{name}.png", bbox_inches="tight")
        plt.close()

    fig, ax = plt.subplots(figsize=(6, 4)); sns.countplot(data=data, x="is_fraud", ax=ax); ax.set(title="Training class distribution", xlabel="Label (0 normal, 1 fraud)", ylabel="Transactions"); save("01_class_distribution")
    missing = data.isna().mean().sort_values(ascending=False).head(20)
    fig, ax = plt.subplots(figsize=(9, 4)); sns.barplot(x=missing.values, y=missing.index, ax=ax, color="#4C78A8"); ax.set(title="Missing-value rate (training)", xlabel="Share of rows", ylabel="Field"); save("02_missing_values")
    fig, ax = plt.subplots(figsize=(8, 4)); sns.histplot(data=data, x="amt", bins=80, ax=ax); ax.set(title="Transaction amount distribution", xlabel="Amount (source currency unspecified)", ylabel="Transactions"); save("03_amount_distribution")
    fig, ax = plt.subplots(figsize=(8, 4)); sns.histplot(x=np.log1p(data["amt"]), bins=80, ax=ax); ax.set(title="Log-scaled transaction amount distribution", xlabel="log(1 + amount)", ylabel="Transactions"); save("04_log_amount_distribution")
    fig, ax = plt.subplots(figsize=(7, 4)); sns.boxplot(data=data, x="is_fraud", y="amt", showfliers=False, ax=ax); ax.set(title="Amounts by label (whiskers hide extreme display points only)", xlabel="Label (0 normal, 1 fraud)", ylabel="Amount (source currency unspecified)"); save("05_amount_by_label")
    category = _group_rates(data, "category").sort_values("fraud_rate", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5)); sns.barplot(data=category, x="category", y="fraud_rate", ax=ax); ax.tick_params(axis="x", rotation=40); ax.set(title="Fraud rate by category (counts available in CSV)", xlabel="Category", ylabel="Fraud rate"); save("06_fraud_rate_by_category")
    by_hour = data.groupby("hour", observed=True)["is_fraud"].agg(transactions="size", fraud="sum"); by_hour["rate"] = by_hour["fraud"] / by_hour["transactions"]
    fig, ax = plt.subplots(figsize=(8, 4)); sns.lineplot(x=by_hour.index, y=by_hour["rate"], marker="o", ax=ax); ax.set(title="Fraud rate by transaction hour", xlabel="Hour of day (source local time unspecified)", ylabel="Fraud rate", xticks=range(0, 24, 2)); save("07_fraud_rate_by_hour")
    by_day = data.groupby("day_of_week", observed=True)["is_fraud"].agg(transactions="size", fraud="sum"); by_day["rate"] = by_day["fraud"] / by_day["transactions"]
    fig, ax = plt.subplots(figsize=(7, 4)); sns.barplot(x=by_day.index, y=by_day["rate"], ax=ax); ax.set(title="Fraud rate by day of week", xlabel="Day (Monday=0)", ylabel="Fraud rate", xticks=range(7)); save("08_fraud_rate_by_day")
    freq = data.groupby("cc_num", observed=True).size()
    fig, ax = plt.subplots(figsize=(8, 4)); sns.histplot(freq, bins=40, ax=ax); ax.set(title="Transaction frequency per card (training only)", xlabel="Transactions per card", ylabel="Cards"); save("09_card_transaction_frequency")
    fig, ax = plt.subplots(figsize=(8, 6)); sns.heatmap(corr, cmap="vlag", center=0, annot=True, fmt=".2f", ax=ax); ax.set(title="Spearman correlation (numeric training fields)"); save("10_correlation_heatmap")

    fraud = int(data["is_fraud"].sum()); total = len(data)
    top_category = category.head(5)[["category", "transactions", "fraud", "fraud_rate"]].to_dict("records")
    card_count = int(data["cc_num"].nunique())
    report = f"""# Exploratory data analysis report

## Scope and method

Detailed exploratory analysis uses only the temporal training split ({total:,} transactions; {card_count:,} cards). Validation and test are not used to choose features. This analysis describes associations and distributions; it does not establish causal relationships or model performance.

## Target and imbalance

- Normal: {total - fraud:,}; fraud: {fraud:,}; fraud rate: {fraud / total:.4%}.
- The low fraud prevalence means accuracy alone can look high while missed fraud remains substantial. Compare precision-recall, recall, precision, and cost-aware metrics in Khoa's evaluation.

## Transaction amounts

See `numeric_summary.csv`, `03_amount_distribution.png`, `04_log_amount_distribution.png`, and `05_amount_by_label.png`. Valid large amounts are preserved; amount outliers are not removed. Source currency is unspecified.

## Categories and time

Fraud rates include transaction and fraud counts in `fraud_rate_by_category.csv` to show uncertainty for small groups. Highest observed category rates in this training partition: `{top_category}`. Hour/day/month outputs are descriptive, based on timezone-naive source timestamps.

## Exploratory card-level summaries

`card_behavior_summary.csv` describes transaction, merchant, category, and inter-transaction gap counts within training only. These summaries are for feature discussion and are not added to the baseline table. History features should be produced causally by Trung with strict past-only and timestamp-batch semantics.

## Baseline suggestions and cautions

The agreed transaction-local candidates are amount, calendar fields, age at transaction, straight-line merchant distance, merchant, and category. Large valid amounts can be informative and are retained. Merchant distance is not physical travel distance. Spearman correlation in `spearman_correlation.csv` is a screening summary only; do not remove a feature automatically from correlation alone.

## Limitations

Sparkov is simulated data. The source does not declare timestamp timezone or currency, so hour-of-day and amount units are source-relative. Association by label is not causal evidence, and findings may not generalize to production transaction streams.

## Figures

Ten PNG charts are saved in `results/eda/` with counts, labels, and units where applicable.
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return {"rows": total, "fraud": fraud, "fraud_rate": fraud / total, "cards": card_count, "charts": 10, "output_dir": str(output_dir)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=ROOT / "data" / "splits" / "train.parquet")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "eda")
    args = parser.parse_args()
    print(run_eda(args.train, args.output_dir))


if __name__ == "__main__":
    main()
