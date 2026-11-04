"""Evidence-gating tests: original recommendations are preserved, never auto-approved."""

import unittest
import numpy as np
import pandas as pd

from decision_assurance import (
    build_decision_ledger, acossensitivity, TERM, CLICKS,
    ORDERS, ACTIONS,
)


class DecisionAssuranceTests(unittest.TestCase):
    @staticmethod
    def samples():
        rules = pd.DataFrame(
            {
                TERM: ["empty", "sparse", "outlier", "mature", "invalid"],
                CLICKS: [0, 7, 80, 120, 6],
                ORDERS: [0, 1, 10, 20, 9],
                ACTIONS: [
                    "Collect data", "Scale carefully", "Scale carefully",
                    "Maintain / harvest", "Negative / pause review",
                ],
                "Bid Adjustment %": [0, 30, 20, 0, -100],
                "Reason": ["No clicks", "Rule", "Rule", "Rule", "Rule"],
                "ACOS %": [np.nan, 4, 10, 24, np.nan],
            }
        )
        ml = pd.DataFrame(
            {
                TERM: ["mature", "invalid", "outlier", "sparse", "empty"],
                "ML review flag": [
                    "Typical within dataset", "Not evaluated",
                    "Unusual pattern — review", "Not evaluated",
                    "Not evaluated",
                ],
                "CVR 90% lower": [12, np.nan, 6, 2, np.nan],
                "CVR 90% upper": [22, np.nan, 17, 46, np.nan],
                "Evidence note": ["Check", "Invalid", "Check", "Sparse", "Empty"],
            }
        )
        return rules, ml

    def test_guardrails_and_original_rule_preservation(self):
        rules, ml = self.samples()
        result = build_decision_ledger(rules, ml)
        states = result.set_index(TERM)["Evidence status"].to_dict()
        self.assertEqual(states["empty"], "More evidence needed")
        self.assertEqual(states["sparse"], "More evidence needed")
        self.assertEqual(states["outlier"], "Investigate model-rule conflict")
        self.assertEqual(states["mature"], "Manual review ready")
        self.assertEqual(states["invalid"], "Check data quality")
        self.assertEqual(result[ACTIONS].tolist(), rules[ACTIONS].tolist())
        self.assertTrue(all("approved" not in s.lower() for s in states.values()))
        self.assertEqual(
            result.loc[result[TERM] == "outlier", "ML review flag"].iloc[0],
            "Unusual pattern — review",
        )

    def test_does_not_join_model_info_by_wrong_row(self):
        rules, ml = self.samples()
        a = build_decision_ledger(rules, ml)
        b = build_decision_ledger(rules, ml.iloc[::-1].reset_index(drop=True))
        pd.testing.assert_frame_equal(a, b)

    def test_rejects_mismatched_or_duplicate_terms(self):
        rules, ml = self.samples()
        with self.assertRaises(ValueError):
            build_decision_ledger(rules, ml.iloc[:3])
        duplicate = rules.copy()
        duplicate.loc[1, TERM] = "empty"
        with self.assertRaises(ValueError):
            build_decision_ledger(duplicate, ml)

    def test_poor_uncertainty_withholds_high_impact(self):
        rules, ml = self.samples()
        rules.loc[3, ACTIONS] = "Scale carefully"
        rules.loc[3, "Bid Adjustment %"] = 25
        ml.loc[0, "CVR 90% upper"] = 45
        assessment = build_decision_ledger(rules, ml, max_interval_width_pp=15)
        self.assertEqual(
            assessment.loc[assessment[TERM] == "mature", "Evidence status"].iloc[0],
            "More evidence needed",
        )

    def test_sensitivity_is_not_prospective_performance(self):
        rules, _ = self.samples()
        def fake_classifier(frame, target, min_clicks, min_orders):
            result = frame.copy()
            result[ACTIONS] = np.where(
                result["ACOS %"].fillna(10_000) <= target,
                "Maintain / harvest", "Reduce bid"
            )
            return result
        # For this isolated test, align the baseline with the fake classifier.
        rules[ACTIONS] = fake_classifier(rules, 25, 15, 3)[ACTIONS]
        assessed = acossensitivity(
            rules, fake_classifier, 25, negative_clicks=15, min_orders=3,
        )
        self.assertEqual(len(assessed), len(rules))
        self.assertEqual(
            assessed["Target ACOS 100% of current"].tolist(),
            rules[ACTIONS].tolist(),
        )
        self.assertTrue(
            assessed["Scenario agreement (of 5)"].between(1, 5).all()
        )


if __name__ == "__main__":
    unittest.main()
