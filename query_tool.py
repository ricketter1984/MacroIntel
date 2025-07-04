#!/usr/bin/env python3
"""
MacroIntel Database Query Tool

A CLI utility for querying data from the MacroIntel SQLite database.
Supports querying regime scores, economic events, and news headlines.
"""

import argparse
import sys
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from tabulate import tabulate

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import data store functions
try:
    from data_store import (
        get_regime_scores_by_date_range,
        get_economic_events_by_date,
        get_recent_news_by_symbol,
        get_latest_regime_score
    )
    DATA_STORE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing data store: {e}")
    print("Make sure you're running this from the MacroIntel project root directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MacroIntelQueryTool:
    """CLI utility for querying MacroIntel database."""
    
    def __init__(self):
        """Initialize the query tool."""
        self.output_dir = project_root / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def query_regime_scores(self, days: int = 5, export_csv: bool = False) -> None:
        """
        Query regime scores from the past X days.
        
        Args:
            days: Number of days to look back
            export_csv: Whether to export results to CSV
        """
        try:
            # Calculate date range
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            print(f"📊 Querying regime scores from {start_date} to {end_date}...")
            
            # Get regime scores
            scores = get_regime_scores_by_date_range(start_date, end_date)
            
            if not scores:
                print("❌ No regime scores found for the specified date range.")
                return
            
            # Prepare data for display
            table_data = []
            for score in scores:
                table_data.append([
                    score['timestamp'][:19],  # Truncate to show date and time only
                    f"{score['total_score']:.1f}",
                    score['strategy'],
                    score['instrument'],
                    f"{score['volatility']:.1f}",
                    f"{score['structure']:.1f}",
                    f"{score['momentum']:.1f}",
                    f"{score['breadth']:.1f}",
                    f"{score['institutional']:.1f}"
                ])
            
            # Display results
            headers = ["Timestamp", "Total Score", "Strategy", "Instrument", "Volatility", "Structure", "Momentum", "Breadth", "Institutional"]
            print(f"\n📈 Found {len(scores)} regime scores:")
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Export to CSV if requested
            if export_csv:
                self._export_to_csv(table_data, headers, "regime_scores")
                
        except Exception as e:
            logger.error(f"❌ Error querying regime scores: {e}")
            print(f"❌ Error: {e}")
    
    def query_economic_events(self, date: str, category: Optional[str] = None, export_csv: bool = False) -> None:
        """
        Query economic events for a given date.
        
        Args:
            date: Date in YYYY-MM-DD format
            category: Optional category filter
            export_csv: Whether to export results to CSV
        """
        try:
            print(f"📅 Querying economic events for {date}...")
            
            # Get economic events
            events = get_economic_events_by_date(date)
            
            if not events:
                print(f"❌ No economic events found for {date}.")
                return
            
            # Filter by category if specified
            if category:
                events = [event for event in events if event.get('category', '').lower() == category.lower()]
                if not events:
                    print(f"❌ No economic events found for {date} in category '{category}'.")
                    return
                print(f"🔍 Filtered by category: {category}")
            
            # Prepare data for display
            table_data = []
            for event in events:
                table_data.append([
                    event['date'],
                    event['time'],
                    event['event_name'],
                    event['impact_level'],
                    event.get('forecast', ''),
                    event.get('actual', ''),
                    event.get('category', '')
                ])
            
            # Display results
            headers = ["Date", "Time", "Event", "Impact", "Forecast", "Actual", "Category"]
            print(f"\n📋 Found {len(events)} economic events:")
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Export to CSV if requested
            if export_csv:
                self._export_to_csv(table_data, headers, f"economic_events_{date}")
                
        except Exception as e:
            logger.error(f"❌ Error querying economic events: {e}")
            print(f"❌ Error: {e}")
    
    def query_headlines(self, symbol: str, days: int = 7, export_csv: bool = False) -> None:
        """
        Query GPT-summarized headlines by symbol.
        
        Args:
            symbol: Stock/crypto symbol to search for
            days: Number of days to look back
            export_csv: Whether to export results to CSV
        """
        try:
            print(f"📰 Querying headlines for {symbol.upper()} from the past {days} days...")
            
            # Get recent news by symbol
            headlines = get_recent_news_by_symbol(symbol.upper(), limit=100)  # Get more to filter by date
            
            if not headlines:
                print(f"❌ No headlines found for {symbol.upper()}.")
                return
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_headlines = []
            for headline in headlines:
                try:
                    headline_date = datetime.fromisoformat(headline['timestamp'].replace('Z', '+00:00'))
                    if headline_date >= cutoff_date:
                        recent_headlines.append(headline)
                except (ValueError, TypeError):
                    # Skip headlines with invalid timestamps
                    continue
            
            if not recent_headlines:
                print(f"❌ No headlines found for {symbol.upper()} in the past {days} days.")
                return
            
            # Sort by timestamp (newest first)
            recent_headlines.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Prepare data for display
            table_data = []
            for headline in recent_headlines:
                # Truncate summary for display
                summary = headline.get('summary', '')
                if len(summary) > 80:
                    summary = summary[:77] + "..."
                
                table_data.append([
                    headline['timestamp'][:19],  # Truncate to show date and time only
                    headline['source'],
                    headline['headline'][:60] + "..." if len(headline['headline']) > 60 else headline['headline'],
                    summary,
                    headline.get('sentiment', 'neutral')
                ])
            
            # Display results
            headers = ["Timestamp", "Source", "Headline", "Summary", "Sentiment"]
            print(f"\n📰 Found {len(recent_headlines)} headlines for {symbol.upper()}:")
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Export to CSV if requested
            if export_csv:
                self._export_to_csv(table_data, headers, f"headlines_{symbol.lower()}")
                
        except Exception as e:
            logger.error(f"❌ Error querying headlines: {e}")
            print(f"❌ Error: {e}")
    
    def _export_to_csv(self, data: List[List], headers: List[str], filename_prefix: str) -> None:
        """
        Export data to CSV file.
        
        Args:
            data: Table data to export
            headers: Column headers
            filename_prefix: Prefix for the CSV filename
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.csv"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(data)
            
            print(f"💾 Data exported to: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error exporting to CSV: {e}")
            print(f"❌ Error exporting to CSV: {e}")
    
    def show_latest_regime_score(self) -> None:
        """Show the most recent regime score."""
        try:
            print("📊 Fetching latest regime score...")
            
            latest_score = get_latest_regime_score()
            
            if not latest_score:
                print("❌ No regime scores found in database.")
                return
            
            print(f"\n🎯 LATEST REGIME SCORE:")
            print(f"   Timestamp: {latest_score['timestamp']}")
            print(f"   Total Score: {latest_score['total_score']:.1f}/100")
            print(f"   Strategy: {latest_score['strategy']}")
            print(f"   Instrument: {latest_score['instrument']}")
            print(f"   Components:")
            print(f"     • Volatility: {latest_score['volatility']:.1f}")
            print(f"     • Structure: {latest_score['structure']:.1f}")
            print(f"     • Momentum: {latest_score['momentum']:.1f}")
            print(f"     • Breadth: {latest_score['breadth']:.1f}")
            print(f"     • Institutional: {latest_score['institutional']:.1f}")
            
        except Exception as e:
            logger.error(f"❌ Error fetching latest regime score: {e}")
            print(f"❌ Error: {e}")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="MacroIntel Database Query Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query_tool.py --regime --days 7
  python query_tool.py --events --date 2024-01-15 --category Fed
  python query_tool.py --headlines --symbol BTC --days 3 --export
  python query_tool.py --latest
        """
    )
    
    # Create mutually exclusive group for query types
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument('--regime', action='store_true', help='Query regime scores')
    query_group.add_argument('--events', action='store_true', help='Query economic events')
    query_group.add_argument('--headlines', action='store_true', help='Query news headlines')
    query_group.add_argument('--latest', action='store_true', help='Show latest regime score')
    
    # Common arguments
    parser.add_argument('--days', type=int, default=5, help='Number of days to look back (default: 5)')
    parser.add_argument('--export', action='store_true', help='Export results to CSV file')
    
    # Event-specific arguments
    parser.add_argument('--date', type=str, help='Date for events query (YYYY-MM-DD format)')
    parser.add_argument('--category', type=str, help='Category filter for events (e.g., Fed, Jobs, Inflation)')
    
    # Headline-specific arguments
    parser.add_argument('--symbol', type=str, help='Symbol for headlines query (e.g., BTC, AAPL)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.events and not args.date:
        print("❌ Error: --date is required for events query")
        sys.exit(1)
    
    if args.headlines and not args.symbol:
        print("❌ Error: --symbol is required for headlines query")
        sys.exit(1)
    
    # Initialize query tool
    query_tool = MacroIntelQueryTool()
    
    # Execute query based on arguments
    try:
        if args.regime:
            query_tool.query_regime_scores(days=args.days, export_csv=args.export)
        elif args.events:
            query_tool.query_economic_events(date=args.date, category=args.category, export_csv=args.export)
        elif args.headlines:
            query_tool.query_headlines(symbol=args.symbol, days=args.days, export_csv=args.export)
        elif args.latest:
            query_tool.show_latest_regime_score()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Query interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 