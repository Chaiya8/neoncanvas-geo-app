import streamlit as st
import pandas as pd
from main import run_geo_analysis 
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

st.set_page_config(page_title="GEO Dashboard", layout="wide")

# Login Page
def login_page():
    st.title("🔐 GEO Dashboard Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if username == ADMIN_USER and password == ADMIN_PASS:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

#  Dashboard Page
def dashboard():
    st.title("📊 Generative Engine Optimization (GEO) Dashboard")
    st.sidebar.write(f"👤 Logged in as: {st.session_state['username']}")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    #  Safe load client list (clients.csv)
    try:
        client_df = pd.read_csv("clients.csv")  
    except (FileNotFoundError, pd.errors.EmptyDataError):
        client_df = pd.DataFrame(columns=["client_name"])

    client_list = client_df['client_name'].dropna().unique().tolist()

    #  Safe load GEO results (geo_results_aggregated.csv)
    try:
        df = pd.read_csv("geo_results_aggregated.csv")
    except (FileNotFoundError,  pd.errors.EmptyDataError):
        df = pd.DataFrame(columns=["client_name", "prompt_id", "prompt_text", "appearances",
                                "appearance_percent", "avg_position", "avg_sentiment", "timestamp"])
    
    # Sidebar client selector
    selected_client = st.sidebar.selectbox("Choose a client", client_list)

    # Sidebar form to add new client
    st.sidebar.markdown("### ➕ Add a New Client")
    with st.sidebar.form("add_client_form"):
        new_client_name = st.text_input("Client Name")
        add_client = st.form_submit_button("Add Client")

        if add_client and new_client_name.strip():
            if new_client_name.strip() not in client_list:
                new_row = {"client_name": new_client_name.strip()}
                client_df = pd.concat([client_df, pd.DataFrame([new_row])], ignore_index=True)
                client_df.to_csv("clients.csv", index=False)
                st.success(f"✅ Added {new_client_name.strip()}")
                st.rerun()
            else:
                st.warning("⚠️ That client already exists.")

    # Run GEO Analysis button
    st.sidebar.markdown("### Run GEO Analysis")
    if st.sidebar.button(f"🔄 Run GEO for {selected_client}"):
        with st.spinner("Running analysis..."):
            run_geo_analysis(selected_client)
            st.rerun()
            df = pd.read_csv("geo_results_aggregated.csv")
            st.success("✅ GEO analysis complete")

    # Filter GEO results for selected client
    filtered = df[df['client_name'] == selected_client]
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

# App Entry Point
if "logged_in" not in st.session_state:
    login_page()
else:
    dashboard()
