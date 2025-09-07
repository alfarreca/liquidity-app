import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Net Liquidity vs Sideline Cash vs VIX", layout="wide")
st.title("Net Liquidity vs Sideline Cash vs VIX Dashboard")

uploaded_file = st.file_uploader("Upload your Macro-Flows-Data-Auto.xlsx file", type=["xlsx"])
if uploaded_file:
    try:
        # Load all sheets
        liq_df = pd.read_excel(uploaded_file, sheet_name="Liquidity Data")
        side_df = pd.read_excel(uploaded_file, sheet_name="Sideline Cash")
        vix_df = pd.read_excel(uploaded_file, sheet_name="Sentiment")
        st.write("Liquidity Data columns:", list(liq_df.columns))
        st.write("Sideline Cash columns:", list(side_df.columns))
        st.write("Sentiment columns:", list(vix_df.columns))

        # Column selections
        liq_date_col = st.selectbox(
            "Select Date column for Liquidity Data", list(liq_df.columns), index=0 if "Date" in liq_df.columns else 0
        )
        side_date_col = st.selectbox(
            "Select Date column for Sideline Cash", list(side_df.columns), index=0 if "Date" in side_df.columns else 0
        )
        vix_date_col = st.selectbox(
            "Select Date column for Sentiment (VIX)", list(vix_df.columns), index=0 if "index" in vix_df.columns else 0
        )

        liq_value_col = st.selectbox(
            "Select Net Liquidity column", list(liq_df.columns), index=list(liq_df.columns).index("Net Liquidity") if "Net Liquidity" in liq_df.columns else 1
        )
        side_value_col = st.selectbox(
            "Select Sideline Cash column", list(side_df.columns), index=list(side_df.columns).index("Amount") if "Amount" in side_df.columns else 1
        )
        vix_value_col = st.selectbox(
            "Select VIX column", list(vix_df.columns), index=list(vix_df.columns).index("VIX") if "VIX" in vix_df.columns else 1
        )

        # Prepare and forward-fill missing values in Net Liquidity
        liq_df[liq_date_col] = pd.to_datetime(liq_df[liq_date_col])
        side_df[side_date_col] = pd.to_datetime(side_df[side_date_col])
        vix_df[vix_date_col] = pd.to_datetime(vix_df[vix_date_col])
        liq_df[liq_value_col] = liq_df[liq_value_col].fillna(method='ffill')

        # Merge
        merged = pd.merge(
            liq_df[[liq_date_col, liq_value_col]].rename(columns={liq_date_col:"Date", liq_value_col:"Net Liquidity"}),
            side_df[[side_date_col, side_value_col]].rename(columns={side_date_col:"Date", side_value_col:"Sideline Cash"}),
            on="Date", how="inner"
        )
        merged = pd.merge(
            merged,
            vix_df[[vix_date_col, vix_value_col]].rename(columns={vix_date_col:"Date", vix_value_col:"VIX"}),
            on="Date", how="left"
        )

        # --- DIAGNOSTICS ---
        st.write("NaN counts:", merged[["Net Liquidity", "Sideline Cash", "VIX"]].isnull().sum())
        if merged["Net Liquidity"].isnull().all():
            st.error("All Net Liquidity values are missing after merge! Check date alignment.")
        if merged["Sideline Cash"].isnull().all():
            st.error("All Sideline Cash values are missing after merge! Check date alignment.")
        if merged["VIX"].isnull().all():
            st.error("All VIX values are missing after merge! Check date alignment.")

        # Normalize using first valid values
        first_valid_nl = merged["Net Liquidity"].dropna().iloc[0]
        first_valid_sc = merged["Sideline Cash"].dropna().iloc[0]
        merged["Net Liquidity (idx)"] = merged["Net Liquidity"] / first_valid_nl * 100
        merged["Sideline Cash (idx)"] = merged["Sideline Cash"] / first_valid_sc * 100

        # Diagnostics
        st.write("Sample of VIX:")
        st.write(merged[["Date", "VIX"]].tail(30))
        st.write("VIX min/max:", merged["VIX"].min(), merged["VIX"].max())

        # Plot with three Y-axes (Net Liquidity, Sideline Cash, VIX)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=merged["Date"], y=merged["Net Liquidity (idx)"],
            mode="lines", name="Net Liquidity (Indexed)",
            yaxis="y1"
        ))
        fig.add_trace(go.Scatter(
            x=merged["Date"], y=merged["Sideline Cash (idx)"],
            mode="lines", name="Sideline Cash (Indexed)",
            yaxis="y2"
        ))
        fig.add_trace(go.Scatter(
            x=merged["Date"], y=merged["VIX"],
            mode="lines", name="VIX",
            yaxis="y3"
        ))

        fig.update_layout(
            xaxis=dict(title="Date"),
            yaxis=dict(
                title="Net Liquidity (Indexed)",
                side="left",
                showgrid=True,
                zeroline=True
            ),
            yaxis2=dict(
                title="Sideline Cash (Indexed)",
                side="right",
                overlaying="y",
                showgrid=False,
                zeroline=False
            ),
            yaxis3=dict(
                title="VIX",
                side="right",
                overlaying="y",
                anchor="free",
                position=1,
                showgrid=False
            ),
            title="Net Liquidity vs. Sideline Cash vs. VIX (Indexed, Multi Y-Axis)",
            legend=dict(orientation="h"),
            height=600,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(merged[["Date", "Net Liquidity", "Sideline Cash", "VIX"]].tail(10))
    except Exception as e:
        st.error(f"Error reading or processing file: {e}")
else:
    st.info("Please upload your `Macro-Flows-Data-Auto.xlsx` file to see the chart.")
