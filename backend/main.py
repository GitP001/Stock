from app import create_app
from api.news_service import update_news

updated_count = update_news()

app = create_app()

if __name__ == '__main__':
    # By default runs on http://127.0.0.1:5000
    app.run(debug=True)