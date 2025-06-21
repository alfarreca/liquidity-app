import pandas as pd
import requests
from datetime import datetime
import io

# --- SETTINGS ---
START_DATE = "2021-08-06"
FRED_API_KEY = 'a79018b53e3085363528cf148b358708'
FRED_SERIES = {
    'Fed BS': 'WALCL',
    'TGA': 'WTREGEN',
    'RRP': 'RRPONTSYD',
    'Sideline Cash': 'WCMFNS',  # Money Market Fund Assets (All)
    'Sentiment': 'AAIISENT'     # Example: AAII Sentiment Index (substitute with any sentiment series)
}
ETF_FLOWS_URL = 'https://api.farside.co.uk/btc/etf.csv'  # Farside BTC ETF flows, adapt as needed

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

# --- Fetch Liquidity Data ---
walcl_df = fetch_fred_series_df(FRED_SERIES['Fed BS'], START_DATE)
tga_df   = fetch_fred_series_df(FRED_SERIES['TGA'], START_DATE)
rrp_df   = fetch_fred_series_df(FRED_SERIES['RRP'], START_DATE)

# Reindex to Fridays, forward-fill the latest known value
walcl_ff = walcl_df.set_index("Date").reindex(fridays, method='ffill')
tga_ff = tga_df.set_index("Date").reindex(fridays, method='ffill')
rrp_ff = rrp_df.set_index("Date").reindex(fridays, method='ffill')

liq_df = pd.DataFrame({
    "Date": fridays,
    "Fed BS": walcl_ff["Value"].values,
    "TGA": tga_ff["Value"].values,
    "RRP": rrp_ff["Value"].values,
})
liq_df["Net Liquidity"] = liq_df["Fed BS"] - liq_df["TGA"] - liq_df["RRP"]

# --- Fetch Sideline Cash (Money Market Fund Assets) ---
sideline_df = fetch_fred_series_df(FRED_SERIES['Sideline Cash'], START_DATE)
sideline_df = sideline_df.set_index("Date").reindex(fridays, method='ffill').reset_index()
sideline_df.rename(columns={'Value': 'Amount'}, inplace=True)

# --- Fetch Sentiment (AAII or other, example series) ---
sentiment_df = fetch_fred_series_df(FRED_SERIES['Sentiment'], START_DATE)
sentiment_df = sentiment_df.set_index("Date").reindex(fridays, method='ffill').reset_index()
sentiment_df.rename(columns={'Value': 'Index'}, inplace=True)

# --- Fetch ETF Flows (BTC ETF example from Farside) ---
# The CSV has columns: Date, Fund, Inflow/Outflow, ... (may require cleaning)
r = requests.get(ETF_FLOWS_URL)
etf_flows_df = pd.read_csv(io.StringIO(r.text))
etf_flows_df['Date'] = pd.to_datetime(etf_flows_df['Date'])
etf_flows_df = etf_flows_df[etf_flows_df['Date'] >= pd.to_datetime(START_DATE)]
# Clean and keep only relevant columns
keep_cols = [col for col in etf_flows_df.columns if col.lower() in ['date', 'fund', 'inflow', 'outflow', 'netflow', 'inflow/outflow', 'inflow / outflow']]
etf_flows_df = etf_flows_df[keep_cols]

# --- Save all to Excel ---
filename = "Macro-Flows-Data-Auto.xlsx"
with pd.ExcelWriter(filename) as writer:
    liq_df.to_excel(writer, sheet_name="Liquidity Data", index=False)
    sideline_df.to_excel(writer, sheet_name="Sideline Cash", index=False)
    sentiment_df.to_excel(writer, sheet_name="Sentiment", index=False)
    etf_flows_df.to_excel(writer, sheet_name="ETF Flows", index=False)

print(f"\nAll done! File saved as {filename}\n")
