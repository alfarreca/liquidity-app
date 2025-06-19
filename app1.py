import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="US Liquidity Monitor", layout="wide")
st.title("US Liquidity Monitor (FRED, BTC, NASDAQ, SPX)")
st.write("Auto-updating dashboard: Net Liquidity, Bitcoin, NASDAQ, S&P 500")

uploaded_file = st.file_uploader("Upload your Excel (.xlsx) file", type=["xlsx"])

if uploaded_file is not None:
    try:
        # --- Load data ---
        liq_df = pd.read_excel(uploaded_file, sheet_name="Liquidity Data")
        btc_df = pd.read_excel(uploaded_file, sheet_name="Bitcoin")
        nasdaq_spx_df = pd.read_excel(uploaded_file, sheet_name="NASDAQ_SPX")

        # Ensure all Date columns are datetime
        liq_df['Date'] = pd.to_datetime(liq_df['Date'])
        btc_df['Date'] = pd.to_datetime(btc_df['Date'])
        nasdaq_spx_df['Date'] = pd.to_datetime(nasdaq_spx_df['Date'])

        # Merge all sheets on Date (outer join)
        df_merged = liq_df.merge(btc_df, on="Date", how="outer").merge(nasdaq_spx_df, on="Date", how="outer")
        df_merged = df_merged.sort_values("Date").reset_index(drop=True)

        st.success("Excel data loaded successfully!")

        st.markdown("### Raw Table (merged, recent values)")
        st.dataframe(df_merged.tail(15))

        # --- PLOT: Original Values ---
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_merged['Date'], y=df_merged['Net Liquidity'], mode='lines', name='Net Liquidity'))
        fig1.add_trace(go.Scatter(x=df_merged['Date'], y=df_merged['BTC Close'], mode='lines', name='BTC Close'))
        fig1.add_trace(go.Scatter(x=df_merged['Date'], y=df_merged['NASDAQ'], mode='lines', name='NASDAQ'))
        fig1.add_trace(go.Scatter(x=df_merged['Date'], y=df_merged['SPX'], mode='lines', name='SPX'))
        fig1.update_layout(
            title="Liquidity, BTC, and Indexes (Raw Values)",
            xaxis_title="Date",
            yaxis_title="Value",
            legend_title="Series",
            template="plotly_white",
            hovermode="x unified"
        )

        st.subheader("Liquidity, BTC, and Indexes — Raw Values")
        st.plotly_chart(fig1, use_container_width=True)

        # --- PLOT: Normalized (Start at 100) ---
        plot_cols = ['Net Liquidity', 'BTC Close', 'NASDAQ', 'SPX']
        norm_df = df_merged.copy()
        for col in plot_cols:
            if col in norm_df and norm_df[col].dropna().shape[0] > 0:
                base = norm_df[col].dropna().iloc[0]
                norm_df[col + ' (Norm)'] = norm_df[col] / base * 100

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=norm_df['Date'], y=norm_df['Net Liquidity (Norm)'],
            mode='lines', name='Net Liquidity (Norm)'
        ))
        fig2.add_trace(go.Scatter(
            x=norm_df['Date'], y=norm_df['BTC Close (Norm)'],
            mode='lines', name='BTC Close (Norm)'
        ))
        fig2.add_trace(go.Scatter(
            x=norm_df['Date'], y=norm_df['NASDAQ (Norm)'],
            mode='lines', name='NASDAQ (Norm)'
        ))
        fig2.add_trace(go.Scatter(
            x=norm_df['Date'], y=norm_df['SPX (Norm)'],
            mode='lines', name='SPX (Norm)'
        ))

        fig2.update_layout(
            title="Liquidity, BTC, and Indexes (All Series Normalized to 100)",
            xaxis_title="Date",
            yaxis_title="Normalized Value (100 = value at start)",
            legend_title="Series",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=10, r=10, t=60, b=30)
        )

        st.subheader("Liquidity, BTC, and Indexes — Normalized")
        st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")

else:
    st.warning("Please upload your Excel file before proceeding.")
