from pytrends.request import TrendReq
import pandas as pd
import numpy as np

pytrends = TrendReq(hl='en-US', tz=360)

bags = [
    "Chanel Classic Flap",
    "Hermes Birkin",
    "Hermes Kelly",
    "Dior Saddle Bag",
    "Bottega Veneta Pouch",
    "Louis Vuitton Capucines"
]

anchor = "Louis Vuitton Neverfull"

def fetch_batch(keywords):
    pytrends.build_payload(keywords,
                           timeframe='2018-01-01 2026-02-23',  # ← updated
                           geo='')
    data = pytrends.interest_over_time().drop(columns=['isPartial'])
    return data

all_batches = []
for i in range(0, len(bags), 4):
    batch_terms = bags[i:i+4] + [anchor]
    batch_data = fetch_batch(batch_terms)
    batch_data = batch_data.reset_index()
    all_batches.append(batch_data)

scaled_frames = []
for df in all_batches:
    anchor_max = df[anchor].max()
    for col in df.columns:
        if col not in ["date", anchor]:
            df[col] = df[col] / anchor_max
    scaled_frames.append(df.drop(columns=[anchor]))

gtrends_df = scaled_frames[0]
for df in scaled_frames[1:]:
    gtrends_df = gtrends_df.merge(df, on="date", how="outer")

gtrends_df["month"] = gtrends_df["date"].dt.to_period("M").astype(str)
gtrends_df = gtrends_df.drop(columns=["date"])
gtrends_df.to_csv("google.csv", index=False)
print(f" Saved — last month: {gtrends_df['month'].max()}")