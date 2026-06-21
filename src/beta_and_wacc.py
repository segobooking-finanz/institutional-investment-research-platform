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
# Configuration — CAPM / WACC Inputs
# -----------------------------
TICKER = "NVDA"
RISK_FREE_RATE = 0.043       # 10-Year US Treasury yield (approx.) — update as needed
MARKET_RISK_PREMIUM = 0.045  # US equity risk premium (approx.) — update as needed
TAX_RATE = 0.21              # US federal statutory corporate tax rate

# -----------------------------
# Load Price Data
# -----------------------------
nvda_prices = pd.read_csv(DATA_DIR / "price_history.csv", index_col=0, parse_dates=True)
sp500_prices = pd.read_csv(DATA_DIR / "sp500_price_history.csv", index_col=0, parse_dates=True)

nvda_close = nvda_prices["Close"]
sp500_close = sp500_prices["Close"]

# -----------------------------
# Daily Returns
# -----------------------------
nvda_returns = nvda_close.pct_change().dropna()
sp500_returns = sp500_close.pct_change().dropna()

# Align both series on matching dates only
returns_df = pd.DataFrame({
    "NVDA": nvda_returns,
    "SP500": sp500_returns
}).dropna()

# -----------------------------
# Beta Method 1 — Regression (calculated by us)
# -----------------------------
covariance = returns_df["NVDA"].cov(returns_df["SP500"])
market_variance = returns_df["SP500"].var()
beta_regression = covariance / market_variance

# -----------------------------
# Beta Method 2 — yfinance reported beta
# -----------------------------
ticker_info = yf.Ticker(TICKER).info
beta_yfinance = ticker_info.get("beta", None)

# -----------------------------
# Cost of Equity (CAPM) — both betas
# -----------------------------
cost_of_equity_regression = RISK_FREE_RATE + beta_regression * MARKET_RISK_PREMIUM
cost_of_equity_yfinance = (
    RISK_FREE_RATE + beta_yfinance * MARKET_RISK_PREMIUM
    if beta_yfinance is not None else None
)

# -----------------------------
# Cost of Debt — from financial statements
# -----------------------------
cash_flow = pd.read_csv(DATA_DIR / "cash_flow.csv", index_col=0)
balance_sheet = pd.read_csv(DATA_DIR / "balance_sheet.csv", index_col=0)

interest_paid = cash_flow.loc["Interest Paid Supplemental Data"].sort_index()
total_debt = balance_sheet.loc["Total Debt"].sort_index()

# Use the most recent fiscal year with data available for both
latest_year = interest_paid.dropna().index[-1]
cost_of_debt_pretax = abs(interest_paid[latest_year]) / total_debt[latest_year]
cost_of_debt_aftertax = cost_of_debt_pretax * (1 - TAX_RATE)

# -----------------------------
# Capital Structure Weights — from latest balance sheet
# -----------------------------
stockholders_equity = balance_sheet.loc["Stockholders Equity"].sort_index()

market_cap = ticker_info.get("marketCap", None)
equity_value = market_cap if market_cap is not None else stockholders_equity[latest_year]
debt_value = total_debt[latest_year]

total_capital = equity_value + debt_value
weight_equity = equity_value / total_capital
weight_debt = debt_value / total_capital

# -----------------------------
# WACC — calculated for both betas
# -----------------------------
wacc_regression = (
    weight_equity * cost_of_equity_regression
    + weight_debt * cost_of_debt_aftertax
)

wacc_yfinance = (
    weight_equity * cost_of_equity_yfinance
    + weight_debt * cost_of_debt_aftertax
    if cost_of_equity_yfinance is not None else None
)

# -----------------------------
# Results Summary
# -----------------------------
print("=" * 60)
print(f"BETA & WACC ANALYSIS — {TICKER}")
print("=" * 60)
print(f"Risk-Free Rate:               {RISK_FREE_RATE:.2%}")
print(f"Market Risk Premium:          {MARKET_RISK_PREMIUM:.2%}")
print(f"Tax Rate:                     {TAX_RATE:.2%}")
print(f"Latest Fiscal Year Used:      {latest_year}")
print("-" * 60)
print(f"Beta (Regression, daily):     {beta_regression:.3f}")
print(f"Beta (yfinance reported):     {beta_yfinance:.3f}" if beta_yfinance else "Beta (yfinance reported): N/A")
print("-" * 60)
print(f"Cost of Equity (Regression):  {cost_of_equity_regression:.2%}")
if cost_of_equity_yfinance:
    print(f"Cost of Equity (yfinance):    {cost_of_equity_yfinance:.2%}")
print(f"Cost of Debt (pre-tax):       {cost_of_debt_pretax:.2%}")
print(f"Cost of Debt (after-tax):     {cost_of_debt_aftertax:.2%}")
print("-" * 60)
print(f"Equity Value Used:            ${equity_value:,.0f}")
print(f"Debt Value Used:               ${debt_value:,.0f}")
print(f"Weight of Equity:              {weight_equity:.2%}")
print(f"Weight of Debt:                {weight_debt:.2%}")
print("-" * 60)
print(f"WACC (using Regression Beta):  {wacc_regression:.2%}")
if wacc_yfinance:
    print(f"WACC (using yfinance Beta):    {wacc_yfinance:.2%}")
print("=" * 60)

# -----------------------------
# Chart — NVDA Returns vs S&P 500 Returns (Scatter + Regression Line)
# -----------------------------
plt.figure(figsize=(8, 6))
plt.scatter(returns_df["SP500"], returns_df["NVDA"], alpha=0.3, s=10, label="Daily Returns")

x_line = np.linspace(returns_df["SP500"].min(), returns_df["SP500"].max(), 100)
y_line = beta_regression * x_line + (returns_df["NVDA"].mean() - beta_regression * returns_df["SP500"].mean())
plt.plot(x_line, y_line, color="red", linewidth=2, label=f"Regression Line (Beta = {beta_regression:.2f})")

plt.title("NVDA Daily Returns vs S&P 500 Daily Returns")
plt.xlabel("S&P 500 Daily Return")
plt.ylabel("NVDA Daily Return")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "beta_regression.png")
plt.close()

# -----------------------------
# Chart — WACC Comparison
# -----------------------------
wacc_labels = ["WACC (Regression Beta)"]
wacc_values = [wacc_regression]

if wacc_yfinance:
    wacc_labels.append("WACC (yfinance Beta)")
    wacc_values.append(wacc_yfinance)

plt.figure(figsize=(6, 5))
bars = plt.bar(wacc_labels, wacc_values, color=["#1f77b4", "#ff7f0e"])
for bar, value in zip(bars, wacc_values):
    plt.text(bar.get_x() + bar.get_width() / 2, value + 0.001, f"{value:.2%}",
              ha="center", va="bottom", fontsize=10)
plt.title("NVIDIA WACC — Regression Beta vs yfinance Beta")
plt.ylabel("WACC")
plt.grid(True, axis="y")
plt.tight_layout()
plt.savefig(IMAGES_DIR / "wacc_comparison.png")
plt.close()

print("\nBeta and WACC charts saved successfully.")