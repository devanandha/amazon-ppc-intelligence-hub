# Model-Misspecification Experiment — Results

17 October 2026. **Exploratory synthetic research only. Not an empirical Amazon Ads evaluation.**

## Experimental design

25 automated unit tests passed across the current v4 codebase (20 prior plus five new). The six held-out stress scenarios and 20-seed design are described in `MISSPECIFICATION_PROTOCOL.md`. Each scenario assesses the same five action-matched policies against the same synthetic terms, outcomes and prospective economic horizon. Cost of acquiring ten exploratory clicks is set to two fictional currency units for the main comparison. All monetary estimates below are simulated regret per term; lower is better.

| Synthetic environment | Immediate Bayes regret | One-step VOI regret | VOI minus immediate (paired 95% CI half-width) | Finding |
|---|---:|---:|---:|---|
| Stationary reference | 2.9768 | 2.7581 | -0.2187 ± 0.0526 | VOI advantage under design assumptions |
| CVR decline 40% | 7.3513 | 7.0028 | -0.3485 ± 0.0595 | VOI advantage under simulated decline |
| CVR increase 50% | 10.7184 | 9.6501 | -1.0684 ± 0.1153 | VOI beats immediate, **but loses** to the 95% confidence gate (regret 8.9896) |
| Delayed attribution, 65% visible | 8.1775 | 8.1336 | -0.0440 ± 0.0987 | Uncertain VOI advantage; interval includes zero |
| True margin 12–40%, unobserved | 6.1635 | 5.9455 | -0.2180 ± 0.0749 | VOI advantage under heterogeneous margins |
| Combined adverse | 4.5258 | 4.4193 | -0.1064 ± 0.0478 | Small simulated VOI advantage |

Across these simulations, the VOI policy made a deferral decision for about 5.6–5.7% of terms with a cost of two units. The confidence gate deferred about 46% of terms, which explains part of the differing risk–coverage trade-off. These gate thresholds were **not tuned to matched risk or coverage**, and this is not a definitive fairness comparison.

## Interpretation

The experiment shows how differences in scenario design and missing conversion evidence affect policies. It does **not** show that the VOI policy is novel, optimal in advertising markets, robust to arbitrary data drift, or beneficial on real accounts. The VOI policy optimises the same stylised economic model against which it is initially assessed; improvement over an immediate policy is partly structurally expected. Some failure is visible: no reliable advantage in the delayed-attribution scenario, and a simpler confidence gate beats it when future CVR increases sharply in the simulated environment. The model omits auctions, placement response, competitive bids, budgets, inventory constraints, seasonality and longer-term learning.

## Consequences for the next research steps

1. Do **not** cite this as external validation or an identified new invention.
2. Add risk/coverage-matched policy tuning on *independent training seeds*, keeping test seeds untouched.
3. Add auction-dependent CPC, finite budgets, time-varying CVR and a model that allows a useful `MAINTAIN` decision to challenge the extreme-action oracle.
4. Produce a source-checked novelty comparison against Bayesian online bid optimisation, contextual bandits, optimal stopping and selective prediction.
5. Seek honest external expert critique of a frozen reviewer package; obtain authorised independent seller usability feedback without collecting confidential data.

Reproduce:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python misspecification_experiment.py
```

CSV outputs: `results/misspecification_per_seed.csv`, `results/misspecification_summary.csv`, `results/misspecification_paired_differences.csv`.
