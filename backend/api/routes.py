from flask import Blueprint, jsonify
from .news_service import fetch_marketaux_news

api_bp = Blueprint('api_bp', __name__)

@api_bp.route('/news', methods=['GET'])
def get_news():
    """
    Returns news articles in JSON format for the Flutter frontend.
    """
    marketaux_response = fetch_marketaux_news()
    
    # Example: parse the response and transform it to a simpler JSON
    if "data" in marketaux_response:
        # 'data' is a list of articles from MarketAux
        articles = []
        for i, article in enumerate(marketaux_response["data"], start=1):
            articles.append({
                "id": article.get("uuid", str(i)),
                "image_url": article.get("image_url", ""),
                "title": article.get("title", "No Title"),
                "snippet": article.get("snippet", "No Summary"),
                "source": article.get("source", "Unknown"),
                "published_at": article.get("published_at", "N/A")
            })
        return jsonify(articles)
    else:
        # Return an error message or empty list
        return jsonify([]), 500