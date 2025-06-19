import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- Assume df_merged is your merged dataframe ---
# Columns: Date, Net Liquidity, BTC Close, NASDAQ, SPX

# Normalize each series so all start at 100
plot_cols = ['Net Liquidity', 'BTC Close', 'NASDAQ', 'SPX']
norm_df = df_merged.copy()
for col in plot_cols:
    # Use first non-NA value as base
    base = norm_df[col].dropna().iloc[0]
    norm_df[col + ' (Norm)'] = norm_df[col] / base * 100

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=norm_df['Date'], y=norm_df['Net Liquidity (Norm)'],
    mode='lines', name='Net Liquidity (Norm)'
))
fig.add_trace(go.Scatter(
    x=norm_df['Date'], y=norm_df['BTC Close (Norm)'],
    mode='lines', name='BTC Close (Norm)'
))
fig.add_trace(go.Scatter(
    x=norm_df['Date'], y=norm_df['NASDAQ (Norm)'],
    mode='lines', name='NASDAQ (Norm)'
))
fig.add_trace(go.Scatter(
    x=norm_df['Date'], y=norm_df['SPX (Norm)'],
    mode='lines', name='SPX (Norm)'
))

fig.update_layout(
    title="Liquidity, BTC, and Indexes (All Series Normalized to 100)",
    xaxis_title="Date",
    yaxis_title="Normalized Value (100 = value at start)",
    legend_title="Series",
    template="plotly_white",
    hovermode="x unified",
    margin=dict(l=10, r=10, t=60, b=30)
)

st.subheader("Liquidity, BTC, and Indexes — Normalized")
st.plotly_chart(fig, use_container_width=True)
