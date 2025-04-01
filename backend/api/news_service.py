import http.client
import urllib.parse
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from .api_manager import APIUsageTracker

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

# Define paths using Path for better cross-platform compatibility
DATA_DIR = Path(os.getenv("NEWS_DATA_DIR",
                          Path(__file__).parent.parent / 'data'))
ARCHIVE_DIR = DATA_DIR / 'archive'

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# File paths
CURRENT_NEWS_FILE = DATA_DIR / 'batmmaan_news.json'
ARCHIVE_PATTERN = str(ARCHIVE_DIR / 'batmmaan_news_{date}.json')

# Initialize API usage tracker
api_tracker = APIUsageTracker(DATA_DIR)

# BATMMAAN companies (Broadcom, Amazon, Tesla, Microsoft, Meta, Apple, Alphabet, Nvidia)
BATMMAAN_SYMBOLS = "AVGO,AMZN,TSLA,MSFT,META,AAPL,GOOGL,GOOG,NVDA"


# API Client Functions
def fetch_marketaux_news(symbols=BATMMAAN_SYMBOLS, limit=3):
    """
    Fetch news from MarketAux API for BATMMAAN companies.
    Free tier allows 3 articles per request, up to 100 requests daily.

    Args:
        symbols (str): Comma-separated list of stock symbols
        limit (int): Number of articles per request (max 3 for free tier)

    Returns:
        dict: API response with news data or error message
    """
    # Check if we can make a request
    if not api_tracker.can_make_request():
        reset_hours = api_tracker.get_usage_stats()['reset_in_hours']
        remaining_msg = f"Daily API limit reached. Reset in {reset_hours} hours."
        print(remaining_msg)
        return {"error": remaining_msg}

    try:
        conn = http.client.HTTPSConnection('api.marketaux.com')
        params = urllib.parse.urlencode({
            'api_token': API_TOKEN,
            'symbols': symbols,
            'limit': limit,
        })

        conn.request('GET', f'/v1/news/all?{params}')
        res = conn.getresponse()
        data = res.read()

        # Record the API request
        api_tracker.record_request()

        return json.loads(data.decode('utf-8'))
    except json.JSONDecodeError:
        return {"error": "Failed to parse MarketAux response"}
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}

def fetch_news_by_tickers(max_requests=8):
    """
    Fetch news individually for each company ticker.

    Parameters:
    max_requests (int): Maximum number of requests (default is the number of BATMMAAN companies)

    Returns:
    dict: News data
    """
    # Separate BATMMAAN company tickers individually
    batmmaan_tickers = [
        "AVGO",    # Broadcom
        "AMZN",    # Amazon
        "TSLA",    # Tesla
        "MSFT",    # Microsoft
        "META",    # Meta
        "AAPL",    # Apple
        "GOOGL",   # Alphabet (Class A)
        "NVDA"     # Nvidia
    ]

    all_articles = []
    seen_ids = set()  # Set of IDs to prevent duplicates

    # Check the number of available API requests
    available_requests = min(api_tracker.get_remaining_requests(), max_requests)

    if available_requests <= 0:
        return {"error": "Daily API limit reached", "data": []}

    # Make individual API requests for each ticker
    for ticker in batmmaan_tickers[:available_requests]:
        print(f"Fetching news for {ticker}...")
        news_data = fetch_marketaux_news(symbols=ticker, limit=3)

        if "data" in news_data and news_data["data"]:
            # Add articles while removing duplicates
            for article in news_data["data"]:
                article_id = article.get("uuid", "")
                if article_id and article_id not in seen_ids:
                    seen_ids.add(article_id)
                    all_articles.append(article)

        # Small delay between requests to be nice to the API
        if ticker != batmmaan_tickers[available_requests-1]:
            time.sleep(1)

    # Return in the same format
    return {"data": all_articles}

# File Storage Functions
def archive_current_news():
    """
    Archive the current news file if it exists.

    Returns:
        bool: True if archiving succeeded, False otherwise
    """
    if not CURRENT_NEWS_FILE.exists():
        return False

    # Get current timestamp for archive filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = ARCHIVE_PATTERN.format(date=timestamp)

    try:
        # Copy current file to archive
        shutil.copy2(CURRENT_NEWS_FILE, archive_path)
        return True
    except Exception as e:
        print(f"Error archiving news file: {e}")
        return False


def format_articles(news_data):
    """
    Format raw API articles into a consistent structure.

    Args:
        news_data (dict): Raw API response

    Returns:
        list: Formatted articles
    """
    if "data" not in news_data:
        return []

    articles = []
    for i, article in enumerate(news_data["data"], start=1):
        # Extract company symbols from entities
        symbols = []
        if "entities" in article and article["entities"]:
            for entity in article["entities"]:
                if entity.get("symbol"):
                    symbols.append(entity.get("symbol"))

        articles.append({
            "id": article.get("uuid", str(i)),
            "image_url": article.get("image_url", ""),
            "title": article.get("title", "No Title"),
            "snippet": article.get("snippet", "No Summary"),
            "source": article.get("source", "Unknown"),
            "published_at": article.get("published_at", "N/A"),
            "symbols": symbols,
            "url": article.get("url", "")
        })

    return articles


def save_news_to_json(news_data):
    """
    Save the formatted news data to the current JSON file.

    Args:
        news_data (dict): News data from API

    Returns:
        int: Number of articles saved
    """
    articles = format_articles(news_data)

    if not articles:
        print(f"Error in news data: {news_data.get('error', 'No articles found')}")
        return 0

    # Archive the current file first
    archive_result = archive_current_news()
    if not archive_result:
        print("Note: No existing news file to archive")

    # Create data object with articles and metadata
    data_to_save = {
        "last_updated": datetime.now().isoformat(),
        "version": "1.0",
        "environment": os.getenv("FLASK_ENV", "development"),
        "api_stats": api_tracker.get_usage_stats(),
        "articles": articles
    }

    try:
        # Save to current news file
        with open(CURRENT_NEWS_FILE, 'w') as json_file:
            json.dump(data_to_save, json_file, indent=2)
        return len(articles)
    except Exception as e:
        print(f"Error saving news to JSON: {e}")
        return 0


def get_news_from_json():
    """
    Read news from the current JSON file.

    Returns:
        list: List of news articles or empty list if file not found/invalid
    """
    try:
        if CURRENT_NEWS_FILE.exists():
            with open(CURRENT_NEWS_FILE, 'r') as json_file:
                data = json.load(json_file)
                return data.get("articles", [])
        return []
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading news JSON: {e}")
        return []


# Public API Functions
def update_news(article_count=24):
    """
    Fetch news by ticker and update the JSON file.
    Default is 24 articles (3 articles × 8 tickers = 24 total articles).

    Args:
        article_count (int): Maximum number of articles to fetch

    Returns:
        int: Number of articles actually saved
    """
    # Limit the number of requests to not exceed the number of BATMMAAN tickers
    max_requests = min((article_count + 2) // 3, 8)  # 8 = number of BATMMAAN tickers

    # Fetch news by ticker
    news_data = fetch_news_by_tickers(max_requests)

    # Save to JSON file
    return save_news_to_json(news_data)


def get_api_usage_stats():
    """
    Get the current API usage statistics.

    Returns:
        dict: API usage statistics
    """
    return api_tracker.get_usage_stats()