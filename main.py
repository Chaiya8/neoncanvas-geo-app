# main.py
import os
import time
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
from textblob import TextBlob
from google import genai
from google.genai import types
import streamlit as st

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PROMPT_BANK = DATA_DIR / "prompt_bank.csv"
DB_PATH = DATA_DIR / "geo_results.db"

# ---------- Mode / limits ----------
# DEV_MODE=True  -> small, fast runs that stay under free-tier limits
# DEV_MODE=False -> full audits (needs higher Gemini quota or paid plan)
DEV_MODE = True

RUNS_PER_PROMPT = 1          # how many times to ask Gemini per prompt
MAX_PROMPTS_PER_RUN_DEV = 5  # max prompts per click in DEV_MODE

# ---------- Gemini client ----------
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set. Set it in environment or .env / Streamlit secrets.")

client = genai.Client(api_key=api_key)

# ---------- Gemini call ----------
def real_gemini_response(prompt: str) -> str:
    """Call Gemini 2.5 Flash with Google Search grounding.
    Handles rate-limit errors gracefully for the Streamlit UI.
    """
    # Google Search tool
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    system_instruction = (
        "You are simulating a real user searching for local services on the web. "
        "Use Google Search when needed to answer the query accurately and with "
        "up-to-date information. Respond in a natural, human-like way."
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        system_instruction=system_instruction,
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )
        return response.text.strip()

    except Exception as e:
        msg = str(e)

        # Hit free-tier rate limit / quota
        if "RESOURCE_EXHAUSTED" in msg or "rate-limits" in msg or "quota" in msg.lower():
            st.error(
                "⚠️ Gemini free-tier rate limit reached.\n\n"
                "This API key only allows a small number of requests per minute. "
                "Please wait ~60 seconds and try again, or switch to a paid Gemini "
                "plan / higher quota for full audits."
            )
            print(f"[DEBUG] Gemini rate limit: {e}")
            # Signal run_geo_analysis to stop this run
            raise RuntimeError("Gemini rate limit exceeded") from e

        # Other kind of error
        st.error(f"Gemini API error: {e}")
        print(f"[DEBUG] Gemini API error: {e}")
        raise

# ---------- Helper functions ----------
def detect_mention(response_text: str, client_name: str) -> bool:
    return client_name.lower() in response_text.lower()

def get_sentiment_score(text: str) -> float:
    return TextBlob(text).sentiment.polarity

def find_mention_position(response_text: str, client_name: str):
    idx = response_text.lower().find(client_name.lower())
    if idx == -1:
        return None
    return round(idx / len(response_text), 2)

# ---------- DB ----------
def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS geo_results (
            client_name TEXT,
            prompt_id INTEGER,
            prompt_text TEXT,
            appearances INTEGER,
            appearance_percent REAL,
            avg_position REAL,
            avg_sentiment REAL,
            raw_responses TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()  # run on import

def save_results_to_db(aggregate_results: list[dict]):
    if not aggregate_results:
        return

    conn = get_db_connection()
    cur = conn.cursor()

    for row in aggregate_results:
        # ensure only latest record per client+prompt_id
        cur.execute(
            "DELETE FROM geo_results WHERE client_name = ? AND prompt_id = ?",
            (row["client_name"], row["prompt_id"])
        )
        cur.execute("""
            INSERT INTO geo_results
            (client_name, prompt_id, prompt_text, appearances, appearance_percent,
             avg_position, avg_sentiment, raw_responses, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["client_name"],
            row["prompt_id"],
            row["prompt_text"],
            row["appearances"],
            row["appearance_percent"],
            row["avg_position"],
            row["avg_sentiment"],
            row["raw_responses"],
            row["timestamp"].isoformat(),
        ))

    conn.commit()
    conn.close()   

def get_client_results(client_name: str) -> pd.DataFrame:
    conn = get_db_connection()
    df = pd.read_sql_query(
        """
        SELECT *
        FROM geo_results
        WHERE client_name = ?
        ORDER BY timestamp DESC, prompt_id
        """,
        conn,
        params=(client_name,),
    )
    conn.close()
    return df

def get_all_clients_from_results() -> list[str]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT client_name FROM geo_results ORDER BY client_name")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

# ---------- Core GEO analysis ----------
def run_geo_analysis(client_name: str):
    print(f"[DEBUG] Starting GEO analysis for client: {client_name}")

    if not PROMPT_BANK.exists():
        print(f"[DEBUG] {PROMPT_BANK} not found. Generate it with prompt_generator.py first.")
        st.error("Prompt bank not found. Please generate prompts first.")
        return

    try:
        prompts = pd.read_csv(PROMPT_BANK)
        print(f"[DEBUG] Loaded prompt bank from: {PROMPT_BANK}")
    except Exception as e:
        print(f"[DEBUG] Error reading {PROMPT_BANK}: {e}")
        st.error(f"Error reading prompt bank: {e}")
        return

    # Normalize client names
    filtered_prompts = prompts[
        prompts["client_name"]
        .astype(str)
        .str.strip()
        .str.lower()
        == client_name.strip().lower()
    ]

    print(f"[DEBUG] Found {len(filtered_prompts)} prompts for client '{client_name}'")

    # In DEV mode, cap prompts to stay under free-tier limits
    if DEV_MODE and len(filtered_prompts) > MAX_PROMPTS_PER_RUN_DEV:
        filtered_prompts = filtered_prompts.head(MAX_PROMPTS_PER_RUN_DEV)
        print(f"[DEBUG] DEV_MODE: limiting to {len(filtered_prompts)} prompts this run")

    if filtered_prompts.empty:
        print("[DEBUG] No prompts to process. Exiting.")
        st.info("No prompts found for this client in the prompt bank.")
        return

    aggregate_results = []
    total = len(filtered_prompts)

    # Simple progress bar in the UI
    progress = st.progress(0.0, text="Running GEO analysis...")
    for idx, (_, row) in enumerate(filtered_prompts.iterrows(), start=1):
        prompt = row["prompt_text"]
        prompt_id = int(row["prompt_id"])

        print(f"\n[DEBUG] Processing Prompt ID {prompt_id}/{total}: {prompt}")

        appearances, positions, sentiments, raw_responses = 0, [], [], []

        try:
            for run in range(RUNS_PER_PROMPT):
                response = real_gemini_response(prompt)
                raw_responses.append(response)

                if detect_mention(response, client_name):
                    appearances += 1
                    pos = find_mention_position(response, client_name)
                    if pos is not None:
                        positions.append(pos)

                sentiments.append(get_sentiment_score(response))

        except RuntimeError:
            # Hit rate limit or fatal Gemini error; stop early
            print("[DEBUG] Stopping GEO run early due to Gemini rate limit/error.")
            break

        avg_position = sum(positions) / len(positions) if positions else None
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        appearance_pct = appearances / RUNS_PER_PROMPT * 100

        aggregate_results.append({
            "client_name": client_name,
            "prompt_id": prompt_id,
            "prompt_text": prompt,
            "appearances": appearances,
            "appearance_percent": appearance_pct,
            "avg_position": avg_position,
            "avg_sentiment": avg_sentiment,
            "raw_responses": " ||| ".join(raw_responses),
            "timestamp": datetime.now(),
        })

        progress.progress(idx / total, text=f"Running GEO analysis… {idx}/{total}")

    progress.empty()
    save_results_to_db(aggregate_results)
    print(f"[DEBUG] ✅ Saved {len(aggregate_results)} GEO rows for {client_name} to {DB_PATH}")
