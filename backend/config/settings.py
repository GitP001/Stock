import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_secret')
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///stock_app.db')