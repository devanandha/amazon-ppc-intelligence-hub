"""Smoke-test v3's preserved analytics without importing the interactive UI."""
import unittest
import pandas as pd

from create_synthetic_demo import make_synthetic_dataframe
from ppc_engine import (
    COL, clean_report, aggregate, build_action_tables, totals, make_export,
)
from ml_insights import analyse_search_terms
from decision_assurance import build_decision_ledger


class V3EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        report, missing = clean_report(make_synthetic_dataframe())
        cls.report = report
        cls.missing = missing

    def test_demo_is_valid_and_aggregates(self):
        self.assertEqual(self.missing, [])
        self.assertFalse(self.report.empty)
        kpi = totals(self.report)
        self.assertGreater(kpi["Spend"], 0)
        self.assertGreater(kpi["Sales"], 0)
        campaigns = aggregate(self.report, [COL["campaign"]])
        self.assertGreater(len(campaigns), 0)

    def test_v3_rule_ml_and_evidence_pipeline(self):
        terms, harvest, negatives, asins = build_action_tables(
            self.report, 25.0, 15, 3,
        )
        self.assertGreaterEqual(len(terms), 12)
        ml, meta = analyse_search_terms(terms, min_clicks=5)
        ledger = build_decision_ledger(terms, ml)
        self.assertEqual(len(ledger), len(terms))
        self.assertIn("Evidence status", ledger)
        self.assertIn("Recommended Action", ledger)
        self.assertEqual(ledger["Recommended Action"].tolist(), terms["Recommended Action"].tolist())
        self.assertGreaterEqual(meta["eligible_terms"], 12)

    def test_eight_sheet_excel_export(self):
        kpi = totals(self.report)
        terms, harvest, negatives, asins = build_action_tables(
            self.report, 25, 15, 3,
        )
        summary = pd.DataFrame(
            [{"Metric": k, "Value": v} for k, v in kpi.items()]
        )
        campaigns = aggregate(self.report, [COL["campaign"]])
        adgroups = aggregate(self.report, [COL["campaign"], COL["ad_group"]])
        wasted = terms[(terms[COL["orders"]] == 0) & (terms[COL["spend"]] > 0)]
        output = make_export(
            summary, campaigns, adgroups, terms,
            harvest, negatives, asins, wasted, "£",
        )
        with pd.ExcelFile(output) as book:
            self.assertEqual(len(book.sheet_names), 8)
            self.assertIn("Executive Summary", book.sheet_names)
            self.assertIn("All Search Terms", book.sheet_names)


if __name__ == "__main__":
    unittest.main()
