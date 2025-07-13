# scripts/create_test_db.py
import sqlite3

conn = sqlite3.connect("data/macrointel_data.sqlite")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS etf_holdings (
    symbol TEXT,
    etf TEXT,
    sector TEXT,
    weight FLOAT
)
""")

cursor.executemany("INSERT INTO etf_holdings VALUES (?, ?, ?, ?)", [
    ("AAPL", "QQQ", "Technology", 12.4),
    ("MSFT", "QQQ", "Technology", 10.2),
    ("TSLA", "QQQ", "Consumer Discretionary", 4.5),
    ("GOOG", "QQQ", "Communication Services", 6.0)
])

conn.commit()
conn.close()
print("✅ Test database created") 