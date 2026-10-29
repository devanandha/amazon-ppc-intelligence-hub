"""Independent, deterministic verification checks for the v3 research-only prototype.

Do not interpret passing tests as evidence of originality or real-world effectiveness.
"""
from __future__ import annotations

import sys
from pathlib import Path
import unittest
import numpy as np
from scipy.stats import betabinom

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adaptive_policy import (_posterior, posterior_profit_probability, immediate_bayes,
                             confidence_gate, one_step_voi)
from evaluate_pilot import draw_terms, initial, METHODS, EXPOSURE, HORIZON, EXPLORE, MARGIN


class IndependentChecks(unittest.TestCase):
    def test_posterior_is_exact_beta_binomial_update(self):
        a, b = _posterior([0, 10, 100], [0, 2, 30], (2, 8))
        np.testing.assert_allclose(a, [2, 4, 32])
        np.testing.assert_allclose(b, [8, 16, 78])

    def test_invalid_counts_fail_closed(self):
        for clicks, orders in [(np.nan, 0), (np.inf, 0), (-1, 0),
                               (12, 13), (10.5, 3), (10, 3.5), (3, -1)]:
            with self.subTest(clicks=clicks, orders=orders):
                with self.assertRaises(ValueError):
                    _posterior(clicks, orders)

    def test_invalid_priors_fail_closed(self):
        for prior in [(0, 9), (1, -2), (np.nan, 2), (np.inf, 3), (1,), (1, 2, 3)]:
            with self.subTest(prior=prior):
                with self.assertRaises(ValueError):
                    _posterior(10, 1, prior)

    def test_invalid_economics_fail_closed(self):
        for cpc, aov, margin in [(np.nan, 20, .25), (1, np.inf, .25),
                                 (-1, 20, .25), (1, 0, .25),
                                 (1, 20, -1), (1, 20, 1.2)]:
            with self.subTest(cpc=cpc, aov=aov, margin=margin):
                with self.assertRaises(ValueError):
                    one_step_voi(10, 1, cpc, aov, margin)
                with self.assertRaises(ValueError):
                    immediate_bayes(10, 1, cpc, aov, margin)

    def test_invalid_horizon_cost_fail_closed(self):
        for kw in [{'horizon': 10, 'explore_clicks': 10},
                   {'horizon': 10, 'explore_clicks': 0},
                   {'horizon': 100.5}, {'explore_clicks': 3.5},
                   {'explore_cost': -1}, {'explore_cost': np.nan},
                   {'scale_factor': 0.5}]:
            with self.subTest(kwargs=kw):
                with self.assertRaises(ValueError):
                    one_step_voi(10, 1, 1, 20, **kw)

    def test_profit_probability_matches_known_distribution(self):
        # Beta(2,2) survival at threshold 0.5 = 0.5 by symmetry.
        prob = posterior_profit_probability(2, 1, 1, 8, margin=.25, prior=(1, 1))
        self.assertAlmostEqual(float(prob), .5, places=11)

    def test_posterior_predictive_normalizes(self):
        a, b, m = 2., 17., 10
        probs = betabinom.pmf(np.arange(m+1), m, a, b)
        self.assertAlmostEqual(float(probs.sum()), 1., places=11)
        self.assertAlmostEqual(float(np.dot(np.arange(m+1), probs)), m*a/(a+b), places=11)

    def test_one_step_matches_explicit_enumeration(self):
        # Independent hand-derived comparison for a single term.
        n, y, cpc, aov, margin, H, m, factor, cost = 16, 2, .55, 29., .25, 35, 4, 1.25, .1
        a, b = 1+y, 9+n-y
        mu = a/(a+b)*aov*margin-cpc
        act_now = H*factor*max(mu, 0)
        expected_later = 0.
        for k in range(m+1):
            pk = betabinom.pmf(k, m, a, b)
            post_mu = (a+k)/(a+b+m)*aov*margin-cpc
            expected_later += pk*max(post_mu, 0)
        sample = m*mu+(H-m)*factor*expected_later-cost
        predicted = one_step_voi(n, y, cpc, aov, margin, (1,9), H, m, factor, cost)
        wanted = 'COLLECT_DATA' if sample > act_now+1e-9 else ('SCALE' if mu>0 else 'NEGATIVE')
        self.assertEqual(np.asarray(predicted).item(), wanted)

    def test_exploration_cost_cannot_increase_deferral(self):
        n, y, cpc, aov, p, _ = draw_terms(2042, 500)
        cheap = one_step_voi(n, y, cpc, aov, explore_cost=0)
        expensive = one_step_voi(n, y, cpc, aov, explore_cost=10)
        self.assertLessEqual(np.count_nonzero(expensive=='COLLECT_DATA'),
                             np.count_nonzero(cheap=='COLLECT_DATA'))

    def test_expected_value_of_information_not_negative_when_cost_zero(self):
        # With correct expectations and zero acquisition overhead, the optimal choice
        # over immediate/deferral can never have lower model-expected utility.
        n, y, cpc, aov, p, _ = draw_terms(2025, 100)
        a, b = _posterior(n, y)
        mu = a/(a+b)*aov*MARGIN-cpc
        expected_immediate = HORIZON*1.25*np.maximum(mu,0)
        k = np.arange(EXPLORE+1)
        predictive = betabinom.pmf(k[None,:], EXPLORE, a[:,None], b[:,None])
        post_mu = (a[:,None]+k[None,:])/(a[:,None]+b[:,None]+EXPLORE)*aov[:,None]*MARGIN-cpc[:,None]
        expected_collect = EXPLORE*mu + (HORIZON-EXPLORE)*1.25*(predictive*np.maximum(post_mu,0)).sum(axis=1)
        selected = one_step_voi(n,y,cpc,aov)
        best = np.where(selected=='COLLECT_DATA', expected_collect, expected_immediate)
        self.assertTrue(np.all(best >= expected_immediate-1e-7))

    def test_sample_generation_is_deterministic(self):
        first=draw_terms(2025, 25)
        second=draw_terms(2025, 25)
        for x, z in zip(first,second):np.testing.assert_array_equal(x,z)
        self.assertFalse(np.array_equal(first[0],draw_terms(2026,25)[0]))

    def test_synthetic_regret_nonnegative_and_comparable(self):
        n,y,cpc,aov,p,follow=draw_terms(2110, 400)
        mu=p*aov*.25-cpc
        oracle=HORIZON*1.25*np.maximum(mu,0)
        for method in METHODS:
            actions=initial(n,y,cpc,aov,method,(1,9))
            utility=HORIZON*np.array([EXPOSURE[a] for a in actions])*mu
            deferred=actions=='COLLECT_DATA'
            # For the initial policy before observation, oracle upper-bounds any
            # action with permitted exposure between 0 and 1.25.
            self.assertTrue(np.all(oracle>=utility-1e-8))
            self.assertTrue(np.isfinite(utility).all())

    def test_no_information_is_neither_automatically_profitable_nor_losing(self):
        self.assertEqual(str(immediate_bayes(0,0,.1,40)), 'SCALE')
        self.assertEqual(str(immediate_bayes(0,0,2.,20)), 'NEGATIVE')


if __name__=='__main__': unittest.main()

