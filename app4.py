import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Net Liquidity vs Sideline Cash", layout="wide")
st.title("Net Liquidity vs Sideline Cash Dashboard")

uploaded_file = st.file_uploader("Upload your Macro-Flows-Data-Auto.xlsx file", type=["xlsx"])
if uploaded_file:
    try:
        # Load sheets
        liq_df = pd.read_excel(uploaded_file, sheet_name="Liquidity Data")
        side_df = pd.read_excel(uploaded_file, sheet_name="Sideline Cash")
        # Merge by date
        merged = pd.merge(
            liq_df[["Date", "Net Liquidity"]],
            side_df[["Date", "Amount"]],
            on="Date", how="inner"
        )
        # Normalize both to 100
        merged["Net Liquidity (idx)"] = merged["Net Liquidity"] / merged["Net Liquidity"].iloc[0] * 100
        merged["Sideline Cash (idx)"] = merged["Amount"] / merged["Amount"].iloc[0] * 100

        # Plotly line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=merged["Date"], y=merged["Net Liquidity (idx)"], 
            mode="lines", name="Net Liquidity (Indexed)"
        ))
        fig.add_trace(go.Scatter(
            x=merged["Date"], y=merged["Sideline Cash (idx)"], 
            mode="lines", name="Sideline Cash (Indexed)"
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Indexed Value (100 = Start)",
            title="Net Liquidity vs. Sideline Cash (Indexed)",
            legend=dict(orientation="h"),
            height=500,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(merged[["Date", "Net Liquidity", "Amount"]].tail(10))
    except Exception as e:
        st.error(f"Error reading or processing file: {e}")
else:
    st.info("Please upload your `Macro-Flows-Data-Auto.xlsx` file to see the chart.")
