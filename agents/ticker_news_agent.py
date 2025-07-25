#!/usr/bin/env python3
"""
Ticker News Agent for MacroIntel Swarm
Fetches and summarizes news for specific tickers using Perplexity API or Google News fallback.
"""

import os
import sys
import json
import logging
import requests
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_clients import strip_emojis
from core.ai_clients import MistralClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import QuiverAgent for congressional trading data
try:
    from agents.quiver_agent import QuiverAgent
    QUIVER_AVAILABLE = True
    logger.info("✅ QuiverAgent module imported successfully")
except ImportError as e:
    QUIVER_AVAILABLE = False
    logger.warning(f"⚠️ QuiverAgent module not available: {e}")

class TickerNewsAgent:
    """Agent responsible for fetching and summarizing news for specific tickers."""
    
    def __init__(self, include_quiver: bool = False):
        """Initialize the ticker news agent."""
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.include_quiver = include_quiver
        
        # Clean the model name - remove any comments or extra text
        raw_model = os.getenv("PERPLEXITY_MODEL", "sonar")
        self.perplexity_model = raw_model.split('#')[0].strip() if '#' in raw_model else raw_model.strip()
        
        self.perplexity_base_url = "https://api.perplexity.ai"
        self.perplexity_chat_endpoint = "https://api.perplexity.ai/chat/completions"
        
        # Initialize AI client as None (will be set when needed)
        self.ai_client: Any = None
        
        # Initialize AI client based on model selection
        self._initialize_ai_client()
        
        # Sector mapping for common tickers
        self.sector_mapping = {
            # ETFs
            "SPY": "Broad Market ETF",
            "QQQ": "Technology ETF", 
            "IWM": "Small Cap ETF",
            "XLE": "Energy ETF",
            "XLF": "Financial ETF",
            "XLV": "Healthcare ETF",
            "XLI": "Industrial ETF",
            "XLP": "Consumer Staples ETF",
            "XLY": "Consumer Discretionary ETF",
            "XLK": "Technology ETF",
            "XLB": "Materials ETF",
            "XLU": "Utilities ETF",
            "XLRE": "Real Estate ETF",
            
            # Commodities
            "GLD": "Gold ETF",
            "SLV": "Silver ETF",
            "USO": "Oil ETF",
            "UNG": "Natural Gas ETF",
            "DBA": "Agriculture ETF",
            
            # Futures/Commodities
            "MGC": "Micro Gold Futures",
            "GC": "Gold Futures",
            "CL": "Crude Oil Futures",
            "NG": "Natural Gas Futures",
            "ES": "E-mini S&P 500 Futures",
            "NQ": "E-mini NASDAQ Futures",
            "YM": "E-mini Dow Futures",
            "RTY": "E-mini Russell 2000 Futures",
            
            # Major Stocks
            "AAPL": "Technology",
            "MSFT": "Technology",
            "GOOGL": "Technology",
            "AMZN": "Consumer Discretionary",
            "TSLA": "Consumer Discretionary",
            "NVDA": "Technology",
            "META": "Technology",
            "NFLX": "Communication Services",
            "JPM": "Financial",
            "JNJ": "Healthcare",
            "PG": "Consumer Staples",
            "V": "Financial",
            "HD": "Consumer Discretionary",
            "MA": "Financial",
            "UNH": "Healthcare",
            "BAC": "Financial",
            "PFE": "Healthcare",
            "ABBV": "Healthcare",
            "KO": "Consumer Staples",
            "PEP": "Consumer Staples"
        }
        
        logger.info("📰 Ticker News Agent initialized")
        if self.perplexity_api_key:
            logger.info("✅ Perplexity API key found")
            logger.info(f"🤖 Using Perplexity model: {self.perplexity_model}")
        else:
            logger.warning("⚠️ Perplexity API key not found")
            
        logger.info("✅ OpenAI support disabled (API key removed from environment)")
            
        if self.include_quiver and QUIVER_AVAILABLE:
            logger.info("🏛️ Quiver congressional trading data enabled")
        elif self.include_quiver and not QUIVER_AVAILABLE:
            logger.warning("⚠️ Quiver requested but module not available")
        else:
            logger.info("🏛️ Quiver congressional trading data disabled")
    
    def _initialize_ai_client(self, model: str = "claude"):
        """Initialize AI client based on model selection."""
        try:
            if model == "mistral":
                self.ai_client = MistralClient()
                logger.info("🤖 Initialized MistralClient for analysis")
            elif model == "claude":
                # TODO: Add ClaudeClient when available
                logger.info("🤖 Claude model selected (not yet implemented)")
                self.ai_client = None
            elif model == "perplexity":
                # Use existing Perplexity API integration
                logger.info("🤖 Using existing Perplexity API integration")
                self.ai_client = None  # Perplexity is handled separately
            else:
                logger.warning(f"⚠️ Unknown model '{model}', defaulting to Claude")
                self.ai_client = None
        except Exception as e:
            logger.error(f"❌ Error initializing AI client for {model}: {str(e)}")
            self.ai_client = None
    
    def _make_perplexity_api_request(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Make a request to the Perplexity API for news search.
        
        Args:
            query: Search query string
            
        Returns:
            API response or None if failed
        """
        if not self.perplexity_api_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.perplexity_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a financial news assistant. Search for recent news about the given ticker and return ONLY a JSON array of 3 articles with title, url, and brief summary. Format: [{\"title\": \"...\", \"url\": \"...\", \"summary\": \"...\"}]"
                    },
                    {
                        "role": "user",
                        "content": f"Find the top 3 most recent and relevant news articles about {query} stock/ticker. Focus on market-moving news, earnings, analyst ratings, and significant developments."
                    }
                ]
            }
            
            response = requests.post(
                self.perplexity_chat_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Perplexity API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Perplexity API request failed: {str(e)}")
            return None
    
    def _make_fallback_analysis(self, content: str, task: str) -> str:
        """
        Provide fallback analysis when OpenAI is not available.
        
        Args:
            content: Content to analyze
            task: Specific task (summarize, sector, impact)
            
        Returns:
            Fallback analysis result
        """
        logger.info(f"🔄 Using fallback analysis for {task} (OpenAI disabled)")
        
        if task == "summarize":
            # Simple fallback: extract first few sentences
            sentences = content.split('.')
            if len(sentences) > 2:
                return '. '.join(sentences[:2]) + '.'
            else:
                return content[:200] + "..." if len(content) > 200 else content
        elif task == "sector":
            # Simple keyword-based sector detection
            content_lower = content.lower()
            if any(word in content_lower for word in ['tech', 'software', 'ai', 'digital']):
                return "Technology"
            elif any(word in content_lower for word in ['health', 'medical', 'pharma', 'biotech']):
                return "Healthcare"
            elif any(word in content_lower for word in ['energy', 'oil', 'gas', 'renewable']):
                return "Energy"
            elif any(word in content_lower for word in ['bank', 'finance', 'financial', 'insurance']):
                return "Financial"
            else:
                return "Unknown"
        elif task == "impact":
            # Simple sentiment-based impact detection
            content_lower = content.lower()
            positive_words = ['bullish', 'positive', 'gain', 'rise', 'up', 'strong', 'growth']
            negative_words = ['bearish', 'negative', 'loss', 'fall', 'down', 'weak', 'decline']
            
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            if positive_count > negative_count:
                return "Bullish"
            elif negative_count > positive_count:
                return "Bearish"
            else:
                return "Neutral"
        else:
            return "Unknown"
    
    def _parse_perplexity_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Perplexity API response to extract articles.
        
        Args:
            response: Perplexity API response
            
        Returns:
            List of parsed articles
        """
        try:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Try to extract JSON from the response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                articles = json.loads(json_match.group())
                return articles
            
            # Fallback: try to parse the content manually
            articles = []
            lines = content.split('\n')
            current_article = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('"title"') or line.startswith('title'):
                    current_article['title'] = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('"url"') or line.startswith('url'):
                    current_article['url'] = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('"summary"') or line.startswith('summary'):
                    current_article['summary'] = line.split(':', 1)[1].strip().strip('"')
                    if len(current_article) == 3:
                        articles.append(current_article.copy())
                        current_article = {}
            
            return articles[:3]  # Limit to 3 articles
            
        except Exception as e:
            logger.error(f"❌ Failed to parse Perplexity response: {str(e)}")
            return []
    
    def _get_sector_for_ticker(self, ticker: str) -> str:
        """
        Get sector for a given ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Sector name or "Unknown"
        """
        return self.sector_mapping.get(ticker.upper(), "Unknown")
    
    def _fetch_congressional_trades(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Fetch recent congressional trading data for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of congressional trades within last 7 days
        """
        if not self.include_quiver or not QUIVER_AVAILABLE:
            return []
        
        try:
            quiver_agent = QuiverAgent()
            
            # Get recent trades for the ticker (last 7 days)
            activity = quiver_agent.get_ticker_activity(ticker)
            congress_trades = activity.get("congress_trading", [])
            
            # Filter for trades within last 7 days
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=7)
            
            recent_trades = []
            for trade in congress_trades:
                try:
                    # Parse disclosure date
                    disclosure_date = datetime.strptime(trade.get("disclosure_date", ""), "%Y-%m-%d")
                    if disclosure_date >= cutoff_date:
                        recent_trades.append(trade)
                except (ValueError, TypeError):
                    # Skip trades with invalid dates
                    continue
            
            logger.info(f"🏛️ Found {len(recent_trades)} recent congressional trades for {ticker}")
            return recent_trades
            
        except Exception as e:
            logger.error(f"❌ Error fetching congressional trades for {ticker}: {str(e)}")
            return []
    
    def _format_congressional_trade(self, trade: Dict[str, Any]) -> str:
        """
        Format a congressional trade into a readable string.
        
        Args:
            trade: Congressional trade data
            
        Returns:
            Formatted trade string
        """
        politician = trade.get("politician", "Unknown")
        chamber = trade.get("chamber", "")
        transaction_type = trade.get("transaction_type", "").lower()
        amount_range = trade.get("amount_range", "")
        
        # Format chamber prefix
        chamber_prefix = "Sen." if chamber == "Senate" else "Rep." if chamber == "House" else ""
        
        # Format amount
        if amount_range:
            amount_str = f"${amount_range}"
        else:
            amount_str = "unknown amount"
        
        # Format transaction type
        if "buy" in transaction_type or "purchase" in transaction_type:
            action = "bought"
        elif "sell" in transaction_type:
            action = "sold"
        else:
            action = transaction_type
        
        return f"{chamber_prefix} {politician} {action} {amount_str}"
    
    def _analyze_article(self, title: str, url: str, summary: str = "", summarizer=None) -> Dict[str, Any]:
        """
        Analyze a single article for summary, sector, and impact.
        
        Args:
            title: Article title
            url: Article URL
            summary: Article summary (if available)
            summarizer: AI summarizer client to use for analysis
            
        Returns:
            Dictionary with analysis results
        """
        content = f"Title: {title}\nURL: {url}\nSummary: {summary}"
        
        # Use AI summarizer if available
        if summarizer and hasattr(summarizer, 'summarize'):
            try:
                messages = [
                    {"role": "system", "content": "You are a financial news analyst. Analyze the given article and provide: 1) A concise summary, 2) The sector/industry, 3) Market impact (Bullish/Bearish/Neutral). Return as JSON: {\"summary\": \"...\", \"sector\": \"...\", \"impact\": \"...\"}"},
                    {"role": "user", "content": f"Analyze this article: {content}"}
                ]
                ai_response = summarizer.summarize(messages)
                
                # Try to parse JSON response
                try:
                    import json
                    analysis = json.loads(ai_response)
                    article_summary = analysis.get('summary', summary if summary else "Summary not available")
                    sector = analysis.get('sector', 'Unknown')
                    impact = analysis.get('impact', 'Neutral')
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    article_summary = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                    sector = "Unknown"
                    impact = "Neutral"
                    
            except Exception as e:
                logger.warning(f"⚠️ AI summarizer failed: {str(e)}, using fallback")
                article_summary = self._make_fallback_analysis(content, "summarize")
                sector = self._make_fallback_analysis(content, "sector")
                impact = self._make_fallback_analysis(content, "impact")
        else:
            # Use fallback analysis
            article_summary = self._make_fallback_analysis(content, "summarize")
            sector = self._make_fallback_analysis(content, "sector")
            impact = self._make_fallback_analysis(content, "impact")
        
        # Ensure we have valid values
        if not article_summary:
            article_summary = summary if summary else "Summary not available"
        
        if not sector or sector.lower() == "unknown":
            sector = "Unknown"
        
        if not impact or impact not in ["Bullish", "Bearish", "Neutral"]:
            impact = "Neutral"
        
        return {
            "title": strip_emojis(title),
            "url": url,
            "summary": strip_emojis(article_summary),
            "sector": sector,
            "impact": impact
        }
    
    def fetch_ticker_news(self, ticker: str, summarizer=None) -> List[Dict[str, Any]]:
        """
        Fetch news for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            summarizer: AI summarizer client to use for analysis
            
        Returns:
            List of news articles with analysis
        """
        try:
            logger.info(f"📰 Fetching news for {ticker}...")
            
            # Search for news using Perplexity
            query = f"{ticker} stock news"
            response = self._make_perplexity_api_request(query)
            
            if not response:
                logger.warning(f"⚠️ No response for {ticker}, skipping")
                return []
            
            # Parse articles from response
            raw_articles = self._parse_perplexity_response(response)
            
            if not raw_articles:
                logger.warning(f"⚠️ No articles found for {ticker}")
                return []
            
            # Fetch congressional trading data if enabled
            congressional_trades = []
            if self.include_quiver:
                congressional_trades = self._fetch_congressional_trades(ticker)
            
            # Analyze each article
            analyzed_articles = []
            for article in raw_articles[:3]:  # Limit to top 3
                try:
                    title = article.get('title', '')
                    url = article.get('url', '')
                    summary = article.get('summary', '')
                    
                    if title and url:
                        analyzed = self._analyze_article(title, url, summary, summarizer)
                        
                        # Add congressional trading data to the article
                        if congressional_trades:
                            trade_summaries = []
                            for trade in congressional_trades[:3]:  # Limit to 3 trades
                                trade_summary = self._format_congressional_trade(trade)
                                trade_summaries.append(trade_summary)
                            
                            analyzed["congressional_trades"] = trade_summaries
                            analyzed["congressional_trade_count"] = len(congressional_trades)
                        else:
                            analyzed["congressional_trades"] = []
                            analyzed["congressional_trade_count"] = 0
                        
                        analyzed_articles.append(analyzed)
                        logger.info(f"✅ Analyzed article for {ticker}: {title[:50]}...")
                    else:
                        logger.warning(f"⚠️ Skipping article for {ticker} - missing title or URL")
                        
                except Exception as e:
                    logger.error(f"❌ Error analyzing article for {ticker}: {str(e)}")
                    continue
            
            logger.info(f"✅ Found {len(analyzed_articles)} articles for {ticker}")
            return analyzed_articles
            
        except Exception as e:
            logger.error(f"❌ Error fetching news for {ticker}: {str(e)}")
            return []
    
    def process_tickers(self, tickers: List[str], summarizer=None) -> Dict[str, Any]:
        """
        Process multiple tickers and generate comprehensive results.
        
        Args:
            tickers: List of ticker symbols
            summarizer: AI summarizer client to use for analysis
            
        Returns:
            Dictionary with results for all tickers
        """
        logger.info(f"🚀 Processing {len(tickers)} tickers: {', '.join(tickers)}")
        
        all_results = {}
        total_articles = 0
        
        for ticker in tickers:
            ticker_upper = ticker.upper()
            articles = self.fetch_ticker_news(ticker_upper, summarizer)
            
            if articles:
                all_results[ticker_upper] = {
                    "ticker": ticker_upper,
                    "headlines": articles
                }
                total_articles += len(articles)
            else:
                logger.warning(f"⚠️ No results for {ticker_upper}")
                all_results[ticker_upper] = {
                    "ticker": ticker_upper,
                    "headlines": []
                }
        
        logger.info(f"✅ Processed {len(tickers)} tickers, found {total_articles} total articles")
        return all_results
    
    def save_markdown_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Save results to a Markdown file.
        
        Args:
            results: Results dictionary
            filename: Optional filename, defaults to timestamped name
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/news_summary_{timestamp}.md"
        
        try:
            # Ensure output directory exists
            os.makedirs("output", exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Ticker News Summary\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for ticker, data in results.items():
                    f.write(f"## {ticker}\n\n")
                    
                    headlines = data.get("headlines", [])
                    if headlines:
                        for i, article in enumerate(headlines, 1):
                            f.write(f"### Article {i}\n\n")
                            f.write(f"**Title:** {article.get('title', 'N/A')}\n\n")
                            f.write(f"**URL:** {article.get('url', 'N/A')}\n\n")
                            f.write(f"**Summary:** {article.get('summary', 'N/A')}\n\n")
                            f.write(f"**Sector:** {article.get('sector', 'Unknown')}\n\n")
                            f.write(f"**Impact:** {article.get('impact', 'Neutral')}\n\n")
                            
                            # Add congressional trading data if available
                            congressional_trades = article.get('congressional_trades', [])
                            if congressional_trades:
                                f.write(f"**🏛️ Recent Congressional Trades:**\n")
                                for trade in congressional_trades:
                                    f.write(f"- {trade}\n")
                                f.write("\n")
                            
                            f.write("---\n\n")
                    else:
                        f.write("No articles found.\n\n")
                
                f.write("\n---\n\n")
                f.write("*Report generated by MacroIntel TickerNewsAgent*\n")
            
            logger.info(f"✅ Markdown report saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error saving markdown report: {str(e)}")
            return ""
    
    def run(self, tickers: List[str] = None, include_quiver: bool = None, model: str = "claude") -> Dict[str, Any]:
        """
        Main execution method for the TickerNewsAgent.
        
        Args:
            tickers: List of ticker symbols to process
            include_quiver: Whether to include congressional trading data (overrides instance setting)
            model: AI model to use for analysis (claude, perplexity, mistral)
            
        Returns:
            Dictionary with execution results
        """
        if not tickers:
            # Default tickers if none provided
            tickers = ["SPY", "QQQ", "XLE"]
            logger.info("📋 Using default tickers: SPY, QQQ, XLE")
        
        # Update quiver setting if provided
        if include_quiver is not None:
            self.include_quiver = include_quiver
            if self.include_quiver and QUIVER_AVAILABLE:
                logger.info("🏛️ Quiver congressional trading data enabled")
            elif self.include_quiver and not QUIVER_AVAILABLE:
                logger.warning("⚠️ Quiver requested but module not available")
        
        # Initialize summarizer based on model selection
        if model == "mistral":
            from core.ai_clients import MistralClient
            summarizer = MistralClient()
            logger.info("🤖 Using MistralClient for summarization")
        elif model == "perplexity":
            # Use existing Perplexity API integration
            summarizer = None  # Will use existing _make_perplexity_api_request method
            logger.info("🤖 Using existing Perplexity API integration")
        elif model == "claude":
            # TODO: Add ClaudeClient when available
            summarizer = None
            logger.info("🤖 ClaudeClient not yet implemented, using fallback")
        else:
            logger.warning(f"⚠️ Unknown model '{model}', falling back to Perplexity.")
            summarizer = None  # Will use existing Perplexity API integration
        
        try:
            logger.info("🚀 Starting TickerNewsAgent...")
            
            # Process tickers
            results = self.process_tickers(tickers, summarizer)
            
            # Save markdown report
            markdown_file = self.save_markdown_report(results)
            
            # Prepare return data
            total_tickers = len(tickers)
            total_articles = sum(len(data.get("headlines", [])) for data in results.values())
            
            return {
                "status": "success",
                "tickers_processed": total_tickers,
                "total_articles": total_articles,
                "results": results,
                "markdown_file": markdown_file,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ TickerNewsAgent execution failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TickerNewsAgent - Fetch and analyze news for specific tickers")
    parser.add_argument("--tickers", nargs="+", help="List of ticker symbols to process")
    parser.add_argument("--output", help="Output filename for markdown report")
    parser.add_argument("--include-quiver", action="store_true", help="Include congressional trading data from Quiver")
    
    args = parser.parse_args()
    
    agent = TickerNewsAgent(include_quiver=args.include_quiver)
    
    if args.tickers:
        tickers = args.tickers
    else:
        # Default tickers
        tickers = ["SPY", "QQQ", "XLE"]
        print("📋 Using default tickers: SPY, QQQ, XLE")
    
    print(f"🚀 Processing tickers: {', '.join(tickers)}")
    if args.include_quiver:
        print("🏛️ Including congressional trading data")
    
    results = agent.run(tickers)
    
    if results["status"] == "success":
        print(f"✅ Successfully processed {results['tickers_processed']} tickers")
        print(f"📰 Found {results['total_articles']} total articles")
        print(f"📄 Report saved to: {results['markdown_file']}")
        
        # Print summary
        for ticker, data in results["results"].items():
            article_count = len(data.get("headlines", []))
            print(f"   {ticker}: {article_count} articles")
    else:
        print(f"❌ Error: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main() 