"""Held-out, action-matched fixed-budget synthetic policy-selection experiment.

CAUTION: Fully synthetic model; scores use posterior economics. The common
budget FORCES an identical count of deferred decisions, even when a score is
negative. This measures allocation *ranking* at fixed coverage, rather than
unconstrained optimal deployment of any policy.

Training and test seeds never overlap. Historical observations, not latent
future conversion rates or economic oracle values, define test-time rankings.
"""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.special import betaln, gammaln
from scipy.stats import beta as beta_dist, betabinom

from adaptive_policy import immediate_bayes
from misspecification_experiment import sample_cohort, SCENARIOS

N = 1600
TRAIN_SEEDS = tuple(range(6000, 6020))
TEST_SEEDS = tuple(range(12000, 12030))
BUDGETS = (.05, .10, .20)
PRIMARY_BUDGET = .10
H = 100
M = 10
SCALE = 1.25
ASSUMED_MARGIN = .25
OVERHEAD = 2.
PRIOR_OPTIONS = ((.5, 4.5), (1., 9.), (2., 18.), (1., 1.))
LAMBDAS = (0., .25, .50, .75, 1.)
METHODS = ('Random allocation','Fewest clicks','Profitability uncertainty',
           'One-step VOI rank','Train-tuned hybrid')
SCENARIO_NAMES = tuple(SCENARIOS.keys())
OUT = Path(__file__).resolve().parent/'results'


def beta_binomial_logscore(clicks, orders, prior):
    """Marginal log predictive score of *historical* order counts only."""
    a,b = prior
    n,k = np.asarray(clicks),np.asarray(orders)
    return gammaln(n+1)-gammaln(k+1)-gammaln(n-k+1) + betaln(k+a,n-k+b)-betaln(a,b)


def fit_prior(train_cohorts):
    """Choose one shared prior without accessing test outcomes or test seeds."""
    losses = {}
    for prior in PRIOR_OPTIONS:
        losses[prior] = float(np.mean([
            -beta_binomial_logscore(d['clicks'],d['orders'],prior).mean()
            for d in train_cohorts
        ]))
    selected = min(PRIOR_OPTIONS,key=lambda p:(losses[p],PRIOR_OPTIONS.index(p)))
    return selected, losses


def voi_increment(clicks, orders, cpc, aov, prior, overhead=OVERHEAD):
    """Expected net gain of observing m clicks rather than acting now.

    Matches one_step_voi's action calculation but retains its continuous
    gain for fixed-capacity ranking. No latent future outcomes are accessed.
    """
    c=np.asarray(clicks,dtype=float)
    o=np.asarray(orders,dtype=float)
    cp=np.asarray(cpc,dtype=float)
    av=np.asarray(aov,dtype=float)
    a,b=prior[0]+o, prior[1]+c-o
    mu=a/(a+b)*av*ASSUMED_MARGIN-cp
    immediate=H*SCALE*np.maximum(mu,0.)
    k=np.arange(M+1, dtype=float)
    probs=betabinom.pmf(k[None,:], M, a[:,None], b[:,None])
    future_mu=(a[:,None]+k[None,:])/(a[:,None]+b[:,None]+M)*av[:,None]*ASSUMED_MARGIN-cp[:,None]
    collect=M*mu+(H-M)*SCALE*np.sum(probs*np.maximum(future_mu,0.),axis=1)-overhead
    return collect-immediate


def percentile_rank(values):
    """Deterministic ordering with stable ties (index order), 0..1 scale."""
    v=np.asarray(values,dtype=float)
    if not np.isfinite(v).all():
        raise ValueError('Scores must be finite')
    order=np.argsort(v,kind='stable')
    ranks=np.empty(len(v),float)
    ranks[order]=np.arange(len(v),dtype=float)/max(len(v)-1,1)
    return ranks


def compute_scores(cohort,prior,seed):
    c,o,cp,av=(cohort[z] for z in ('clicks','orders','cpc','aov'))
    a,b=prior[0]+o,prior[1]+c-o
    prob=beta_dist.sf(cp/(ASSUMED_MARGIN*av),a,b)
    # near .5 means unresolved profitability, not necessarily valuable exploration
    uncertain=.5-np.abs(prob-.5)
    voi=voi_increment(c,o,cp,av,prior)
    # Fixed, reproducible random benchmark independent of observed outcomes.
    random=np.random.default_rng(1_000_000+int(seed)).random(len(c))
    return {'Random allocation':random, 'Fewest clicks':-c.astype(float),
            'Profitability uncertainty':uncertain,'One-step VOI rank':voi,
            'hybrid_voi_ranks':percentile_rank(voi),
            'hybrid_uncertainty_ranks':percentile_rank(uncertain)}


def allocate(scores, budget):
    """Select exactly round(n*budget) highest-ranked terms; compulsory quota."""
    a=np.asarray(scores,dtype=float)
    if a.ndim!=1 or len(a)==0 or not np.isfinite(a).all() or not 0<budget<1:
        raise ValueError('Invalid scores or budget')
    count=int(np.floor(len(a)*budget+0.5))
    # Deterministic within-cohort tie-break, no dependence on true outcomes.
    order=np.argsort(-a,kind='stable')
    chosen=np.zeros(len(a),dtype=bool)
    chosen[order[:count]]=True
    return chosen


def score_fixed_allocation(cohort,selected,prior,overhead=OVERHEAD):
    """Same action/follow-up/economics model for every ranking policy."""
    c,o,cp,av=(cohort[z] for z in ('clicks','orders','cpc','aov'))
    selected=np.asarray(selected,dtype=bool)
    if selected.shape!=(len(c),):
        raise ValueError('Allocation length does not match cohort')
    true_mu=cohort['future_p']*av*cohort['true_margin']-cp
    oracle=H*SCALE*np.maximum(true_mu,0.)
    first=immediate_bayes(c,o,cp,av,ASSUMED_MARGIN,prior)
    utility=np.where(first=='SCALE',H*SCALE*true_mu,0.).astype(float)
    ix=np.flatnonzero(selected)
    if len(ix):
        final=immediate_bayes(c[ix]+M,o[ix]+cohort['observed_followup'][ix],
                              cp[ix],av[ix],ASSUMED_MARGIN,prior)
        utility[ix]=M*true_mu[ix]+(H-M)*SCALE*np.where(final=='SCALE',true_mu[ix],0.)-overhead
    regret=oracle-utility
    if (np.min(regret)<-1e-8 or not np.all(np.isfinite(regret))):
        raise AssertionError('Oracle/regret failed consistency check')
    return {'regret':float(np.mean(regret)),
            'utility':float(np.mean(utility)),
            'defer_rate':float(np.mean(selected)),
            'harmful_initial_scale_rate':float(np.mean((~selected)&(first=='SCALE')&(true_mu<0))),
            'harmful_initial_negative_rate':float(np.mean((~selected)&(first=='NEGATIVE')&(true_mu>0)))}


def hybrid_score(scores,lmbda):
    return lmbda*scores['hybrid_voi_ranks']+(1-lmbda)*scores['hybrid_uncertainty_ranks']


def fit_hybrid(train_cohorts,train_seeds,prior):
    """Minimize synthetic TRAIN regret at primary 10% allocation only."""
    per_lambda={l:[] for l in LAMBDAS}
    for cohort,seed in zip(train_cohorts,train_seeds):
        scores=compute_scores(cohort,prior,seed)
        for l in LAMBDAS:
            selected=allocate(hybrid_score(scores,l),PRIMARY_BUDGET)
            per_lambda[l].append(score_fixed_allocation(cohort,selected,prior)['regret'])
    means={l:float(np.mean(xs)) for l,xs in per_lambda.items()}
    best=min(LAMBDAS,key=lambda l:(means[l], LAMBDAS.index(l)))
    return best,means


def test_evaluation(prior,hybrid_lambda,seed_set=TEST_SEEDS,n=N,
                    scenario_names=SCENARIO_NAMES,budgets=BUDGETS):
    rows=[]
    for scenario in scenario_names:
        for seed in seed_set:
            cohort=sample_cohort(seed,n,SCENARIOS[scenario])
            scores=compute_scores(cohort,prior,seed)
            scores['Train-tuned hybrid']=hybrid_score(scores,hybrid_lambda)
            for budget in budgets:
                for method in METHODS:
                    selected=allocate(scores[method],budget)
                    metric=score_fixed_allocation(cohort,selected,prior)
                    rows.append(dict(scenario=scenario,seed=seed,budget=budget,
                                     method=method,**metric))
    return pd.DataFrame(rows)


def summarize(frame):
    grouped=frame.groupby(['scenario','budget','method'],sort=False)
    out=grouped.agg(regret=('regret','mean'), regret_sd=('regret','std'),
                    defer_rate=('defer_rate','mean'),utility=('utility','mean')).reset_index()
    out['ci95_half_width']=1.96*out['regret_sd']/np.sqrt(frame.seed.nunique())
    pairs=[]
    for (scenario,budget),df in frame.groupby(['scenario','budget'],sort=False):
        pv=df.pivot(index='seed',columns='method',values='regret')
        for baseline in METHODS:
            if baseline=='One-step VOI rank':continue
            diff=pv['One-step VOI rank']-pv[baseline]
            pairs.append(dict(scenario=scenario,budget=budget,
                              voi_minus=baseline,mean_difference=float(diff.mean()),
                              ci95_half_width=float(1.96*diff.std(ddof=1)/np.sqrt(len(diff)))))
    return out,pd.DataFrame(pairs)



def natural_policy_diagnostic(prior,seed_set=TEST_SEEDS,n=N,scenario_names=SCENARIO_NAMES):
    """Unconstrained VOI and zero-deferral Bayesian reference; unmatched rates."""
    rows=[]
    for scenario in scenario_names:
        for seed in seed_set:
            cohort=sample_cohort(seed,n,SCENARIOS[scenario])
            gains=compute_scores(cohort,prior,seed)['One-step VOI rank']
            for name,selected in (
                ('No deferral (immediate Bayes)', np.zeros(len(gains),dtype=bool)),
                ('Unconstrained positive VOI', gains>1e-9)):
                rows.append(dict(scenario=scenario,seed=seed,method=name,
                                 **score_fixed_allocation(cohort,selected,prior)))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    train=[sample_cohort(s,N,SCENARIOS['Stationary reference']) for s in TRAIN_SEEDS]
    prior,prior_scores=fit_prior(train)
    hybrid_lambda,hybrid_scores=fit_hybrid(train,TRAIN_SEEDS,prior)
    # Test seeds touched only AFTER all hyperparameters are locked.
    test=test_evaluation(prior,hybrid_lambda)
    summary,paired=summarize(test)
    test.to_csv(OUT/'fair_per_seed.csv',index=False)
    summary.to_csv(OUT/'fair_summary.csv',index=False)
    paired.to_csv(OUT/'fair_paired.csv',index=False)
    natural=natural_policy_diagnostic(prior)
    natural.to_csv(OUT/'fair_unconstrained_per_seed.csv',index=False)
    natural.groupby(['scenario','method'],sort=False).agg(
        regret=('regret','mean'),defer_rate=('defer_rate','mean'),
        utility=('utility','mean')).reset_index().to_csv(
            OUT/'fair_unconstrained_summary.csv',index=False)
    fitted={'train_seeds':list(TRAIN_SEEDS),'test_seeds':list(TEST_SEEDS),
            'terms_per_seed':N,'common_prior':list(prior),
            'train_prior_logscore_loss':{str(p):v for p,v in prior_scores.items()},
            'train_hybrid_lambda':hybrid_lambda,
            'train_hybrid_regret':{str(p):v for p,v in hybrid_scores.items()},
            'primary_quota':PRIMARY_BUDGET,'quotas':list(BUDGETS),
            'overhead':OVERHEAD,'observational_source':'synthetic only',
            'quota_mode':'exact mandatory, not unconstrained policy'}
    (OUT/'fair_training_config.json').write_text(json.dumps(fitted,indent=2)+'\n',encoding='utf-8')
    main=summary[(summary.scenario=='Stationary reference') & (np.isclose(summary.budget,PRIMARY_BUDGET))]
    print('PRIOR:',prior,'HYBRID LAMBDA:',hybrid_lambda)
    print(main[['method','regret','ci95_half_width','defer_rate']].round(5).to_string(index=False))
    print('\nPAIRED differences VOI minus others (stationary primary):')
    p=paired[(paired.scenario=='Stationary reference') & (np.isclose(paired.budget,PRIMARY_BUDGET))]
    print(p[['voi_minus','mean_difference','ci95_half_width']].round(5).to_string(index=False))

if __name__=='__main__':
    main()
