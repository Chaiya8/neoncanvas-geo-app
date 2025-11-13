import pandas as pd
from datetime import datetime
import time
from textblob import TextBlob
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyAASvZ6pj_05d0c6-VWJb1P8kqd3exc-Hk") 

RUNS_PER_PROMPT = 2
def real_gemini_response(prompt):
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt  # just a string
            )
            return response.text.strip()
        except Exception as e:
            print(f"[DEBUG] Gemini API error: {e}, retrying in 10s...")
            time.sleep(10)
    return "[DEBUG] API error after 3 retries"



def detect_mention(response_text, client_name):
    return client_name.lower() in response_text.lower()

def get_sentiment_score(text):
    return TextBlob(text).sentiment.polarity

def find_mention_position(response_text, client_name):
    idx = response_text.lower().find(client_name.lower())
    if idx == -1:
        return None
    return round(idx / len(response_text), 2)

def run_geo_analysis(client_name):
    print(f"[DEBUG] Starting GEO analysis for client: {client_name}")

    INPUT_CSV = "prompt_bank.csv"
    OUTPUT_CSV = "geo_results_aggregated.csv"

    # Load prompts
    try:
        prompts = pd.read_csv(INPUT_CSV)
    except Exception as e:
        print(f"[DEBUG] Error reading {INPUT_CSV}: {e}")
        return

    filtered_prompts = prompts[prompts['client_name'].str.strip().str.lower() == client_name.lower()]
    print(f"[DEBUG] Found {len(filtered_prompts)} prompts for client '{client_name}'")

    if filtered_prompts.empty:
        print("[DEBUG] No prompts to process. Exiting.")
        return

    aggregate_results = []

    for _, row in filtered_prompts.iterrows():
        prompt = row['prompt_text']
        prompt_id = row['prompt_id']

        print(f"\n[DEBUG] Processing Prompt ID {prompt_id}: {prompt}")

        appearances, positions, sentiments, raw_responses = 0, [], [], []

        for run in range(RUNS_PER_PROMPT):
            response = real_gemini_response(prompt)
            print(f"[DEBUG] Run {run+1} Gemini Response:\n{response}\n{'-'*50}")

            raw_responses.append(response)
            if detect_mention(response, client_name):
                appearances += 1
                pos = find_mention_position(response, client_name)
                if pos is not None:
                    positions.append(pos)
            sentiments.append(get_sentiment_score(response))

        avg_position = sum(positions)/len(positions) if positions else None
        avg_sentiment = sum(sentiments)/len(sentiments) if sentiments else 0
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
            "timestamp": datetime.now()
        })

<<<<<<< HEAD
    # Save results
=======
    #new_df = pd.DataFrame(aggregate_results)

    #       NEW                                                    
    
>>>>>>> 29bd776811db3c3e32d5bf73d1104e3a4ff0b589
    new_df = pd.DataFrame(aggregate_results)
    try:
<<<<<<< HEAD
=======
       
>>>>>>> 29bd776811db3c3e32d5bf73d1104e3a4ff0b589
        existing_df = pd.read_csv(OUTPUT_CSV)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        existing_df = pd.DataFrame()

    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce')
    combined_df = combined_df.dropna(subset=['timestamp'])
    combined_df = combined_df.sort_values('timestamp').drop_duplicates(
        subset=['client_name', 'prompt_id'], keep='last'
    )
<<<<<<< HEAD
=======

>>>>>>> 29bd776811db3c3e32d5bf73d1104e3a4ff0b589
    combined_df.to_csv(OUTPUT_CSV, index=False)
    print(f"[DEBUG] ✅ Saved GEO results to {OUTPUT_CSV}")

if __name__ == "__main__":
    run_geo_analysis("Saddle Creek Orthodontics")


<<<<<<< HEAD
=======
    print(f"✅ Saved aggregated GEO results to {OUTPUT_CSV}")
>>>>>>> 29bd776811db3c3e32d5bf73d1104e3a4ff0b589
