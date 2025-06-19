import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta

# Settings
START_DATE = "2021-08-06"
today = pd.to_datetime("today")
fridays = pd.date_range(start=START_DATE, end=today, freq="W-FRI")

# --- 1. Fetch NASDAQ and SPX from Yahoo Finance ---
nasdaq = yf.download("^IXIC", start=START_DATE, end=today + pd.Timedelta(days=2), interval="1d")
spx = yf.download("^GSPC", start=START_DATE, end=today + pd.Timedelta(days=2), interval="1d")

nasdaq_spx = []
for date in fridays:
    date_str = date.strftime("%Y-%m-%d")
    nas_close = nasdaq.loc[date_str]["Close"] if date_str in nasdaq.index else None
    spx_close = spx.loc[date_str]["Close"] if date_str in spx.index else None
    nasdaq_spx.append({"Date": date_str, "NASDAQ": nas_close, "SPX": spx_close})
nasdaq_spx_df = pd.DataFrame(nasdaq_spx)

# --- 2. Fetch BTC weekly (CoinGecko: Friday's close = Saturday's open) ---
btc_rows = []
for date in fridays:
    sat = date + timedelta(days=1)
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/history?date={sat.strftime('%d-%m-%Y')}"
    try:
        resp = requests.get(url, timeout=10)
        price = resp.json()["market_data"]["current_price"]["usd"]
    except Exception:
        price = None
    btc_rows.append({"Date": sat.strftime("%Y-%m-%d"), "Close": price})
btc_df = pd.DataFrame(btc_rows)

# --- 3. Save to Excel ---
filename = "Liquidity-Data-Auto.xlsx"
with pd.ExcelWriter(filename) as writer:
    btc_df.to_excel(writer, sheet_name="Bitcoin", index=False)
    nasdaq_spx_df.to_excel(writer, sheet_name="NASDAQ_SPX", index=False)

print(f"File saved as {filename}")
