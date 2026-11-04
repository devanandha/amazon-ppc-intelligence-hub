"""PPC Buddy is decorative, data-grounded and clearly not a chatbot."""

import unittest
from unittest.mock import patch

from landing_experience import render_ppc_buddy, inject_experience_styles


class PPCBuddyTests(unittest.TestCase):
    def test_demo_summary_uses_real_calculated_inputs(self):
        with patch("landing_experience.st.html") as html:
            render_ppc_buddy(
                account_acos=32.84, target_acos=25.0,
                ad_sales=31580.12, harvest_count=7,
                negative_count=3, demo_mode=True,
            )
        emitted = html.call_args.args[0]
        self.assertIn("I'm PPC Buddy.", emitted)
        self.assertIn("7.8 percentage points above", emitted)
        self.assertIn("7 harvest candidates", emitted)
        self.assertIn("3 negative-review candidates", emitted)
        self.assertIn("Fictional demonstration", emitted)
        self.assertIn("not a conversational AI", emitted)
        self.assertIn('class="dv-robot-head"', emitted)

    def test_uploaded_report_is_not_mislabeled_synthetic(self):
        with patch("landing_experience.st.html") as html:
            render_ppc_buddy(
                account_acos=15.0, target_acos=25.0,
                ad_sales=400.0, harvest_count=0,
                negative_count=0, demo_mode=False,
            )
        emitted = html.call_args.args[0]
        self.assertIn("10.0 percentage points within", emitted)
        self.assertIn("Uploaded report", emitted)
        self.assertNotIn("Fictional demonstration", emitted)

    def test_no_sales_does_not_claim_zero_acos_means_profitable(self):
        with patch("landing_experience.st.html") as html:
            render_ppc_buddy(
                account_acos=0.0, target_acos=25.0,
                ad_sales=0.0, harvest_count=0,
                negative_count=0, demo_mode=True,
            )
        emitted = html.call_args.args[0]
        self.assertIn("no attributed sales", emitted)
        self.assertNotIn("within your target", emitted)

    def test_robot_styles_are_embedded_without_external_assets(self):
        with patch("landing_experience.st.html") as html:
            inject_experience_styles()
        emitted = html.call_args.args[0]
        self.assertIn(".dv-buddy-panel", emitted)
        self.assertIn(".dv-robot-head", emitted)
        self.assertIn("prefers-reduced-motion", emitted)
        self.assertNotIn("@import", emitted)


if __name__ == "__main__":
    unittest.main()
