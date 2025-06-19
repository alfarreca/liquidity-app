import yfinance as yf
import pandas as pd
from datetime import timedelta

# Set your desired start and end dates
start_date = pd.to_datetime("2021-08-06")
end_date = pd.to_datetime("today")

# Get list of all Fridays between start and today
fridays = pd.date_range(start=start_date, end=end_date, freq='W-FRI')

# Download daily data for all series
nasdaq = yf.download("^IXIC", start=start_date, end=end_date + pd.Timedelta(days=2), interval="1d")
spx = yf.download("^GSPC", start=start_date, end=end_date + pd.Timedelta(days=2), interval="1d")
btc = yf.download("BTC-USD", start=start_date, end=end_date + pd.Timedelta(days=2), interval="1d")

# Build NASDAQ_SPX DataFrame
nasdaq_spx_rows = []
for date in fridays:
    date_str = date.strftime("%Y-%m-%d")
    nasdaq_close = nasdaq.loc[date_str]["Close"] if date_str in nasdaq.index else None
    spx_close = spx.loc[date_str]["Close"] if date_str in spx.index else None
    nasdaq_spx_rows.append({"Date": date_str, "NASDAQ": nasdaq_close, "SPX": spx_close})
nasdaq_spx_df = pd.DataFrame(nasdaq_spx_rows)

# Build Bitcoin DataFrame (Saturday after each Friday)
btc_rows = []
for date in fridays:
    sat = date + timedelta(days=1)
    sat_str = sat.strftime("%Y-%m-%d")
    btc_close = btc.loc[sat_str]["Close"] if sat_str in btc.index else None
    btc_rows.append({"Date": sat_str, "Close": btc_close})
btc_df = pd.DataFrame(btc_rows)

# Save to Excel
with pd.ExcelWriter("streamlit_liquidity_fullhistory.xlsx") as writer:
    btc_df.to_excel(writer, sheet_name='Bitcoin', index=False)
    nasdaq_spx_df.to_excel(writer, sheet_name='NASDAQ_SPX', index=False)

print("Excel file created: streamlit_liquidity_fullhistory.xlsx")
