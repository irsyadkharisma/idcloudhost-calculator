import streamlit as st
import pandas as pd

st.title("Server Recommendations")

# Load data from CSV
df = pd.read_csv("data/server_recommendation.csv")

# Display as table
st.dataframe(df, use_container_width=True, hide_index=True)

# Optional: show as static Markdown table
st.markdown("### Plain Text View")
st.write(df.to_markdown(index=False))

st.caption("Use this as a starting reference before calculating VPS costs.")
