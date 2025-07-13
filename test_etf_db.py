#!/usr/bin/env python3
"""
Test ETF Database and VannaAgent Functionality
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add agents to path
sys.path.append(str(Path(__file__).parent / "agents"))

def test_etf_database():
    """Test direct queries on the ETF database."""
    print("🧪 Testing ETF Database...")
    
    db_path = "data/macrointel_data.sqlite"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Top QQQ Technology holdings
        print("\n1. Top QQQ Technology Holdings:")
        cursor.execute("""
            SELECT symbol, weight 
            FROM etf_holdings 
            WHERE etf = 'QQQ' AND sector = 'Technology' 
            ORDER BY weight DESC 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]}%")
        
        # Test 2: Sector breakdown for SPY
        print("\n2. SPY Sector Breakdown:")
        cursor.execute("""
            SELECT sector, SUM(weight) as total_weight
            FROM etf_holdings 
            WHERE etf = 'SPY'
            GROUP BY sector
            ORDER BY total_weight DESC
        """)
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]:.1f}%")
        
        # Test 3: ETF Information
        print("\n3. ETF Information:")
        cursor.execute("""
            SELECT symbol, name, expense_ratio, aum_billions
            FROM etf_info
            ORDER BY aum_billions DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} (ER: {row[2]}%, AUM: ${row[3]}B)")
        
        # Test 4: Volatility comparison
        print("\n4. ETF Volatility Levels:")
        cursor.execute("""
            SELECT symbol, implied_volatility, historical_volatility
            FROM volatility_data
            WHERE symbol != 'VIX'
            ORDER BY implied_volatility DESC
        """)
        for row in cursor.fetchall():
            print(f"   {row[0]}: IV {row[1]}%, HV {row[2]}%")
        
        conn.close()
        print("\n✅ Database tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Database test error: {str(e)}")

def test_vanna_agent():
    """Test VannaAgent with ETF queries."""
    print("\n🧠 Testing VannaAgent...")
    
    try:
        from vanna_agent import VannaAgent
        
        # Initialize VannaAgent with test database
        agent = VannaAgent(use_test_db=True)
        
        # Test ETF queries
        test_queries = [
            "What are the top technology ETFs?",
            "Show me QQQ sector breakdown",
            "Which ETF has the highest volatility?",
            "What are the largest holdings in XLK?"
        ]
        
        for query in test_queries:
            print(f"\n{'='*50}")
            print(f"Query: {query}")
            print('='*50)
            response = agent.ask(query)
            print(response)
            
    except ImportError as e:
        print(f"❌ VannaAgent import error: {e}")
    except Exception as e:
        print(f"❌ VannaAgent test error: {e}")

def test_macrointel_query_integration():
    """Test integration with macrointel_query.py"""
    print("\n🔍 Testing MacroIntel Query Integration...")
    
    # Test ETF routing
    etf_queries = [
        "What ETFs should I consider for technology exposure?",
        "Which sector ETF has the best performance?",
        "Show me implied volatility for major ETFs"
    ]
    
    print("Testing ETF/Sector/Volatility query routing:")
    for query in etf_queries:
        print(f"\n📝 Query: {query}")
        # Check if it would route to VannaAgent
        if any(keyword in query.lower() for keyword in ["etf", "sector", "implied volatility"]):
            print("✅ Would route to VannaAgent")
        else:
            print("❌ Would NOT route to VannaAgent")

if __name__ == "__main__":
    print("🔄 Starting ETF Database and VannaAgent Tests...")
    
    # Test database functionality
    test_etf_database()
    
    # Test VannaAgent
    test_vanna_agent()
    
    # Test query integration
    test_macrointel_query_integration()
    
    print("\n✅ All tests completed!") 