"""Independently check validation split, allocation, rankings and economics."""
import unittest
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from adaptive_policy import one_step_voi
from fair_baselines import (TRAIN_SEEDS, TEST_SEEDS, N, SCENARIOS,
    SCENARIO_NAMES, M, H, SCALE, OVERHEAD, PRIOR_OPTIONS, beta_binomial_logscore,
    fit_prior, fit_hybrid, allocate, voi_increment, compute_scores,
    score_fixed_allocation, test_evaluation, hybrid_score, summarize)
from misspecification_experiment import sample_cohort


class FairBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cohort=sample_cohort(7011, 300, SCENARIOS['Stationary reference'])
        cls.prior=(1., 9.)

    def test_disjoint_seed_sets(self):
        self.assertFalse(set(TRAIN_SEEDS)&set(TEST_SEEDS))
        self.assertTrue(set(SCENARIO_NAMES)==set(SCENARIOS))

    def test_budget_is_exact_for_each_policy(self):
        scores=compute_scores(self.cohort,self.prior,7011)
        for name in ('Random allocation','Fewest clicks','Profitability uncertainty',
                     'One-step VOI rank'):
            for quota in (.05,.10,.20):
                a=allocate(scores[name],quota)
                self.assertEqual(a.sum(),int(np.floor(len(a)*quota+.5)))
                self.assertEqual(a.dtype,np.dtype(bool))

    def test_score_has_no_future_outcome_leakage(self):
        baseline=compute_scores(self.cohort,self.prior,7011)
        changed=dict(self.cohort)
        changed['future_p']=np.ones(len(self.cohort['clicks']))
        changed['true_margin']=np.zeros(len(self.cohort['clicks']))
        changed['observed_followup']=np.zeros(len(self.cohort['clicks']),dtype=int)
        rerun=compute_scores(changed,self.prior,7011)
        for k,v in baseline.items():
            np.testing.assert_array_equal(v,rerun[k])

    def test_gain_sign_equivalent_to_existing_voi_action(self):
        d=self.cohort
        scores=voi_increment(d['clicks'],d['orders'],d['cpc'],d['aov'],self.prior)
        actions=one_step_voi(d['clicks'],d['orders'],d['cpc'],d['aov'],
                             prior=self.prior,horizon=H,explore_clicks=M,
                             scale_factor=SCALE,explore_cost=OVERHEAD)
        np.testing.assert_array_equal(scores>1e-9,actions=='COLLECT_DATA')

    def test_regret_oracle_with_no_selection(self):
        d=self.cohort
        score=score_fixed_allocation(d,np.zeros(len(d['clicks']),bool),self.prior)
        self.assertEqual(score['defer_rate'],0.)
        self.assertGreaterEqual(score['regret'],0.)
        self.assertTrue(np.isfinite(score['utility']))

    def test_all_deferred_pays_cost(self):
        d=self.cohort
        a=np.ones(len(d['clicks']),bool)
        x=score_fixed_allocation(d,a,self.prior,overhead=0.)
        y=score_fixed_allocation(d,a,self.prior,overhead=2.)
        self.assertAlmostEqual(y['regret']-x['regret'],2.,places=8)
        self.assertAlmostEqual(y['utility']-x['utility'],-2.,places=8)

    def test_all_scores_deterministic(self):
        a=compute_scores(self.cohort,self.prior,7011)
        b=compute_scores(self.cohort,self.prior,7011)
        for key in a:np.testing.assert_array_equal(a[key],b[key])

    def test_stable_ties_budget(self):
        a=allocate(np.ones(10),.20)
        np.testing.assert_array_equal(a, [True,True]+[False]*8)

    def test_invalid_budget_and_score_rejected(self):
        for x in (0.,1.,-1.):
            with self.assertRaises(ValueError):allocate(np.ones(10),x)
        with self.assertRaises(ValueError):allocate(np.array([1.,np.nan]),.10)

    def test_hybrid_weights_boundaries(self):
        scores=compute_scores(self.cohort,self.prior,7011)
        np.testing.assert_array_equal(hybrid_score(scores,0.),scores['hybrid_uncertainty_ranks'])
        np.testing.assert_array_equal(hybrid_score(scores,1.),scores['hybrid_voi_ranks'])

    def test_shared_prior_uses_historical_data(self):
        a=beta_binomial_logscore(np.array([10,20]),np.array([2,3]),(1.,9.))
        self.assertEqual(len(a),2)
        self.assertTrue(np.isfinite(a).all())

    def test_fit_train_smoke(self):
        ds=[sample_cohort(i,150,SCENARIOS['Stationary reference']) for i in (801,802)]
        prior,_=fit_prior(ds)
        self.assertIn(prior,PRIOR_OPTIONS)
        best,_=fit_hybrid(ds,[801,802],prior)
        self.assertIn(best,(0.,.25,.5,.75,1.))

    def test_tiny_test_and_paired_result(self):
        df=test_evaluation(self.prior,1.,seed_set=(20001,20002,20003),n=100,
            scenario_names=('Stationary reference',),budgets=(.1,))
        self.assertEqual(len(df),3*5)
        self.assertTrue(np.allclose(df['defer_rate'],.1))
        a,b=summarize(df)
        self.assertEqual(len(a),5)
        self.assertEqual(len(b),4)

if __name__=='__main__':unittest.main()
