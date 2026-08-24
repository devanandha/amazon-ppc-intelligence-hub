"""Create a fictional Amazon Ads report for safe portfolio demonstrations."""

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    rng = np.random.default_rng(42)
    rows = []
    campaigns = ["Demo | Core | Exact", "Demo | Discovery | Broad", "Demo | Product Targeting"]
    terms = [
        "professional styling brush", "detangling hair brush", "salon paddle brush",
        "vented styling brush", "travel hair brush", "B012DEMO34", "B056DEMO78",
        "unrelated accessory", "cheap plastic comb", "premium hair styling tool",
    ]
    for day in pd.date_range("2026-06-01", periods=30, freq="D"):
        for campaign in campaigns:
            for term in rng.choice(terms, size=5, replace=False):
                impressions = int(rng.integers(100, 4000))
                clicks = int(rng.binomial(impressions, rng.uniform(0.003, 0.025)))
                cpc = rng.uniform(0.35, 1.25)
                spend = round(clicks * cpc, 2)
                conversion = 0 if term in {"unrelated accessory", "cheap plastic comb"} else rng.uniform(0.03, 0.18)
                orders = int(rng.binomial(clicks, conversion)) if clicks else 0
                sales = round(orders * rng.uniform(12, 35), 2)
                rows.append({
                    "Start Date": day, "End Date": day, "Portfolio name": "Synthetic Portfolio",
                    "Currency": "GBP", "Campaign Name": campaign, "Ad Group Name": campaign + " | Group 1",
                    "Retailer": "Synthetic", "Country": "UK", "Targeting": term,
                    "Match Type": "TARGETING_EXPRESSION" if term.startswith("B0") else rng.choice(["EXACT", "BROAD", "PHRASE"]),
                    "Customer Search Term": term, "Impressions": impressions, "Clicks": clicks,
                    "Click-Thru Rate (CTR)": clicks / impressions if impressions else 0,
                    "Cost Per Click (CPC)": cpc if clicks else 0, "Spend": spend,
                    "7 Day Total Sales": sales,
                    "Total Advertising Cost of Sales (ACOS)": spend / sales if sales else np.nan,
                    "Total Return on Advertising Spend (ROAS)": sales / spend if spend else 0,
                    "7 Day Total Orders (#)": orders, "7 Day Total Units (#)": orders,
                    "7 Day Conversion Rate": orders / clicks if clicks else 0,
                })
    output = Path(__file__).with_name("Synthetic_Sponsored_Products_Report.xlsx")
    pd.DataFrame(rows).to_excel(output, index=False)
    print(f"Created {output.name} with fictional data.")


if __name__ == "__main__":
    main()
