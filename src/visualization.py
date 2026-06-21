from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

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
income_statement = pd.read_csv(
    DATA_DIR / "income_statement.csv",
    index_col=0
)

# -----------------------------
# Extract Metrics
# -----------------------------
revenue = income_statement.loc["Total Revenue"]
gross_profit = income_statement.loc["Gross Profit"]
operating_income = income_statement.loc["Operating Income"]
net_income = income_statement.loc["Net Income"]

# -----------------------------
# Revenue Growth
# -----------------------------
revenue_chronological = revenue.sort_index()
revenue_growth = revenue_chronological.pct_change() * 100

# -----------------------------
# Margins
# -----------------------------
gross_margin = (gross_profit / revenue) * 100
operating_margin = (operating_income / revenue) * 100
net_margin = (net_income / revenue) * 100

gross_margin = gross_margin.sort_index()
operating_margin = operating_margin.sort_index()
net_margin = net_margin.sort_index()

# -----------------------------
# Revenue Growth Chart
# -----------------------------
plt.figure(figsize=(8, 5))
revenue_growth.dropna().plot(marker="o")
plt.title("NVIDIA Revenue Growth (%)")
plt.ylabel("Growth %")
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "revenue_growth.png")
plt.close()

# -----------------------------
# Gross Margin Chart
# -----------------------------
plt.figure(figsize=(8, 5))
gross_margin.dropna().plot(marker="o")
plt.title("NVIDIA Gross Margin (%)")
plt.ylabel("Margin %")
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "gross_margin.png")
plt.close()

# -----------------------------
# Operating Margin Chart
# -----------------------------
plt.figure(figsize=(8, 5))
operating_margin.dropna().plot(marker="o")
plt.title("NVIDIA Operating Margin (%)")
plt.ylabel("Margin %")
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "operating_margin.png")
plt.close()

# -----------------------------
# Net Margin Chart
# -----------------------------
plt.figure(figsize=(8, 5))
net_margin.dropna().plot(marker="o")
plt.title("NVIDIA Net Margin (%)")
plt.ylabel("Margin %")
plt.grid(True)
plt.tight_layout()
plt.savefig(IMAGES_DIR / "net_margin.png")
plt.close()

print("Charts saved successfully.")