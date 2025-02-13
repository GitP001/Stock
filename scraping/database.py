CREATE TABLE stock_news (
    id SERIAL PRIMARY KEY,
    headline TEXT NOT NULL,
    snippet TEXT,
    ticker VARCHAR(10) NOT NULL,
    date TIMESTAMP NOT NULL,
    source VARCHAR(255),
    keywords TEXT[],  -- Store extracted keywords (optional)
    sentiment_score FLOAT  -- Store sentiment analysis score (optional)
); 

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define database connection
engine = create_engine("postgresql://user:password@localhost/stock_helper")
Base = declarative_base()

# Define Table Schema
class StockNews(Base):
    __tablename__ = "stock_news"
    id = Column(Integer, primary_key=True)
    headline = Column(Text, nullable=False)
    snippet = Column(Text)
    ticker = Column(String(10), nullable=False)
    date = Column(DateTime, nullable=False)
    source = Column(String(255))
    keywords = Column(Text)  # Comma-separated keywords
    sentiment_score = Column(Float)

# Initialize the Database
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Insert Data
def insert_news(data):
    for article in data:
        news_item = StockNews(
            headline=article["headline"],
            snippet=article["snippet"],
            ticker=article["ticker"],
            date=article["date"],
            source=article["source"]
        )
        session.add(news_item)
    session.commit()

# Example Usage
processed_data = preprocess_news_data(news_data)
insert_news(processed_data)

