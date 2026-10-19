# Bayesian evidence-collection experiments (exploratory)

This directory contains a self-contained *research extension* to the Amazon PPC Intelligence Hub. It investigates decision deferral when conversion evidence is sparse, using posterior decision policies and one-step value-of-information (VOI) calculations.

**Research status:** exploratory synthetic simulations; no advertiser data, external review, measured commercial impact, or independently established algorithmic novelty. These scripts are not integrated with the live Streamlit app and should **not** be used to change ad bids or campaign settings.

## What is included

- `adaptive_policy.py`: Beta-binomial posterior and experimental immediate/deferred policies.
- `evaluate_pilot.py`: initial synthetic comparison; its legacy ACOS heuristic comparisons are *not action matched* and should not be used as proof of superiority.
- `stress_test.py`: earlier exploratory synthetic scenarios.
- `matched_comparison.py`: five decision policies using the same simplified action and cost framework.
- `misspecification_experiment.py`: six scenarios involving conversion drift, incomplete attribution and margin uncertainty.
- `MISSPECIFICATION_PROTOCOL.md`: stated assumptions, comparisons and constraints.
- `MISSPECIFICATION_RESULTS.md`: summary, including unfavourable and inconclusive results.
- `TECHNICAL_AUDIT.md`: verification details and remaining limitations.
- `tests/`: automated tests; `results/`: seed-level and aggregate synthetic outputs.
- `ENVIRONMENT.txt`: observed reproduction environment, **not a dependency lockfile**.

## Reproduce

From the repository root (tested using Python 3.13.5; other Python versions have not been verified):

```bash
cd research/bayesian_voi
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python evaluate_pilot.py
python stress_test.py
python matched_comparison.py
python misspecification_experiment.py
```

The four experiment scripts write CSV files under `results/`. Review the experiment protocol and validation limitations before comparing policy outcomes. The captured example outputs were generated using Python 3.13.5, NumPy 2.3.5, pandas 2.2.3 and SciPy 1.17.0 (see `ENVIRONMENT.txt`); ranges in `requirements.txt` are not an exact lock.

## Selected findings (simulated regret; lower is better)

For 25 synthetic seeds of 2,500 observations each, matched Bayesian policies with zero acquisition overhead had regret 2.9719 (immediate decision) and 2.6571 (one-step VOI). This result was obtained under a stylised stationary economic model that is also the basis of the VOI decision rule; it is not independent validation of the method.

In six additional misspecification scenarios, results were mixed. Under delayed attribution, the observed VOI advantage over immediate action was inconclusive. With sharply increasing future conversion rates, a simple posterior-confidence gate achieved lower regret than VOI. These results are important limitations rather than outcomes to omit.

## Evidence boundaries and next work

- Models do not reproduce Amazon auctions, dynamic bids, inventory limits, budget constraints, actual attribution processes, or longitudinal exploration benefits.
- Fixed thresholds and confidence gates were not selected using held-out, matched-coverage tuning; comparative superiority cannot be claimed.
- A Beta-binomial decision rule and value of information are established techniques. Novelty in this specific application has not been independently established.
- Future work: independent held-out tuning, credible economic/auction simulation, literature novelty analysis, specialist critique and authorised seller usability assessment.
- No employer or other confidential advertiser data are present or required to reproduce these experiments.

**Related original research:** [Earlier rule-based PPC benchmark](../README.md). **App:** [`../../app.py`](../../app.py) (unchanged by this research extension).

## v5 held-out, quota-matched validation (local, not yet merged)

The proposed v5 extension adds [`fair_baselines.py`](fair_baselines.py) and a 13-test suite for budget-matched evidence-collection ranking. It uses 20 training and 30 distinct test seeds; see [`FAIR_BASELINE_PROTOCOL.md`](FAIR_BASELINE_PROTOCOL.md) and [`FAIR_BASELINE_RESULTS.md`](FAIR_BASELINE_RESULTS.md). The comparison forces equal deferral rates across policies and is **not** proof of better real advertising outcomes. The trained hybrid chose the same VOI ranking; the uncertainty gate beat VOI under some adverse synthetic scenarios.

Reproduce with `python fair_baselines.py`, then read the generated `results/fair_*.csv` files. This change does not integrate the prototype into `app.py`.
