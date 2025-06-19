import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="US Liquidity Monitor", layout="wide")

st.title("US Liquidity Monitor (FRED, BTC, NASDAQ, SPX)")
st.write("Upload your Excel (.xlsx) with 'Liquidity Data', 'Bitcoin', and 'NASDAQ_SPX' sheets.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Load sheets
        liq_df = pd.read_excel(uploaded_file, sheet_name="Liquidity Data")
        btc_df = pd.read_excel(uploaded_file, sheet_name="Bitcoin")
        idx_df = pd.read_excel(uploaded_file, sheet_name="NASDAQ_SPX")
        
        # --- Detect BTC close column (robust) ---
        btc_close_col = None
        for col in btc_df.columns:
            if "close" in col.lower():
                btc_close_col = col
                break
        if btc_close_col is None:
            st.error("No 'Close' column found in the Bitcoin sheet!")
            st.stop()
        btc_df = btc_df.rename(columns={btc_close_col: "BTC Close"})
        
        # Ensure Date columns are datetime for merge
        liq_df["Date"] = pd.to_datetime(liq_df["Date"])
        btc_df["Date"] = pd.to_datetime(btc_df["Date"])
        idx_df["Date"] = pd.to_datetime(idx_df["Date"])

        # Merge all on Date (outer join to preserve all dates)
        df_merged = liq_df.merge(btc_df[["Date", "BTC Close"]], on="Date", how="left")
        df_merged = df_merged.merge(idx_df, on="Date", how="left")

        st.success("Excel data loaded successfully!")
        st.markdown("### Raw Table (merged, recent values)")
        st.dataframe(df_merged.tail(20))

        # Plot
        st.markdown("### Liquidity, BTC, and Indexes")
        fig = go.Figure()
        if "Net Liquidity" in df_merged.columns:
            fig.add_trace(go.Scatter(x=df_merged['Date'], y=df_merged['Net Liquidity'], mode='lines', name='Net Liquidity'))
        if "BTC Close" in df_merged.columns:
            fig.add_trace(go.Scatter(x=df_merged['Date'], y=df_merged['BTC Close'], mode='lines', name='BTC Close'))
        # Try to find NASDAQ and SPX columns
        nasdaq_col = next((col for col in idx_df.columns if "nasdaq" in col.lower()), None)
        spx_col = next((col for col in idx_df.columns if "spx" in col.lower() or "sp500" in col.lower() or "sp 500" in col.lower()), None)
        if nasdaq_col and nasdaq_col in df_merged.columns:
            fig.add_trace(go.Scatter(x=df_merged['Date'], y=df_merged[nasdaq_col], mode='lines', name=nasdaq_col))
        if spx_col and spx_col in df_merged.columns:
            fig.add_trace(go.Scatter(x=df_merged['Date'], y=df_merged[spx_col], mode='lines', name=spx_col))
        fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=450, legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")

else:
    st.info("Please upload your Excel file with 'Liquidity Data', 'Bitcoin', and 'NASDAQ_SPX' sheets.")
