import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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

        # Matplotlib plot
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(merged["Date"], merged["Net Liquidity (idx)"], label="Net Liquidity (Indexed)", linewidth=2)
        ax.plot(merged["Date"], merged["Sideline Cash (idx)"], label="Sideline Cash (Indexed)", linewidth=2)
        ax.set_xlabel("Date")
        ax.set_ylabel("Indexed Value (100 = Start)")
        ax.set_title("Net Liquidity vs. Sideline Cash (Indexed)")
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)
        st.dataframe(merged[["Date", "Net Liquidity", "Amount"]].tail(10))

    except Exception as e:
        st.error(f"Error reading or processing file: {e}")
else:
    st.info("Please upload your `Macro-Flows-Data-Auto.xlsx` file to see the chart.")

