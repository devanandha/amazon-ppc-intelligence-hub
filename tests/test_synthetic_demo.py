"""Sanity checks for the public demonstration dataset."""

import unittest

from create_synthetic_demo import make_synthetic_dataframe


class SyntheticDemoTests(unittest.TestCase):
    def test_demo_is_reproducible_and_nonempty(self):
        first = make_synthetic_dataframe()
        second = make_synthetic_dataframe()
        self.assertGreater(len(first), 100)
        self.assertTrue(first.equals(second))

    def test_demo_has_required_advertising_fields(self):
        report = make_synthetic_dataframe()
        required = [
            "Campaign Name", "Ad Group Name", "Targeting", "Match Type",
            "Customer Search Term", "Impressions", "Clicks", "Spend",
            "7 Day Total Sales", "7 Day Total Orders (#)",
        ]
        self.assertTrue(set(required).issubset(report.columns))
        self.assertTrue((report["Clicks"] <= report["Impressions"]).all())
        self.assertTrue((report["7 Day Total Orders (#)"] <= report["Clicks"]).all())
        self.assertTrue((report["Spend"] >= 0).all())
        self.assertTrue((report["7 Day Total Sales"] >= 0).all())

    def test_demo_does_not_use_company_data(self):
        report = make_synthetic_dataframe()
        self.assertEqual(set(report["Portfolio name"]), {"Synthetic Portfolio"})
        self.assertEqual(set(report["Retailer"]), {"Synthetic"})


if __name__ == "__main__":
    unittest.main()
