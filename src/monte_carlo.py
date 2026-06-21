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
N_SIMULATIONS = 10_000
RANDOM_SEED = 42  # for reproducibility

np.random.seed(RANDOM_SEED)

# -----------------------------
# Input Distributions
# -----------------------------
# Each variable is modeled as a probability distribution rather than a fixed
# point estimate, anchored to the range already explored across the four
# deterministic DCF scenarios (Conservative / Base / Base 3-Year Beta / Optimistic).

# WACC: Normal distribution centered on the average of the three beta
# methodologies calculated in beta_and_wacc.py (12.47%, 13.78%, 14.19%).
WACC_MEAN = 0.1348
WACC_STD = 0.0080

# Year 1 FCF growth: Normal distribution spanning the Conservative-to-Optimistic
# range (15% to 35%), centered on the Base case (25%).
INITIAL_GROWTH_MEAN = 0.25
INITIAL_GROWTH_STD = 0.06

# Final-year (Year 10) FCF growth: Normal distribution spanning 4% to 9%,
# centered on the Base case (6%).
FINAL_GROWTH_MEAN = 0.06
FINAL_GROWTH_STD = 0.015

# Terminal growth rate: truncated Normal between 2.0% and 4.0%, centered on 3.0%.
# Truncation prevents draws from approaching the WACC, which would make the
# Gordon Growth Model mathematically unstable.
TERMINAL_GROWTH_MEAN = 0.030
TERMINAL_GROWTH_STD = 0.005
TERMINAL_GROWTH_MIN = 0.020
TERMINAL_GROWTH_MAX = 0.040

# -----------------------------
# Load Historical Free Cash Flow & Balance Sheet Data
# -----------------------------
cash_flow = pd.read_csv(DATA_DIR / "cash_flow.csv", index_col=0)
free_cash_flow = cash_flow.loc["Free Cash Flow"].sort_index().dropna()
base_fcf = free_cash_flow.iloc[-1]

balance_sheet = pd.read_csv(DATA_DIR / "balance_sheet.csv", index_col=0)
total_debt_latest = balance_sheet.loc["Total Debt"].sort_index().iloc[-1]
cash_latest = balance_sheet.loc["Cash And Cash Equivalents"].sort_index().iloc[-1]

ticker_info = yf.Ticker(TICKER).info
shares_outstanding = ticker_info.get("sharesOutstanding")
current_price = ticker_info.get("currentPrice", ticker_info.get("regularMarketPrice"))

# -----------------------------
# Draw Random Samples for Each Variable
# -----------------------------
wacc_samples = np.random.normal(WACC_MEAN, WACC_STD, N_SIMULATIONS)
# Guard against unrealistic/negative WACC draws
wacc_samples = np.clip(wacc_samples, 0.08, 0.20)

initial_growth_samples = np.random.normal(INITIAL_GROWTH_MEAN, INITIAL_GROWTH_STD, N_SIMULATIONS)
final_growth_samples = np.random.normal(FINAL_GROWTH_MEAN, FINAL_GROWTH_STD, N_SIMULATIONS)

terminal_growth_samples = np.random.normal(TERMINAL_GROWTH_MEAN, TERMINAL_GROWTH_STD, N_SIMULATIONS)
terminal_growth_samples = np.clip(terminal_growth_samples, TERMINAL_GROWTH_MIN, TERMINAL_GROWTH_MAX)

# Ensure terminal growth never reaches/exceeds WACC for any simulation pair
# (would make the Gordon Growth Model explode). Cap terminal growth at
# WACC - 1.0 percentage point as a safety margin.
terminal_growth_samples = np.minimum(terminal_growth_samples, wacc_samples - 0.01)

# -----------------------------
# Run the DCF for Each Simulation
# -----------------------------
implied_prices = np.zeros(N_SIMULATIONS)

for i in range(N_SIMULATIONS):

    wacc = wacc_samples[i]
    initial_growth = initial_growth_samples[i]
    final_growth = final_growth_samples[i]
    terminal_growth = terminal_growth_samples[i]

    growth_rates = np.linspace(initial_growth, final_growth, PROJECTION_YEARS)

    projected_fcf = []
    fcf = base_fcf
    for g in growth_rates:
        fcf = fcf * (1 + g)
        projected_fcf.append(fcf)

    discount_factors = [(1 + wacc) ** (year + 1) for year in range(PROJECTION_YEARS)]
    pv_fcf = sum(cf / df for cf, df in zip(projected_fcf, discount_factors))

    terminal_value = (projected_fcf[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / discount_factors[-1]

    enterprise_value = pv_fcf + pv_terminal_value
    equity_value = enterprise_value - total_debt_latest + cash_latest
    implied_price = equity_value / shares_outstanding

    implied_prices[i] = implied_price

# -----------------------------
# Summary Statistics
# -----------------------------
mean_price = np.mean(implied_prices)
median_price = np.median(implied_prices)
std_price = np.std(implied_prices)
p10 = np.percentile(implied_prices, 10)
p25 = np.percentile(implied_prices, 25)
p75 = np.percentile(implied_prices, 75)
p90 = np.percentile(implied_prices, 90)

prob_above_market = np.mean(implied_prices > current_price) * 100

print("=" * 70)
print(f"MONTE CARLO DCF SIMULATION — {TICKER}")
print(f"Number of simulations: {N_SIMULATIONS:,}")
print("=" * 70)
print(f"Mean Implied Price:        ${mean_price:,.2f}")
print(f"Median Implied Price:      ${median_price:,.2f}")
print(f"Standard Deviation:        ${std_price:,.2f}")
print("-" * 70)
print(f"10th Percentile:           ${p10:,.2f}")
print(f"25th Percentile:           ${p25:,.2f}")
print(f"75th Percentile:           ${p75:,.2f}")
print(f"90th Percentile:           ${p90:,.2f}")
print("-" * 70)
print(f"Current Market Price:      ${current_price:,.2f}")
print(f"Probability intrinsic value exceeds current market price: {prob_above_market:.1f}%")
print("=" * 70)

# -----------------------------
# Chart 1 — Histogram of Implied Share Price Distribution
# -----------------------------
plt.figure(figsize=(10, 6))
plt.hist(implied_prices, bins=80, color="#1f77b4", alpha=0.75, edgecolor="white")

plt.axvline(current_price, color="black", linestyle="--", linewidth=2,
            label=f"Current Market Price (${current_price:,.2f})")
plt.axvline(median_price, color="red", linestyle="-", linewidth=2,
            label=f"Median Simulated Price (${median_price:,.2f})")
plt.axvline(p10, color="orange", linestyle=":", linewidth=1.5, label=f"P10 (${p10:,.2f})")
plt.axvline(p90, color="orange", linestyle=":", linewidth=1.5, label=f"P90 (${p90:,.2f})")

plt.title(f"{TICKER} — Monte Carlo DCF: Distribution of Implied Share Price\n({N_SIMULATIONS:,} simulations)")
plt.xlabel("Implied Share Price (USD)")
plt.ylabel("Frequency")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "monte_carlo_distribution.png", dpi=150)
plt.close()

# -----------------------------
# Chart 2 — Cumulative Probability Curve
# -----------------------------
sorted_prices = np.sort(implied_prices)
cumulative_prob = np.arange(1, N_SIMULATIONS + 1) / N_SIMULATIONS * 100

plt.figure(figsize=(9, 6))
plt.plot(sorted_prices, cumulative_prob, color="#1f77b4", linewidth=2)
plt.axvline(current_price, color="black", linestyle="--", linewidth=1.5,
            label=f"Current Market Price (${current_price:,.2f})")
plt.axhline(prob_above_market, color="red", linestyle=":", linewidth=1.5)

plt.title(f"{TICKER} — Monte Carlo DCF: Cumulative Probability Distribution")
plt.xlabel("Implied Share Price (USD)")
plt.ylabel("Cumulative Probability (%)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "monte_carlo_cumulative.png", dpi=150)
plt.close()

print("\nMonte Carlo simulation charts saved successfully.")