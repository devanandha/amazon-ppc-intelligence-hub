"""EXPERIMENTAL posterior and one-step evidence-acquisition policies.

Research only: not validated on Amazon Ads, not suitable for automated bid changes.
Actions: SCALE, NEGATIVE, COLLECT_DATA.
Assumes a single conversion per click, known CPC and AOV, margin, fixed response,
no auction/budget/spillover/delayed attribution and a Beta prior for conversion rate.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import beta as beta_dist, betabinom


def _posterior(clicks, orders, prior=(1.0, 9.0)):
    clicks = np.asarray(clicks, dtype=float)
    orders = np.asarray(orders, dtype=float)
    prior = np.asarray(prior, dtype=float)
    if prior.shape != (2,) or not np.all(np.isfinite(prior)) or np.any(prior <= 0):
        raise ValueError('Beta prior must contain two finite positive parameters')
    if (np.any(~np.isfinite(clicks)) or np.any(~np.isfinite(orders))
            or np.any(clicks < 0) or np.any(orders < 0) or np.any(orders > clicks)
            or np.any(clicks != np.floor(clicks)) or np.any(orders != np.floor(orders))):
        raise ValueError('Clicks and orders must be finite non-negative integer counts with orders <= clicks')
    return prior[0] + orders, prior[1] + clicks - orders


def _validate_economics(cpc, aov, margin):
    cpc, aov = np.asarray(cpc, dtype=float), np.asarray(aov, dtype=float)
    if (not np.isfinite(margin) or not (0 < margin <= 1)
            or np.any(~np.isfinite(cpc)) or np.any(~np.isfinite(aov))
            or np.any(cpc < 0) or np.any(aov <= 0)):
        raise ValueError('Require 0 < margin <= 1, finite nonnegative CPC and finite positive AOV')
    return cpc, aov


def posterior_profit_probability(clicks, orders, cpc, aov, margin=.25, prior=(1., 9.)):
    """Posterior probability expected contribution per click is positive.

    Threshold CVR is cpc/(margin*AOV). These are simplified contribution
    assumptions, not an Amazon Ads outcome prediction.
    """
    alpha, beta = _posterior(clicks, orders, prior)
    cpc, aov = _validate_economics(cpc, aov, margin)
    threshold = cpc / (margin * aov)
    return np.where(threshold >= 1, 0., np.where(threshold <= 0, 1., beta_dist.sf(threshold, alpha, beta)))


def immediate_bayes(clicks, orders, cpc, aov, margin=.25, prior=(1., 9.)):
    """Choose SCALE/NEGATIVE using posterior expected contribution."""
    a, b = _posterior(clicks, orders, prior)
    cpc, aov = _validate_economics(cpc, aov, margin)
    exp_profit = a / (a+b) * aov*margin - cpc
    return np.where(exp_profit > 0, 'SCALE', 'NEGATIVE')


def confidence_gate(clicks, orders, cpc, aov, margin=.25, prior=(1., 9.), confidence=.95):
    if not (.5 < confidence < 1):
        raise ValueError('Confidence must be between 0.5 and 1')
    chance = posterior_profit_probability(clicks, orders, cpc, aov, margin, prior)
    return np.where(chance >= confidence, 'SCALE',
                    np.where(chance <= 1-confidence, 'NEGATIVE', 'COLLECT_DATA'))


def one_step_voi(clicks, orders, cpc, aov, margin=.25, prior=(1., 9.),
                 horizon=100, explore_clicks=10, scale_factor=1.25, explore_cost=0.):
    """Compare acting now with collecting evidence for the first m of H opportunities.

    Collecting uses m unscaled clicks (with contribution or loss); on the remaining
    H-m opportunities use the posterior-mean optimal SCALE/NEGATIVE decision.
    Exact beta-binomial predictive averaging for the m exploratory conversions.
    This is a one-step toy decision model, not an advertising platform simulator.
    """
    if (not isinstance(explore_clicks, (int, np.integer)) or not isinstance(horizon, (int, np.integer))
            or not (0 < explore_clicks < horizon) or not np.isfinite(scale_factor)
            or scale_factor < 1 or not np.isfinite(explore_cost) or explore_cost < 0):
        raise ValueError('Require positive integer horizon/explore clicks, 0 < explore < horizon, scale_factor >= 1, finite nonnegative cost')
    a, b = _posterior(clicks, orders, prior)
    cpc, aov = _validate_economics(cpc, aov, margin)
    exp_p = a/(a+b)
    exp_mu = exp_p*aov*margin - cpc
    immediate = horizon*scale_factor*np.maximum(exp_mu, 0.)
    # Vectorise beta-binomial expectation; with no new orders k in [0,m].
    k = np.arange(explore_clicks + 1, dtype=float)
    prob = betabinom.pmf(k[None, :], explore_clicks, a[..., None], b[..., None])
    exp_mu_after = (a[..., None] + k[None, :]) / (a[..., None]+b[..., None]+explore_clicks)*aov[..., None]*margin-cpc[..., None]
    collect = explore_clicks*exp_mu + (horizon-explore_clicks)*scale_factor*np.sum(prob*np.maximum(exp_mu_after, 0.),axis=-1)-explore_cost
    return np.where(collect > immediate + 1e-9, 'COLLECT_DATA',
                    np.where(exp_mu > 0, 'SCALE','NEGATIVE'))
