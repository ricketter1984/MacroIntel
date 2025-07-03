import os
from utils.api_clients import init_env
from news_scanner.news_insight_feed import scan_benzinga_news
from news_scanner.alert_manager import classify_alerts

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path="config/.env")
init_env()

# Initialize OpenAI client with correct v1 syntax
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_article(title, url, content):
    try:
        prompt = (
            f"Summarize the following news article for a financial trader. "
            f"Highlight market impact, affected assets, and relevance:\n\n{content}"
        )
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[❌ Error summarizing article]\n{e}"

def run_summary():
    print("🔍 Scanning Benzinga headlines...\n")
    headlines = scan_benzinga_news()
    alerts = classify_alerts(headlines)

    # Combine Tier 1 and Tier 2 alerts for summarization
    target_articles = alerts["tier_1"] + alerts["tier_2"]

    print("\n🧠 Summarizing Tier 1 + Tier 2 headlines using GPT...\n")
    for i, article in enumerate(target_articles, 1):
        print(f"  {i}. {article['title']}")

    print("\n🧾 Final GPT-Generated Summary Report:\n")
    for article in target_articles:
        print(f"📌 {article['title']}")
        print(f"🔗 {article['url']}")
        summary = summarize_article(article['title'], article['url'], article['body'])
        print(f"🧠 {summary}\n" + "-"*60)

if __name__ == "__main__":
    run_summary()
