import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.graph_objs as go

FRED_API_KEY = "a79018b53e3085363528cf148b358708"
FRED_SERIES = {
    "Fed BS": "WALCL",
    "TGA": "WTREGEN",
    "RRP": "RRPONTSYD"
}

def fetch_fred_series(series_id, start_date):
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    obs = r.json()['observations']
    data = {o['date']: float(o['value']) if o['value'] not in ['.', None, ''] else 0.0 for o in obs}
    return data

def get_weekly_liquidity_data(start_date="2021-08-05"):
    data = {}
    for name, series_id in FRED_SERIES.items():
        data[name] = fetch_fred_series(series_id, start_date)
    all_dates = sorted(set(data['Fed BS'].keys()) | set(data['TGA'].keys()) | set(data['RRP'].keys()))
    output = []
    def num(x): return float(x) if x not in [None, '', '.'] else 0.0
    for d in all_dates:
        date_obj = datetime.strptime(d, "%Y-%m-%d")
        if date_obj.weekday() == 4:  # Friday
            bs = num(data['Fed BS'].get(d, 0))
            tga = num(data['TGA'].get(d, 0))
            rrp = num(data['RRP'].get(d, 0))
            netliq = bs - tga - rrp
            output.append([d, bs, tga, rrp, netliq])
    return pd.DataFrame(output, columns=['Date','Fed BS','TGA','RRP','Net Liquidity'])

def align_btc_to_friday(friday_dates, btc_df):
    btc_map = {pd.to_datetime(r['Date']).date(): r['Close'] for _, r in btc_df.iterrows()}
    result = []
    for d in friday_dates:
        dt = pd.to_datetime(d).date() + timedelta(days=1)
        result.append(btc_map.get(dt, None))
    return result

st.title("US Liquidity Monitor (FRED, BTC, NASDAQ, SPX)")

uploaded_file = st.file_uploader("Upload your Excel (.xlsx) for BTC and NASDAQ/SPX data:", type=["xlsx"])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        btc_df = pd.read_excel(xls, "Bitcoin")
        nasdaq_spx_df = pd.read_excel(xls, "NASDAQ_SPX")
    except Exception as e:
        st.error(f"Error reading uploaded Excel file: {e}")
        st.stop()
else:
    st.info("⬆️ Please upload your Excel file with 'Bitcoin' and 'NASDAQ_SPX' sheets (see template above).")
    st.stop()

st.subheader("Downloading latest weekly FRED liquidity data...")
liq_df = get_weekly_liquidity_data()
friday_dates = liq_df["Date"].tolist()

st.subheader("Merging with Bitcoin and Index Data...")
btc_col = align_btc_to_friday(friday_dates, btc_df)
nasdaq_map = {pd.to_datetime(r['Date']).date(): r['NASDAQ'] for _, r in nasdaq_spx_df.iterrows()}
spx_map = {pd.to_datetime(r['Date']).date(): r['SPX'] for _, r in nasdaq_spx_df.iterrows()}
nasdaq_col = [nasdaq_map.get(pd.to_datetime(d).date(), None) for d in friday_dates]
spx_col = [spx_map.get(pd.to_datetime(d).date(), None) for d in friday_dates]

liq_df['BTC Close'] = btc_col
liq_df['NASDAQ'] = nasdaq_col
liq_df['SPX'] = spx_col

st.dataframe(liq_df)

fig = go.Figure()
fig.add_trace(go.Scatter(x=liq_df['Date'], y=liq_df['Net Liquidity'], mode='lines', name='Net Liquidity'))
fig.add_trace(go.Scatter(x=liq_df['Date'], y=liq_df['BTC Close'], mode='lines', name='BTC Close'))
fig.add_trace(go.Scatter(x=liq_df['Date'], y=liq_df['NASDAQ'], mode='lines', name='NASDAQ'))
fig.add_trace(go.Scatter(x=liq_df['Date'], y=liq_df['SPX'], mode='lines', name='SPX'))
fig.update_layout(
    title='Liquidity, BTC, and Indexes',
    xaxis_title='Date',
    yaxis_title='Value',
    legend=dict(orientation="h")
)
st.plotly_chart(fig, use_container_width=True)
