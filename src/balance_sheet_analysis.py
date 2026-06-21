from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

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
# Load Data
# -----------------------------
balance_sheet = pd.read_csv(DATA_DIR / "balance_sheet.csv", index_col=0)
cash_flow = pd.read_csv(DATA_DIR / "cash_flow.csv", index_col=0)
income_statement = pd.read_csv(DATA_DIR / "income_statement.csv", index_col=0)

# -----------------------------
# Extract Balance Sheet Metrics
# -----------------------------
total_assets = balance_sheet.loc["Total Assets"]
current_assets = balance_sheet.loc["Current Assets"]
current_liabilities = balance_sheet.loc["Current Liabilities"]
total_liabilities = balance_sheet.loc["Total Liabilities Net Minority Interest"]
stockholders_equity = balance_sheet.loc["Stockholders Equity"]
total_debt = balance_sheet.loc["Total Debt"]
net_debt = balance_sheet.loc["Net Debt"]
cash_and_equivalents = balance_sheet.loc["Cash And Cash Equivalents"]
inventory = balance_sheet.loc["Inventory"]
working_capital = balance_sheet.loc["Working Capital"]

# -----------------------------
# Extract Cash Flow Metrics
# -----------------------------
operating_cash_flow = cash_flow.loc["Operating Cash Flow"]
free_cash_flow = cash_flow.loc["Free Cash Flow"]
capital_expenditure = cash_flow.loc["Capital Expenditure"]

# -----------------------------
# Extract Income Statement Metrics
# -----------------------------
net_income = income_statement.loc["Net Income"]
revenue = income_statement.loc["Total Revenue"]

# -----------------------------
# Liquidity Ratios
# -----------------------------
current_ratio = current_assets / current_liabilities
quick_ratio = (current_assets - inventory) / current_liabilities

# -----------------------------
# Solvency Ratios
# -----------------------------
debt_to_equity = total_debt / stockholders_equity
debt_to_assets = total_debt / total_assets

# -----------------------------
# Profitability / Efficiency Ratios
# -----------------------------
roe = (net_income / stockholders_equity) * 100
roa = (net_income / total_assets) * 100
fcf_margin = (free_cash_flow / revenue) * 100
cash_conversion = (free_cash_flow / net_income) * 100

# -----------------------------
# Sort chronologically for all series
# -----------------------------
current_ratio = current_ratio.sort_index()
quick_ratio = quick_ratio.sort_index()
debt_to_equity = debt_to_equity.sort_index()
debt_to_assets = debt_to_assets.sort_index()
roe = roe.sort_index()
roa = roa.sort_index()
fcf_margin = fcf_margin.sort_index()
cash_conversion = cash_conversion.sort_index()
working_capital_sorted = working_capital.sort_index()
net_debt_sorted = net_debt.sort_index()
free_cash_flow_sorted = free_cash_flow.sort_index()
operating_cash_flow_sorted = operating_cash_flow.sort_index()
capital_expenditure_sorted = capital_expenditure.sort_index()

# -----------------------------
# Chart 1: Liquidity (Current Ratio vs Quick Ratio)
# -----------------------------
plt.figure(figsize=(8, 5))
current_ratio.plot(marker="o", label="Current Ratio")
quick_ratio.plot(marker="o", label="Quick Ratio")
plt.title("NVIDIA Liquidity Ratios")
plt.ylabel("Ratio")
plt.axhline(1, color="gray", linestyle="--", linewidth=1)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "liquidity_ratios.png")
plt.close()

# -----------------------------
# Chart 2: Solvency (Debt-to-Equity vs Debt-to-Assets)
# -----------------------------
plt.figure(figsize=(8, 5))
debt_to_equity.plot(marker="o", label="Debt-to-Equity")
debt_to_assets.plot(marker="o", label="Debt-to-Assets")
plt.title("NVIDIA Solvency Ratios")
plt.ylabel("Ratio")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "solvency_ratios.png")
plt.close()

# -----------------------------
# Chart 3: Returns (ROE vs ROA)
# -----------------------------
plt.figure(figsize=(8, 5))
roe.plot(marker="o", label="ROE")
roa.plot(marker="o", label="ROA")
plt.title("NVIDIA Return on Equity vs Return on Assets")
plt.ylabel("%")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "returns_roe_roa.png")
plt.close()

# -----------------------------
# Chart 4: Cash Flow (Operating CF vs Free CF vs CapEx)
# -----------------------------
plt.figure(figsize=(8, 5))
operating_cash_flow_sorted.plot(marker="o", label="Operating Cash Flow")
free_cash_flow_sorted.plot(marker="o", label="Free Cash Flow")
capital_expenditure_sorted.plot(marker="o", label="Capital Expenditure")
plt.title("NVIDIA Cash Flow Overview")
plt.ylabel("USD")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "cash_flow_overview.png")
plt.close()

# -----------------------------
# Chart 5: FCF Margin & Cash Conversion
# -----------------------------
plt.figure(figsize=(8, 5))
fcf_margin.plot(marker="o", label="FCF Margin")
cash_conversion.plot(marker="o", label="Cash Conversion (FCF/Net Income)")
plt.title("NVIDIA Cash Efficiency Metrics")
plt.ylabel("%")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "cash_efficiency.png")
plt.close()

# -----------------------------
# Chart 6: Working Capital & Net Debt Trend
# -----------------------------
plt.figure(figsize=(8, 5))
working_capital_sorted.plot(marker="o", label="Working Capital")
net_debt_sorted.plot(marker="o", label="Net Debt")
plt.title("NVIDIA Working Capital vs Net Debt")
plt.ylabel("USD")
plt.axhline(0, color="gray", linestyle="--", linewidth=1)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "working_capital_net_debt.png")
plt.close()

# -----------------------------
# Summary Table (printed to console)
# -----------------------------
summary = pd.DataFrame({
    "Current Ratio": current_ratio,
    "Quick Ratio": quick_ratio,
    "Debt-to-Equity": debt_to_equity,
    "Debt-to-Assets": debt_to_assets,
    "ROE (%)": roe,
    "ROA (%)": roa,
    "FCF Margin (%)": fcf_margin,
    "Cash Conversion (%)": cash_conversion,
})

print(summary.round(2))
print()
print("Balance sheet and cash flow charts saved successfully.")