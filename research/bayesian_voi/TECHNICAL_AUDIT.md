# Technical Audit — PPC Bayesian Evidence-Collection Prototype

**Version note (17 October 2026):** The main narrative below documents the v3 20-test audit. The v4 extension adds five tests (25 total), six model-misspecification scenarios and a separate protocol/results report. See `MISSPECIFICATION_PROTOCOL.md`, `MISSPECIFICATION_RESULTS.md`, and the test suite for the v4 additions. All v3 findings remain historical rather than claims of external validation.

Date: 17 October 2026

## Confirmed in this audit

- Original experimental program and 25-seed synthetic results retained unchanged as a separate v2 archive.
- Input validation tightened in v3. Finite positive Beta prior, integer nonnegative click/order counts, and valid cost/economic parameters are now required.
- Automated tests increased from 4 to **20**. These check posterior arithmetic, posterior profitability, predictive distribution, explicit enumeration of one-step expected value, basic oracle bounds, invalid-input handling and deterministic synthetic data generation.
- Fresh executions of `evaluate_pilot.py` and `stress_test.py` exactly reproduced the previous four summary/seed result CSVs. No change in previously reported outcomes.
- New **action-matched comparison** (`matched_comparison.py`) evaluates five Bayesian policies with the same actions, horizon, observed information, follow-up opportunity, and contribution model. In the zero acquisition-cost setting, regret was 2.9719 (immediate Bayes), 2.9476 (fixed 15-click Bayesian gate) and 2.6571 (VOI); with a cost of 2 simulated currency units, VOI regret became 2.8052. This is a more coherent comparison but remains within the same researcher-created model.
- Tests and simulations use synthetic observations only; no Denman advertising information used.

## Important remaining research limitations

1. VOI optimization maximizes expected value under the same assumptions used in its decision calculation. Its advantage relative to immediate action within this model is not intrinsically surprising and not, alone, evidence of novelty.
2. The original comparison with ACOS rules is not a well-controlled algorithmic comparison: objective and action sets differ, and the toy economic oracle structurally prefers scale or exclude. The new `matched_comparison.py` addresses only action/economics matching; stronger tuned risk/coverage baselines and externally independent outcome models are still missing.
3. No independent ground-truth campaign outcomes are available. Historical labeling in early experiments is coupled to the researcher's state definitions.
4. Prior conversion model is stationary, cost and order value are treated as known, and no auction response, attribution delay, changing conversion rates, inventory limits, budget constraint or data acquisition risk is modeled.
5. The 95% confidence threshold is an arbitrary decision policy rather than a capacity/risk-matched comparator. Comparisons must include matched action budgets and selective risk-coverage curves.
6. A qualified external researcher must examine technical originality; an independent useful application of known Bayesian decision ideas is not necessarily a new scientific method.

## Reproducibility commands

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python evaluate_pilot.py
python stress_test.py
python matched_comparison.py
```

Note: all reported outcomes are simulated currency units under fictional assumptions, not customer outcomes or demonstrated advertising lift. No source code was committed to GitHub or integrated into the production Streamlit dashboard as part of this audit.

