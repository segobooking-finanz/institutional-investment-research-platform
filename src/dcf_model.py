from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# -----------------------------
# Display Options
# -----------------------------
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

# -----------------------------
# Paths
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
IMAGES_DIR = ROOT_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# -----------------------------
# Configuration
# -----------------------------
TICKER = "NVDA"
PROJECTION_YEARS = 10

# WACC inputs — carried over from beta_and_wacc.py results
WACC_REGRESSION_BETA = 0.1247      # 12.47% — 10-year daily regression beta
WACC_REGRESSION_BETA_3Y = 0.1378   # 13.78% — 3-year daily regression beta
WACC_YFINANCE_BETA = 0.1419        # 14.19% — yfinance reported beta
WACC_AVERAGE = (WACC_REGRESSION_BETA + WACC_YFINANCE_BETA) / 2

# -----------------------------
# Scenario Definitions
# -----------------------------
# Each scenario fades FCF growth linearly from an initial rate (Year 1)
# down to a terminal-consistent rate by Year 5, then applies a terminal
# growth rate in perpetuity (Gordon Growth Model) from Year 6 onward.

SCENARIOS = {
    "Conservative": {
        "initial_growth": 0.15,
        "final_year_growth": 0.04,
        "terminal_growth": 0.025,
        "wacc": WACC_YFINANCE_BETA,
    },
    "Base": {
        "initial_growth": 0.25,
        "final_year_growth": 0.06,
        "terminal_growth": 0.030,
        "wacc": WACC_AVERAGE,
    },
    "Base (3-Year Beta)": {
        "initial_growth": 0.25,
        "final_year_growth": 0.06,
        "terminal_growth": 0.030,
        "wacc": WACC_REGRESSION_BETA_3Y,
    },
    "Optimistic": {
        "initial_growth": 0.35,
        "final_year_growth": 0.09,
        "terminal_growth": 0.035,
        "wacc": WACC_REGRESSION_BETA,
    },
}

# -----------------------------
# Load Historical Free Cash Flow
# -----------------------------
cash_flow = pd.read_csv(DATA_DIR / "cash_flow.csv", index_col=0)
free_cash_flow = cash_flow.loc["Free Cash Flow"].sort_index().dropna()

base_fcf = free_cash_flow.iloc[-1]
base_year = free_cash_flow.index[-1]

print("=" * 70)
print(f"DCF MODEL — {TICKER}")
print("=" * 70)
print(f"Base Year (last reported FCF): {base_year}")
print(f"Base Free Cash Flow:           ${base_fcf:,.0f}")
print("=" * 70)

# -----------------------------
# Get Shares Outstanding & Current Price (for implied price comparison)
# -----------------------------
ticker_info = yf.Ticker(TICKER).info
shares_outstanding = ticker_info.get("sharesOutstanding")
current_price = ticker_info.get("currentPrice", ticker_info.get("regularMarketPrice"))
total_debt_latest = pd.read_csv(DATA_DIR / "balance_sheet.csv", index_col=0).loc["Total Debt"].sort_index().iloc[-1]
cash_latest = pd.read_csv(DATA_DIR / "balance_sheet.csv", index_col=0).loc["Cash And Cash Equivalents"].sort_index().iloc[-1]

# -----------------------------
# Run DCF for Each Scenario
# -----------------------------
results = {}
projection_tables = {}

for scenario_name, params in SCENARIOS.items():

    initial_growth = params["initial_growth"]
    final_year_growth = params["final_year_growth"]
    terminal_growth = params["terminal_growth"]
    wacc = params["wacc"]

    # Linearly fade growth rate from initial_growth (Year 1) to final_year_growth (final projection year)
    growth_rates = np.linspace(initial_growth, final_year_growth, PROJECTION_YEARS)

    projected_fcf = []
    fcf = base_fcf
    for g in growth_rates:
        fcf = fcf * (1 + g)
        projected_fcf.append(fcf)

    # Discount each projected year's FCF to present value
    discount_factors = [(1 + wacc) ** (i + 1) for i in range(PROJECTION_YEARS)]
    pv_fcf = [cf / df for cf, df in zip(projected_fcf, discount_factors)]

    # Terminal Value (Gordon Growth Model), discounted back to present
    terminal_value = (projected_fcf[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / discount_factors[-1]

    enterprise_value = sum(pv_fcf) + pv_terminal_value
    equity_value = enterprise_value - total_debt_latest + cash_latest
    implied_share_price = equity_value / shares_outstanding if shares_outstanding else None

    results[scenario_name] = {
        "growth_rates": growth_rates,
        "projected_fcf": projected_fcf,
        "pv_fcf": pv_fcf,
        "terminal_value": terminal_value,
        "pv_terminal_value": pv_terminal_value,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "implied_share_price": implied_share_price,
        "wacc": wacc,
        "terminal_growth": terminal_growth,
    }

    projection_tables[scenario_name] = pd.DataFrame({
        "Growth Rate": growth_rates,
        "Projected FCF": projected_fcf,
        "PV of FCF": pv_fcf,
    }, index=[f"Year {i+1}" for i in range(PROJECTION_YEARS)])

# -----------------------------
# Print Results
# -----------------------------
for scenario_name, r in results.items():
    print(f"\n--- {scenario_name} Scenario ---")
    print(f"WACC used:                {r['wacc']:.2%}")
    print(f"Terminal Growth Rate:      {r['terminal_growth']:.2%}")

    display_table = projection_tables[scenario_name].copy()
    display_table["Growth Rate"] = display_table["Growth Rate"].map(lambda x: f"{x:.2%}")
    display_table["Projected FCF"] = display_table["Projected FCF"].map(lambda x: f"${x:,.0f}")
    display_table["PV of FCF"] = display_table["PV of FCF"].map(lambda x: f"${x:,.0f}")
    print(display_table)

    print(f"Terminal Value:            ${r['terminal_value']:,.0f}")
    print(f"PV of Terminal Value:      ${r['pv_terminal_value']:,.0f}")
    print(f"Enterprise Value:          ${r['enterprise_value']:,.0f}")
    print(f"Equity Value:              ${r['equity_value']:,.0f}")
    if r["implied_share_price"]:
        print(f"Implied Share Price:       ${r['implied_share_price']:,.2f}")

print("\n" + "=" * 70)
print(f"Current Market Price:       ${current_price:,.2f}" if current_price else "Current Market Price: N/A")
print("=" * 70)

# -----------------------------
# Summary Comparison Table
# -----------------------------
summary = pd.DataFrame({
    name: {
        "WACC": r["wacc"],
        "Terminal Growth": r["terminal_growth"],
        "Enterprise Value ($B)": r["enterprise_value"] / 1e9,
        "Equity Value ($B)": r["equity_value"] / 1e9,
        "Implied Share Price": r["implied_share_price"],
    }
    for name, r in results.items()
}).T

print("\nSCENARIO COMPARISON")
print(summary.round(2))

# -----------------------------
# Chart 1 — Implied Share Price by Scenario vs Current Price
# -----------------------------
plt.figure(figsize=(9, 5))
scenario_names = list(results.keys())
implied_prices = [results[s]["implied_share_price"] for s in scenario_names]
bar_colors = ["#d62728", "#1f77b4", "#9467bd", "#2ca02c"]

bars = plt.bar(scenario_names, implied_prices, color=bar_colors[:len(scenario_names)])
for bar, price in zip(bars, implied_prices):
    plt.text(bar.get_x() + bar.get_width() / 2, price, f"${price:,.0f}",
              ha="center", va="bottom", fontsize=10)

if current_price:
    plt.axhline(current_price, color="black", linestyle="--", linewidth=1.5,
                label=f"Current Price (${current_price:,.2f})")
    plt.legend()

plt.title(f"{TICKER} — DCF Implied Share Price by Scenario")
plt.ylabel("Implied Share Price (USD)")
plt.xticks(rotation=10)
plt.grid(True, axis="y")
plt.tight_layout()
plt.savefig(IMAGES_DIR / "dcf_scenario_comparison.png")
plt.close()

# -----------------------------
# Chart 2 — Projected FCF Trajectories by Scenario
# -----------------------------
plt.figure(figsize=(8, 5))
years = [f"Year {i+1}" for i in range(PROJECTION_YEARS)]

for scenario_name, r in results.items():
    plt.plot(years, [v / 1e9 for v in r["projected_fcf"]], marker="o", label=scenario_name)

plt.title(f"{TICKER} — Projected Free Cash Flow by Scenario")
plt.ylabel("Projected FCF ($B)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "dcf_fcf_projections.png")
plt.close()

print("\nDCF charts saved successfully.")
