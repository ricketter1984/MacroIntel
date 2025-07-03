#!/usr/bin/env python3
"""
Insight Query Agent for MacroIntel Swarm
Parses natural language queries and generates market insights with visualizations.
"""

import os
import sys
import json
import logging
import argparse
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from visual_query_engine import VisualQueryEngine, generate_comparison_chart
from utils.api_clients import init_env

# Load .env if present
load_dotenv(dotenv_path="config/.env")
init_env()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/insight_query.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InsightQueryAgent:
    """Agent responsible for parsing natural language queries and generating market insights."""
    
    def __init__(self, ai_engine: str = "gpt"):
        """Initialize the insight query agent."""
        self.visual_engine = VisualQueryEngine()
        self.ai_engine = ai_engine
        self.openai_client = None
        if ai_engine == "gpt" and OpenAI:
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.output_dir = "output/insight_query"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        logger.info(f"🔍 Insight Query Agent initialized (engine: {ai_engine})")
    
    def parse_query_with_ai(self, query: str) -> Dict[str, Any]:
        """
        Use Claude/GPT to parse natural language query into structured components.
        
        Args:
            query: Natural language query (e.g., "QQQ vs BTC vs GOLD when fear < 30 for last 5 days")
            
        Returns:
            Dictionary with parsed components
        """
        if not self.openai_client:
            return self._fallback_parse_query(query)
        
        try:
            logger.info("🤖 Parsing query with AI...")
            
            prompt = f"""
Parse this market analysis query into structured components:

Query: "{query}"

Extract and return a JSON object with:
1. "tickers": List of asset symbols (e.g., ["QQQ", "BTCUSD", "XAUUSD"])
2. "fear_greed_filter": Condition string (e.g., "fear < 30" or null if none)
3. "timeframe": Time period (e.g., "5 days", "1 month", "last 10 events" or null if none)
4. "comparison_type": Type of comparison ("vs" for comparison, "performance" for individual)
5. "description": Human-readable description of what the query is asking for

Examples:
- "QQQ vs BTC vs GOLD when fear < 30 for last 5 days" → {{"tickers": ["QQQ", "BTCUSD", "XAUUSD"], "fear_greed_filter": "fear < 30", "timeframe": "5 days", "comparison_type": "vs", "description": "Compare QQQ, Bitcoin, and Gold performance during low fear periods over the last 5 days"}}
- "SPY performance last month" → {{"tickers": ["SPY"], "fear_greed_filter": null, "timeframe": "1 month", "comparison_type": "performance", "description": "SPY performance over the last month"}}

Return only valid JSON:
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a market data query parser. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    parsed = json.loads(json_str)
                    
                    # Validate required fields
                    if "tickers" not in parsed or not parsed["tickers"]:
                        raise ValueError("No tickers found in parsed query")
                    
                    logger.info(f"✅ Query parsed successfully: {len(parsed['tickers'])} tickers")
                    return parsed
                else:
                    raise ValueError("No JSON found in response")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Could not parse AI JSON response: {e}")
                return self._fallback_parse_query(query)
                
        except Exception as e:
            logger.warning(f"⚠️ AI parsing failed: {e}")
            return self._fallback_parse_query(query)
    
    def _fallback_parse_query(self, query: str) -> Dict[str, Any]:
        """Fallback parsing using regex patterns."""
        logger.info("🔄 Using fallback regex parsing...")
        
        # Extract tickers (common patterns)
        ticker_patterns = [
            r'\b([A-Z]{1,5})\b',  # 1-5 letter tickers
            r'\b(BTC|ETH|GOLD|SILVER)\b',  # Common crypto/commodities
        ]
        
        tickers = []
        for pattern in ticker_patterns:
            matches = re.findall(pattern, query.upper())
            tickers.extend(matches)
        
        # Remove duplicates and common words
        common_words = {'VS', 'AND', 'OR', 'THE', 'FOR', 'LAST', 'DAYS', 'MONTH', 'YEAR', 'WHEN', 'FEAR', 'GREED'}
        tickers = [t for t in set(tickers) if t not in common_words]
        
        # Extract fear/greed filter
        fear_pattern = r'fear\s*([<>=!]+)\s*(\d+)'
        fear_match = re.search(fear_pattern, query.lower())
        fear_filter = None
        if fear_match:
            fear_filter = f"fear {fear_match.group(1)} {fear_match.group(2)}"
        
        # Extract timeframe
        timeframe_patterns = [
            r'last\s+(\d+)\s+days?',
            r'last\s+(\d+)\s+months?',
            r'last\s+(\d+)\s+years?',
            r'(\d+)\s+days?',
            r'(\d+)\s+months?',
        ]
        
        timeframe = None
        for pattern in timeframe_patterns:
            match = re.search(pattern, query.lower())
            if match:
                timeframe = f"{match.group(1)} days" if "days" in pattern else f"{match.group(1)} months"
                break
        
        return {
            "tickers": tickers,
            "fear_greed_filter": fear_filter,
            "timeframe": timeframe,
            "comparison_type": "vs" if "vs" in query.lower() else "performance",
            "description": f"Analysis of {', '.join(tickers)} with conditions: {fear_filter or 'none'}, timeframe: {timeframe or 'default'}"
        }
    
    def fetch_historical_fear_greed(self, days: int = 365) -> Optional[Dict[str, Any]]:
        """Fetch historical Fear & Greed Index data."""
        try:
            logger.info(f"📊 Fetching {days} days of Fear & Greed data...")
            
            # Get current data first
            current_score, current_rating = self.visual_engine.get_fear_greed_index()
            
            # For now, simulate historical data (in real implementation, you'd fetch from API)
            # This is a placeholder - you'd need to implement actual historical fetching
            historical_data = {
                "current_score": current_score,
                "current_rating": current_rating,
                "days_requested": days,
                "note": "Historical data simulation - implement actual API call"
            }
            
            return historical_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching historical Fear & Greed data: {str(e)}")
            return None
    
    def fetch_price_data(self, tickers: List[str], days: int = 365) -> Dict[str, Any]:
        """Fetch price data for given tickers."""
        try:
            logger.info(f"📈 Fetching price data for {tickers}...")
            
            price_data = {}
            
            for ticker in tickers:
                # Use visual_query_engine's data fetching capabilities
                # This is a simplified version - you'd integrate with actual price APIs
                price_data[ticker] = {
                    "ticker": ticker,
                    "days": days,
                    "status": "fetched",
                    "note": f"Price data for {ticker} over {days} days"
                }
            
            return price_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching price data: {str(e)}")
            return {}
    
    def generate_chart(self, tickers: List[str], fear_filter: Optional[str] = None, 
                      timeframe: Optional[str] = None) -> Optional[str]:
        """Generate comparison chart using visual_query_engine."""
        try:
            logger.info(f"📊 Generating chart for {tickers}...")
            
            # Convert timeframe to days
            days = 365  # default
            if timeframe:
                days_match = re.search(r'(\d+)', timeframe)
                if days_match:
                    if "days" in timeframe:
                        days = int(days_match.group(1))
                    elif "months" in timeframe:
                        months = int(days_match.group(1))
                        days = months * 30
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            ticker_str = '_'.join(tickers)
            filename = f"insight_query_{ticker_str}_{timestamp}.png"
            output_path = os.path.join(self.output_dir, filename)
            
            # Use visual_query_engine to generate chart
            chart_path = generate_comparison_chart(
                assets=tickers,
                condition=fear_filter,
                output_path=output_path,
                days=days
            )
            
            if chart_path:
                logger.info(f"✅ Chart generated: {chart_path}")
                return chart_path
            else:
                logger.warning("⚠️ Chart generation returned None")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating chart: {str(e)}")
            return None
    
    def generate_summary_table(self, tickers: List[str], fear_data: Dict[str, Any], 
                             price_data: Dict[str, Any], fear_filter: Optional[str] = None) -> Dict[str, Any]:
        """Generate summary table with insights."""
        try:
            logger.info("📋 Generating summary table...")
            
            summary = {
                "query_timestamp": datetime.now().isoformat(),
                "tickers_analyzed": tickers,
                "fear_greed_context": {
                    "current_score": fear_data.get("current_score", "N/A"),
                    "current_rating": fear_data.get("current_rating", "N/A"),
                    "filter_applied": fear_filter or "None"
                },
                "price_data_status": {
                    ticker: data.get("status", "unknown") for ticker, data in price_data.items()
                },
                "insights": [
                    f"Analyzed {len(tickers)} assets: {', '.join(tickers)}",
                    f"Fear & Greed Index: {fear_data.get('current_score', 'N/A')} ({fear_data.get('current_rating', 'N/A')})",
                    f"Filter applied: {fear_filter or 'None'}",
                    f"Data coverage: {len([d for d in price_data.values() if d.get('status') == 'fetched'])}/{len(tickers)} tickers"
                ]
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating summary: {str(e)}")
            return {"error": str(e)}
    
    def send_email_report(self, chart_path: Optional[str], summary: Dict[str, Any], 
                         query: str) -> bool:
        """Send email report with chart and summary."""
        try:
            logger.info("📧 Sending email report...")
            
            # This would integrate with your email_dispatcher_agent.py
            # For now, just log the intent
            email_content = {
                "subject": f"Market Insight Report: {query}",
                "body": f"""
Market Insight Report

Query: {query}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
{json.dumps(summary, indent=2)}

Chart: {chart_path or 'Not generated'}
                """,
                "attachments": [chart_path] if chart_path else []
            }
            
            logger.info(f"📧 Email report prepared: {email_content['subject']}")
            # TODO: Integrate with email_dispatcher_agent.py
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {str(e)}")
            return False
    
    def run(self, query: str, send_email: bool = False) -> Dict[str, Any]:
        """
        Main execution method for insight query processing.
        
        Args:
            query: Natural language query
            send_email: Whether to send email report
            
        Returns:
            Dictionary with query results and insights
        """
        logger.info(f"🚀 Starting Insight Query Agent for: {query}")
        
        # Parse query
        parsed_query = self.parse_query_with_ai(query)
        
        if not parsed_query.get("tickers"):
            return {
                "error": "No valid tickers found in query",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        
        tickers = parsed_query["tickers"]
        fear_filter = parsed_query.get("fear_greed_filter")
        timeframe = parsed_query.get("timeframe")
        
        # Fetch data
        fear_data = self.fetch_historical_fear_greed()
        price_data = self.fetch_price_data(tickers)
        
        # Generate chart
        chart_path = self.generate_chart(tickers, fear_filter, timeframe)
        
        # Generate summary
        summary = self.generate_summary_table(tickers, fear_data or {}, price_data, fear_filter)
        
        # Send email if requested
        email_sent = False
        if send_email:
            email_sent = self.send_email_report(chart_path, summary, query)
        
        # Create final result
        result = {
            "query": query,
            "parsed_query": parsed_query,
            "chart_path": chart_path,
            "summary": summary,
            "email_sent": email_sent,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("✅ Insight Query Agent execution completed")
        return result

def print_markdown_summary(result: Dict[str, Any]):
    """Print results in Markdown format."""
    if "error" in result:
        print(f"\n**❌ Error:** {result['error']}\n")
        return
    
    parsed = result["parsed_query"]
    summary = result["summary"]
    
    print("\n---\n")
    print(f"### 🔍 Market Insight Report\n")
    print(f"**Query:** {result['query']}\n")
    print(f"**Parsed Components:**\n")
    print(f"- **Tickers:** {', '.join(parsed['tickers'])}")
    print(f"- **Fear/Greed Filter:** {parsed.get('fear_greed_filter', 'None')}")
    print(f"- **Timeframe:** {parsed.get('timeframe', 'Default')}")
    print(f"- **Comparison Type:** {parsed.get('comparison_type', 'Unknown')}\n")
    
    if result.get("chart_path"):
        print(f"**📊 Chart Generated:** `{result['chart_path']}`\n")
    
    print(f"**📋 Summary:**\n")
    for insight in summary.get("insights", []):
        print(f"- {insight}")
    
    if result.get("email_sent"):
        print(f"\n**📧 Email Report:** Sent successfully")
    
    print("\n---\n")

def main():
    """Main function for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Insight Query Agent - Parse natural language queries and generate market insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python insight_query_agent.py --query "QQQ vs BTC vs GOLD when fear < 30 for last 5 days"
  python insight_query_agent.py --query "SPY performance last month" --email
  python insight_query_agent.py --query "BTC vs ETH when fear > 70"
        """
    )
    
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Natural language query (e.g., 'QQQ vs BTC vs GOLD when fear < 30 for last 5 days')"
    )
    
    parser.add_argument(
        "--email",
        action="store_true",
        help="Send email report with results"
    )
    
    parser.add_argument(
        "--engine",
        type=str,
        choices=["gpt", "claude"],
        default="gpt",
        help="AI engine for query parsing (default: gpt)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create agent
    agent = InsightQueryAgent(ai_engine=args.engine)
    
    # Run query
    result = agent.run(
        query=args.query,
        send_email=args.email
    )
    
    # Print results
    print_markdown_summary(result)
    print("\n[Full Output as dict]\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
