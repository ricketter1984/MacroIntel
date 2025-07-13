#!/usr/bin/env python3
"""
MacroIntel Natural Language Query Interface

This module provides a natural language interface to the MacroIntel system,
allowing users to query various components using plain English and receive
appropriate responses from charts, summaries, or data.

Usage:
    python macrointel_query.py "What's the current market regime?"
    python macrointel_query.py "Show me volatility trends for oil"
    python macrointel_query.py "Any major economic events this week?"
    python macrointel_query.py "Latest news headlines"

Author: MacroIntel System
Version: 1.0.0
"""

import os
import sys
import json
import logging
import argparse
import shutil
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create required directories
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

class MacroIntelQueryEngine:
    """
    Natural language query engine for MacroIntel system.
    
    Routes queries to appropriate modules based on keyword analysis
    and provides unified response interface.
    """
    
    def __init__(self):
        """Initialize the query engine."""
        self.query_log_path = "logs/query_log.json"
        self.output_dir = "output"
        
        # Define keyword mappings for routing
        self.route_keywords = {
            'chart': ['compare', 'trend', 'volatility', 'chart', 'graph', 'plot', 'visual', 'show', 'display'],
            'calendar': ['event', 'calendar', 'macro', 'economic', 'fomc', 'cpi', 'gdp', 'employment', 'inflation'],
            'news': ['news', 'headlines', 'articles', 'stories', 'breaking', 'alert', 'update'],
            'regime': ['regime', 'strategy', 'tier', 'score', 'market', 'condition', 'recommendation'],
            'database': ['data', 'database', 'records', 'query', 'sql', 'stats', 'history', 'table', 'stored', 'retrieve']
        }
        
        # Initialize module availability flags
        self.modules_available = self._check_module_availability()
        
        logger.info("🔍 MacroIntel Query Engine initialized")
    
    def _check_module_availability(self) -> Dict[str, bool]:
        """Check which modules are available for querying."""
        availability = {}
        
        # Check chart generator
        try:
            from agents.chart_generator_agent import ChartGeneratorAgent
            availability['chart_generator'] = True
        except ImportError:
            availability['chart_generator'] = False
            logger.warning("⚠️ Chart Generator Agent not available")
        
        # Check regime calculator
        try:
            from regime_score_calculator import get_daily_regime_score
            availability['regime_calculator'] = True
        except ImportError:
            availability['regime_calculator'] = False
            logger.warning("⚠️ Regime Score Calculator not available")
        
        # Check calendar sync
        try:
            from utils.api_clients import fetch_fmp_calendar
            availability['calendar_sync'] = True
        except ImportError:
            availability['calendar_sync'] = False
            logger.warning("⚠️ Calendar Google Sync not available")
        
        # Check news alerts
        try:
            from news_alerts import NewsAlertsEngine
            availability['news_alerts'] = True
        except ImportError:
            availability['news_alerts'] = False
            logger.warning("⚠️ News Alerts Engine not available")
        
        # Check summarizer agent for fallback
        try:
            from agents.summarizer_agent import SummarizerAgent
            availability['summarizer'] = True
        except ImportError:
            availability['summarizer'] = False
            logger.warning("⚠️ Summarizer Agent not available")
        
        return availability
    
    def analyze_query(self, query: str) -> Tuple[str, float]:
        """
        Analyze query and determine the best route.
        
        Args:
            query: Natural language query string
            
        Returns:
            Tuple of (route_type, confidence_score)
        """
        query_lower = query.lower()
        route_scores = {}
        
        # Calculate scores for each route based on keyword matches
        for route_type, keywords in self.route_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            
            route_scores[route_type] = score
        
        # Find the best route
        if route_scores:
            best_route = max(route_scores.items(), key=lambda x: x[1])
            # Only return a route if it has at least 1 keyword match
            if best_route[1] > 0:
                return best_route[0], best_route[1] / len(query_lower.split())
        
        return 'unknown', 0.0
    
    def handle_chart_query(self, query: str) -> Dict[str, Any]:
        """Handle chart-related queries."""
        logger.info(f"📈 Processing chart query: {query}")
        
        if not self.modules_available['chart_generator']:
            return {
                'success': False,
                'error': 'Chart Generator Agent not available',
                'response': 'Chart generation capability is currently unavailable.'
            }
        
        try:
            from agents.chart_generator_agent import ChartGeneratorAgent
            
            # Initialize chart generator
            chart_agent = ChartGeneratorAgent()
            
            # Extract potential instruments from query
            instruments = self._extract_instruments(query)
            
            # Auto-add oil futures symbol for oil-related queries
            if "oil" in query.lower() and "MCL=F" not in instruments:
                instruments.append("MCL=F")
                logger.info(f"🛢️ Auto-added MCL=F for oil query")
            
            # Get current regime data for chart generation
            regime_data = self._get_regime_data()
            fear_greed_score = self._get_fear_greed_score()
            
            # Generate chart with extracted context
            chart_result = chart_agent.generate_intelligent_chart(
                regime_data=regime_data,
                fear_greed_score=fear_greed_score,
                dominant_keywords=instruments,
                tags=self._extract_tags(query)
            )
            

            if chart_result.get('success', False):
                # Copy chart to standard query response location
                source_path = chart_result.get('file_path', '')
                if source_path and os.path.exists(source_path):
                    dest_path = os.path.join(self.output_dir, 'query_response.png')
                    shutil.copy2(source_path, dest_path)
                    
                    return {
                        'success': True,
                        'type': 'chart',
                        'file_path': dest_path,
                        'description': chart_result.get('description', 'Chart generated successfully'),
                        'response': f"Chart generated and saved to {dest_path}",
                        'details': chart_result
                    }
            
            return {
                'success': False,
                'error': 'Chart generation failed',
                'response': 'Unable to generate chart for the requested query.'
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling chart query: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': f'Error processing chart query: {str(e)}'
            }
    
    def handle_calendar_query(self, query: str) -> Dict[str, Any]:
        """Handle calendar/event-related queries."""
        logger.info(f"📅 Processing calendar query: {query}")
        
        if not self.modules_available['calendar_sync']:
            return {
                'success': False,
                'error': 'Calendar sync module not available',
                'response': 'Calendar and economic event data is currently unavailable.'
            }
        
        try:
            from utils.api_clients import fetch_fmp_calendar
            
            # Fetch upcoming economic events
            events = fetch_fmp_calendar()
            
            if not events:
                return {
                    'success': True,
                    'type': 'calendar',
                    'response': 'No major economic events found in the next 7 days.',
                    'events': []
                }
            
            # Format events for response
            formatted_events = []
            for event in events[:10]:  # Show top 10 events
                formatted_events.append({
                    'date': event.get('date', ''),
                    'time': event.get('time', ''),
                    'event': event.get('event', ''),
                    'country': event.get('country', ''),
                    'impact': event.get('impact', ''),
                    'previous': event.get('previous', ''),
                    'consensus': event.get('consensus', ''),
                    'actual': event.get('actual', '')
                })
            
            # Create response text
            response_lines = ["📅 Upcoming Economic Events:"]
            for event in formatted_events:
                impact_emoji = "🔴" if event['impact'] == 'High' else "🟡" if event['impact'] == 'Medium' else "🟢"
                response_lines.append(
                    f"{impact_emoji} {event['date']} {event['time']} - {event['event']} ({event['country']})"
                )
                if event['consensus']:
                    response_lines.append(f"   Expected: {event['consensus']}")
            
            return {
                'success': True,
                'type': 'calendar',
                'response': '\n'.join(response_lines),
                'events': formatted_events,
                'count': len(formatted_events)
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling calendar query: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': f'Error processing calendar query: {str(e)}'
            }
    
    def handle_news_query(self, query: str) -> Dict[str, Any]:
        """Handle news-related queries."""
        logger.info(f"📰 Processing news query: {query}")
        
        if not self.modules_available['news_alerts']:
            return {
                'success': False,
                'error': 'News alerts module not available',
                'response': 'News and headline data is currently unavailable.'
            }
        
        try:
            from news_alerts import NewsAlertsEngine
            
            # Initialize news alerts engine
            news_engine = NewsAlertsEngine()
            
            # Get recent alerts summary
            summary = news_engine.get_alerts_summary(hours=24)
            
            if not summary:
                return {
                    'success': True,
                    'type': 'news',
                    'response': 'No recent news alerts found in the last 24 hours.',
                    'articles': []
                }
            
            # Format summary for response
            response_lines = ["📰 Recent News Summary (Last 24 Hours):"]
            response_lines.append(f"Total Articles: {summary.get('total_articles', 0)}")
            response_lines.append(f"High Priority: {summary.get('high_priority', 0)}")
            response_lines.append(f"Medium Priority: {summary.get('medium_priority', 0)}")
            response_lines.append("")
            
            # Add top articles
            articles = summary.get('articles', [])[:5]  # Show top 5
            for i, article in enumerate(articles, 1):
                response_lines.append(f"{i}. {article.get('title', 'No title')}")
                if article.get('summary'):
                    response_lines.append(f"   Summary: {article['summary'][:100]}...")
                response_lines.append("")
            
            return {
                'success': True,
                'type': 'news',
                'response': '\n'.join(response_lines),
                'summary': summary,
                'articles': articles
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling news query: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': f'Error processing news query: {str(e)}'
            }
    
    def handle_regime_query(self, query: str) -> Dict[str, Any]:
        """Handle regime/strategy-related queries."""
        logger.info(f"🎯 Processing regime query: {query}")
        
        if not self.modules_available['regime_calculator']:
            return {
                'success': False,
                'error': 'Regime calculator module not available',
                'response': 'Market regime analysis is currently unavailable.'
            }
        
        try:
            from regime_score_calculator import get_daily_regime_score
            
            # Get current regime score
            regime_results = get_daily_regime_score()
            
            if 'error' in regime_results:
                return {
                    'success': False,
                    'error': regime_results['error'],
                    'response': f'Error calculating regime score: {regime_results["error"]}'
                }
            
            # Format regime analysis for response
            total_score = regime_results.get('total_score', 0)
            classification = regime_results.get('regime_classification', 'Unknown')
            strategy = regime_results.get('strategy_recommendation', 'Unknown')
            instrument = regime_results.get('instrument', 'Unknown')
            risk_allocation = regime_results.get('risk_allocation', 'Unknown')
            
            response_lines = [
                "🎯 Current Market Regime Analysis:",
                f"📊 Regime Score: {total_score:.1f}/100",
                f"🏷️ Classification: {classification}",
                f"💡 Strategy: {strategy}",
                f"📈 Recommended Instrument: {instrument}",
                f"💰 Risk Allocation: {risk_allocation}",
                "",
                "📈 Component Breakdown:"
            ]
            
            # Add component scores
            component_breakdown = regime_results.get('component_breakdown', {})
            for component, data in component_breakdown.items():
                component_name = component.replace('_', ' ').title()
                score = data.get('raw_score', 0)
                interpretation = data.get('interpretation', '')
                response_lines.append(f"   • {component_name}: {score:.1f}/100 - {interpretation}")
            
            return {
                'success': True,
                'type': 'regime',
                'response': '\n'.join(response_lines),
                'regime_data': regime_results,
                'score': total_score,
                'strategy': strategy
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling regime query: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': f'Error processing regime query: {str(e)}'
            }
    
    def handle_database_query(self, query: str) -> Dict[str, Any]:
        """Handle database-related queries using SQLite agent."""
        logger.info(f"🗄️ Processing database query: {query}")
        
        try:
            # Import SQLite integration
            from agents.sqlite_integration import MacroIntelDataManager
            
            # Initialize data manager
            manager = MacroIntelDataManager()
            
            # Check if query is asking for stats/summary - provide fallback
            if any(keyword in query.lower() for keyword in ['stats', 'statistics', 'summary', 'dashboard']):
                # Fallback to dashboard/stats functionality
                dashboard = manager.get_analytics_dashboard()
                if 'error' not in dashboard:
                    db_stats = dashboard.get('database_stats', {})
                    market_summary = dashboard.get('market_summary', {})
                    
                    response = "📊 Database Statistics:\n"
                    response += f"Database size: {db_stats.get('database_size_mb', 0):.2f} MB\n"
                    response += f"Market data: {db_stats.get('market_data_count', 0):,} records\n"
                    response += f"Regime scores: {db_stats.get('regime_scores_count', 0):,} records\n"
                    response += f"Economic events: {db_stats.get('economic_events_count', 0):,} records\n"
                    
                    if 'summary_data' in market_summary:
                        response += f"\nSymbols tracked: {market_summary.get('symbols_count', 0)}"
                    
                    return {
                        'success': True,
                        'response': response,
                        'data': dashboard
                    }
            
            # Execute natural language query
            result = manager.query_data(query)
            
            if result['success']:
                # Format response
                response = f"Query executed successfully ({result['execution_time']:.3f}s)"
                if result['row_count'] > 0:
                    response += f" - {result['row_count']} rows returned"
                    
                    # Format data for display
                    if result['data']:
                        data_preview = ""
                        for i, row in enumerate(result['data'][:5]):  # Show first 5 rows
                            data_preview += f"\n{i+1}. {row}"
                        
                        if len(result['data']) > 5:
                            data_preview += f"\n... and {len(result['data']) - 5} more rows"
                        
                        response += data_preview
                else:
                    response += " - No data returned"
                
                if result.get('cached'):
                    response += " (cached result)"
                
                return {
                    'success': True,
                    'response': response,
                    'data': result.get('data', []),
                    'sql_query': result.get('sql_query'),
                    'execution_time': result['execution_time'],
                    'row_count': result['row_count']
                }
            else:
                # If natural language fails, try stats fallback
                if any(keyword in query.lower() for keyword in ['data', 'records', 'table']):
                    dashboard = manager.get_analytics_dashboard()
                    if 'error' not in dashboard:
                        db_stats = dashboard.get('database_stats', {})
                        response = "📊 Database contains:\n"
                        response += f"Market data: {db_stats.get('market_data_count', 0):,} records\n"
                        response += f"Regime scores: {db_stats.get('regime_scores_count', 0):,} records\n"
                        response += f"Economic events: {db_stats.get('economic_events_count', 0):,} records\n"
                        response += f"News data: {db_stats.get('news_data_count', 0):,} records\n"
                        response += "\nNote: Natural language queries require OpenAI API key for detailed results."
                        
                        return {
                            'success': True,
                            'response': response,
                            'data': dashboard
                        }
                
                return {
                    'success': False,
                    'error': result.get('error', 'Database query failed'),
                    'response': f"Database query failed: {result.get('error', 'Unknown error')}"
                }
                
        except ImportError:
            logger.error("❌ SQLite integration not available")
            return {
                'success': False,
                'error': 'SQLite integration not available',
                'response': 'Database query functionality is not available. Please ensure SQLite agent is installed.'
            }
        except Exception as e:
            logger.error(f"❌ Error in database query: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Error processing database query: {str(e)}"
            }
    
    def handle_unknown_query(self, query: str) -> Dict[str, Any]:
        """Handle unknown queries using fallback methods."""
        logger.info(f"❓ Processing unknown query: {query}")
        
        # Try to use summarizer agent as fallback
        if self.modules_available['summarizer']:
            try:
                from agents.summarizer_agent import SummarizerAgent
                
                summarizer = SummarizerAgent()
                
                # Generate a general response
                response = f"""I'm not sure how to process that specific query: "{query}"

Here are some examples of what I can help you with:

📈 Chart Queries:
   • "Show me volatility trends"
   • "Compare oil and gold"
   • "Display current market trends"

📅 Calendar Queries:
   • "What economic events are coming up?"
   • "Show me this week's macro calendar"
   • "Any FOMC meetings scheduled?"

📰 News Queries:
   • "Latest headlines"
   • "Recent news alerts"
   • "What's happening in the markets?"

🎯 Regime Queries:
   • "What's the current market regime?"
   • "Show me the regime score"
   • "What strategy is recommended?"

Try rephrasing your query using these keywords, or use 'python macrointel_query.py --help' for more information."""
                
                return {
                    'success': True,
                    'type': 'help',
                    'response': response,
                    'original_query': query
                }
                
            except Exception as e:
                logger.error(f"❌ Error in fallback handling: {str(e)}")
        
        # Basic fallback response
        return {
            'success': False,
            'type': 'unknown',
            'response': f'Unable to process query: "{query}". Please try rephrasing or use --help for available commands.',
            'original_query': query
        }
    
    def _extract_instruments(self, query: str) -> list:
        """Extract potential trading instruments from query."""
        instruments = []
        query_lower = query.lower()
        
        # Common instrument mappings
        instrument_keywords = {
            'oil': ['oil', 'crude', 'wti', 'mcl'],
            'gold': ['gold', 'precious', 'mgc'],
            'sp500': ['sp500', 's&p', 'spy', 'mes'],
            'nasdaq': ['nasdaq', 'qqq', 'tech', 'mnq'],
            'dow': ['dow', 'dji', 'mym'],
            'russell': ['russell', 'iwm', 'm2k'],
            'bitcoin': ['bitcoin', 'btc', 'crypto'],
            'forex': ['forex', 'currency', 'dxy', 'euro', 'yen']
        }
        
        for instrument, keywords in instrument_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                instruments.append(instrument)
        
        return instruments if instruments else ['general']
    
    def _extract_tags(self, query: str) -> list:
        """Extract relevant tags from query."""
        tags = []
        query_lower = query.lower()
        
        # Common tag mappings
        tag_keywords = {
            'volatility': ['volatility', 'vol', 'vix'],
            'trend': ['trend', 'direction', 'momentum'],
            'breakout': ['breakout', 'break', 'resistance', 'support'],
            'reversal': ['reversal', 'turn', 'change'],
            'economic': ['economic', 'macro', 'gdp', 'inflation'],
            'geopolitical': ['war', 'conflict', 'political', 'election']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                tags.append(tag)
        
        return tags if tags else ['general']
    
    def _get_regime_data(self) -> Dict[str, Any]:
        """Get current regime data for chart generation."""
        try:
            from regime_score_calculator import get_daily_regime_score
            regime_results = get_daily_regime_score()
            return regime_results if 'error' not in regime_results else {}
        except Exception:
            return {'total_score': 50, 'regime_classification': 'Neutral'}
    
    def _get_fear_greed_score(self) -> int:
        """Get current Fear & Greed score."""
        try:
            from dashboards.fear_greed_dashboard import get_fear_greed_report
            fear_greed = get_fear_greed_report()
            return int(fear_greed.get('score', 50))
        except Exception:
            return 50
    
    def log_query(self, query: str, result: Dict[str, Any]) -> None:
        """Log query and result to JSON file."""
        try:
            # Load existing log
            if os.path.exists(self.query_log_path):
                with open(self.query_log_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
            else:
                log_data = {'queries': []}
            
            # Add new query
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'route': result.get('type', 'unknown'),
                'success': result.get('success', False),
                'response_length': len(result.get('response', '')),
                'error': result.get('error', None)
            }
            
            log_data['queries'].append(log_entry)
            
            # Keep only last 1000 queries
            if len(log_data['queries']) > 1000:
                log_data['queries'] = log_data['queries'][-1000:]
            
            # Save log
            with open(self.query_log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📝 Query logged: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Error logging query: {str(e)}")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query and return appropriate response.
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary with response data
        """
        logger.info(f"🔍 Processing query: {query}")
        
        # Analyze query to determine route
        route_type, confidence = self.analyze_query(query)
        
        logger.info(f"📍 Route determined: {route_type} (confidence: {confidence:.2f})")
        
        # Route to appropriate handler
        if route_type == 'chart':
            result = self.handle_chart_query(query)
        elif route_type == 'calendar':
            result = self.handle_calendar_query(query)
        elif route_type == 'news':
            result = self.handle_news_query(query)
        elif route_type == 'regime':
            result = self.handle_regime_query(query)
        elif route_type == 'database':
            result = self.handle_database_query(query)
        else:
            result = self.handle_unknown_query(query)
        
        # Log the query
        self.log_query(query, result)
        
        return result


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description='MacroIntel Natural Language Query Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python macrointel_query.py "What's the current market regime?"
  python macrointel_query.py "Show me volatility trends for oil"
  python macrointel_query.py "Any major economic events this week?"
  python macrointel_query.py "Latest news headlines"
  python macrointel_query.py "Compare gold and bitcoin trends"
        """
    )
    
    parser.add_argument(
        'query',
        type=str,
        help='Natural language query to process'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output result as JSON'
    )
    
    args = parser.parse_args()
    
    # Initialize query engine
    query_engine = MacroIntelQueryEngine()
    
    # Special routing for ETF/sector/implied volatility queries
    if "etf" in args.query.lower() or "sector" in args.query.lower() or "implied volatility" in args.query.lower():
        try:
            from agents.vanna_agent import VannaAgent
            agent = VannaAgent()
            response = agent.ask(args.query)
            print(response)
            return
        except ImportError:
            print("❌ VannaAgent not available - falling back to standard processing")
        except Exception as e:
            print(f"❌ Error with VannaAgent: {str(e)} - falling back to standard processing")
    
    # Process query
    result = query_engine.process_query(args.query)
    
    # Output result
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "="*60)
        print("🔍 MACROINTEL QUERY RESPONSE")
        print("="*60)
        print(result.get('response', 'No response available'))
        
        if result.get('success', False) and result.get('type') == 'chart':
            print(f"\n📈 Chart saved to: {result.get('file_path', 'Unknown')}")
        
        if args.verbose:
            print("\n" + "-"*40)
            print("📋 QUERY DETAILS:")
            print("-"*40)
            print(f"Query: {args.query}")
            print(f"Route: {result.get('type', 'unknown')}")
            print(f"Success: {result.get('success', False)}")
            if result.get('error'):
                print(f"Error: {result.get('error')}")
    
    return result


if __name__ == "__main__":
    main() 