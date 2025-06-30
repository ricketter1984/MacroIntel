from utils.api_clients import init_env, fetch_all_news
from news_scanner.alert_manager import classify_alerts
from news_scanner.macro_insight_builder import summarize_all

init_env()

# 🧠 Fetch and combine all news sources
articles = fetch_all_news()

# 🔎 Classify into alert tiers
tiers = classify_alerts(articles)

# 🧠 Focus on Tier 1 and 2 only
tier1_2 = tiers["tier_1"] + tiers["tier_2"]

# 🤖 Generate GPT summaries
summaries = summarize_all(tier1_2)

# 📋 Output results
for s in summaries:
    print(f"\n📌 {s['title']}\n🔗 {s['url']}\n🧠 {s['summary']}\n" + "-"*60)
