import requests
import pandas as pd
from datetime import datetime

FRED_API_KEY = 'a79018b53e3085363528cf148b358708'
FRED_SERIES = {
    'Fed BS': 'WALCL',
    'TGA': 'WTREGEN',
    'RRP': 'RRPONTSYD'
}
START_DATE = "2021-08-06"

def fetch_fred_series(series_id, start_date):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
    }
    r = requests.get(url, params=params)
    obs = r.json()['observations']
    data = {o['date']: float(o['value']) if o['value'] not in ['.', None, ''] else None for o in obs}
    return data

def get_weekly_liquidity_data(start_date=START_DATE):
    # Fetch all series into dicts
    all_data = {name: fetch_fred_series(code, start_date) for name, code in FRED_SERIES.items()}
    # Use the union of all available dates
    all_dates = sorted(set().union(*[d.keys() for d in all_data.values()]))
    output = []
    for d in all_dates:
        date_obj = datetime.strptime(d, "%Y-%m-%d")
        # Keep only Fridays (weekday=4)
        if date_obj.weekday() == 4:
            row = [d]
            # Append each value, using None for missing
            vals = [all_data[name].get(d) for name in ['Fed BS', 'TGA', 'RRP']]
            if any(v is not None for v in vals):  # Only keep if at least one value
                bs, tga, rrp = [v if v is not None else 0 for v in vals]
                netliq = bs - tga - rrp
                output.append([d, bs, tga, rrp, netliq])
    return pd.DataFrame(output, columns=['Date','Fed BS','TGA','RRP','Net Liquidity'])

# TEST
df = get_weekly_liquidity_data()
print(df.head())
