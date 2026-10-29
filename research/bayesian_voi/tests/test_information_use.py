import unittest
import numpy as np
import information_use as m
import v8_budget_aware as v8
import independent_outcomes as v7
from fair_baselines import allocate

class InformationInterventionTests(unittest.TestCase):
    def cohort(self,scenario='Mixture reference'):
        return v7.make_cohort(910001,v7.SCENARIOS[scenario])
    def test_original_use_parity(self):
        for scenario in v8.SCENARIOS:
            c=self.cohort(scenario)
            s=allocate(m.ranking_scores(c,910001)['v8 budget VOI'],.1)
            a=m.run_information_policy(c,s)
            b=v8.run_policy_v8(c,s,0.)
            for k in b:np.testing.assert_allclose(a[k],b[k],rtol=0,atol=1e-10)
    def test_identical_probe_cashflows_and_decomposition(self):
        c=self.cohort();s=allocate(m.ranking_scores(c,910001)['Random'],.2)
        a=m.run_information_policy(c,s);b=m.run_information_policy(c,s,use_evidence=False)
        for k in ('probe_contribution_per_term','probe_spend','probe_spend_by_campaign','probe_complete_rate'):
            np.testing.assert_array_equal(a[k],b[k])
        for r in (a,b):self.assertAlmostEqual(r['profit'],r['probe_contribution_per_term']+r['downstream_contribution_per_term'])
    def test_withheld_decisions_use_historical_counts(self):
        c=self.cohort();s=np.ones(len(c['clicks']),bool)
        r=m.run_information_policy(c,s,use_evidence=False)
        expected=v8.budget_action(c['clicks'],c['orders'],c['cpc'],c['aov'],c['campaign'],c['scenario']['budget_mult'],0.)
        np.testing.assert_array_equal(r['actions'],expected)
        p=(2+c['orders'])/(20+c['clicks'])
        np.testing.assert_allclose(r['priority'],(p*.25*c['aov']-c['cpc'])/c['cpc'])
    def test_no_probe_parity(self):
        c=self.cohort();s=np.zeros(len(c['clicks']),bool)
        a=m.run_information_policy(c,s);b=m.run_information_policy(c,s,use_evidence=False)
        self.assertEqual(a['profit'],b['profit']);self.assertEqual(a['probe_contribution_per_term'],0.)
        self.assertEqual(a['profit'],v8.run_policy_v8(c,s,0.)['profit'])
    def test_budget_and_determinism(self):
        c=self.cohort('Combined adverse');s=np.ones(len(c['clicks']),bool)
        for use in (True,False):
            a=m.run_information_policy(c,s,use_evidence=use);b=m.run_information_policy(c,s,use_evidence=use)
            self.assertEqual(a['profit'],b['profit'])
            self.assertTrue(np.all(a['spend_by_campaign']<=a['campaign_caps']+1e-6))
    def test_selection_hidden_outcome_invariance(self):
        c=self.cohort();d=dict(c)
        for k in ('future_p','probe_u','future_u','report_u','margin','auction_shock','demand'):d[k]=np.zeros_like(c[k])
        for k,v in m.ranking_scores(c,910001).items():np.testing.assert_array_equal(v,m.ranking_scores(d,910001)[k])
    def test_new_seeds_disjoint(self):
        self.assertFalse(set(m.SEEDS)&(set(v8.TEST_SEEDS)|set(v8.TRAIN_SEEDS)|set(v7.SEEDS)))
    def test_small_grid_and_exact_quota(self):
        a,b,c=m.evaluate(seeds=[910001,910002],scenarios=['Mixture reference'],quotas=[.1])
        self.assertEqual(len(a),30);self.assertEqual(len(b),14);self.assertEqual(len(c),2)
        self.assertTrue(np.all(a[a.arm!='no_probe'].defer_rate==.1))
        summary,contrasts=m.summarize(a,b);self.assertEqual(len(contrasts),21)

if __name__=='__main__':unittest.main()
