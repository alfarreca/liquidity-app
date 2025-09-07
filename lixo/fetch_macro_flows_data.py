def fetch_fred_series_df(series_id, start_date):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
    }
    r = requests.get(url, params=params)
    try:
        data = r.json()
    except Exception:
        print(f"Error: Could not decode JSON for {series_id}")
        print(r.text)
        raise
    if 'observations' not in data:
        print(f"API Error for {series_id}: {data}")
        raise KeyError(f"No 'observations' in response for {series_id}")
    obs = data['observations']
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
