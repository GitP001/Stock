from flask import jsonify, current_app, request
from .news_service import get_news_from_json, update_news, get_api_usage_stats

# Import the blueprint instance from the package
from . import api_bp

@api_bp.route('/news', methods=['GET'])
def get_news():
    """
    Returns news articles in JSON format for the Flutter frontend.
    Optionally refreshes data if requested or if data is stale.
    """
    # Check if we should force refresh
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    articles = get_news_from_json()
    
    # If articles are empty or force refresh is requested
    if not articles or force_refresh:
        current_app.logger.info("Fetching fresh articles from API...")
        update_news()
        articles = get_news_from_json()

    if articles:
        return jsonify(articles)
    else:
        return jsonify([]), 500

@api_bp.route('/news/update', methods=['POST'])
def force_news_update():
    """
    Force an update of the news data.
    This endpoint can be used for manual updates if needed.
    """
    try:
        # Get optional count parameter with default of 24 (3 articles × 8 tickers)
        article_count = request.args.get('count', 24, type=int)
        articles_count = update_news(article_count)

        api_stats = get_api_usage_stats()
        return jsonify({
            "status": "success",
            "message": f"Updated {articles_count} articles",
            "api_usage": api_stats
        })
    except Exception as e:
        current_app.logger.error(f"Error in force update: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/news/api-usage', methods=['GET'])
def api_usage():
    """
    Get the current API usage statistics.
    """
    try:
        return jsonify(get_api_usage_stats())
    except Exception as e:
        current_app.logger.error(f"Error getting API usage: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500