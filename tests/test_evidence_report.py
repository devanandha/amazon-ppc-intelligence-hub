"""HTML report does not execute or leak untrusted search-term markup."""

import unittest
import pandas as pd

from evidence_report import create_evidence_report


class EvidenceReportTests(unittest.TestCase):
    @staticmethod
    def audit():
        return pd.DataFrame({
            "Customer Search Term": ["<script>alert('XSS')</script>", "safe search"],
            "Recommended Action": ["Scale carefully", "Monitor"],
            "Evidence status": ["More evidence needed", "Manual review ready"],
            "Evidence justification": ["<img src=x onerror=alert(1)>", "No risk detected"],
            "ML review flag": ["Unusual pattern — review", "Typical within dataset"],
            "High-impact baseline action": [True, False],
        })

    def test_escapes_untrusted_terms_and_explanations(self):
        html = create_evidence_report(
            self.audit(), target_acos=25, synthetic_demo=True,
        ).decode("utf-8")
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;img", html)
        self.assertIn("Devanandha Vellaramkuzhiyil Shaji", html)

    def test_uploaded_report_is_marked_confidential(self):
        html = create_evidence_report(
            self.audit(), target_acos=25, synthetic_demo=False,
        ).decode("utf-8")
        self.assertIn("Treat as confidential", html)
        self.assertIn("USER-UPLOADED ACCOUNT REPORT", html)

    def test_requires_correct_ledger_columns(self):
        with self.assertRaises(ValueError):
            create_evidence_report(
                pd.DataFrame({"broken": [1]}), target_acos=25,
                synthetic_demo=True,
            )


if __name__ == "__main__":
    unittest.main()
