from pathlib import Path
import pandas as pd
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
IMAGES_DIR = ROOT_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# -----------------------------
# Configuration
# -----------------------------
TICKER = "NVDA"

# DCF results from dcf_model.py (carried over manually — see note in README)
DCF_SCENARIOS = {
    "DCF — Conservative": 57.87,
    "DCF — Base": 98.70,
    "DCF — Optimistic": 178.07,
}

# Wall Street analyst consensus (as of analysis date — sourced from public
# aggregators such as TipRanks / S&P Global; see README for citation and date)
WALL_STREET_LOW = 180.00
WALL_STREET_AVERAGE = 298.93
WALL_STREET_HIGH = 500.00
WALL_STREET_ANALYST_COUNT = 62

# -----------------------------
# Get Current Market Price
# -----------------------------
ticker_info = yf.Ticker(TICKER).info
current_price = ticker_info.get("currentPrice", ticker_info.get("regularMarketPrice"))

# -----------------------------
# Build Comparison Table
# -----------------------------
comparison = pd.DataFrame({
    "Source": list(DCF_SCENARIOS.keys()) + [
        "Wall Street — Low",
        "Wall Street — Average",
        "Wall Street — High",
        "Current Market Price",
    ],
    "Implied / Target Price": list(DCF_SCENARIOS.values()) + [
        WALL_STREET_LOW,
        WALL_STREET_AVERAGE,
        WALL_STREET_HIGH,
        current_price,
    ],
})

comparison["% vs Current Price"] = (
    (comparison["Implied / Target Price"] / current_price - 1) * 100
)

# -----------------------------
# Print Results
# -----------------------------
print("=" * 70)
print(f"{TICKER} — DCF vs. WALL STREET ANALYST CONSENSUS")
print("=" * 70)
print(comparison.round(2).to_string(index=False))
print("=" * 70)
print(f"Wall Street consensus based on {WALL_STREET_ANALYST_COUNT} analysts (Strong Buy rating)")
print(f"Current Market Price: ${current_price:,.2f}")
print("=" * 70)

# -----------------------------
# Chart — DCF Scenarios vs Wall Street Range vs Current Price
# -----------------------------
plt.figure(figsize=(10, 6))

labels = list(DCF_SCENARIOS.keys()) + [
    "Wall Street\nLow",
    "Wall Street\nAverage",
    "Wall Street\nHigh",
]
values = list(DCF_SCENARIOS.values()) + [
    WALL_STREET_LOW,
    WALL_STREET_AVERAGE,
    WALL_STREET_HIGH,
]
colors = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#9467bd", "#9467bd"]

bars = plt.bar(labels, values, color=colors)
for bar, value in zip(bars, values):
    plt.text(bar.get_x() + bar.get_width() / 2, value, f"${value:,.0f}",
              ha="center", va="bottom", fontsize=9)

plt.axhline(current_price, color="black", linestyle="--", linewidth=1.5,
            label=f"Current Price (${current_price:,.2f})")

plt.title(f"{TICKER} — Fundamental DCF vs. Wall Street Analyst Consensus")
plt.ylabel("Price per Share (USD)")
plt.xticks(rotation=15)
plt.legend()
plt.grid(True, axis="y")
plt.tight_layout()
plt.savefig(IMAGES_DIR / "dcf_vs_analyst_consensus.png")
plt.close()

print("\nDCF vs. analyst consensus chart saved successfully.")