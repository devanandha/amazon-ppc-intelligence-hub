"""Publication-quality robustness evaluation across 50 synthetic benchmark seeds.

Runs the three frozen decision frameworks on identical synthetic datasets and writes
reproducible aggregate, class-level, confusion-matrix, paired-test, and sensitivity outputs.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel, wilcoxon
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from generate_benchmark import generate, STATES
import baseline_acos, baseline_rules, proposed_framework

MODELS = {
    "ACOS-only": baseline_acos.predict,
    "Evidence-aware": baseline_rules.predict,
    "Multi-metric": proposed_framework.predict,
}

def ci95(values):
    a = np.asarray(values, dtype=float)
    return 1.96 * a.std(ddof=1) / np.sqrt(len(a))

def main():
    root = Path(__file__).parent
    out = root / "results"
    out.mkdir(exist_ok=True)
    runs, class_rows = [], []
    cms = {name: np.zeros((len(STATES), len(STATES)), dtype=int) for name in MODELS}
    datasets = {seed: generate(n=5000, seed=seed) for seed in range(50)}

    for seed, df in datasets.items():
        for name, fn in MODELS.items():
            pred = fn(df)
            p, r, f, _ = precision_recall_fscore_support(
                df.ground_truth, pred, labels=STATES, zero_division=0
            )
            acc = accuracy_score(df.ground_truth, pred)
            runs.append([seed, name, acc, p.mean(), r.mean(), f.mean()])
            for label, pp, rr, ff in zip(STATES, p, r, f):
                class_rows.append([seed, name, label, pp, rr, ff])
            cms[name] += confusion_matrix(df.ground_truth, pred, labels=STATES)

    runs = pd.DataFrame(
        runs,
        columns=["seed", "method", "accuracy", "macro_precision", "macro_recall", "macro_f1"],
    )
    runs.to_csv(out / "robustness_runs.csv", index=False)

    summary = []
    for name, g in runs.groupby("method"):
        row = {"method": name}
        for metric in ["accuracy", "macro_precision", "macro_recall", "macro_f1"]:
            row[f"{metric}_mean"] = g[metric].mean()
            row[f"{metric}_sd"] = g[metric].std(ddof=1)
            row[f"{metric}_ci95_halfwidth"] = ci95(g[metric])
        summary.append(row)
    pd.DataFrame(summary).to_csv(out / "robustness_summary.csv", index=False)

    class_df = pd.DataFrame(
        class_rows, columns=["seed", "method", "class", "precision", "recall", "f1"]
    )
    class_df.groupby(["method", "class"], as_index=False)[
        ["precision", "recall", "f1"]
    ].mean().to_csv(out / "class_metrics.csv", index=False)

    for name, cm in cms.items():
        safe = name.lower().replace(" ", "_").replace("-", "_")
        pd.DataFrame(cm, index=STATES, columns=STATES).to_csv(
            out / f"confusion_50seed_{safe}.csv"
        )

    tests = []
    evidence = runs[runs.method == "Evidence-aware"].sort_values("seed").macro_f1.to_numpy()
    for other in ["ACOS-only", "Multi-metric"]:
        comparator = runs[runs.method == other].sort_values("seed").macro_f1.to_numpy()
        t = ttest_rel(evidence, comparator)
        w = wilcoxon(evidence, comparator)
        tests.append([
            "Evidence-aware", other, (evidence - comparator).mean(),
            t.statistic, t.pvalue, w.statistic, w.pvalue
        ])
    pd.DataFrame(
        tests,
        columns=[
            "method_a", "method_b", "mean_f1_difference",
            "paired_t_stat", "paired_t_p", "wilcoxon_stat", "wilcoxon_p"
        ],
    ).to_csv(out / "paired_tests.csv", index=False)

    sensitivity = []
    for target in [20, 25, 30, 35, 40]:
        for clicks in [10, 15, 20, 25]:
            values = []
            for df in datasets.values():
                pred = baseline_rules.predict(df, target_acos=target, min_clicks=clicks)
                f1 = precision_recall_fscore_support(
                    df.ground_truth, pred, average="macro", zero_division=0
                )[2]
                values.append(f1)
            sensitivity.append([
                target, clicks, np.mean(values), np.std(values, ddof=1), ci95(values)
            ])
    pd.DataFrame(
        sensitivity,
        columns=[
            "target_acos", "min_clicks", "macro_f1_mean",
            "macro_f1_sd", "macro_f1_ci95_halfwidth"
        ],
    ).to_csv(out / "robustness_sensitivity.csv", index=False)

    print(pd.DataFrame(summary)[
        ["method", "accuracy_mean", "macro_f1_mean", "macro_f1_ci95_halfwidth"]
    ].to_string(index=False))

if __name__ == "__main__":
    main()
