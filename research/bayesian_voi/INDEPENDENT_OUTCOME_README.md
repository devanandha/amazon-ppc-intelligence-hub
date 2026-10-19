# v7 independent-outcome stress experiment

This is an **additive, experimental** folder update only. It does not alter the existing v5 VOI rank, prior, live `app.py`, or real advertising accounts. It tests transfer from v5’s model-aligned synthetic regret to a separate internally created portfolio outcome simulator with auction-cost shocks, budget caps, delayed reporting, bid-sensitive future clicks and a shared three-action follow-up decision.

- **Protocol:** `INDEPENDENT_OUTCOME_PROTOCOL.md`
- **Results:** `INDEPENDENT_OUTCOME_RESULTS.md`
- **Reproduction:** `python independent_outcomes.py`
- **Tests:** `python -m unittest discover -s tests -v`
- **Data:** Only synthetic `results/independent_*` files are produced.

**Headline:** At a fixed 10% exploration quota, the prior VOI rank loses to a simpler profitability-uncertainty rank in all six predefined stress scenarios in this internally generated outcome simulator. This is important negative evidence and should not be disguised as support for real-world advertising gain. A *separately developed* multi-action/budget-aware VOI method and genuinely independent real-world evaluation would be required for stronger claims.
