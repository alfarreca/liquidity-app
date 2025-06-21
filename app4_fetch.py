import streamlit as st
import pandas as pd

st.set_page_config(page_title="Macro Data Previewer", layout="wide")
st.title("Macro Data Previewer (Simple)")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file is not None:
    try:
        # List all sheet names
        xl = pd.ExcelFile(uploaded_file)
        sheet_names = xl.sheet_names
        st.write("Available sheets:", sheet_names)

        # Pick a sheet to view
        sheet = st.selectbox("Select a sheet to preview", options=sheet_names)
        df = xl.parse(sheet)
        st.dataframe(df.head(30))
        st.success("Sheet loaded! If you want, upload a file with more sheets (ETF flows, sentiment, etc.)")
    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Upload your Excel file with any of: ETF Flows, Sideline Cash, Liquidity, Sentiment... Each as a separate sheet.")
