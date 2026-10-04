# PPC Optimisation Research Experiment

This directory contains a reproducible benchmark for comparing Amazon Sponsored Products decision rules.

## Research question
Can a multi-metric, evidence-aware decision framework provide more reliable optimisation recommendations than simpler ACOS-based rules?

## Methods
1. ACOS-only baseline.
2. Evidence-aware baseline using ACOS plus click/order thresholds.
3. Proposed multi-metric framework using efficiency, conversion and evidence-volume signals.

The benchmark is fully synthetic and generated from explicit latent performance states. It contains no employer, customer or confidential advertising data.

## Reproduce
```bash
python research/generate_benchmark.py
python research/evaluate.py
```

Results are written to `research/results/`. Synthetic benchmark results are methodological evidence only and must not be represented as observed commercial performance.
