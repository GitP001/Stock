import http.client
import urllib.parse
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from .api_manager import APIUsageTracker, DAILY_REQUEST_LIMIT

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
print(f"API Token first 4 chars: {API_TOKEN[:4] if API_TOKEN else 'N/A'}")

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
def fetch_marketaux_news(symbols=BATMMAAN_SYMBOLS, limit=3, language="en"):
    """
    Fetch news from MarketAux API for BATMMAAN companies.
    Free tier allows 3 articles per request, up to 100 requests daily.

    Args:
        symbols (str): Comma-separated list of stock symbols
        limit (int): Number of articles per request (max 3 for free tier)
        language (str): Language filter (default: "en" for English only)

    Returns:
        dict: API response with news data or error message
    """
   # Check if we can make a request
    usage_stats = api_tracker.get_usage_stats()
    
    if not api_tracker.can_make_request():
        reset_hours = usage_stats['reset_in_hours']
        remaining_msg = f"Daily API limit reached. Reset in {reset_hours} hours."
        print(remaining_msg)
        return {"error": remaining_msg}

    try:
        conn = http.client.HTTPSConnection('api.marketaux.com')
        params = urllib.parse.urlencode({
            'api_token': API_TOKEN,
            'symbols': symbols,
            'limit': limit,
            'language': language,
        })

        conn.request('GET', f'/v1/news/all?{params}')
        res = conn.getresponse()
        status = res.status
        
        data = res.read()
        # Record the API request
        api_tracker.record_request()
        
        return json.loads(data.decode('utf-8'))
    except json.JSONDecodeError:
        return {"error": "Failed to parse MarketAux response"}
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}

def fetch_news_by_tickers(max_requests=8, language="en"):
    """
    Fetch news individually for each company ticker.

    Parameters:
    max_requests (int): Maximum number of requests (default is the number of BATMMAAN companies)
    language (str): Language filter (default: "en" for English only)

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
        news_data = fetch_marketaux_news(symbols=ticker, limit=3, language=language)

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


# Changes to news_service.py

def format_articles(news_data):
    """
    Format raw API articles into a consistent structure,
    with enhanced titles and summaries.

    Args:
        news_data (dict): Raw API response

    Returns:
        list: Formatted articles
    """
    if "data" not in news_data:
        return []
    
    # Import here to avoid circular imports
    from .summarize_service import summarize_text, enhance_title

    articles = []
    for i, article in enumerate(news_data["data"], start=1):
        # Extract company symbols from entities
        symbols = []
        company_name = None
        if "entities" in article and article["entities"]:
            for entity in article["entities"]:
                if entity.get("symbol"):
                    symbols.append(entity.get("symbol"))
                    # Use the first symbol's name as company_name for context
                    if not company_name and entity.get("name"):
                        company_name = entity.get("name")

        # Get full description for better summarization
        description = article.get("description", "")
        
        # Enhance the title - make it more concise and impactful
        original_title = article.get("title", "No Title")
        enhanced_title = enhance_title(original_title)
        
        # If enhance_title returned None or empty string, use original title
        if not enhanced_title:
            enhanced_title = original_title
            
        # NEW: Don't include title in the full text to avoid redundancy
        # This helps ensure the summary doesn't repeat the title
        smart_summary = summarize_text(description, company_name, title_text=enhanced_title)
        
        # NEW: Additional check to ensure summary is not too similar to title
        if smart_summary and enhanced_title:
            # Simple check for high similarity
            if smart_summary.lower() == enhanced_title.lower() or (
                    len(smart_summary) > 0 and len(enhanced_title) > 0 and 
                    (smart_summary.lower() in enhanced_title.lower() or 
                     enhanced_title.lower() in smart_summary.lower())):
                
                # Try to extract a different summary by focusing on later parts of the text
                sentences = description.split('.')
                if len(sentences) > 3:
                    # Use later sentences for the summary
                    alternative_text = '. '.join(sentences[2:])
                    smart_summary = summarize_text(alternative_text, company_name, title_text=enhanced_title)
                    
                    # If still too similar or empty, use a generic summary
                    if not smart_summary or smart_summary.lower() == enhanced_title.lower():
                        if company_name:
                            smart_summary = f"Read more details about this {company_name} news story in the full article."
                        else:
                            smart_summary = "The article provides more details on this topic. Read the full text for comprehensive information."

        articles.append({
            "id": article.get("uuid", str(i)),
            "image_url": article.get("image_url", ""),
            "title": enhanced_title,
            "original_title": original_title,  # Keep original title for reference
            "description": description,
            "snippet": smart_summary,
            "source": article.get("source", "Unknown"),
            "published_at": article.get("published_at", "N/A"),
            "symbols": symbols,
            "language": article.get("language", "N/A"),
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
def update_news(article_count=24, language="en"):
    """
    Fetch news by ticker and update the JSON file.
    Default is 24 articles (3 articles × 8 tickers = 24 total articles).

    Args:
        article_count (int): Maximum number of articles to fetch
        language (str): Language filter (default: "en" for English only)

    Returns:
        int: Number of articles actually saved
    """
    print(f"Starting news update: requested {article_count} articles, language={language}")
    
    # Check API usage
    usage_stats = get_api_usage_stats()
    print(f"Current API usage: {usage_stats['requests_today']}/{DAILY_REQUEST_LIMIT} requests used today")
    
    # Limit the number of requests to not exceed the number of BATMMAAN tickers
    max_requests = min((article_count + 2) // 3, 8)  # 8 = number of BATMMAAN tickers
    print(f"Will make up to {max_requests} API requests")

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