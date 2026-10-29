"""Independent-outcome v7 unit and invariant tests (all fully synthetic)."""
import copy
import unittest
import numpy as np
from independent_outcomes import (
    make_cohort, rank_terms, three_action_policy, run_policy, evaluate,
    summarize, natural_diagnostics, SCENARIOS, PRIOR, POLICIES, SEEDS,
    N_TERMS, TERMS_PER_CAMPAIGN, PROBE_CLICKS,
)
from fair_baselines import allocate, TRAIN_SEEDS, TEST_SEEDS


class TestIndependentOutcomeSimulator(unittest.TestCase):
    def setUp(self):
        self.scenario = SCENARIOS['Mixture reference']
        self.data = make_cohort(23002, self.scenario, 180)

    def test_training_and_old_and_new_test_seeds_disjoint(self):
        self.assertFalse(set(SEEDS) & set(TRAIN_SEEDS))
        self.assertFalse(set(SEEDS) & set(TEST_SEEDS))

    def test_prior_frozen_from_v5(self):
        self.assertEqual(PRIOR, (2., 18.))

    def test_deterministic_cohort(self):
        other=make_cohort(23002, self.scenario,180)
        for key in ('clicks','orders','margin','future_u','probe_u','auction_shock'):
            np.testing.assert_array_equal(self.data[key],other[key])

    def test_scenarios_have_different_future_processes(self):
        worse=make_cohort(23002,SCENARIOS['Future CVR -40%'],180)
        self.assertTrue(np.all(worse['future_p']<=self.data['future_p']))
        np.testing.assert_array_equal(worse['historical_p'],self.data['historical_p'])

    def test_invalid_cohort_size(self):
        with self.assertRaises(ValueError):make_cohort(1,self.scenario,1)

    def test_observed_orders_do_not_exceed_historical_clicks(self):
        self.assertTrue(np.all(self.data['orders']<=self.data['clicks']))

    def test_no_future_or_confidential_features_in_rank(self):
        scores=rank_terms(self.data,23002)
        altered=self.data.copy()
        for key in ('future_p','margin','auction_shock','demand','future_u','probe_u','report_u'):
            altered[key]=np.zeros_like(self.data[key])
        for method in POLICIES:
            np.testing.assert_array_equal(scores[method],rank_terms(altered,23002)[method])

    def test_random_rank_reproducible(self):
        a=rank_terms(self.data,23002)['Random']
        b=rank_terms(self.data,23002)['Random']
        np.testing.assert_array_equal(a,b)

    def test_fixed_selection_exact_quota(self):
        for fraction in (.05,.10,.20):
            for score in rank_terms(self.data,23002).values():
                self.assertEqual(int(allocate(score,fraction).sum()),round(180*fraction))

    def test_three_distinct_actions_possible(self):
        clicks=np.array([100,100,100]);orders=np.array([30,10,0]);cpc=np.array([1.,1.,1.]);aov=np.array([40.,40.,40.])
        self.assertEqual(set(three_action_policy(clicks,orders,cpc,aov)),{'SCALE','MAINTAIN','NEGATIVE'})

    def test_defer_allocation_only_changes_own_followup_data(self):
        s=np.zeros(180,dtype=bool)
        none=run_policy(self.data,s)
        s[0]=True
        one=run_policy(self.data,s)
        self.assertEqual(none['defer_rate'],0)
        self.assertAlmostEqual(one['defer_rate'],1/180)
        self.assertEqual(one['probe_complete_rate'],1)

    def test_spend_never_exceeds_per_campaign_caps(self):
        for sc in SCENARIOS.values():
            d=make_cohort(23002,sc,180)
            for method,ranking in rank_terms(d,23002).items():
                selected=allocate(ranking,.2)
                out=run_policy(d,selected)
                self.assertTrue(np.all(out['spend_by_campaign'] <= out['campaign_caps']+1e-6),method)
                self.assertEqual(out['probe_complete_rate'],1.0)

    def test_budget_constraint_also_holds_under_extreme_quota(self):
        for sc in SCENARIOS.values():
            d=make_cohort(23002,sc,180)
            out=run_policy(d,np.ones(180,dtype=bool))
            self.assertTrue(np.all(out['spend_by_campaign']<=out['campaign_caps']+1e-6))

    def test_actual_budget_changes_with_scenario(self):
        constrained=make_cohort(23002,SCENARIOS['Campaign budgets halved'],180)
        selected=allocate(rank_terms(self.data,23002)['v5 VOI rank'],.1)
        original=run_policy(self.data,selected)
        tight=run_policy(constrained,selected)
        self.assertTrue(np.allclose(tight['campaign_caps'],original['campaign_caps']*.5))
        self.assertLessEqual(tight['spend_per_term'],original['spend_per_term'])

    def test_delayed_reporting_not_more_observed_than_true(self):
        delayed=make_cohort(23002,SCENARIOS['Conversions 50% visible'],180)
        self.assertTrue(np.all(delayed['orders']<=self.data['orders']))
        selected=np.ones(180,dtype=bool)
        result=run_policy(delayed,selected)
        self.assertLessEqual(result['probe_orders_visible_fraction'],1.)

    def test_exploration_changes_profit_under_hidden_outcomes(self):
        s=allocate(rank_terms(self.data,23002)['v5 VOI rank'],.1)
        original=run_policy(self.data,s)
        mutated=self.data.copy()
        mutated['margin']=np.full(180,.01)
        different=run_policy(mutated,s)
        self.assertNotEqual(original['profit'],different['profit'])

    def test_action_proportions_partition_terms(self):
        selected=allocate(rank_terms(self.data,23002)['v5 VOI rank'],.1)
        r=run_policy(self.data,selected)
        self.assertAlmostEqual(r['scale_rate']+r['maintain_rate']+r['negative_rate'],1.)
        self.assertGreater(r['maintain_rate'],0.)

    def test_evaluation_expected_grid_and_exact_defer(self):
        f=evaluate(seeds=(23002,23003),scenario_names=('Mixture reference',),quotas=(.10,),n=180)
        self.assertEqual(len(f),2*len(POLICIES))
        self.assertTrue(np.allclose(f.defer_rate,.10))
        self.assertTrue(np.allclose(f.probe_complete_rate,1.0))
        s,p=summarize(f)
        self.assertEqual(len(s),len(POLICIES))
        self.assertEqual(len(p),len(POLICIES)-1)

    def test_unmatched_diagnostics_label_zero_exploration(self):
        f=natural_diagnostics(seeds=(23002,),scenario_names=('Mixture reference',),n=180)
        self.assertEqual(len(f),2)
        self.assertEqual(f[f.method=='No exploration'].iloc[0].defer_rate,0.)


if __name__=='__main__':
    unittest.main()

