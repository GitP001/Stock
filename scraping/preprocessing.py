import pandas as pd
import re

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())  # Remove special characters
    return text.strip()

def preprocess_news_data(raw_data):
    processed_data = []
    for article in raw_data:
        processed_data.append({
            "headline": clean_text(article.get("title", "")),
            "snippet": clean_text(article.get("summary", "")),
            "ticker": article.get("ticker", None),  # Ensure tickers are valid
            "date": article.get("date", ""),
            "source": article.get("source", "")
        })
    return processed_data