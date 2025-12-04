# prompt_generator.py
from pathlib import Path
import itertools
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CLIENTS_CSV = DATA_DIR / "clients.csv"
PROMPT_BANK = DATA_DIR / "prompt_bank.csv"

if not CLIENTS_CSV.exists():
    raise FileNotFoundError(f"{CLIENTS_CSV} not found")

clients_df = pd.read_csv(CLIENTS_CSV)

# ---------- your existing template logic ----------
templates = [
    "Who is the best {service} provider in {city}?",
    "Where can I find {service} for {demographic} in {city}?",
    "Affordable {service} in {city} for someone {intent}.",
    "Looking for {service} options in {city} that are {intent}.",
    "What are the top-rated {service} options in {city}?"
]

def parse_column(cell):
    if pd.isna(cell):
        return []
    return [item.strip() for item in str(cell).split(";") if item.strip()]

all_prompts = []
prompt_id = 1

for _, row in clients_df.iterrows():
    client = row["client_name"].strip()
    city = str(row.get("city", "")).strip() or "my area"
    services = parse_column(row.get("services_offered", ""))
    demographics = parse_column(row.get("demographic_focus", "")) or [""]
    has_payment = str(row.get("has_payment_plans", "")).lower() == "yes"

    intents = ["with payment plans"] if has_payment else ["without insurance"]
    intents += ["affordable", "available this month"]

    for service, demographic, intent, template in itertools.product(
        services, demographics, intents, templates
    ):
        prompt_text = template.format(
            service=service,
            city=city,
            demographic=demographic,
            intent=intent,
        ).replace("  ", " ").strip()

        all_prompts.append({
            "prompt_id": prompt_id,
            "prompt_text": prompt_text,
            "client_name": client,
            "city": city,
            "service": service,
            "demographic": demographic,
            "intent": intent,
        })
        prompt_id += 1

output_df = pd.DataFrame(all_prompts)
output_df.to_csv(PROMPT_BANK, index=False)
print(f"✅ Generated {len(all_prompts)} prompts for {len(clients_df)} clients at {PROMPT_BANK}")
