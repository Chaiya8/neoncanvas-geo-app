import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from main import run_geo_analysis, get_client_results, get_all_clients_from_results


# Environment
load_dotenv()
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

st.set_page_config(
    page_title="GEO Dashboard",
    layout="wide",
    page_icon="📊"
)


# Login Screen
def login_page():
    st.markdown("<h2 style='text-align:center;'>🔐 GEO Dashboard Login</h2>", unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if username == ADMIN_USER and password == ADMIN_PASS:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Invalid username or password")


# Dashboard Page
def dashboard():

    # ---------------- Sidebar ----------------
    with st.sidebar:
        st.markdown("### 👤 User")
        st.success(f"Logged in as **{ADMIN_USER}**")

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎯 Client Selection")

        clients = get_all_clients_from_results()

        if "clients.csv" in os.listdir("data"):
            cdf = pd.read_csv("data/clients.csv")
            listed_clients = cdf["client_name"].dropna().unique().tolist()
            clients = sorted(set(clients + listed_clients))

        selected_client = st.selectbox("Choose client:", clients)

        st.markdown("### ➕ Add New Client")
        with st.form("add_client_form", clear_on_submit=True):
            newname = st.text_input("Client name")
            if st.form_submit_button("Add"):
                if newname.strip():
                    df = pd.read_csv("data/clients.csv") if os.path.exists("data/clients.csv") else pd.DataFrame(columns=["client_name"])
                    if newname not in df["client_name"].values:
                        df = pd.concat([df, pd.DataFrame([{"client_name": newname}])], ignore_index=True)
                        df.to_csv("data/clients.csv", index=False)
                        st.success(f"Added {newname}")
                        st.rerun()

        st.markdown("---")
        st.markdown("### 🔄 Run Audit")
        if st.button(f"Run GEO for {selected_client}", use_container_width=True):
            with st.spinner("Running analysis..."):
                run_geo_analysis(selected_client)
            st.success("GEO analysis complete")
            st.rerun()

    # ---------------- Main UI ----------------
    st.markdown(f"<h1>📊 GEO Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"### Brand Visibility & Sentiment Analysis for **{selected_client}**")

    df = get_client_results(selected_client)
    if df.empty:
        st.info("No data yet. Run GEO analysis to populate results.")
        return

    # Keep latest rows per prompt
    df_latest = (
        df.sort_values("timestamp")
          .drop_duplicates(subset=["prompt_id"], keep="last")
    )

    # Summary
    last_ts = pd.to_datetime(df["timestamp"]).max()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Prompts Tested", len(df_latest))
    c2.metric("Avg Appearance %", f"{df_latest['appearance_percent'].mean():.2f}%")
    c3.metric("Avg Sentiment", f"{df_latest['avg_sentiment'].mean():.2f}")
    c4.metric("Last Audit", str(last_ts).split(".")[0])

    st.markdown("---")

    # ---------------- Charts ----------------
    st.subheader("📊 Appearance Ranking by Prompt")

    chart = df_latest[["prompt_id", "appearance_percent"]].sort_values("appearance_percent")
    st.bar_chart(chart, x="prompt_id", y="appearance_percent")

    st.markdown("---")

    tabs = st.tabs(["📄 Prompt Overview", "💬 AI Responses"])

    # ---------------- Overview Tab ----------------
    with tabs[0]:
        st.subheader("Prompt Results")
        search = st.text_input("Search prompts")

        show_df = df_latest.copy()
        if search.strip():
            show_df = show_df[show_df["prompt_text"].str.contains(search, case=False, na=False)]

        st.dataframe(
            show_df[["prompt_id", "prompt_text", "appearance_percent", "avg_position", "avg_sentiment"]],
            hide_index=True,
            use_container_width=True
        )

        dl = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", dl, f"{selected_client}_results.csv", "text/csv")

    # ---------------- Responses Tab ----------------
    with tabs[1]:
        st.subheader("Model Responses (per prompt)")

        for _, row in df_latest.iterrows():
            with st.expander(f"Prompt {row['prompt_id']}: {row['prompt_text'][:60]}..."):
                st.markdown("**Prompt Text**")
                st.info(row["prompt_text"])

                responses = str(row["raw_responses"]).split("|||")
                for i, r in enumerate(responses, start=1):
                    st.markdown(f"**Run {i} Response:**")
                    st.write(r.strip())
                    st.markdown("---")



# App Entry Point
if "logged_in" not in st.session_state:
    login_page()
else:
    dashboard()
