import http.client
import urllib.parse
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

def fetch_marketaux_news(symbols="AAPL,TSLA", limit=5):
    """
    Fetch news from MarketAux API for given symbols.
    """
    conn = http.client.HTTPSConnection('api.marketaux.com')
    params = urllib.parse.urlencode({
        'api_token': API_TOKEN,
        'symbols': symbols,
        'limit': limit,
    })

    conn.request('GET', f'/v1/news/all?{params}')
    res = conn.getresponse()
    data = res.read()

    try:
        return json.loads(data.decode('utf-8'))
    except json.JSONDecodeError:
        return {"error": "Failed to parse MarketAux response"}