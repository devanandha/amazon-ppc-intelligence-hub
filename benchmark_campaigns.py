"""Reproducible comparison of Amazon PPC campaign rules and unsupervised ML.

No supervised labels, automatic bidding, causal effect or validated 'accuracy'.
No private source reports are committed or uploaded by this module.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

COLUMNS = ("Week", "Campaign", "Campaign_Type", "Product",
           "Impressions", "Clicks", "Spend", "Orders", "Sales")
METRICS = ("Impressions", "Clicks", "Spend", "Orders", "Sales")
SEEDS = (42, 43, 44, 45, 46)


def validate_campaigns(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError("Missing campaign columns: " + ", ".join(missing))
    df = frame.loc[:, list(COLUMNS)].copy()
    if df.empty:
        raise ValueError("The campaign report is empty")
    df["Week"] = pd.to_datetime(df["Week"], errors="coerce")
    if df["Week"].isna().any():
        raise ValueError("Invalid week values")
    for column in METRICS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        if df[column].isna().any() or (df[column] < 0).any() or not np.isfinite(df[column]).all():
            raise ValueError(f"Invalid {column} metrics")
    if (df["Clicks"] > df["Impressions"]).any():
        raise ValueError("Clicks cannot exceed impressions")
    for column in ("Campaign", "Campaign_Type", "Product"):
        if df[column].isna().any() or (df[column].astype(str).str.strip() == "").any():
            raise ValueError(f"Missing {column} values")
        df[column] = df[column].astype(str).str.strip()
    return df.reset_index(drop=True)


def baseline_labels(frame: pd.DataFrame, target_acos: float = 25.0,
                    min_clicks: int = 15, min_orders: int = 3) -> pd.DataFrame:
    """Transparent campaign-week review screen, NOT expert-labeled truth."""
    if not np.isfinite(target_acos) or target_acos <= 0:
        raise ValueError("Target ACOS must be positive")
    if min_clicks < 1 or min_orders < 1:
        raise ValueError("Evidence thresholds must be positive")
    df = validate_campaigns(frame)
    sales = df["Sales"].to_numpy(dtype=float)
    spend = df["Spend"].to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        df["ACOS %"] = np.where(sales > 0, 100 * spend / sales, np.nan)
    labels = []
    for row in df.itertuples(index=False):
        clicks = float(row.Clicks)
        orders = float(row.Orders)
        spend = float(row.Spend)
        sales = float(row.Sales)
        acos = (spend / sales * 100) if sales > 0 else float("nan")
        if clicks < min_clicks:
            label = "Evidence insufficient"
        elif spend > 0 and sales <= 0:
            label = "No attributed sales review"
        elif orders < min_orders:
            label = "Evidence insufficient"
        elif np.isfinite(acos) and acos > target_acos * 1.5:
            label = "High ACOS review"
        elif np.isfinite(acos) and acos > target_acos:
            label = "Above-target monitor"
        else:
            label = "Within-target monitor"
        labels.append(label)
    df["Baseline screen"] = labels
    df["Baseline priority review"] = df["Baseline screen"].isin(
        ("High ACOS review", "No attributed sales review")
    )
    return df


def model_flags(frame: pd.DataFrame, seed: int = 42, contamination: float = 0.10,
                min_rows: int = 20) -> np.ndarray:
    """Match the dashboard's 5-feature Isolation Forest configuration."""
    if not 0 < contamination <= 0.5:
        raise ValueError("contamination must be in (0, 0.5]")
    if len(frame) < min_rows:
        return np.zeros(len(frame), dtype=bool)
    features = np.log1p(frame[list(METRICS)].astype(float).to_numpy())
    scaled = RobustScaler().fit_transform(features)
    model = IsolationForest(
        n_estimators=150, contamination=contamination, random_state=int(seed)
    )
    return model.fit_predict(scaled) == -1


def _jaccard(a: np.ndarray, b: np.ndarray) -> float:
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / union) if union else 1.0


def run_benchmark(frame: pd.DataFrame, target_acos: float = 25.0,
                  min_clicks: int = 15, min_orders: int = 3,
                  seeds: tuple[int, ...] = SEEDS) -> dict:
    """Compare review overlap and sensitivity, never predictive accuracy."""
    if not seeds:
        raise ValueError("Provide at least one reproducible seed")
    checked = baseline_labels(frame, target_acos, min_clicks, min_orders)
    flags = {}
    for seed in seeds:
        flags[int(seed)] = model_flags(checked, seed=int(seed))
    primary = flags[int(seeds[0])]
    checked["ML anomaly flag"] = primary
    b = checked["Baseline priority review"].to_numpy(dtype=bool)
    checked["Review overlap"] = np.where(
        b & primary, "Both rule and ML",
        np.where(b, "Rule only", np.where(primary, "ML only", "Neither"))
    )
    stable = np.vstack([flags[int(seed)] for seed in seeds])
    checked["ML seed agreement %"] = (100.0 * stable.mean(axis=0)).round(1)
    jaccards = [_jaccard(primary, flags[int(seed)]) for seed in seeds[1:]]
    sensitivity = []
    for level in (0.05, 0.10, 0.15):
        f = model_flags(checked, seed=int(seeds[0]), contamination=level)
        sensitivity.append({
            "Contamination setting": level,
            "ML flags": int(f.sum()),
            "Overlap with baseline priority": int(np.logical_and(f, b).sum()),
            "Jaccard vs 10% setting": _jaccard(primary, f),
        })
    summary = {
        "dataset_rows": int(len(checked)),
        "campaigns": int(checked["Campaign"].nunique()),
        "weeks": int(checked["Week"].nunique()),
        "baseline_priority_review_rows": int(b.sum()),
        "baseline_other_rows": int((~b).sum()),
        "ml_anomaly_rows": int(primary.sum()),
        "overlap_rule_and_ml": int(np.logical_and(b, primary).sum()),
        "rule_only": int(np.logical_and(b, ~primary).sum()),
        "ml_only": int(np.logical_and(~b, primary).sum()),
        "neither": int(np.logical_and(~b, ~primary).sum()),
        "seed_jaccard_mean_vs_primary": round(float(np.mean(jaccards)), 4) if jaccards else None,
        "seed_jaccard_min_vs_primary": round(float(np.min(jaccards)), 4) if jaccards else None,
        "baseline_labels": {str(k): int(v) for k, v in checked["Baseline screen"].value_counts().items()},
        "model_feature_columns": list(METRICS),
        "target_acos_percent": float(target_acos),
        "min_clicks": int(min_clicks),
        "min_orders": int(min_orders),
        "contamination_primary": 0.10,
        "model_seeds": list(map(int, seeds)),
        "ground_truth_labels_available": False,
        "validated_accuracy_or_sales_lift": False,
    }
    checked["Week"] = checked["Week"].dt.strftime("%Y-%m-%d")
    return {"summary": summary, "observations": checked,
            "sensitivity": pd.DataFrame(sensitivity)}


def write_benchmark(result: dict, outdir: str | Path,
                    source: str = "Uploaded dataset") -> list[Path]:
    """Local only; no network or dataset redistribution."""
    path = Path(outdir)
    path.mkdir(parents=True, exist_ok=True)
    outputs = []
    summary_path = path / "summary.json"
    summary_path.write_text(
        json.dumps(result["summary"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    outputs.append(summary_path)
    for key, filename in (
        ("observations", "observation_comparison.csv"),
        ("sensitivity", "ml_sensitivity.csv"),
    ):
        out = path / filename
        result[key].to_csv(out, index=False)
        outputs.append(out)
    readme = path / "EVALUATION_NOTES.txt"
    readme.write_text(
        f"Data source: {source}\n"
        "This benchmark uses historical/simulated campaign-level observations.\n"
        "Baseline: transparent ACOS + minimum-click/order screening; NOT expert ground truth.\n"
        "ML: IsolationForest, 150 trees, log1p five metrics, RobustScaler, contamination=10%.\n"
        "Overlap measures review coverage agreement, not predictive accuracy.\n"
        "Seed Jaccard measures robustness to random state on the same dataset.\n"
        "Contamination sensitivity measures imposed alert-budget changes.\n"
        "No ground-truth labels, experiments, causal uplift, optimal bids or live validation.\n"
        "Respect source copyright, licensing and confidentiality.\n",
        encoding="utf-8",
    )
    outputs.append(readme)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Campaign rule screen vs ML anomaly review benchmark"
    )
    parser.add_argument("--input", required=True, help="Local CSV; never committed")
    parser.add_argument("--output", default="benchmark_output")
    parser.add_argument("--target-acos", type=float, default=25.0)
    parser.add_argument("--min-clicks", type=int, default=15)
    parser.add_argument("--min-orders", type=int, default=3)
    args = parser.parse_args()
    result = run_benchmark(
        pd.read_csv(args.input), args.target_acos, args.min_clicks, args.min_orders
    )
    for file in write_benchmark(result, args.output, source=str(args.input)):
        print(file)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
