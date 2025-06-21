import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="US Liquidity Monitor", layout="wide")
st.title("US Liquidity Monitor (FRED, BTC, NASDAQ, SPX)")
st.write("Upload your Excel (.xlsx) with 'Liquidity Data', 'Bitcoin', and 'NASDAQ_SPX' sheets.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        # --- Load sheets ---
        liq_df = pd.read_excel(uploaded_file, sheet_name="Liquidity Data")
        btc_df = pd.read_excel(uploaded_file, sheet_name="Bitcoin")
        idx_df = pd.read_excel(uploaded_file, sheet_name="NASDAQ_SPX")

        # --- Ensure Date columns are datetime and sorted ---
        liq_df["Date"] = pd.to_datetime(liq_df["Date"])
        btc_df["Date"] = pd.to_datetime(btc_df["Date"])
        idx_df["Date"] = pd.to_datetime(idx_df["Date"])

        liq_df = liq_df.sort_values("Date")
        btc_df = btc_df.sort_values("Date")
        idx_df = idx_df.sort_values("Date")

        # --- Robustly detect BTC close column ---
        btc_close_col = next((col for col in btc_df.columns if "close" in col.lower()), None)
        if btc_close_col is None:
            st.error("No 'Close' column found in the Bitcoin sheet!")
            st.stop()
        btc_df = btc_df.rename(columns={btc_close_col: "BTC Close"})

        # --- Merge BTC onto liquidity data using "merge_asof" (nearest previous date) ---
        merged_df = pd.merge_asof(
            liq_df,
            btc_df[["Date", "BTC Close"]],
            on="Date",
            direction="backward"
        )

        # --- Merge Index data as usual (outer join) ---
        merged_df = merged_df.merge(idx_df, on="Date", how="left")

        st.success("Excel data loaded successfully!")
        st.markdown("### Raw Table (merged, recent values)")
        st.dataframe(merged_df.tail(20))

        # --- Normalization (start at 100) ---
        plot_cols = []
        col_name_map = {}

        if 'Net Liquidity' in merged_df.columns and merged_df['Net Liquidity'].dropna().size > 0:
            plot_cols.append('Net Liquidity')
            col_name_map['Net Liquidity'] = 'Net Liquidity'

        if 'BTC Close' in merged_df.columns and merged_df['BTC Close'].dropna().size > 0:
            plot_cols.append('BTC Close')
            col_name_map['BTC Close'] = 'BTC'

        nasdaq_col = next((col for col in merged_df.columns if "nasdaq" in col.lower()), None)
        if nasdaq_col and merged_df[nasdaq_col].dropna().size > 0:
            plot_cols.append(nasdaq_col)
            col_name_map[nasdaq_col] = 'NASDAQ'

        spx_col = next((col for col in merged_df.columns if "spx" in col.lower() or "sp500" in col.lower() or "sp 500" in col.lower()), None)
        if spx_col and merged_df[spx_col].dropna().size > 0:
            plot_cols.append(spx_col)
            col_name_map[spx_col] = 'SPX'

        if not plot_cols:
            st.error("No valid columns to plot! Please check your data.")
            st.stop()

        # --- Normalize (start at 100) ---
        norm_df = merged_df.copy()
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
