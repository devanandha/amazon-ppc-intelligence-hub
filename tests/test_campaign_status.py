"""Offline regression tests for campaign snapshot reconciliation.

All samples are invented. No client or account data is committed.
"""
import unittest

import pandas as pd

from campaign_status import parse_campaign_status, reconcile_campaigns


class CampaignStatusTests(unittest.TestCase):
    def test_simple_status_csv(self):
        data = b"Campaign Name,Status\nDemo Alpha,Enabled\nDemo Beta,Paused\n"
        roster = parse_campaign_status(data, "status.csv")
        self.assertEqual(roster.loc[0, "Status classification"], "Enabled")
        self.assertEqual(roster.loc[1, "Status classification"], "Paused")

    def test_bulksheet_ignores_ad_group_and_other_products(self):
        data = (
            "Product,Entity,Campaign Name,State\n"
            "Sponsored Products,Campaign,Demo Alpha,enabled\n"
            "Sponsored Products,Ad Group,Demo Alpha,paused\n"
            "Sponsored Brands,Campaign,Demo Gamma,enabled\n"
        ).encode()
        roster = parse_campaign_status(data, "bulk.csv")
        self.assertEqual(len(roster), 1)
        self.assertEqual(roster.loc[0, "Campaign"], "Demo Alpha")
        self.assertEqual(roster.loc[0, "Status classification"], "Enabled")

    def test_conflicting_states_never_assumed_active(self):
        data = b"Campaign Name,State\nDemo Alpha,enabled\nDemo Alpha,paused\n"
        roster = parse_campaign_status(data, "status.csv")
        self.assertEqual(roster.loc[0, "Status classification"], "Conflicting states")

    def test_reconciliation_finds_missing_and_unverified_campaigns(self):
        perf = pd.DataFrame([
            {"Campaign": "Demo Alpha", "Spend": 30, "Sales": 120, "Clicks": 10},
            {"Campaign": "Demo Delta", "Spend": 5, "Sales": 0, "Clicks": 2},
        ])
        roster = parse_campaign_status(
            b"Campaign Name,Status\nDemo Alpha,Enabled\nDemo Beta,Enabled\nDemo Gamma,Paused\n",
            "status.csv",
        )
        joined = reconcile_campaigns(perf, roster, 25)
        beta = joined.loc[joined["Campaign"] == "Demo Beta"].iloc[0]
        self.assertEqual(beta["Report coverage"], "Missing from selected report")
        self.assertEqual(beta["Strategy status"], "Coverage gap")
        gamma = joined.loc[joined["Campaign"] == "Demo Gamma"].iloc[0]
        self.assertEqual(gamma["Strategy status"], "Paused review")
        delta = joined.loc[joined["Campaign"] == "Demo Delta"].iloc[0]
        self.assertEqual(delta["Status classification"], "Not verified")
        self.assertEqual(delta["Strategy status"], "Status unknown")

    def test_no_snapshot_does_not_invent_enabled_state(self):
        perf = pd.DataFrame([
            {"Campaign": "Demo Alpha", "Spend": 15, "Sales": 75, "Clicks": 10},
        ])
        result = reconcile_campaigns(perf, None, 25)
        self.assertEqual(result.loc[0, "Status classification"], "Not verified")


if __name__ == "__main__":
    unittest.main()
