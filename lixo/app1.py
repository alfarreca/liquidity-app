import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="US Liquidity Monitor", layout="wide")
st.title("US Liquidity Monitor (FRED, BTC, NASDAQ, SPX)")
st.write("Upload your Excel (.xlsx) with 'Liquidity Data', 'Bitcoin', and 'NASDAQ_SPX' sheets.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        liq_df = pd.read_excel(uploaded_file, sheet_name="Liquidity Data")
        btc_df = pd.read_excel(uploaded_file, sheet_name="Bitcoin")
        idx_df = pd.read_excel(uploaded_file, sheet_name="NASDAQ_SPX")

        # --- Detect BTC close column robustly ---
        btc_close_col = next((col for col in btc_df.columns if "close" in col.lower()), None)
        if btc_close_col is None:
            st.error("No 'Close' column found in the Bitcoin sheet!")
            st.stop()
        btc_df = btc_df.rename(columns={btc_close_col: "BTC Close"})

        # Ensure Date columns are datetime
        liq_df["Date"] = pd.to_datetime(liq_df["Date"])
        btc_df["Date"] = pd.to_datetime(btc_df["Date"])
        idx_df["Date"] = pd.to_datetime(idx_df["Date"])

        # Merge all on Date (outer join)
        df_merged = liq_df.merge(btc_df[["Date", "BTC Close"]], on="Date", how="left")
        df_merged = df_merged.merge(idx_df, on="Date", how="left")

        st.success("Excel data loaded successfully!")
        st.markdown("### Raw Table (merged, recent values)")
        st.dataframe(df_merged.tail(20))

        # --- Normalization (robust) ---
        plot_cols = []
        col_name_map = {}

        # Always add if available, mapping to label for chart
        if 'Net Liquidity' in df_merged.columns and df_merged['Net Liquidity'].dropna().size > 0:
            plot_cols.append('Net Liquidity')
            col_name_map['Net Liquidity'] = 'Net Liquidity'

        if 'BTC Close' in df_merged.columns and df_merged['BTC Close'].dropna().size > 0:
            plot_cols.append('BTC Close')
            col_name_map['BTC Close'] = 'BTC Close'

        nasdaq_col = next((col for col in df_merged.columns if "nasdaq" in col.lower()), None)
        if nasdaq_col and df_merged[nasdaq_col].dropna().size > 0:
            plot_cols.append(nasdaq_col)
            col_name_map[nasdaq_col] = 'NASDAQ'

        spx_col = next((col for col in df_merged.columns if "spx" in col.lower() or "sp500" in col.lower() or "sp 500" in col.lower()), None)
        if spx_col and df_merged[spx_col].dropna().size > 0:
            plot_cols.append(spx_col)
            col_name_map[spx_col] = 'SPX'

        if not plot_cols:
            st.error("No valid columns to plot! Please check your data.")
            st.stop()

        # --- Normalize (start at 100) ---
        norm_df = df_merged.copy()
        for col in plot_cols:
            non_na = norm_df[col].dropna()
            if non_na.size > 0:
                base = non_na.iloc[0]
                norm_df[col + " (idx)"] = 100 * norm_df[col] / base

        # --- Chart ---
        st.markdown("### Indexed Chart (all start at 100)")
        fig = go.Figure()
        for col in plot_cols:
            idx_col = col + " (idx)"
            if idx_col in norm_df.columns:
                fig.add_trace(go.Scatter(
                    x=norm_df['Date'],
                    y=norm_df[idx_col],
                    mode='lines',
                    name=col_name_map.get(col, col)
                ))
        fig.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            height=500,
            yaxis_title="Indexed (100 = start value)",
            legend=dict(orientation="h"),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")

else:
    st.info("Please upload your Excel file with 'Liquidity Data', 'Bitcoin', and 'NASDAQ_SPX' sheets.")
