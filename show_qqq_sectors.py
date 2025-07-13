#!/usr/bin/env python3
import sqlite3

print("🔍 QQQ Sector Breakdown from Database:")
conn = sqlite3.connect("data/macrointel_data.sqlite")
cursor = conn.cursor()

# Get sector breakdown for QQQ
cursor.execute("""
    SELECT sector, SUM(weight) as total_weight, COUNT(*) as holdings_count
    FROM etf_holdings 
    WHERE etf = 'QQQ'
    GROUP BY sector
    ORDER BY total_weight DESC
""")

print("\n📊 QQQ Sector Weights:")
total_weight = 0
for row in cursor.fetchall():
    sector, weight, count = row
    total_weight += weight
    print(f"   {sector}: {weight:.1f}% ({count} holdings)")

print(f"\nTotal tracked weight: {total_weight:.1f}%")

# Show top holdings by sector
print("\n🏆 Top Holdings by Sector:")

sectors = ["Technology", "Communication Services", "Consumer Discretionary", "Consumer Staples"]
for sector in sectors:
    cursor.execute("""
        SELECT symbol, weight 
        FROM etf_holdings 
        WHERE etf = 'QQQ' AND sector = ?
        ORDER BY weight DESC 
        LIMIT 3
    """, (sector,))
    
    holdings = cursor.fetchall()
    if holdings:
        print(f"\n{sector}:")
        for symbol, weight in holdings:
            print(f"   {symbol}: {weight}%")

conn.close() 