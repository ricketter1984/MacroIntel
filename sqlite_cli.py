#!/usr/bin/env python3
"""
SQLite Agent CLI for MacroIntel

Simple command-line interface for the SQLite agent.
Usage:
    python sqlite_cli.py sync         # Sync all data
    python sqlite_cli.py query "natural language query"
    python sqlite_cli.py stats        # Show database stats
    python sqlite_cli.py dashboard    # Show analytics dashboard
"""

import argparse
import json
import sys
from pathlib import Path

# Add agents to path
sys.path.append(str(Path(__file__).parent / "agents"))

try:
    from sqlite_integration import MacroIntelDataManager
except ImportError as e:
    print(f"❌ Error importing SQLite integration: {e}")
    print("Make sure you're running from the MacroIntel directory")
    sys.exit(1)

def handle_sync(args):
    """Handle data synchronization command."""
    print("🔄 Starting data synchronization...")
    
    manager = MacroIntelDataManager()
    
    # Define symbols to sync
    symbols = [
        'SPY', 'QQQ', 'IWM', 'DIA',
        'MES=F', 'MNQ=F', 'MYM=F', 'M2K=F',
        'MCL=F', 'MGC=F', 'CL=F', 'GC=F',
        '^VIX', '^GSPC', '^IXIC', '^DJI'
    ]
    
    # Override with custom symbols if provided
    if args.symbols:
        symbols = args.symbols.split(',')
        print(f"📊 Using custom symbols: {symbols}")
    
    # Run synchronization
    results = manager.run_full_sync(symbols)
    
    # Display results
    print("\n" + "="*60)
    print("📊 SYNCHRONIZATION RESULTS")
    print("="*60)
    
    print(f"⏰ Started: {results['sync_started']}")
    print(f"⏰ Completed: {results.get('sync_completed', 'In Progress')}")
    
    print(f"\n📈 Market Data:")
    market_results = results.get('market_data', {})
    successful = sum(1 for success in market_results.values() if success)
    total = len(market_results)
    print(f"   Success Rate: {successful}/{total} symbols")
    
    for symbol, success in market_results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {symbol}")
    
    print(f"\n🎯 Regime Scores: {'✅' if results.get('regime_scores') else '❌'}")
    print(f"📅 Economic Events: {'✅' if results.get('economic_events') else '❌'}")
    print(f"📰 News Data: {'✅' if results.get('news_data') else '❌'}")
    
    if results.get('errors'):
        print(f"\n❌ Errors:")
        for error in results['errors']:
            print(f"   • {error}")
    
    print(f"\n✅ Synchronization completed!")

def handle_query(args):
    """Handle natural language query command."""
    query = args.query
    print(f"🧠 Processing query: {query}")
    
    manager = MacroIntelDataManager()
    result = manager.query_data(query)
    
    print("\n" + "="*60)
    print("🔍 QUERY RESULTS")
    print("="*60)
    
    if result['success']:
        print(f"✅ Query successful")
        print(f"⏱️ Execution time: {result['execution_time']:.3f}s")
        print(f"📊 Rows returned: {result['row_count']}")
        
        if result.get('cached'):
            print("💾 Result from cache")
        
        if result.get('sql_query'):
            print(f"\n🔧 Generated SQL:")
            print(f"   {result['sql_query']}")
        
        if result.get('explanation'):
            print(f"\n💡 Explanation:")
            print(f"   {result['explanation']}")
        
        if result['data']:
            print(f"\n📋 Data:")
            # Display first 10 rows
            for i, row in enumerate(result['data'][:10]):
                print(f"   {i+1}. {row}")
            
            if len(result['data']) > 10:
                print(f"   ... and {len(result['data']) - 10} more rows")
        else:
            print("📋 No data returned")
    else:
        print(f"❌ Query failed: {result.get('error', 'Unknown error')}")

def handle_stats(args):
    """Handle database statistics command."""
    print("📊 Fetching database statistics...")
    
    manager = MacroIntelDataManager()
    stats = manager.agent.get_database_stats()
    
    print("\n" + "="*60)
    print("🗄️ DATABASE STATISTICS")
    print("="*60)
    
    print(f"📁 Database size: {stats.get('database_size_mb', 0):.2f} MB")
    print(f"🧠 Vanna AI enabled: {'✅' if stats.get('vanna_enabled') else '❌'}")
    
    print(f"\n📋 Table Row Counts:")
    tables = ['market_data', 'regime_scores', 'economic_events', 'news_data', 'query_cache']
    for table in tables:
        count = stats.get(f"{table}_count", 0)
        print(f"   {table}: {count:,}")
    
    # Show date ranges
    print(f"\n📅 Data Date Ranges:")
    for table in ['market_data', 'regime_scores', 'economic_events']:
        range_key = f"{table}_date_range"
        if range_key in stats:
            date_range = stats[range_key]
            print(f"   {table}: {date_range['from']} to {date_range['to']}")
        else:
            print(f"   {table}: No data")
    
    # Cache stats
    cache_stats = stats.get('cache_24h', {})
    if cache_stats:
        print(f"\n💾 Cache (24h):")
        print(f"   Queries cached: {cache_stats.get('queries', 0)}")
        print(f"   Total accesses: {cache_stats.get('accesses', 0)}")
    
    print(f"\n⏰ Generated: {stats.get('generated_at', 'Unknown')}")

def handle_dashboard(args):
    """Handle analytics dashboard command."""
    print("📊 Generating analytics dashboard...")
    
    manager = MacroIntelDataManager()
    dashboard = manager.get_analytics_dashboard()
    
    if 'error' in dashboard:
        print(f"❌ Error generating dashboard: {dashboard['error']}")
        return
    
    print("\n" + "="*80)
    print("📊 MACROINTEL ANALYTICS DASHBOARD")
    print("="*80)
    
    # Database overview
    db_stats = dashboard.get('database_stats', {})
    print(f"🗄️ Database: {db_stats.get('database_size_mb', 0):.2f} MB")
    print(f"📋 Market Data: {db_stats.get('market_data_count', 0):,} records")
    print(f"🎯 Regime Scores: {db_stats.get('regime_scores_count', 0):,} records")
    print(f"📅 Economic Events: {db_stats.get('economic_events_count', 0):,} records")
    
    # Market summary
    market_summary = dashboard.get('market_summary', {})
    if 'summary_data' in market_summary:
        print(f"\n📈 Market Summary (30-day):")
        print(f"   Symbols tracked: {market_summary.get('symbols_count', 0)}")
        
        for symbol_data in market_summary['summary_data'][:5]:  # Show top 5
            symbol = symbol_data['symbol']
            avg_price = symbol_data['avg_price']
            range_pct = symbol_data['price_range_pct']
            print(f"   📊 {symbol}: Avg ${avg_price}, Range {range_pct}%")
    
    # Current regime
    current_regime = market_summary.get('current_regime')
    if current_regime:
        print(f"\n🎯 Current Market Regime:")
        print(f"   Classification: {current_regime.get('regime_classification', 'Unknown')}")
        print(f"   Score: {current_regime.get('total_score', 0):.1f}/100")
        print(f"   Strategy: {current_regime.get('strategy_recommendation', 'Unknown')}")
    
    # Recent regime scores
    recent_scores = dashboard.get('recent_regime_scores', [])
    if recent_scores:
        print(f"\n📈 Recent Regime Scores (7-day):")
        for score in recent_scores[:3]:  # Show last 3
            date = score['date']
            total = score['total_score']
            classification = score['regime_classification']
            print(f"   {date}: {total:.1f} ({classification})")
    
    # Upcoming events
    upcoming_events = dashboard.get('upcoming_events', [])
    if upcoming_events:
        print(f"\n📅 Upcoming Economic Events:")
        for event in upcoming_events[:5]:  # Show next 5
            date = event['date']
            name = event['event_name']
            impact = event['impact']
            country = event['country']
            print(f"   {date}: {name} ({country}) - {impact} Impact")
    
    print(f"\n⏰ Generated: {dashboard.get('generated_at', 'Unknown')}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SQLite Agent CLI for MacroIntel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sqlite_cli.py sync
  python sqlite_cli.py sync --symbols "SPY,QQQ,MCL=F"
  python sqlite_cli.py query "What is the latest SPY price?"
  python sqlite_cli.py stats
  python sqlite_cli.py dashboard
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Synchronize data from external sources')
    sync_parser.add_argument('--symbols', help='Comma-separated list of symbols to sync')
    sync_parser.set_defaults(func=handle_sync)
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Execute natural language query')
    query_parser.add_argument('query', help='Natural language query string')
    query_parser.set_defaults(func=handle_query)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.set_defaults(func=handle_stats)
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Show analytics dashboard')
    dashboard_parser.set_defaults(func=handle_dashboard)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 