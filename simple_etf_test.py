#!/usr/bin/env python3
import sqlite3

print("🧪 Testing ETF Database...")

# Test database connection and queries
conn = sqlite3.connect("data/macrointel_data.sqlite")
cursor = conn.cursor()

# Test 1: Count total holdings
cursor.execute("SELECT COUNT(*) FROM etf_holdings")
total_holdings = cursor.fetchone()[0]
print(f"📊 Total ETF Holdings: {total_holdings}")

# Test 2: Top QQQ holdings
print("\n🏆 Top QQQ Holdings:")
cursor.execute("""
    SELECT symbol, weight 
    FROM etf_holdings 
    WHERE etf = 'QQQ' 
    ORDER BY weight DESC 
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}%")

# Test 3: ETF info
print("\n📋 Available ETFs:")
cursor.execute("SELECT symbol, name FROM etf_info ORDER BY symbol")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}")

# Test 4: Sector performance
print("\n📈 Sector Performance (YTD):")
cursor.execute("""
    SELECT sector, return_ytd 
    FROM sector_performance 
    ORDER BY return_ytd DESC 
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}%")

conn.close()
print("\n✅ Database tests completed successfully!")

# Test ETF query routing
print("\n🔍 Testing ETF Query Routing:")
test_queries = [
    "What are the best technology ETFs?",
    "Show me sector performance",
    "What is the implied volatility of major ETFs?",
    "Which ETF has the lowest expense ratio?"
]

for query in test_queries:
    etf_keywords = ["etf", "sector", "implied volatility"]
    is_etf_query = any(keyword in query.lower() for keyword in etf_keywords)
    print(f"📝 '{query}' → {'✅ ETF Query' if is_etf_query else '❌ Regular Query'}")

print("\n🎉 All tests completed!") 