"""Tests for exploratory, non-predictive ML review and CVR uncertainty."""

import unittest

import numpy as np
import pandas as pd

from create_synthetic_demo import make_synthetic_dataframe
from ml_insights import (
    analyse_search_terms, TERM, IMPRESSIONS, CLICKS,
    SPEND, ORDERS, SALES,
)


class MLReviewTests(unittest.TestCase):
    @staticmethod
    def report():
        raw = make_synthetic_dataframe()
        return (
            raw.groupby(TERM, as_index=False)[
                [IMPRESSIONS, CLICKS, SPEND, ORDERS, SALES]
            ]
            .sum()
        )

    def test_model_runs_on_reproducible_synthetic_report(self):
        reviewed, info = analyse_search_terms(self.report())
        self.assertTrue(info["trained"])
        self.assertGreaterEqual(info["eligible_terms"], 12)
        self.assertGreater(info["flagged_terms"], 0)
        self.assertIn("ML review flag", reviewed.columns)
        self.assertIn("CVR 90% upper", reviewed.columns)

    def test_model_is_deterministic_given_same_input(self):
        source = self.report()
        a, left = analyse_search_terms(source)
        b, right = analyse_search_terms(source)
        pd.testing.assert_frame_equal(a, b)
        self.assertEqual(left, right)

    def test_interval_bounds_when_binomial_assumptions_hold(self):
        assessed, _ = analyse_search_terms(self.report())
        valid = assessed.dropna(subset=["CVR 90% lower", "CVR 90% upper"])
        self.assertGreater(len(valid), 0)
        self.assertTrue((valid["CVR 90% lower"] >= 0).all())
        self.assertTrue((valid["CVR 90% upper"] <= 100).all())
        self.assertTrue(
            (valid["CVR 90% lower"] <= valid["CVR 90% upper"]).all()
        )

    def test_withholds_interval_for_multiple_orders_per_click(self):
        report = pd.DataFrame([
            {TERM: "example", IMPRESSIONS: 100, CLICKS: 2,
             SPEND: 4.5, ORDERS: 3, SALES: 30}
        ])
        assessed, info = analyse_search_terms(report)
        self.assertFalse(info["trained"])
        self.assertTrue(np.isnan(assessed.loc[0, "CVR 90% lower"]))
        self.assertIn("Orders exceed clicks", assessed.loc[0, "Evidence note"])

    def test_too_few_terms_does_not_fake_ml_output(self):
        assessed, info = analyse_search_terms(self.report().head(5))
        self.assertFalse(info["trained"])
        self.assertEqual(info["flagged_terms"], 0)
        self.assertTrue((assessed["ML review flag"] == "Not evaluated").all())

    def test_input_report_remains_unchanged(self):
        report = self.report()
        original = report.copy(deep=True)
        analyse_search_terms(report)
        pd.testing.assert_frame_equal(report, original)


if __name__ == "__main__":
    unittest.main()
