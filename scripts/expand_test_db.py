#!/usr/bin/env python3
"""
Expand Test Database with Comprehensive ETF Holdings Data

This script adds extensive ETF holdings data for testing VannaAgent functionality.
"""

import sqlite3
import os

def expand_test_database():
    """Expand the test database with more comprehensive ETF data."""
    
    # Connect to the database
    db_path = "data/macrointel_data.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 Expanding test database with comprehensive ETF data...")
    
    # Clear existing data to avoid duplicates
    cursor.execute("DELETE FROM etf_holdings")
    
    # Comprehensive ETF holdings data
    etf_holdings_data = [
        # QQQ (NASDAQ-100) Holdings - Technology heavy
        ("AAPL", "QQQ", "Technology", 12.4),
        ("MSFT", "QQQ", "Technology", 10.2),
        ("GOOGL", "QQQ", "Communication Services", 3.8),
        ("GOOG", "QQQ", "Communication Services", 3.7),
        ("AMZN", "QQQ", "Consumer Discretionary", 5.2),
        ("NVDA", "QQQ", "Technology", 8.1),
        ("TSLA", "QQQ", "Consumer Discretionary", 4.3),
        ("META", "QQQ", "Communication Services", 4.9),
        ("AVGO", "QQQ", "Technology", 3.2),
        ("COST", "QQQ", "Consumer Staples", 2.1),
        
        # SPY (S&P 500) Holdings - Broad market
        ("AAPL", "SPY", "Technology", 7.1),
        ("MSFT", "SPY", "Technology", 6.8),
        ("GOOGL", "SPY", "Communication Services", 2.0),
        ("GOOG", "SPY", "Communication Services", 1.9),
        ("AMZN", "SPY", "Consumer Discretionary", 3.1),
        ("NVDA", "SPY", "Technology", 4.2),
        ("BRK.B", "SPY", "Financial", 1.8),
        ("META", "SPY", "Communication Services", 2.3),
        ("TSLA", "SPY", "Consumer Discretionary", 2.1),
        ("UNH", "SPY", "Healthcare", 1.2),
        
        # XLK (Technology Sector ETF) Holdings
        ("AAPL", "XLK", "Technology", 22.8),
        ("MSFT", "XLK", "Technology", 21.2),
        ("NVDA", "XLK", "Technology", 6.1),
        ("AVGO", "XLK", "Technology", 4.8),
        ("CRM", "XLK", "Technology", 3.2),
        ("ORCL", "XLK", "Technology", 3.1),
        ("ACN", "XLK", "Technology", 2.9),
        ("AMD", "XLK", "Technology", 2.8),
        ("ADBE", "XLK", "Technology", 2.6),
        ("NOW", "XLK", "Technology", 2.4),
        
        # XLF (Financial Sector ETF) Holdings
        ("JPM", "XLF", "Financial", 10.2),
        ("BAC", "XLF", "Financial", 7.8),
        ("WFC", "XLF", "Financial", 6.9),
        ("GS", "XLF", "Financial", 4.2),
        ("MS", "XLF", "Financial", 3.8),
        ("AXP", "XLF", "Financial", 3.6),
        ("C", "XLF", "Financial", 3.4),
        ("BLK", "XLF", "Financial", 3.2),
        ("SCHW", "XLF", "Financial", 3.1),
        ("USB", "XLF", "Financial", 2.9),
        
        # XLE (Energy Sector ETF) Holdings
        ("XOM", "XLE", "Energy", 23.1),
        ("CVX", "XLE", "Energy", 15.2),
        ("COP", "XLE", "Energy", 7.8),
        ("EOG", "XLE", "Energy", 5.1),
        ("SLB", "XLE", "Energy", 4.9),
        ("PSX", "XLE", "Energy", 4.2),
        ("VLO", "XLE", "Energy", 4.1),
        ("MPC", "XLE", "Energy", 3.8),
        ("PXD", "XLE", "Energy", 3.6),
        ("OXY", "XLE", "Energy", 3.4),
        
        # XLV (Healthcare Sector ETF) Holdings
        ("UNH", "XLV", "Healthcare", 9.8),
        ("JNJ", "XLV", "Healthcare", 8.2),
        ("PFE", "XLV", "Healthcare", 7.1),
        ("LLY", "XLV", "Healthcare", 6.9),
        ("ABBV", "XLV", "Healthcare", 5.8),
        ("TMO", "XLV", "Healthcare", 4.2),
        ("MRK", "XLV", "Healthcare", 4.1),
        ("ABT", "XLV", "Healthcare", 3.9),
        ("DHR", "XLV", "Healthcare", 3.6),
        ("BMY", "XLV", "Healthcare", 3.4),
        
        # IWM (Russell 2000 Small Cap) Holdings
        ("SMCI", "IWM", "Technology", 0.8),
        ("KVUE", "IWM", "Healthcare", 0.7),
        ("TPG", "IWM", "Financial", 0.6),
        ("SOLV", "IWM", "Healthcare", 0.6),
        ("RYAN", "IWM", "Financial", 0.5),
        ("FTAI", "IWM", "Industrial", 0.5),
        ("ATGE", "IWM", "Financial", 0.5),
        ("DOCS", "IWM", "Healthcare", 0.4),
        ("ALKT", "IWM", "Healthcare", 0.4),
        ("KRYS", "IWM", "Healthcare", 0.4),
        
        # VTI (Total Stock Market) Holdings - Similar to SPY but broader
        ("AAPL", "VTI", "Technology", 6.2),
        ("MSFT", "VTI", "Technology", 5.9),
        ("GOOGL", "VTI", "Communication Services", 1.7),
        ("GOOG", "VTI", "Communication Services", 1.6),
        ("AMZN", "VTI", "Consumer Discretionary", 2.7),
        ("NVDA", "VTI", "Technology", 3.6),
        ("BRK.B", "VTI", "Financial", 1.6),
        ("META", "VTI", "Communication Services", 2.0),
        ("TSLA", "VTI", "Consumer Discretionary", 1.8),
        ("UNH", "VTI", "Healthcare", 1.0)
    ]
    
    # Insert all the data
    cursor.executemany("INSERT INTO etf_holdings VALUES (?, ?, ?, ?)", etf_holdings_data)
    
    # Create additional useful tables for testing
    
    # ETF Information Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS etf_info (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        category TEXT,
        expense_ratio FLOAT,
        aum_billions FLOAT
    )
    """)
    
    etf_info_data = [
        ("SPY", "SPDR S&P 500 ETF Trust", "Large Cap Blend", 0.0945, 450.2),
        ("QQQ", "Invesco QQQ Trust", "Large Cap Growth", 0.20, 180.5),
        ("IWM", "iShares Russell 2000 ETF", "Small Cap Blend", 0.19, 65.8),
        ("XLK", "Technology Select Sector SPDR Fund", "Technology", 0.10, 55.2),
        ("XLF", "Financial Select Sector SPDR Fund", "Financial", 0.10, 42.1),
        ("XLE", "Energy Select Sector SPDR Fund", "Energy", 0.10, 28.9),
        ("XLV", "Health Care Select Sector SPDR Fund", "Healthcare", 0.10, 38.7),
        ("VTI", "Vanguard Total Stock Market ETF", "Total Market", 0.03, 320.1)
    ]
    
    cursor.executemany("INSERT OR REPLACE INTO etf_info VALUES (?, ?, ?, ?, ?)", etf_info_data)
    
    # Sector Performance Table (sample data)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sector_performance (
        sector TEXT,
        date TEXT,
        return_1d FLOAT,
        return_1w FLOAT,
        return_1m FLOAT,
        return_ytd FLOAT
    )
    """)
    
    sector_performance_data = [
        ("Technology", "2025-07-13", 1.2, 3.4, 8.9, 15.6),
        ("Financial", "2025-07-13", 0.8, 2.1, 5.2, 12.3),
        ("Healthcare", "2025-07-13", 0.5, 1.8, 4.1, 9.7),
        ("Energy", "2025-07-13", -0.3, -1.2, 2.8, 18.4),
        ("Consumer Discretionary", "2025-07-13", 0.9, 2.8, 6.7, 11.2),
        ("Communication Services", "2025-07-13", 1.1, 4.2, 7.8, 14.1),
        ("Industrial", "2025-07-13", 0.6, 1.9, 4.8, 10.3),
        ("Consumer Staples", "2025-07-13", 0.2, 0.8, 2.1, 6.8),
        ("Utilities", "2025-07-13", 0.1, 0.5, 1.9, 8.2),
        ("Materials", "2025-07-13", 0.4, 1.3, 3.6, 9.1)
    ]
    
    cursor.executemany("INSERT OR REPLACE INTO sector_performance VALUES (?, ?, ?, ?, ?, ?)", sector_performance_data)
    
    # Volatility data table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS volatility_data (
        symbol TEXT,
        date TEXT,
        implied_volatility FLOAT,
        historical_volatility FLOAT
    )
    """)
    
    volatility_data = [
        ("VIX", "2025-07-13", 18.5, 16.2),
        ("SPY", "2025-07-13", 15.2, 14.8),
        ("QQQ", "2025-07-13", 22.1, 20.5),
        ("IWM", "2025-07-13", 25.8, 24.2),
        ("XLK", "2025-07-13", 19.3, 18.1),
        ("XLF", "2025-07-13", 28.6, 26.4),
        ("XLE", "2025-07-13", 35.2, 33.8)
    ]
    
    cursor.executemany("INSERT OR REPLACE INTO volatility_data VALUES (?, ?, ?, ?)", volatility_data)
    
    # Commit changes
    conn.commit()
    
    # Print summary
    cursor.execute("SELECT COUNT(*) FROM etf_holdings")
    holdings_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM etf_info")
    etf_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sector_performance")
    sector_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM volatility_data")
    volatility_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Test database expanded successfully!")
    print(f"📊 ETF Holdings: {holdings_count} records")
    print(f"📋 ETF Info: {etf_count} ETFs")
    print(f"🎯 Sector Performance: {sector_count} records")
    print(f"📈 Volatility Data: {volatility_count} records")
    print(f"💾 Database file: {db_path}")

def test_database_queries():
    """Test some sample queries on the expanded database."""
    print("\n🧪 Testing sample database queries...")
    
    conn = sqlite3.connect("data/macrointel_data.sqlite")
    cursor = conn.cursor()
    
    # Test 1: ETF holdings by sector
    print("\n1. Technology holdings in QQQ:")
    cursor.execute("""
        SELECT symbol, weight 
        FROM etf_holdings 
        WHERE etf = 'QQQ' AND sector = 'Technology' 
        ORDER BY weight DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}%")
    
    # Test 2: Sector performance
    print("\n2. Best performing sectors (YTD):")
    cursor.execute("""
        SELECT sector, return_ytd 
        FROM sector_performance 
        ORDER BY return_ytd DESC 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}%")
    
    # Test 3: Volatility comparison
    print("\n3. ETF volatility levels:")
    cursor.execute("""
        SELECT symbol, implied_volatility 
        FROM volatility_data 
        WHERE symbol != 'VIX'
        ORDER BY implied_volatility DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}%")
    
    conn.close()

if __name__ == "__main__":
    expand_test_database()
    test_database_queries() 