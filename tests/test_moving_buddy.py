"""Tests for the isolated, animated PPC Buddy component."""
import unittest
from unittest.mock import patch

from ppc_buddy_component import buddy_html, buddy_message, render_buddy


class MovingBuddyTests(unittest.TestCase):
    def sample(self, **overrides):
        values = dict(
            account_acos=33.0,
            target_acos=25.0,
            ad_sales=31580.0,
            harvest_count=7,
            negative_count=3,
            demo_mode=True,
        )
        values.update(overrides)
        return buddy_html(**values)

    def test_animated_robot_contains_movement_and_friendly_copy(self):
        html = self.sample()
        self.assertIn("I'm PPC Buddy.", html)
        self.assertIn("8.0 percentage points above your target", html)
        for keyframe in ("floatBot", "wave", "blink", "heartBeat"):
            self.assertIn("@keyframes " + keyframe, html)
        self.assertIn("motion-on", html)
        self.assertIn("FICTIONAL DEMO", html)
        self.assertNotIn("<script", html)

    def test_motion_can_be_disabled(self):
        html = self.sample(animated=False)
        self.assertIn("motion-off", html)
        self.assertIn("prefers-reduced-motion", html)

    def test_avoids_misleading_claims_for_no_sales(self):
        summary = buddy_message(
            account_acos=0.0, target_acos=25.0, ad_sales=0.0
        )
        self.assertIn("No attributed ad sales", summary)
        self.assertNotIn("below your target", summary)

    def test_uploaded_data_is_not_mislabeled_demo(self):
        html = self.sample(demo_mode=False)
        self.assertIn("YOUR UPLOADED REPORT", html)
        self.assertNotIn("FICTIONAL DEMO", html)

    def test_weekly_campaign_buddy_uses_campaign_specific_guidance(self):
        html = self.sample(
            account_acos=28.30, target_acos=25.0,
            weekly_campaign_mode=True, campaign_count=8, anomaly_count=42,
            demo_mode=False,
        )
        self.assertIn("Observed campaign ACOS is 3.3 percentage points above", html)
        self.assertIn("8 campaigns", html)
        self.assertIn("42 unusual weekly patterns", html)
        self.assertIn("YOUR UPLOADED WEEKLY CAMPAIGN DATA", html)
        self.assertIn("no keyword or automatic bid recommendations", html)
        self.assertIn("@keyframes floatBot", html)
        self.assertNotIn("harvest candidates", html)
        self.assertNotIn("negative-review candidates", html)

    def test_weekly_campaign_buddy_does_not_claim_success_without_sales(self):
        html = self.sample(
            account_acos=float("nan"), ad_sales=0,
            weekly_campaign_mode=True, campaign_count=8, anomaly_count=0,
        )
        self.assertIn("No attributed sales", html)
        self.assertNotIn("percentage points below", html)

    def test_component_has_explicit_height(self):
        with patch("ppc_buddy_component.components.html") as embed:
            render_buddy(
                account_acos=33,
                target_acos=25,
                ad_sales=1000,
                harvest_count=5,
                negative_count=2,
                demo_mode=True,
            )
        self.assertEqual(embed.call_args.kwargs["height"], 293)
        self.assertFalse(embed.call_args.kwargs["scrolling"])


if __name__ == "__main__":
    unittest.main()
