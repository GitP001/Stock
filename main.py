from apscheduler.schedulers.background import BackgroundScheduler
from scraping.scraping import fetch_stock_news
from scraping.preprocessing import preprocess_news_data
from scraping.database import insert_news

def scheduled_job():
    # Fetch, preprocess, and store news data
    symbols = ["AAPL", "GOOGL", "TSLA"]
    raw_data = fetch_stock_news(symbols)
    if raw_data:
        processed_data = preprocess_news_data(raw_data)
        insert_news(processed_data)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_job, "cron", hour=6)
    scheduler.add_job(scheduled_job, "cron", hour=18)

    scheduler.start()
    print("Scheduler started. Press Ctrl+C to exit.")

    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler stopped.")