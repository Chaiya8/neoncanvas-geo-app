import pandas as pd
import itertools


# Load client data
clients_df = pd.read_csv("clients.csv")

# Prompt templates
templates = [
    "Who is the best {service} provider in {city}?",
    "Where can I find {service} for {demographic} in {city}?",
    "Affordable {service} in {city} for someone {intent}.",
    "Looking for {service} options in {city} that are {intent}.",
    "What are the top-rated {service} options in {city}?"
]

# Define demographic and intent categories
demographic_options = ["for teens", "for adults", "for kids"]
intent_options = ["with payment plans", "without insurance", "affordable", "available this month"]

# Helper to extract variations from string columns
def parse_column(cell):
    if pd.isna(cell):
        return []
    return [item.strip() for item in str(cell).split(";")]

# Build prompts
all_prompts = []
prompt_id = 1

# iterate through each client and generate prompts
for _, row in clients_df.iterrows():
    client = row["client_name"]
    city = row["city"]
    services = parse_column(row["services_offered"])
    demographics = parse_column(row.get("demographic_focus", ""))
    has_payment = row.get("has_payment_plans", "").lower() == "yes"

    # Build intent list per client
    intents = ["with payment plans"] if has_payment else ["without insurance"]
    intents += ["affordable", "available this month"]

    # created every combination of service, demo, intent, and template
    for service, demographic, intent, template in itertools.product(services, demographics or [""], intents, templates):
        prompt_text = template.format(
            service=service,
            city=city,
            demographic=demographic,
            intent=intent
        ).replace("  ", " ").strip()

        all_prompts.append({
            "prompt_id": prompt_id,
            "prompt_text": prompt_text,
            "client_name": client,
            "city": city,
            "service": service,
            "demographic": demographic,
            "intent": intent
        })
        prompt_id += 1


output_df = pd.DataFrame(all_prompts)
output_df.to_csv("prompt_bank.csv", index=False)
print(f"✅ Generated {len(all_prompts)} prompts for {len(clients_df)} clients.")
