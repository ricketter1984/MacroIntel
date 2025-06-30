from datetime import datetime

# news_scanner/alert_manager.py

def classify_alerts(articles):
    tier_1 = []
    tier_2 = []
    tier_3 = []

    for article in articles:
        title = article.get("title", "").lower()
        body = article.get("body", "").lower()

        if any(term in body for term in [
            "inflation", "fed", "war", "oil crash", "blackrock",
            "nvidia", "ceasefire", "interest rate", "recession"
        ]):
            tier_1.append(article)
        elif any(term in body for term in [
            "crypto", "bitcoin", "elon musk", "tesla", "earnings",
            "apple", "defense", "china", "iran", "election"
        ]):
            tier_2.append(article)
        else:
            tier_3.append(article)

    return {
        "tier_1": tier_1,
        "tier_2": tier_2,
        "tier_3": tier_3
    }



def route_alerts(articles):
    tier_1, tier_2, tier_3 = [], [], []

    for article in articles:
        tier = classify_article(article)
        if tier == 1:
            tier_1.append(article)
        elif tier == 2:
            tier_2.append(article)
        else:
            tier_3.append(article)

    print("\n🔔 ALERTS CLASSIFIED:")
    if tier_1:
        print(f"\n🚨 Tier 1 Alerts ({len(tier_1)}):")
        for a in tier_1:
            print(f"• {a['title']} — {a['url']}")

    if tier_2:
        print(f"\n⚠️ Tier 2 Watchlist ({len(tier_2)}):")
        for a in tier_2:
            print(f"• {a['title']} — {a['url']}")

    print(f"\n🗃 Tier 3 Noise: {len(tier_3)} articles\n")

    return {"tier1": tier_1, "tier2": tier_2, "tier3": tier_3}
