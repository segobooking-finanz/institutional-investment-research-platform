import yfinance as yf
import pandas as pd
from pathlib import Path


# -----------------------------
# Configuration
# -----------------------------

TICKER = "NVDA"
BENCHMARK_TICKER = "^GSPC"  # S&P 500, used for beta regression

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


# -----------------------------
# Download Financial Statements
# -----------------------------

def download_financial_data(ticker_symbol):

    ticker = yf.Ticker(ticker_symbol)

    income_statement = ticker.financials
    balance_sheet = ticker.balance_sheet
    cash_flow = ticker.cashflow

    return income_statement, balance_sheet, cash_flow


# -----------------------------
# Download Price History
# -----------------------------

def download_price_history(ticker_symbol, period="10y"):

    ticker = yf.Ticker(ticker_symbol)

    price_history = ticker.history(period=period)

    return price_history


# -----------------------------
# Save Data
# -----------------------------

def save_data(df, filename):

    file_path = DATA_DIR / filename

    df.to_csv(file_path)

    print(f"Saved: {file_path}")


# -----------------------------
# Main
# -----------------------------

if __name__ == "__main__":

    print(f"Downloading data for {TICKER}...")

    income_statement, balance_sheet, cash_flow = download_financial_data(TICKER)

    price_history = download_price_history(TICKER)

    save_data(income_statement, "income_statement.csv")
    save_data(balance_sheet, "balance_sheet.csv")
    save_data(cash_flow, "cash_flow.csv")
    save_data(price_history, "price_history.csv")

    print(f"Downloading benchmark data for {BENCHMARK_TICKER}...")

    benchmark_price_history = download_price_history(BENCHMARK_TICKER)

    save_data(benchmark_price_history, "sp500_price_history.csv")

    print("Download completed.")