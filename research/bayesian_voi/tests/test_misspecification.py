import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from misspecification_experiment import sample_cohort,score_cohort,run,summarize,SCENARIOS,POLICIES

class MisspecificationChecks(unittest.TestCase):
    def test_full_attribution_observes_every_order(self):
        a=sample_cohort(7,80,SCENARIOS['Stationary reference'])
        np.testing.assert_array_equal(a['orders'],a['true_orders'])
        np.testing.assert_array_equal(a['observed_followup'],a['prospect_true_orders'])

    def test_cvr_drift_is_defined(self):
        a=sample_cohort(7,80,SCENARIOS['CVR decline 40%'])
        np.testing.assert_allclose(a['future_p'],.6*a['historical_p'])

    def test_censored_conversion_counts_are_bounded(self):
        a=sample_cohort(11,800,SCENARIOS['Delayed attribution 65% visible'])
        self.assertTrue(np.all(a['orders']<=a['true_orders']))
        self.assertTrue(np.all(a['observed_followup']<=a['prospect_true_orders']))

    def test_policy_comparison_deterministic(self):
        a=sample_cohort(7,100,SCENARIOS['Combined adverse'])
        b=sample_cohort(7,100,SCENARIOS['Combined adverse'])
        np.testing.assert_array_equal(a['orders'],b['orders'])
        for policy in POLICIES:
            self.assertEqual(score_cohort(a,policy,2.),score_cohort(b,policy,2.))

    def test_pairing_across_policies(self):
        x=run(seeds=(10,11),n=40,overheads=(0.,),scenarios={'test':SCENARIOS['Stationary reference']})
        self.assertEqual(len(x),2*len(POLICIES))
        s,d=summarize(x)
        self.assertEqual(len(s),len(POLICIES))
        self.assertEqual(len(d),len(POLICIES)-1)
        self.assertTrue((x.regret >=-1e-9).all())

if __name__=='__main__':unittest.main()
