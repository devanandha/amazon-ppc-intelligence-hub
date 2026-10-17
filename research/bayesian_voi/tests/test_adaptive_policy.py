import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from adaptive_policy import _posterior, immediate_bayes, confidence_gate, one_step_voi, posterior_profit_probability
from evaluate_pilot import draw_terms, initial, METHODS, HORIZON, EXPLORE

class TestAdaptivePolicy(unittest.TestCase):
    def test_posterior(self):
        a,b=_posterior([10,20],[2,0],(1,9))
        np.testing.assert_array_equal(a,[3,1]);np.testing.assert_array_equal(b,[17,29])
        with self.assertRaises(ValueError):_posterior([1],[2])
    def test_posterior_profit_monotone(self):
        lo=posterior_profit_probability([40],[0],[1],[30],prior=(1,9))[0]
        hi=posterior_profit_probability([40],[10],[1],[30],prior=(1,9))[0]
        self.assertGreater(hi,lo)
    def test_voi_behavior(self):
        # Very profitable terms prefer SCALE; very unprofitable prefer NEGATIVE.
        s=one_step_voi(np.array([200,200]),np.array([60,0]),np.array([.3,2.]),np.array([50.,20.]))
        self.assertEqual(s[0],'SCALE');self.assertEqual(s[1],'NEGATIVE')
    def test_valid_actions(self):
        clicks,orders,cpc,aov,_,_=draw_terms(2077,200)
        for m in METHODS:
            a=initial(clicks,orders,cpc,aov,m,(1.,9.))
            self.assertEqual(len(a),len(clicks))
            self.assertTrue(set(a).issubset({'SCALE','MAINTAIN','REDUCE','NEGATIVE','COLLECT_DATA'}))

if __name__=='__main__':unittest.main()
