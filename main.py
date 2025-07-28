import pandas as pd
from datetime import datetime
import time
from textblob import TextBlob
#import openai
import os
#import openai
# openai.api_key = "sk-proj blah blah"
#openai.api_key = os.getenv("OPENAI_API_KEY")
#export OPENAI_API_KEY="sk-proj blah blah" 
'''
def real_gpt_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or use gpt-4 or gpt-4o if you have access
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return "API error"

'''

RUNS_PER_PROMPT = 100

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
    return "No strong recommendations found."

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
            response = fake_gpt_response(prompt)
            mentioned = detect_mention(response, CLIENT_NAME)
            sentiment = get_sentiment_score(response)

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

    new_df = pd.DataFrame(aggregate_results)

    # If output CSV exists, append new data; otherwise, create it
    if os.path.exists(OUTPUT_CSV):
        existing_df = pd.read_csv(OUTPUT_CSV)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)

        # Fix timestamp column to ensure sorting works
        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce')
        combined_df = combined_df.dropna(subset=['timestamp'])

        # Sort and keep only latest entries for each prompt
        combined_df = combined_df.sort_values('timestamp').drop_duplicates(
            subset=['client_name', 'prompt_id'], keep='last')

        combined_df.to_csv(OUTPUT_CSV, index=False)
    else:
        new_df.to_csv(OUTPUT_CSV, index=False)

    print(f"✅ Saved aggregated GEO results to {OUTPUT_CSV}")