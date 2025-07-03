import os
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

from utils.api_clients import init_env
from news_scanner.news_insight_feed import scan_benzinga_news
from news_scanner.alert_manager import route_alerts

init_env()
headlines = scan_benzinga_news()
route_alerts(headlines)
