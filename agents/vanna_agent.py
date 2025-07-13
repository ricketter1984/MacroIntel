#!/usr/bin/env python3
"""
Vanna Agent for MacroIntel

Specialized agent for ETF, sector, and implied volatility queries.
Uses Vanna AI for natural language to SQL conversion with financial market focus.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, Union
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    import vanna as vn
    from vanna.local import LocalContext_OpenAI
    VANNA_AVAILABLE = True
except ImportError:
    VANNA_AVAILABLE = False

try:
    from agents.sqlite_agent import MacroIntelSQLiteAgent
except ImportError:
    MacroIntelSQLiteAgent = None

logger = logging.getLogger(__name__)

class VannaAgent:
    """
    Specialized Vanna agent for ETF, sector, and implied volatility queries.
    
    Features:
    - Natural language understanding for financial terms
    - ETF and sector analysis
    - Implied volatility calculations
    - Integration with MacroIntel database
    """
    
    def __init__(self, openai_api_key: str = None, use_test_db: bool = True):
        """
        Initialize the Vanna Agent.
        
        Args:
            openai_api_key: OpenAI API key for Vanna (optional, will try environment)
            use_test_db: Whether to use the test database with ETF data
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.vanna_available = VANNA_AVAILABLE and self.openai_api_key
        self.use_test_db = use_test_db
        
        # Initialize database connection - use test DB for ETF queries if available
        if use_test_db and os.path.exists("data/macrointel_data.sqlite"):
            self.db_path = "data/macrointel_data.sqlite"
            self.db_agent = None  # We'll handle queries directly for test DB
        elif MacroIntelSQLiteAgent:
            self.db_agent = MacroIntelSQLiteAgent()
            self.db_path = None
        else:
            self.db_agent = None
            self.db_path = None
            
        # Initialize Vanna if available
        if self.vanna_available:
            self._init_vanna()
        else:
            logger.warning("⚠️ Vanna not available - using fallback responses")
            self.vn = None
        
        logger.info("🧠 VannaAgent initialized for ETF/sector/implied volatility queries")
    
    def _init_vanna(self):
        """Initialize Vanna with financial market schema."""
        try:
            self.vn = LocalContext_OpenAI(api_key=self.openai_api_key)
            
            # Train with financial market schema
            financial_schema = """
            Financial Market Database Schema:
            
            ETF and Sector Information:
            - Common ETF symbols: SPY (S&P 500), QQQ (NASDAQ), IWM (Russell 2000), DIA (Dow Jones)
            - Sector ETFs: XLK (Technology), XLF (Financial), XLE (Energy), XLV (Healthcare), XLI (Industrial)
            - International: EFA (Developed Markets), EEM (Emerging Markets), VTI (Total Stock Market)
            
            Volatility Information:
            - VIX: CBOE Volatility Index (market fear gauge)
            - Implied volatility: Option-derived volatility expectations
            - Historical volatility: Realized price movements
            
            Market Data Structure:
            - symbol: Trading symbol (e.g., 'SPY', 'QQQ', 'VIX')
            - date: Trading date
            - open_price, high_price, low_price, close_price: OHLC prices
            - volume: Trading volume
            - adjusted_close: Adjusted closing price
            
            Sample Queries:
            - "What is the performance of technology sector ETFs?"
            - "Show me VIX levels over the past month"
            - "Compare SPY and QQQ volatility"
            - "Which sector ETFs have the highest volume?"
            """
            
            # Training examples
            training_examples = [
                {
                    "question": "What is the latest VIX level?",
                    "sql": "SELECT close_price, date FROM market_data WHERE symbol LIKE '%VIX%' ORDER BY date DESC LIMIT 1"
                },
                {
                    "question": "Show me SPY performance this month",
                    "sql": "SELECT date, close_price, volume FROM market_data WHERE symbol = 'SPY' AND date >= date('now', '-30 days') ORDER BY date DESC"
                },
                {
                    "question": "Compare SPY and QQQ prices",
                    "sql": "SELECT symbol, AVG(close_price) as avg_price, MAX(close_price) as max_price, MIN(close_price) as min_price FROM market_data WHERE symbol IN ('SPY', 'QQQ') GROUP BY symbol"
                },
                {
                    "question": "What ETFs have the highest trading volume?",
                    "sql": "SELECT symbol, SUM(volume) as total_volume FROM market_data WHERE symbol IN ('SPY', 'QQQ', 'IWM', 'DIA', 'XLK', 'XLF', 'XLE', 'XLV', 'XLI') GROUP BY symbol ORDER BY total_volume DESC"
                },
                {
                    "question": "Show me implied volatility trends",
                    "sql": "SELECT date, close_price FROM market_data WHERE symbol LIKE '%VIX%' AND date >= date('now', '-30 days') ORDER BY date DESC"
                }
            ]
            
            # Train Vanna
            self.vn.train(documentation=financial_schema)
            
            for example in training_examples:
                self.vn.train(question=example["question"], sql=example["sql"])
            
            logger.info("✅ Vanna training completed for financial markets")
            
        except Exception as e:
            logger.error(f"❌ Error initializing Vanna: {str(e)}")
            self.vn = None
    
    def _execute_test_db_query(self, sql_query: str) -> Optional[Dict[str, Any]]:
        """Execute a query on the test database."""
        if not self.db_path or not os.path.exists(self.db_path):
            return None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql_query)
                rows = cursor.fetchall()
                
                if rows:
                    # Convert to list of dictionaries
                    data = [dict(row) for row in rows]
                    return {
                        "success": True,
                        "data": data,
                        "row_count": len(data)
                    }
                else:
                    return {
                        "success": True,
                        "data": [],
                        "row_count": 0
                    }
        except Exception as e:
            logger.error(f"❌ Test DB query error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def ask(self, question: str) -> str:
        """
        Process a natural language question about ETFs, sectors, or implied volatility.
        
        Args:
            question: Natural language question
            
        Returns:
            Response string
        """
        logger.info(f"🧠 Processing Vanna query: {question}")
        
        try:
            # If Vanna is available, use it for natural language processing
            if self.vn and self.db_agent:
                # Generate SQL from natural language
                sql_query = self.vn.generate_sql(question)
                
                if sql_query:
                    # Execute the query
                    result = self.db_agent.execute_sql_query(sql_query)
                    
                    if result.success and result.data is not None and not result.data.empty:
                        # Format the response
                        response = f"🧠 VannaAgent Analysis:\n"
                        response += f"Generated SQL: {sql_query}\n\n"
                        response += f"📊 Results ({len(result.data)} rows):\n"
                        
                        # Display data in a readable format
                        for i, row in result.data.iterrows():
                            if i < 10:  # Limit to 10 rows
                                row_str = ", ".join([f"{col}: {val}" for col, val in row.items()])
                                response += f"  {i+1}. {row_str}\n"
                        
                        if len(result.data) > 10:
                            response += f"  ... and {len(result.data) - 10} more rows\n"
                        
                        return response
                    else:
                        return f"🧠 VannaAgent: Query executed but no data found.\nGenerated SQL: {sql_query}"
                else:
                    return "🧠 VannaAgent: Could not generate SQL from your question. Please try rephrasing."
            
            # Fallback responses when Vanna is not available
            return self._generate_fallback_response(question)
            
        except Exception as e:
            logger.error(f"❌ Error in VannaAgent: {str(e)}")
            return f"🧠 VannaAgent Error: {str(e)}\n\nFalling back to general information."
    
    def _generate_fallback_response(self, question: str) -> str:
        """Generate fallback responses when Vanna is not available."""
        question_lower = question.lower()
        
        # Check if we can provide specific database-driven responses
        if self.db_path and os.path.exists(self.db_path):
            return self._generate_database_fallback_response(question_lower)
        
        # ETF-related fallback
        if "etf" in question_lower:
            if any(term in question_lower for term in ["sector", "technology", "tech"]):
                return """🧠 VannaAgent (Fallback Mode):

📊 Technology Sector ETFs:
• XLK - Technology Select Sector SPDR Fund
• QQQ - Invesco QQQ Trust (NASDAQ-100)
• VGT - Vanguard Information Technology ETF
• FTEC - Fidelity MSCI Information Technology ETF

💡 These ETFs provide exposure to major technology companies and track different tech-focused indices.

Note: For real-time data and analysis, please configure OpenAI API key for full VannaAgent functionality."""
            
            elif any(term in question_lower for term in ["financial", "finance", "bank"]):
                return """🧠 VannaAgent (Fallback Mode):

📊 Financial Sector ETFs:
• XLF - Financial Select Sector SPDR Fund
• VFH - Vanguard Financials ETF
• KBE - SPDR S&P Bank ETF
• KRE - SPDR S&P Regional Banking ETF

💡 These ETFs provide exposure to banks, insurance companies, and other financial services.

Note: For real-time data and analysis, please configure OpenAI API key for full VannaAgent functionality."""
            
            else:
                return """🧠 VannaAgent (Fallback Mode):

📊 Popular ETFs by Category:
• SPY - SPDR S&P 500 ETF (Large Cap)
• QQQ - Invesco QQQ Trust (Technology/NASDAQ)
• IWM - iShares Russell 2000 ETF (Small Cap)
• DIA - SPDR Dow Jones Industrial Average ETF
• VTI - Vanguard Total Stock Market ETF

💡 ETFs provide diversified exposure to different market segments.

Note: For real-time data and analysis, please configure OpenAI API key for full VannaAgent functionality."""
        
        # Implied volatility fallback
        elif "implied volatility" in question_lower or "vix" in question_lower:
            return """🧠 VannaAgent (Fallback Mode):

📊 Implied Volatility Information:
• VIX - CBOE Volatility Index (S&P 500 implied volatility)
• VXN - CBOE NASDAQ-100 Volatility Index
• RVX - CBOE Russell 2000 Volatility Index

💡 Volatility Levels:
• VIX < 20: Low volatility (market complacency)
• VIX 20-30: Moderate volatility (normal market stress)
• VIX > 30: High volatility (market fear/uncertainty)

Note: For real-time VIX data and analysis, please configure OpenAI API key for full VannaAgent functionality."""
        
        # Sector fallback
        elif "sector" in question_lower:
            return """🧠 VannaAgent (Fallback Mode):

📊 Market Sectors and ETFs:
• Technology: XLK, QQQ, VGT
• Healthcare: XLV, VHT, IHI
• Financial: XLF, VFH, KBE
• Energy: XLE, VDE, IEO
• Consumer Discretionary: XLY, VCR
• Consumer Staples: XLP, VDC
• Industrial: XLI, VIS
• Materials: XLB, VAW
• Utilities: XLU, VPU
• Real Estate: XLRE, VNQ

💡 Each sector responds differently to economic cycles and market conditions.

Note: For real-time sector analysis, please configure OpenAI API key for full VannaAgent functionality."""
        
        else:
            return """🧠 VannaAgent (Fallback Mode):

I can help with questions about:
• ETF analysis and comparisons
• Sector performance and trends  
• Implied volatility and VIX analysis
• Market data queries

Examples:
• "What is the current VIX level?"
• "Compare technology ETF performance"
• "Show me financial sector trends"
• "Which ETFs have the highest volume?"

Note: For full natural language processing, please configure OpenAI API key."""

    def _generate_database_fallback_response(self, question_lower: str) -> str:
        """Generate responses using actual database data when available."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # QQQ sector analysis
                if "qqq" in question_lower and ("sector" in question_lower or "overweight" in question_lower):
                    cursor.execute("""
                        SELECT sector, SUM(weight) as total_weight, COUNT(*) as holdings_count
                        FROM etf_holdings 
                        WHERE etf = 'QQQ'
                        GROUP BY sector
                        ORDER BY total_weight DESC
                    """)
                    sectors = cursor.fetchall()
                    
                    if sectors:
                        response = "🧠 VannaAgent Analysis (Database):\n\n📊 QQQ Sector Breakdown:\n"
                        total_tracked = 0
                        for sector, weight, count in sectors:
                            total_tracked += weight
                            response += f"• {sector}: {weight:.1f}% ({count} holdings)\n"
                        
                        response += f"\nTotal tracked: {total_tracked:.1f}%\n"
                        
                        # Add top holdings for Technology sector (most overweighted)
                        if sectors and sectors[0][0] == "Technology":
                            cursor.execute("""
                                SELECT symbol, weight 
                                FROM etf_holdings 
                                WHERE etf = 'QQQ' AND sector = 'Technology'
                                ORDER BY weight DESC 
                                LIMIT 3
                            """)
                            tech_holdings = cursor.fetchall()
                            if tech_holdings:
                                response += f"\n🏆 Top Technology Holdings:\n"
                                for symbol, weight in tech_holdings:
                                    response += f"• {symbol}: {weight}%\n"
                        
                        response += "\n💡 QQQ is heavily overweighted in Technology compared to broad market indices."
                        return response
                
                # General ETF sector queries
                elif "etf" in question_lower and "sector" in question_lower:
                    cursor.execute("SELECT DISTINCT etf FROM etf_holdings ORDER BY etf")
                    etfs = [row[0] for row in cursor.fetchall()]
                    
                    response = "🧠 VannaAgent Analysis (Database):\n\n📊 Available ETF Sector Data:\n"
                    for etf in etfs:
                        cursor.execute("""
                            SELECT COUNT(DISTINCT sector) as sector_count, SUM(weight) as total_weight
                            FROM etf_holdings WHERE etf = ?
                        """, (etf,))
                        result = cursor.fetchone()
                        if result:
                            response += f"• {etf}: {result[0]} sectors, {result[1]:.1f}% tracked\n"
                    
                    response += "\n💡 Use specific ETF names (QQQ, SPY, XLK, etc.) for detailed breakdowns."
                    return response
                
                # Volatility queries
                elif "volatility" in question_lower or "vix" in question_lower:
                    cursor.execute("""
                        SELECT symbol, implied_volatility, historical_volatility
                        FROM volatility_data
                        ORDER BY implied_volatility DESC
                    """)
                    vol_data = cursor.fetchall()
                    
                    if vol_data:
                        response = "🧠 VannaAgent Analysis (Database):\n\n📊 Current Volatility Levels:\n"
                        for symbol, iv, hv in vol_data:
                            response += f"• {symbol}: IV {iv}%, HV {hv}%\n"
                        
                        response += "\n💡 Higher volatility indicates greater price uncertainty and risk."
                        return response
                
        except Exception as e:
            logger.error(f"❌ Database fallback error: {str(e)}")
        
        # Fall back to generic responses if database query fails
        return self._generate_generic_fallback_response(question_lower)
    
    def _generate_generic_fallback_response(self, question_lower: str) -> str:
        """Generate generic fallback responses when database is not available."""
        # This contains the original fallback logic
        if "sector" in question_lower:
            return """🧠 VannaAgent (Fallback Mode):

📊 Market Sectors and ETFs:
• Technology: XLK, QQQ, VGT
• Healthcare: XLV, VHT, IHI
• Financial: XLF, VFH, KBE
• Energy: XLE, VDE, IEO
• Consumer Discretionary: XLY, VCR
• Consumer Staples: XLP, VDC
• Industrial: XLI, VIS
• Materials: XLB, VAW
• Utilities: XLU, VPU
• Real Estate: XLRE, VNQ

💡 Each sector responds differently to economic cycles and market conditions.

Note: For real-time sector analysis, please configure OpenAI API key for full VannaAgent functionality."""
        
        else:
            return """🧠 VannaAgent (Fallback Mode):

I can help with questions about:
• ETF analysis and comparisons
• Sector performance and trends  
• Implied volatility and VIX analysis
• Market data queries

Examples:
• "What is the current VIX level?"
• "Compare technology ETF performance"
• "Show me financial sector trends"
• "Which ETFs have the highest volume?"

Note: For full natural language processing, please configure OpenAI API key."""

def main():
    """Test function for VannaAgent."""
    print("🧠 Testing VannaAgent...")
    
    agent = VannaAgent()
    
    # Test queries
    test_queries = [
        "What is the latest VIX level?",
        "Show me technology ETF information",
        "Compare SPY and QQQ performance",
        "What sector ETFs are available?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print('='*50)
        response = agent.ask(query)
        print(response)

if __name__ == "__main__":
    main() 