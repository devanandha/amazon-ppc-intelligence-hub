"""Tests of v8 validation, observability, action fairness, and reproducibility."""
import unittest
import numpy as np
import independent_outcomes as v7
import v8_budget_aware as v8
from fair_baselines import allocate


class BudgetDecisionTests(unittest.TestCase):
    def setUp(self):
        self.d = v7.make_cohort(9864,v7.SCENARIOS['Mixture reference'])

    def _inputs(self, d=None):
        d=d or self.d
        return {k:d[k] for k in ('clicks','orders','cpc','aov','campaign')} | dict(budget_mult=d['scenario']['budget_mult'],gamma=.2)

    def test_output_shape(self):
        out=v8.budget_voi_score(**self._inputs())
        self.assertEqual(out.shape,(180,))
        self.assertTrue(np.isfinite(out).all())

    def test_actions_three_valid_classes(self):
        inputs=self._inputs()
        actions=v8.budget_action(**inputs)
        self.assertEqual(actions.shape,(180,))
        self.assertTrue(set(actions).issubset(set(v8.ACTIONS)))

    def test_no_latent_conversion_leak(self):
        before=v8.budget_voi_score(**self._inputs())
        altered=dict(self.d)
        altered['future_p']=np.ones(180)
        altered['margin']=np.zeros(180)
        altered['auction_shock']=np.full(180,10.)
        altered['probe_u']=np.zeros_like(self.d['probe_u'])
        altered['future_u']=np.zeros_like(self.d['future_u'])
        after=v8.budget_voi_score(**self._inputs(altered))
        np.testing.assert_array_equal(before,after)

    def test_no_unreported_future_data_in_rank(self):
        orig=v8.rank_terms(self.d,9864,.2)
        altered=dict(self.d)
        altered['future_p']=np.ones(180)
        altered['demand']=np.full(180,100000)
        altered['margin']=np.zeros(180)
        new=v8.rank_terms(altered,9864,.2)
        for name in v8.METHODS:
            np.testing.assert_array_equal(orig[name],new[name])

    def test_budget_information_affects_decision_scores(self):
        x=self._inputs()
        tight=v8.budget_voi_score(**(x | {'budget_mult':.4}))
        loose=v8.budget_voi_score(**(x | {'budget_mult':1.8}))
        self.assertGreater(np.max(np.abs(tight-loose)),1e-6)

    def test_invalid_counts_rejected(self):
        x=self._inputs()
        with self.assertRaises(ValueError):v8.budget_voi_score(**(x|{'orders':x['clicks']+1}))
        with self.assertRaises(ValueError):v8.budget_voi_score(**(x|{'orders':x['orders']+.25}))

    def test_invalid_economic_inputs_rejected(self):
        x=self._inputs()
        with self.assertRaises(ValueError):v8.budget_action(**(x|{'cpc':np.zeros(180)}))
        with self.assertRaises(ValueError):v8.budget_action(**(x|{'budget_mult':0.}))
        with self.assertRaises(ValueError):v8.budget_action(**(x|{'gamma':2.}))

    def test_budget_conservation(self):
        scores=v8.rank_terms(self.d,9864,.2)
        selection=allocate(scores['v8 budget VOI'],.1)
        r=v8.run_policy_v8(self.d,selection,.2)
        self.assertEqual(selection.sum(),18)
        self.assertTrue((r['spend_by_campaign']<=r['campaign_caps']+1e-7).all())

    def test_matched_action_modes_quota(self):
        results=v8.evaluate_one(self.d,9864,.2,.1,'v8 budget action')
        self.assertEqual(len(results),5)
        self.assertTrue(all(abs(x['defer_rate']-.1)<1e-12 for x in results))
        for x in results:self.assertAlmostEqual(x['scale_rate']+x['maintain_rate']+x['negative_rate'],1.)

    def test_reproducibility(self):
        one=v8.run_policy_v8(self.d,allocate(v8.rank_terms(self.d,9864,.2)['v8 budget VOI'],.1),.2)
        two=v8.run_policy_v8(self.d,allocate(v8.rank_terms(self.d,9864,.2)['v8 budget VOI'],.1),.2)
        self.assertAlmostEqual(one['profit'],two['profit'])
        np.testing.assert_array_equal(one['spend_by_campaign'],two['spend_by_campaign'])

    def test_different_seeds(self):
        other=v7.make_cohort(9865,v7.SCENARIOS['Mixture reference'])
        self.assertFalse(np.array_equal(self.d['orders'],other['orders']))

    def test_train_test_disjoint(self):
        self.assertFalse(set(v8.TRAIN_SEEDS)&set(v8.TEST_SEEDS))
        self.assertFalse(set(v8.TEST_SEEDS)&set(v7.SEEDS))

    def test_predictive_probabilities_well_defined(self):
        x=self._inputs()
        small={k:(v[:2] if hasattr(v,'__len__') else v) for k,v in x.items()}
        self.assertTrue(np.isfinite(v8.budget_voi_score(**small)).all())

    def test_same_scoring_no_test_labels(self):
        result1=v8.budget_voi_score(**self._inputs())
        result2=v8.budget_voi_score(**self._inputs())
        np.testing.assert_array_equal(result1,result2)


if __name__=='__main__':unittest.main()
