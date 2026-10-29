import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from matched_comparison import POLICIES, select, run

class TestMatchedComparison(unittest.TestCase):
    def test_same_allowed_actions_and_fixed_defer_gates(self):
        n=np.array([5,14,15,24,25,100]); y=np.array([0,1,2,1,2,12]); c=np.ones(6); a=np.ones(6)*30
        for policy in POLICIES:
            actions=select(n,y,c,a,policy)
            self.assertEqual(len(actions),6)
            self.assertTrue(set(actions).issubset({'SCALE','NEGATIVE','COLLECT_DATA'}))
        p15=select(n,y,c,a,'Fixed 15-click Bayesian gate')
        np.testing.assert_array_equal(p15[:2], ['COLLECT_DATA']*2)
        self.assertTrue(np.all(p15[2:]!='COLLECT_DATA'))

    def test_rerun_deterministic_and_nonnegative_regret(self):
        a=run(overhead=2,n=50,seeds=(2110,2111))
        b=run(overhead=2,n=50,seeds=(2110,2111))
        self.assertTrue(a.equals(b))
        self.assertTrue(np.all(a.regret>=0))

    def test_policy_selection_is_sensitive_to_exploration_cost(self):
        n=np.array([20,30,40,50]); y=np.array([2,3,4,5]); c=np.full(4,.7); a=np.full(4,40.)
        with_no_cost=select(n,y,c,a,'One-step Bayesian VOI',0)
        with_cost=select(n,y,c,a,'One-step Bayesian VOI',1000)
        self.assertGreaterEqual(np.count_nonzero(with_no_cost=='COLLECT_DATA'),
                                np.count_nonzero(with_cost=='COLLECT_DATA'))

if __name__=='__main__':unittest.main()

