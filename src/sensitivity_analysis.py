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

# Base Scenario growth profile — anchors the sensitivity grid
INITIAL_GROWTH = 0.25
FINAL_YEAR_GROWTH = 0.06

# Sensitivity grid ranges
WACC_RANGE = np.arange(0.11, 0.155, 0.005)        # 11.0% to 15.0%
TERMINAL_GROWTH_RANGE = np.arange(0.020, 0.045, 0.0025)  # 2.0% to 4.25%

# -----------------------------
# Load Historical Free Cash Flow
# -----------------------------
cash_flow = pd.read_csv(DATA_DIR / "cash_flow.csv", index_col=0)
free_cash_flow = cash_flow.loc["Free Cash Flow"].sort_index().dropna()
base_fcf = free_cash_flow.iloc[-1]

# -----------------------------
# Get Shares Outstanding, Current Price, Debt, Cash
# -----------------------------
ticker_info = yf.Ticker(TICKER).info
shares_outstanding = ticker_info.get("sharesOutstanding")
current_price = ticker_info.get("currentPrice", ticker_info.get("regularMarketPrice"))

balance_sheet = pd.read_csv(DATA_DIR / "balance_sheet.csv", index_col=0)
total_debt_latest = balance_sheet.loc["Total Debt"].sort_index().iloc[-1]
cash_latest = balance_sheet.loc["Cash And Cash Equivalents"].sort_index().iloc[-1]

# -----------------------------
# DCF Function — returns implied share price for given WACC & terminal growth
# -----------------------------
def run_dcf(wacc, terminal_growth):

    growth_rates = np.linspace(INITIAL_GROWTH, FINAL_YEAR_GROWTH, PROJECTION_YEARS)

    projected_fcf = []
    fcf = base_fcf
    for g in growth_rates:
        fcf = fcf * (1 + g)
        projected_fcf.append(fcf)

    discount_factors = [(1 + wacc) ** (i + 1) for i in range(PROJECTION_YEARS)]
    pv_fcf = [cf / df for cf, df in zip(projected_fcf, discount_factors)]

    # Guard against terminal_growth >= wacc (mathematically invalid / explosive)
    if terminal_growth >= wacc:
        return np.nan

    terminal_value = (projected_fcf[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / discount_factors[-1]

    enterprise_value = sum(pv_fcf) + pv_terminal_value
    equity_value = enterprise_value - total_debt_latest + cash_latest
    implied_share_price = equity_value / shares_outstanding if shares_outstanding else np.nan

    return implied_share_price

# -----------------------------
# Build Sensitivity Grid
# -----------------------------
sensitivity_table = pd.DataFrame(
    index=[f"{w:.2%}" for w in WACC_RANGE],
    columns=[f"{g:.2%}" for g in TERMINAL_GROWTH_RANGE],
    dtype=float
)

for wacc in WACC_RANGE:
    for tg in TERMINAL_GROWTH_RANGE:
        price = run_dcf(wacc, tg)
        sensitivity_table.loc[f"{wacc:.2%}", f"{tg:.2%}"] = price

sensitivity_table.index.name = "WACC"
sensitivity_table.columns.name = "Terminal Growth"

# -----------------------------
# Print Results
# -----------------------------
print("=" * 90)
print(f"SENSITIVITY ANALYSIS — {TICKER} DCF Implied Share Price")
print(f"(Base growth profile: {INITIAL_GROWTH:.0%} Year 1 fading to {FINAL_YEAR_GROWTH:.0%} Year {PROJECTION_YEARS})")
print("=" * 90)
print(sensitivity_table.round(2))
print("=" * 90)
print(f"Current Market Price: ${current_price:,.2f}" if current_price else "Current Market Price: N/A")
print("=" * 90)

# -----------------------------
# Chart — Heatmap of Implied Share Price
# -----------------------------
fig, ax = plt.subplots(figsize=(10, 7))

data = sensitivity_table.values.astype(float)
im = ax.imshow(data, cmap="RdYlGn", aspect="auto")

ax.set_xticks(range(len(sensitivity_table.columns)))
ax.set_xticklabels(sensitivity_table.columns, rotation=45, ha="right")
ax.set_yticks(range(len(sensitivity_table.index)))
ax.set_yticklabels(sensitivity_table.index)

ax.set_xlabel("Terminal Growth Rate")
ax.set_ylabel("WACC")
ax.set_title(f"{TICKER} DCF Sensitivity — Implied Share Price (USD)\nCurrent Market Price: ${current_price:,.2f}")

# Annotate each cell with its value
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        value = data[i, j]
        if not np.isnan(value):
            ax.text(j, i, f"${value:,.0f}", ha="center", va="center",
                     fontsize=7, color="black")

fig.colorbar(im, ax=ax, label="Implied Share Price (USD)")
plt.tight_layout()
plt.savefig(IMAGES_DIR / "dcf_sensitivity_heatmap.png", dpi=150)
plt.close()

# -----------------------------
# Chart — Implied Price vs WACC (multiple terminal growth lines)
# -----------------------------
plt.figure(figsize=(9, 6))

selected_tg = [TERMINAL_GROWTH_RANGE[0], TERMINAL_GROWTH_RANGE[len(TERMINAL_GROWTH_RANGE) // 2], TERMINAL_GROWTH_RANGE[-1]]

for tg in selected_tg:
    prices = [run_dcf(w, tg) for w in WACC_RANGE]
    plt.plot(WACC_RANGE * 100, prices, marker="o", label=f"Terminal Growth = {tg:.2%}")

if current_price:
    plt.axhline(current_price, color="black", linestyle="--", linewidth=1.5,
                label=f"Current Price (${current_price:,.2f})")

plt.title(f"{TICKER} — Implied Share Price vs WACC")
plt.xlabel("WACC (%)")
plt.ylabel("Implied Share Price (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "dcf_sensitivity_lines.png")
plt.close()

print("\nSensitivity analysis charts saved successfully.")