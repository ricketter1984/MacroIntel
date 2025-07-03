import os
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

from utils.api_clients import init_env
from news_scanner.news_insight_feed import scan_benzinga_news

init_env()
scan_benzinga_news(keyword_filter=["Trump", "Musk", "oil", "Nvidia", "attack", "Middle East"])

