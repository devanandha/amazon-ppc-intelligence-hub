# Independent evaluation guide — Amazon PPC Intelligence Hub

**Purpose:** Invite candid, independent technical and practitioner evaluation of an explainable Amazon Sponsored Products decision-support prototype. This is a research/portfolio project, not an Amazon-endorsed product, or a proven production optimisation system. It includes an **experimental unsupervised ML review feature**, but not a trained advertising-ROI predictor.

**Author:** Devanandha Vellaramkuzhiyil Shaji  
**Project:** https://github.com/devanandha/amazon-ppc-intelligence-hub  
**Public demonstration:** https://devanandha-amazon-ppc-intelligence-hb.streamlit.app/

## What the prototype currently does
- Processes Amazon Sponsored Products Search Term Report exports, with optional Business Report inputs.
- Aggregates repeated customer search terms; calculates ACOS, ROAS, CTR, CPC, CVR, AOV and related KPIs.
- Provides threshold-based campaign health classifications, keyword-harvesting suggestions, possible negatives, ASIN opportunities and directional bidding recommendations.
- Explains action priorities and exports a structured eight-worksheet Excel report.
- Includes data quality checks and synthetic demonstration data.

These recommendations are **rules- and thresholds-based decision support**. Do not describe the current application as an independently validated AI prediction engine.

## Quick start for reviewers

Open the public demonstration and enable **Explore the built-in fictional demo**. This loads reproducible fictional data in one step; there is no need to upload any files. You can then open **Scenario Lab** and compare how recommended actions change under an alternative target ACOS. Open **AI Review** to inspect exploratory outlier flags, conversion-rate uncertainty and hybrid human-review notes. The ML feature does not automatically change bids.

The scenario comparison only reruns transparent decision rules on the same data; it does not forecast causal advertising uplift.

## Reviewer feedback without confidential data

The draft development version includes a **Decision Studio** with human-review policy thresholds, sensitivity visualisation, a locally downloaded HTML evidence report, and a session-only practitioner-feedback form. Reviewers can export their assessments as a CSV. The form is not proof of independent endorsement and does not automatically train an AI model.

## A 20–30 minute independent evaluation
1. Review the public repository, methodology and limitations.
2. Generate fictional demonstration data with `python create_synthetic_demo.py`, or use your own fully synthetic example.
3. Check whether KPI calculations and handling of zero attributed sales are sensible.
4. Review a keyword-harvesting suggestion and a negative keyword candidate: does the explanation support the action, and what evidence is missing?
5. Assess whether campaign-health categories and priorities make sense for differing target ACOS and evidence thresholds.
6. Review the Excel export and identify limitations that would prevent safe real-world use.
7. Examine AI Review: are the flagged patterns sensible? Could peer comparisons be misleading? Does the evidence-uncertainty display appropriately discourage overconfident actions?

**Do not upload confidential client/employer advertising files, credentials or real customer information to the public demonstration.** Any separate testing on real advertising data would need appropriate consent and privacy/security controls.

## Requested independent feedback
Please comment freely; unfavourable conclusions are welcome.

- **Technical correctness:** Are calculations and decision rules sound? Give specific examples of errors or useful behaviours.
- **Practical relevance:** Would this help a practitioner make better-informed decisions? Which actions need manual verification?
- **Explainability:** Are the explanations understandable and proportional to the evidence?
- **Reliability and limitations:** Where could the rules fail, especially for small samples, attribution issues or seasonality?
- **Distinctiveness:** Does anything offer meaningful value compared with your existing workflows or tools?
- **Possible pilot:** Would you consider a limited, consented evaluation? What would success mean, and what would you track?

## If a pilot is feasible
Only record measurements that can actually be verified, for example: number of reports evaluated, errors identified, suggestions accepted/rejected, reviewer time required, and whether a specific team chose to continue using the tool. Do not equate synthetic results or subjective feedback with improved advertising performance.

## Attribution
Feedback is voluntary and need not be positive. Any public quotation, identification of a reviewer, organisation name, logo or claimed adoption would require the relevant person's prior permission. An independent evaluation is **not** a visa recommendation or guarantee of third-party recognition.

## Research distinction
The separate sponsored-search study uses synthetic experimental data. It does not establish real advertising uplift or production deployment. Its current journal submission is not an accepted or peer-reviewed publication.
