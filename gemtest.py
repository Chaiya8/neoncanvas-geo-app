import pandas as pd
df = pd.read_csv("data/prompt_bank.csv")
print(df.head())
print(df["client_name"].unique())
