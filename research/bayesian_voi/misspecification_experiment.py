"""Exploratory, paired synthetic model-misspecification evaluation.

Protocol: MISSPECIFICATION_PROTOCOL.md. NOT external validation.
Policies are kept frozen and are not tuned on scenario results.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from adaptive_policy import immediate_bayes, one_step_voi, confidence_gate

OUT = Path(__file__).resolve().parent / 'results'
SEEDS = tuple(range(4000, 4020))
N = 2500
H, M = 100, 10
SCALE = 1.25
ASSUMED_MARGIN = .25
PRIOR = (1., 9.)
POLICIES = (
    'Immediate Bayesian', 'Fixed 15-click Bayesian gate',
    'Fixed 25-click Bayesian gate', '95% probability Bayesian gate',
    'One-step Bayesian VOI'
)
SCENARIOS = {
    'Stationary reference': dict(p_mult=1., report_fraction=1., uncertain_margin=False),
    'CVR decline 40%': dict(p_mult=.6, report_fraction=1., uncertain_margin=False),
    'CVR increase 50%': dict(p_mult=1.5, report_fraction=1., uncertain_margin=False),
    'Delayed attribution 65% visible': dict(p_mult=1., report_fraction=.65, uncertain_margin=False),
    'Unknown true margins 12-40%': dict(p_mult=1., report_fraction=1., uncertain_margin=True),
    'Combined adverse': dict(p_mult=.6, report_fraction=.65, uncertain_margin=True),
}


def sample_cohort(seed: int, n: int, scenario: dict) -> dict:
    if n <= 0:
        raise ValueError('n must be positive')
    if not (0 <= scenario['report_fraction'] <= 1 and scenario['p_mult'] > 0):
        raise ValueError('invalid scenario')
    rng = np.random.default_rng(seed)
    clicks = rng.integers(5, 201, size=n)
    historical_p = rng.uniform(.005, .20, size=n)
    future_p = np.minimum(.99, historical_p * scenario['p_mult'])
    cpc = rng.uniform(.30, 1.50, size=n)
    aov = rng.uniform(20., 50., size=n)
    true_orders = rng.binomial(clicks, historical_p)
    prospect_true_orders = rng.binomial(M, future_p)
    visible = scenario['report_fraction']
    # A 100%-visible report is literally the full order count.
    observed_orders = true_orders if visible == 1 else rng.binomial(true_orders, visible)
    observed_followup = prospect_true_orders if visible == 1 else rng.binomial(prospect_true_orders, visible)
    true_margin = rng.uniform(.12, .40, size=n) if scenario['uncertain_margin'] else np.full(n, ASSUMED_MARGIN)
    return dict(clicks=clicks, orders=observed_orders, historical_p=historical_p,
                future_p=future_p, cpc=cpc, aov=aov, true_margin=true_margin,
                true_orders=true_orders, prospect_true_orders=prospect_true_orders,
                observed_followup=observed_followup)


def choose(clicks, orders, cpc, aov, policy, overhead: float) -> np.ndarray:
    initial = immediate_bayes(clicks, orders, cpc, aov, ASSUMED_MARGIN, PRIOR)
    if policy == 'Immediate Bayesian':
        return initial
    if policy == 'Fixed 15-click Bayesian gate':
        return np.where(clicks < 15, 'COLLECT_DATA', initial)
    if policy == 'Fixed 25-click Bayesian gate':
        return np.where(clicks < 25, 'COLLECT_DATA', initial)
    if policy == '95% probability Bayesian gate':
        return confidence_gate(clicks, orders, cpc, aov, ASSUMED_MARGIN, PRIOR, confidence=.95)
    if policy == 'One-step Bayesian VOI':
        return one_step_voi(clicks, orders, cpc, aov, ASSUMED_MARGIN, PRIOR,
                            horizon=H, explore_clicks=M, scale_factor=SCALE, explore_cost=overhead)
    raise KeyError(policy)


def score_cohort(cohort: dict, policy: str, overhead: float = 0.) -> dict:
    if not np.isfinite(overhead) or overhead < 0:
        raise ValueError('overhead must be finite and nonnegative')
    clicks, orders, cpc, aov = (cohort[z] for z in ('clicks','orders','cpc','aov'))
    actions = choose(clicks, orders, cpc, aov, policy, overhead)
    mu = cohort['future_p'] * aov * cohort['true_margin'] - cpc
    scale_utility = H * SCALE * mu
    # Baseline can be optimal when no scaled action is available in some future extensions.
    oracle = np.maximum.reduce([np.zeros_like(mu), scale_utility, H * mu])
    util = np.where(actions == 'SCALE', scale_utility, 0.).astype(float)
    ix = np.flatnonzero(actions == 'COLLECT_DATA')
    if len(ix):
        later = immediate_bayes(clicks[ix] + M, orders[ix] + cohort['observed_followup'][ix],
                                cpc[ix], aov[ix], ASSUMED_MARGIN, PRIOR)
        util[ix] = M * mu[ix] + (H-M) * SCALE * np.where(later=='SCALE', mu[ix], 0.) - overhead
    regret = oracle - util
    if (np.any(regret < -1e-7) or not np.all(np.isfinite(regret))):
        raise AssertionError('Oracle invalid or non-finite values')
    return {'regret': float(regret.mean()), 'defer_rate': float((actions=='COLLECT_DATA').mean()),
            'utility': float(util.mean()), 'harmful_scale_rate': float(((actions=='SCALE') & (mu<0)).mean()),
            'harmful_exclude_rate': float(((actions=='NEGATIVE') & (mu>0)).mean())}


def run(seeds=SEEDS, n=N, policies=POLICIES, overheads=(0.,2.), scenarios=SCENARIOS) -> pd.DataFrame:
    rows=[]
    for scenario_name, params in scenarios.items():
        for seed in seeds:
            cohort = sample_cohort(seed, n, params)
            for overhead in overheads:
                for policy in policies:
                    rows.append({'scenario':scenario_name, 'seed':seed, 'overhead':overhead,
                                 'policy':policy, **score_cohort(cohort,policy,overhead)})
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame):
    summary = df.groupby(['scenario','overhead','policy'],sort=False).agg(
        regret=('regret','mean'), regret_sd=('regret','std'),
        defer_rate=('defer_rate','mean'), utility=('utility','mean'),
        harmful_scale_rate=('harmful_scale_rate','mean'),
        harmful_exclude_rate=('harmful_exclude_rate','mean')).reset_index()
    nseeds=df.seed.nunique()
    summary['regret_ci95_half_width']=1.96*summary.regret_sd/np.sqrt(nseeds)
    diffs=[]
    for (sc,ov), d in df.groupby(['scenario','overhead'],sort=False):
        pvt=d.pivot(index='seed',columns='policy',values='regret')
        for method in POLICIES[1:]:
            vals=pvt[method]-pvt['Immediate Bayesian']
            diffs.append(dict(scenario=sc,overhead=ov,policy=method,
                              mean_difference=float(vals.mean()),
                              ci95_half_width=float(1.96*vals.std(ddof=1)/np.sqrt(len(vals)))))
    return summary,pd.DataFrame(diffs)


def main():
    OUT.mkdir(exist_ok=True)
    data=run()
    summary, diffs=summarize(data)
    data.to_csv(OUT/'misspecification_per_seed.csv',index=False)
    summary.to_csv(OUT/'misspecification_summary.csv',index=False)
    diffs.to_csv(OUT/'misspecification_paired_differences.csv',index=False)
    sel=summary.loc[summary.overhead==2.,['scenario','policy','regret','defer_rate']]
    print(sel.round(4).to_string(index=False))

if __name__ == '__main__':
    main()

