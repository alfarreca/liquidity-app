import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="US Liquidity Insights", layout="wide")
st.title("US Liquidity Insights Monitor")
st.write("Analyze liquidity trends and market behavior with additional insights")

# Insights section
st.markdown("""
### Key Liquidity Insights

1. **Sound Insight**:  
   Markets can rise despite falling traditional liquidity due to alternative inflows (ETFs, foreign investment).

2. **Contra-Intuitive Insight**:  
   Tight liquidity can sometimes concentrate investment in "hot" assets, pushing prices higher.

**Current Observation**: When liquidity falls but markets rise, these insights help explain the divergence.
""")

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
        
        # --- Recent Data Analysis ---
        st.markdown("### Recent Trend Analysis")
        
        # Get the last 3 months of data
        recent_df = merged_df.tail(90)  # approx 3 months
        
        # Calculate trends
        liquidity_trend = "↑ Increasing" if recent_df['Net Liquidity'].iloc[-1] > recent_df['Net Liquidity'].iloc[0] else "↓ Decreasing"
        
        # Dynamic insights based on trends
        if 'Net Liquidity' in recent_df.columns and 'BTC Close' in recent_df.columns:
            btc_trend = "↑ Increasing" if recent_df['BTC Close'].iloc[-1] > recent_df['BTC Close'].iloc[0] else "↓ Decreasing"
            
            if liquidity_trend == "↓ Decreasing" and btc_trend == "↑ Increasing":
                st.warning("**Divergence Detected**: Liquidity falling while Bitcoin rises - suggests alternative inflows (ETFs, institutional) or crowding into crypto as a 'hot asset'")
            elif liquidity_trend == "↓ Decreasing" and btc_trend == "↓ Decreasing":
                st.info("**Typical Correlation**: Both liquidity and Bitcoin falling - suggests traditional market dynamics")
            elif liquidity_trend == "↑ Increasing" and btc_trend == "↑ Increasing":
                st.info("**Typical Correlation**: Both liquidity and Bitcoin rising - traditional expansionary environment")
        
        st.markdown("### Raw Table (merged, recent values)")
        st.dataframe(recent_df)

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
        
        # Add annotations for insights
        if 'Net Liquidity (idx)' in norm_df.columns and 'BTC (idx)' in norm_df.columns:
            # Find points where liquidity falls but BTC rises
            for i in range(1, len(norm_df)):
                if (norm_df['Net Liquidity (idx)'].iloc[i] < norm_df['Net Liquidity (idx)'].iloc[i-1] and 
                    norm_df['BTC (idx)'].iloc[i] > norm_df['BTC (idx)'].iloc[i-1]):
                    fig.add_annotation(
                        x=norm_df['Date'].iloc[i],
                        y=norm_df['BTC (idx)'].iloc[i],
                        text="Liquidity↓ BTC↑",
                        showarrow=True,
                        arrowhead=1,
                        ax=0,
                        ay=-40
                    )
        
        fig.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            height=600,
            yaxis_title="Indexed (100 = start value)",
            legend=dict(orientation="h"),
            hovermode="x unified",
            title="Liquidity vs. Markets with Insight Annotations"
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Correlation Analysis ---
        st.markdown("### Correlation Analysis")
        
        if len(plot_cols) > 1:
            corr_df = norm_df[[col + " (idx)" for col in plot_cols if col + " (idx)" in norm_df.columns]].corr()
            st.write("Correlation matrix of indexed series:")
            st.dataframe(corr_df.style.background_gradient(cmap='coolwarm', vmin=-1, vmax=1))
            
            if 'Net Liquidity (idx)' in corr_df.columns:
                liquidity_corrs = corr_df['Net Liquidity (idx)'].drop('Net Liquidity (idx)')
                strongest_corr = liquidity_corrs.abs().idxmax()
                st.write(f"**Strongest correlation with liquidity**: {strongest_corr} ({liquidity_corrs[strongest_corr]:.2f})")
                
                if liquidity_corrs[strongest_corr] < -0.5:
                    st.info("Strong negative correlation detected - when liquidity falls, this asset tends to rise (supports contra-intuitive insight)")

    except Exception as e:
        st.error(f"Error loading data: {e}")

else:
    st.info("Please upload your Excel file with 'Liquidity Data', 'Bitcoin', and 'NASDAQ_SPX' sheets.")
