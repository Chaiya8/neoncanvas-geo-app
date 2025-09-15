import pandas as pd
from datetime import datetime
import time
from textblob import TextBlob
import openai
import os
from openai import OpenAI
import openai
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

import time


def real_gpt_response(prompt):
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                store=True
            )
            return response.choices[0].message.content.strip()
        except openai.RateLimitError:
            print("Rate limit hit. Waiting 20 seconds...")
            time.sleep(20)
    return "API error due to rate limits"
    
RUNS_PER_PROMPT = 2

'''
# Placeholder for GPT (will replace this later)
def fake_gpt_response(prompt):
    responses = {
        "Invisalign": "Saddle Creek Orthodontics is widely known for Invisalign in Memphis.",
        "braces": "There are many providers of braces near Germantown, but Saddle Creek Orthodontics is highly rated.",
        "clear aligners": "For clear aligners, Smile Direct Club is an option in Collierville.",
        "veneers": "Bright Smiles Dental is a top pick for veneers in Austin.",
        "pediatric dentistry": "KidsFirst Dental Group is trusted for pediatric dentistry in San Diego.",
        "checkups": "Healthy Grins Dental offers affordable checkups in Orlando."
    }
    for keyword, response in responses.items():
        if keyword.lower() in prompt.lower():
            return response
    return "No strong recommendations found." '''

# Check if client is mentioned
def detect_mention(response_text, client_name):
    return client_name.lower() in response_text.lower()

# Analyze sentiment
def get_sentiment_score(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity  # Ranges from -1 to 1

# Find the position of the mention
def find_mention_position(response_text, client_name):
    idx = response_text.lower().find(client_name.lower())
    if idx == -1:
        return None
    return round(idx / len(response_text), 2)

# Main GEO engine
def run_geo_analysis(client_name):
    CLIENT_NAME = client_name
    INPUT_CSV = "prompt_bank.csv"
    OUTPUT_CSV = "geo_results_aggregated.csv"

    prompts = pd.read_csv(INPUT_CSV)
    filtered_prompts = prompts[prompts['client_name'].str.lower() == CLIENT_NAME.lower()]

    aggregate_results = []

    for _, row in filtered_prompts.iterrows():
        prompt = row['prompt_text']
        prompt_id = row['prompt_id']

        appearances = 0
        positions = []
        sentiments = []

        # Simulate multiple runs for each prompt
        for _ in range(RUNS_PER_PROMPT):
            response = real_gpt_response(prompt)
            print("\n--- GPT Response ---")
            print(response)
            print("--------------------\n")
            mentioned = detect_mention(response, CLIENT_NAME)
            sentiment = get_sentiment_score(response)
            #time.sleep(10)


            # Collect results
            if mentioned:
                appearances += 1
                pos = find_mention_position(response, CLIENT_NAME)
                if pos is not None:
                    positions.append(pos)
            sentiments.append(sentiment)

        avg_position = sum(positions) / len(positions) if positions else None
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        appearance_pct = appearances / RUNS_PER_PROMPT * 100

        aggregate_results.append({
            "client_name": CLIENT_NAME,
            "prompt_id": prompt_id,
            "prompt_text": prompt,
            "appearances": appearances,
            "appearance_percent": appearance_pct,
            "avg_position": avg_position,
            "avg_sentiment": avg_sentiment,
            "timestamp": datetime.now()
        })

    #new_df = pd.DataFrame(aggregate_results)

    # If output CSV exists, append new data; otherwise, create it
    new_df = pd.DataFrame(aggregate_results)

    # Exit early if there are no new results to save
    if new_df.empty:
        print(f"No new prompts found for {CLIENT_NAME}. File not updated.")
        return

    try:
        # Try to read the existing file
        existing_df = pd.read_csv(OUTPUT_CSV)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # If it doesn't exist or is empty, start with an empty DataFrame
        existing_df = pd.DataFrame()

    # Combine old and new data
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

    # Fix timestamp column to ensure sorting works
    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce')
    combined_df = combined_df.dropna(subset=['timestamp'])

    # Sort and keep only the latest entries for each unique prompt
    combined_df = combined_df.sort_values('timestamp').drop_duplicates(
        subset=['client_name', 'prompt_id'], keep='last'
    )

    # Save the updated DataFrame
    combined_df.to_csv(OUTPUT_CSV, index=False)

    print(f"✅ Saved aggregated GEO results to {OUTPUT_CSV}")