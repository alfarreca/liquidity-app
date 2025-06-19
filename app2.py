import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="US Liquidity Monitor", layout="wide")

st.title("US Liquidity Monitor (FRED, BTC, NASDAQ, SPX)")
st.write("Auto-updating dashboard: Net Liquidity, Bitcoin, NASDAQ, S&P 500")

# --- File uploader ---
uploaded_file = st.file_uploader("Upload your Liquidity-Data-Auto.xlsx", type="xlsx")

if uploaded_file:
    # --- Load data only after upload ---
    @st.cache_data(ttl=3600)
    def load_data(file):
        liq_df = pd.read_excel(file, sheet_name="Liquidity Data")
        btc_df = pd.read_excel(file, sheet_name="Bitcoin")
        nasdaq_spx_df = pd.read_excel(file, sheet_name="NASDAQ_SPX")

        liq_df['Date'] = pd.to_datetime(liq_df['Date'])
        btc_df['Date'] = pd.to_datetime(btc_df['Date'])
        nasdaq_spx_df['Date'] = pd.to_datetime(nasdaq_spx_df['Date'])

        df_merged = liq_df.merge(btc_df, on="Date", how="outer").merge(nasdaq_spx_df, on="Date", how="outer")
        df_merged = df_merged.sort_values("Date").reset_index(drop=True)
        return df_merged

    df_merged = load_data(uploaded_file)
    st.markdown("### Raw Data (recent values)")
    st.dataframe(df_merged.tail(15))

    # --- Date range selection ---
    st.sidebar.header("Date Filter")
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        value=[df_merged['Date'].min(), df_merged['Date'].max()],
        min_value=df_merged['Date'].min(),
        max_value=df_merged['Date'].max()
    )

    filtered_df = df_merged[
        (df_merged['Date'] >= pd.to_datetime(start_date)) &
        (df_merged['Date'] <= pd.to_datetime(end_date))
    ]

    # --- Series selection checkboxes ---
    st.sidebar.header("Series Selection")
    series_options = {
        "Net Liquidity": st.sidebar.checkbox("Net Liquidity", True),
        "BTC Close": st.sidebar.checkbox("BTC Close", True),
        "NASDAQ": st.sidebar.checkbox("NASDAQ", True),
        "SPX": st.sidebar.checkbox("SPX", True)
    }
    selected_series = [series for series, checked in series_options.items() if checked]

    # --- Normalization ---
    def normalize(df, cols):
        norm_df = df.copy()
        for col in cols:
            if col in norm_df and norm_df[col].dropna().shape[0] > 0:
                base = norm_df[col].dropna().iloc[0]
                norm_df[col + ' (Norm)'] = norm_df[col] / base * 100
        return norm_df

    norm_df = normalize(filtered_df, selected_series)

    # --- Plotting ---
    fig = go.Figure()
    for series in selected_series:
        if series + ' (Norm)' in norm_df:
            fig.add_trace(go.Scatter(
                x=norm_df['Date'],
                y=norm_df[series + ' (Norm)'],
                mode='lines',
                name=f'{series} (Normalized)'
            ))
    fig.update_layout(
        title="Liquidity, BTC, and Indexes (Normalized)",
        xaxis_title="Date",
        yaxis_title="Normalized Value (100 = start)",
        legend_title="Series",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=60, b=30)
    )
    st.subheader("Normalized Data Visualization")
    st.plotly_chart(fig, use_container_width=True)

    # --- Error handling ---
    if filtered_df[selected_series].isnull().values.any():
        st.warning("Warning: Data contains missing values. Some series might be incomplete.")

    st.info("For feedback, features, or troubleshooting, ask your AI financial analyst!")

else:
    st.info("Please upload your 'Liquidity-Data-Auto.xlsx' file to get started.")
