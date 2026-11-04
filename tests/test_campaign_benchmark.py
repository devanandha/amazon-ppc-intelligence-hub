"""Tests with fully fictional campaign observations. No commercial data."""
import unittest

import numpy as np
import pandas as pd

from benchmark_campaigns import baseline_labels, model_flags, run_benchmark


def fictional_weeks(rows=40):
    rng = np.random.default_rng(17)
    result = []
    for i in range(rows):
        clicks = int(rng.integers(10, 180))
        impressions = int(clicks * rng.integers(25, 100))
        spend = round(float(clicks * rng.uniform(0.5, 1.4)), 2)
        orders = int(rng.integers(0, 20))
        sales = round(float(orders * rng.uniform(10, 28)), 2)
        result.append({
            "Week": (pd.Timestamp("2025-01-06") + pd.Timedelta(days=7 * i)).date().isoformat(),
            "Campaign": f"Fictional Campaign {i % 3}",
            "Campaign_Type": "Sponsored Products - Auto",
            "Product": "Fictional Product",
            "Impressions": impressions,
            "Clicks": clicks,
            "Spend": spend,
            "Orders": orders,
            "Sales": sales,
        })
    return pd.DataFrame(result)


class CampaignBenchmarkTests(unittest.TestCase):
    def test_empty_and_missing_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            run_benchmark(pd.DataFrame({"Campaign": ["A"]}))
        with self.assertRaises(ValueError):
            run_benchmark(fictional_weeks(0))

    def test_no_sales_with_sufficient_clicks_is_priority_review(self):
        frame = fictional_weeks(2)
        frame.loc[0, ["Clicks", "Orders", "Sales", "Spend"]] = [60, 0, 0, 30]
        result = baseline_labels(frame)
        self.assertEqual(result.loc[0, "Baseline screen"], "No attributed sales review")
        self.assertTrue(bool(result.loc[0, "Baseline priority review"]))

    def test_no_sales_with_tiny_clicks_is_insufficient(self):
        frame = fictional_weeks(2)
        frame.loc[0, ["Clicks", "Orders", "Sales", "Spend"]] = [2, 0, 0, 1]
        result = baseline_labels(frame)
        self.assertEqual(result.loc[0, "Baseline screen"], "Evidence insufficient")

    def test_review_sets_partition_all_rows(self):
        result = run_benchmark(fictional_weeks(40), seeds=(42, 43))
        summary = result["summary"]
        counts = [summary[k] for k in ("overlap_rule_and_ml", "rule_only", "ml_only", "neither")]
        self.assertEqual(sum(counts), 40)
        self.assertEqual(summary["ml_anomaly_rows"], summary["overlap_rule_and_ml"] + summary["ml_only"])
        self.assertEqual(summary["baseline_priority_review_rows"], summary["overlap_rule_and_ml"] + summary["rule_only"])
        self.assertFalse(summary["ground_truth_labels_available"])
        self.assertFalse(summary["validated_accuracy_or_sales_lift"])

    def test_seed_model_is_reproducible(self):
        frame = fictional_weeks(40)
        a = model_flags(frame, seed=42)
        b = model_flags(frame, seed=42)
        self.assertTrue(np.array_equal(a, b))
        self.assertGreater(int(a.sum()), 0)

    def test_small_sample_abstains_from_ml(self):
        flags = model_flags(fictional_weeks(10))
        self.assertEqual(int(flags.sum()), 0)

    def test_invalid_report_and_contamination_rejected(self):
        frame = fictional_weeks(30)
        frame.loc[0, "Clicks"] = frame.loc[0, "Impressions"] + 1
        with self.assertRaises(ValueError):
            run_benchmark(frame)
        with self.assertRaises(ValueError):
            model_flags(fictional_weeks(30), contamination=0.8)

    def test_no_negative_metrics_and_invalid_target(self):
        frame = fictional_weeks(21)
        frame.loc[0, "Spend"] = -1
        with self.assertRaises(ValueError):
            run_benchmark(frame)
        with self.assertRaises(ValueError):
            run_benchmark(fictional_weeks(21), target_acos=0)


if __name__ == "__main__":
    unittest.main()
