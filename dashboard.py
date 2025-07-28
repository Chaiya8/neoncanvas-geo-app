import streamlit as st
import pandas as pd
from main import run_geo_analysis  # Your GEO function

st.set_page_config(page_title="GEO Dashboard", layout="wide")

st.title("📊 Generative Engine Optimization (GEO) Dashboard")

# === Safe load client list (clients.csv) ===
try:
    client_df = pd.read_csv("clients.csv")  # Load your full client list file
except FileNotFoundError:
    # Create empty DataFrame if no file yet
    client_df = pd.DataFrame(columns=["client_name"])

client_list = client_df['client_name'].dropna().unique().tolist()

# === Safe load GEO results (geo_results_aggregated.csv) ===
try:
    df = pd.read_csv("geo_results_aggregated.csv")
except FileNotFoundError:
    # Create empty DataFrame with correct columns if no file yet
    df = pd.DataFrame(columns=["client_name", "prompt_id", "prompt_text", "appearances",
                               "appearance_percent", "avg_position", "avg_sentiment", "timestamp"])

# === Sidebar client selector ===
selected_client = st.sidebar.selectbox("Choose a client", client_list)

# === Sidebar form to add new client ===
st.sidebar.markdown("### ➕ Add a New Client")

with st.sidebar.form("add_client_form"):
    new_client_name = st.text_input("Client Name")
    add_client = st.form_submit_button("Add Client")

    if add_client and new_client_name.strip():
        if new_client_name.strip() not in client_list:
            # Append new client to client_df and save CSV
            new_row = {"client_name": new_client_name.strip()}
            client_df = pd.concat([client_df, pd.DataFrame([new_row])], ignore_index=True)
            client_df.to_csv("clients.csv", index=False)
            st.success(f"✅ Added {new_client_name.strip()}")
            st.rerun()  # Refresh app to update client list in sidebar
        else:
            st.warning("⚠️ That client already exists.")

# === Run GEO Analysis button ===
st.sidebar.markdown("### Run GEO Analysis")
if st.sidebar.button(f"🔄 Run GEO for {selected_client}"):
    with st.spinner("Running analysis..."):
        run_geo_analysis(selected_client)
        st.rerun()  # Refresh to load new data

# === Filter GEO results for selected client ===
filtered = df[df['client_name'] == selected_client]

# === Show results or info message ===
st.markdown(f"### Results for: `{selected_client}`")

if filtered.empty:
    st.info("No data available for this client yet. Click the Run button above to generate GEO results.")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Prompts Tested", len(filtered))
    col2.metric("Avg Appearance %", f"{filtered['appearance_percent'].mean():.2f}%")
    col3.metric("Avg Sentiment", f"{filtered['avg_sentiment'].mean():.2f}")

    st.markdown("#### Prompt-Level Details")
    st.dataframe(
        filtered[['prompt_text', 'appearance_percent', 'avg_position', 'avg_sentiment']]
        .sort_values(by='appearance_percent', ascending=False),
        use_container_width=True
    )

    st.caption("Data from geo_results_aggregated.csv")
