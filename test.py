import os
from openai import OpenAI
import time

# Make sure your env var OPENAI_API_KEY is set
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def real_gpt_response(prompt):
    print("Calling GPT for prompt:", prompt)
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                store=True
            )
            result = response.choices[0].message.content.strip()
            print("Got response:", result)
            return result
        except Exception as e:
            # Catch all exceptions, including rate limits
            print("Error calling GPT:", e)
            print("Waiting 20 seconds before retry...")
            time.sleep(20)
    return "API error after retries"

# Test it
print(real_gpt_response("Hello, can you test this?"))
