import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta

# --- SETTINGS ---
START_DATE = "2021-08-06"
FRED_API_KEY = 'a79018b53e3085363528cf148b358708'
FRED_SERIES = {
    'Fed BS': 'WALCL',
    'TGA': 'WTREGEN',
    'RRP': 'RRPONTSYD',
    'M2': 'M2SL',    # <--- NEW!
}
today = pd.to_datetime("today")
fridays = pd.date_range(start=START_DATE, end=today, freq="W-FRI")

def fetch_fred_series_df(series_id, start_date):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
    }
    r = requests.get(url, params=params)
    obs = r.json()['observations']
    rows = []
    for o in obs:
        try:
            v = float(o['value']) if o['value'] not in ['.', None, ''] else None
        except:
            v = None
        rows.append({"Date": o['date'], "Value": v})
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df

# --- Fetch all FRED series as DataFrames
walcl_df = fetch_fred_series_df(FRED_SERIES['Fed BS'], START_DATE)
tga_df   = fetch_fred_series_df(FRED_SERIES['TGA'], START_DATE)
rrp_df   = fetch_fred_series_df(FRED_SERIES['RRP'], START_DATE)
m2_df    = fetch_fred_series_df(FRED_SERIES['M2'],   START_DATE)   # <--- NEW!

# --- Reindex to Fridays, forward-fill the latest known value
walcl_ff = walcl_df.set_index("Date").reindex(fridays, method='ffill')
tga_ff   = tga_df.set_index("Date").reindex(fridays, method='ffill')
rrp_ff   = rrp_df.set_index("Date").reindex(fridays, method='ffill')
m2_ff    = m2_df.set_index("Date").reindex(fridays, method='ffill')   # <--- NEW!

liq_df = pd.DataFrame({
    "Date": fridays,
    "Fed BS": walcl_ff["Value"].values,
    "TGA":    tga_ff["Value"].values,
    "RRP":    rrp_ff["Value"].values,
    "M2":     m2_ff["Value"].values,   # <--- NEW!
})
liq_df["Net Liquidity"] = liq_df["Fed BS"] - liq_df["TGA"] - liq_df["RRP"]

# --- BTC, NASDAQ, SPX DATA ---
print("Fetching BTC-USD...")
btc = yf.download("BTC-USD", start=START_DATE, end=today + pd.Timedelta(days=2), interval="1d")
print("Fetching NASDAQ (^IXIC)...")
nasdaq = yf.download("^IXIC", start=START_DATE, end=today + pd.Timedelta(days=2), interval="1d")
print("Fetching S&P 500 (^GSPC)...")
spx = yf.download("^GSPC", start=START_DATE, end=today + pd.Timedelta(days=2), interval="1d")

def get_close(df, date_str):
    try:
        val = df.loc[date_str]["Close"]
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        return float(val)
    except Exception:
        return None

btc_rows = []
for date in fridays:
    sat = date + timedelta(days=1)
    sat_str = sat.strftime("%Y-%m-%d")
    btc_close = get_close(btc, sat_str)
    btc_rows.append({"Date": sat_str, "Close": btc_close})
btc_df = pd.DataFrame(btc_rows)

nasdaq_spx_rows = []
for date in fridays:
    date_str = date.strftime("%Y-%m-%d")
    nas_close = get_close(nasdaq, date_str)
    spx_close = get_close(spx, date_str)
    nasdaq_spx_rows.append({"Date": date_str, "NASDAQ": nas_close, "SPX": spx_close})
nasdaq_spx_df = pd.DataFrame(nasdaq_spx_rows)

filename = "Liquidity-Data-Auto.xlsx"
with pd.ExcelWriter(filename) as writer:
    liq_df.to_excel(writer, sheet_name="Liquidity Data", index=False)
    btc_df.to_excel(writer, sheet_name="Bitcoin", index=False)
    nasdaq_spx_df.to_excel(writer, sheet_name="NASDAQ_SPX", index=False)

print(f"\nAll done! File saved as {filename}\n")
