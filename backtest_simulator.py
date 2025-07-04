#!/usr/bin/env python3
"""
MacroIntel Backtest Simulator

A tool for simulating strategy performance based on past regime conditions
logged in the regime_scores table of the SQLite database.
"""

import argparse
import sys
import csv
import logging
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from tabulate import tabulate
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import data store functions
try:
    from data_store import MacroIntelDataStore
    DATA_STORE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing data store: {e}")
    print("Make sure you're running this from the MacroIntel project root directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BacktestSimulator:
    """Simulator for backtesting strategies based on regime conditions."""
    
    def __init__(self):
        """Initialize the backtest simulator."""
        self.output_dir = project_root / "output"
        self.output_dir.mkdir(exist_ok=True)
        self.data_store = MacroIntelDataStore()
    
    def parse_component_filters(self, components_str: str) -> Dict[str, float]:
        """
        Parse component filters from comma-separated string.
        
        Args:
            components_str: String like "volatility>70,structure>60"
            
        Returns:
            Dictionary of component filters
        """
        filters = {}
        if not components_str:
            return filters
        
        for component_filter in components_str.split(','):
            component_filter = component_filter.strip()
            if '>' in component_filter:
                component, threshold = component_filter.split('>')
                filters[component.strip()] = float(threshold.strip())
            elif '<' in component_filter:
                component, threshold = component_filter.split('<')
                filters[component.strip()] = -float(threshold.strip())  # Negative for <
            elif '=' in component_filter:
                component, threshold = component_filter.split('=')
                filters[component.strip()] = float(threshold.strip())
        
        return filters
    
    def query_regime_matches(self, strategy: str, min_score: float, 
                           start_date: str, end_date: str, 
                           component_filters: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Query regime scores table for matching records.
        
        Args:
            strategy: Strategy name to match
            min_score: Minimum total score threshold
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            component_filters: Component score filters
            
        Returns:
            List of matching regime records
        """
        try:
            with self.data_store.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build the base query
                query = """
                    SELECT timestamp, total_score, volatility, structure, momentum, 
                           breadth, institutional, strategy, instrument
                    FROM regime_scores 
                    WHERE strategy = ? 
                    AND total_score >= ?
                    AND date(timestamp) >= ?
                    AND date(timestamp) <= ?
                """
                params = [strategy, min_score, start_date, end_date]
                
                # Add component filters
                for component, threshold in component_filters.items():
                    if threshold < 0:  # Less than filter
                        query += f" AND {component} < ?"
                        params.append(abs(threshold))
                    elif threshold > 0:  # Greater than filter
                        query += f" AND {component} > ?"
                        params.append(threshold)
                    else:  # Equal filter
                        query += f" AND {component} = ?"
                        params.append(threshold)
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                matches = []
                for row in results:
                    matches.append({
                        'timestamp': row[0],
                        'total_score': row[1],
                        'volatility': row[2],
                        'structure': row[3],
                        'momentum': row[4],
                        'breadth': row[5],
                        'institutional': row[6],
                        'strategy': row[7],
                        'instrument': row[8]
                    })
                
                return matches
                
        except Exception as e:
            logger.error(f"❌ Error querying regime matches: {e}")
            raise
    
    def calculate_statistics(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for the regime matches.
        
        Args:
            matches: List of regime match records
            
        Returns:
            Dictionary with calculated statistics
        """
        if not matches:
            return {
                'count': 0,
                'avg_total_score': 0,
                'min_total_score': 0,
                'max_total_score': 0,
                'component_stats': {},
                'instrument_distribution': {},
                'date_range': {'start': None, 'end': None}
            }
        
        # Basic stats
        total_scores = [match['total_score'] for match in matches]
        avg_total_score = statistics.mean(total_scores)
        min_total_score = min(total_scores)
        max_total_score = max(total_scores)
        
        # Component statistics
        components = ['volatility', 'structure', 'momentum', 'breadth', 'institutional']
        component_stats = {}
        
        for component in components:
            values = [match[component] for match in matches]
            component_stats[component] = {
                'min': min(values),
                'avg': statistics.mean(values),
                'max': max(values),
                'std': statistics.stdev(values) if len(values) > 1 else 0
            }
        
        # Instrument distribution
        instrument_counts = {}
        for match in matches:
            instrument = match['instrument']
            instrument_counts[instrument] = instrument_counts.get(instrument, 0) + 1
        
        # Date range
        timestamps = [match['timestamp'] for match in matches]
        date_range = {
            'start': min(timestamps),
            'end': max(timestamps)
        }
        
        return {
            'count': len(matches),
            'avg_total_score': avg_total_score,
            'min_total_score': min_total_score,
            'max_total_score': max_total_score,
            'component_stats': component_stats,
            'instrument_distribution': instrument_counts,
            'date_range': date_range
        }
    
    def display_summary(self, stats: Dict[str, Any], strategy: str, 
                       min_score: float, start_date: str, end_date: str) -> None:
        """
        Display summary statistics.
        
        Args:
            stats: Calculated statistics
            strategy: Strategy name
            min_score: Minimum score threshold
            start_date: Start date
            end_date: End date
        """
        print(f"\n🎯 BACKTEST SUMMARY")
        print(f"   Strategy: {strategy}")
        print(f"   Date Range: {start_date} to {end_date}")
        print(f"   Min Score Threshold: {min_score}")
        print(f"   Regime Matches: {stats['count']}")
        
        if stats['count'] > 0:
            print(f"   Total Score Range: {stats['min_total_score']:.1f} - {stats['max_total_score']:.1f}")
            print(f"   Average Total Score: {stats['avg_total_score']:.1f}")
            
            print(f"\n📊 COMPONENT BREAKDOWN:")
            for component, comp_stats in stats['component_stats'].items():
                print(f"   {component.title()}:")
                print(f"     • Min: {comp_stats['min']:.1f}")
                print(f"     • Avg: {comp_stats['avg']:.1f}")
                print(f"     • Max: {comp_stats['max']:.1f}")
                print(f"     • Std Dev: {comp_stats['std']:.1f}")
            
            print(f"\n🎲 INSTRUMENT DISTRIBUTION:")
            for instrument, count in stats['instrument_distribution'].items():
                percentage = (count / stats['count']) * 100
                print(f"   {instrument}: {count} ({percentage:.1f}%)")
            
            print(f"\n📅 DATE RANGE:")
            print(f"   First Match: {stats['date_range']['start']}")
            print(f"   Last Match: {stats['date_range']['end']}")
        else:
            print("   No regime matches found for the specified criteria.")
    
    def display_detailed_results(self, matches: List[Dict[str, Any]], stats: Dict[str, Any]) -> None:
        """
        Display detailed results in table format.
        
        Args:
            matches: List of regime matches
            stats: Calculated statistics
        """
        if not matches:
            print("❌ No matches to display.")
            return
        
        # Prepare table data
        table_data = []
        for match in matches:
            table_data.append([
                match['timestamp'][:19],  # Truncate timestamp
                f"{match['total_score']:.1f}",
                f"{match['volatility']:.1f}",
                f"{match['structure']:.1f}",
                f"{match['momentum']:.1f}",
                f"{match['breadth']:.1f}",
                f"{match['institutional']:.1f}",
                match['instrument']
            ])
        
        # Display table
        headers = ["Timestamp", "Total Score", "Volatility", "Structure", "Momentum", "Breadth", "Institutional", "Instrument"]
        print(f"\n📋 DETAILED RESULTS ({len(matches)} matches):")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Display summary stats
        self.display_summary(stats, "", 0, "", "")
    
    def export_to_csv(self, matches: List[Dict[str, Any]], stats: Dict[str, Any], 
                     strategy: str, min_score: float, start_date: str, end_date: str) -> None:
        """
        Export results to CSV file.
        
        Args:
            matches: List of regime matches
            stats: Calculated statistics
            strategy: Strategy name
            min_score: Minimum score threshold
            start_date: Start date
            end_date: End date
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_{strategy.replace(' ', '_')}_{start_date}_{end_date}_{timestamp}.csv"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header with metadata
                writer.writerow(["MacroIntel Backtest Results"])
                writer.writerow([f"Strategy: {strategy}"])
                writer.writerow([f"Date Range: {start_date} to {end_date}"])
                writer.writerow([f"Min Score Threshold: {min_score}"])
                writer.writerow([f"Total Matches: {stats['count']}"])
                writer.writerow([f"Average Total Score: {stats['avg_total_score']:.1f}"])
                writer.writerow([])
                
                # Write detailed data
                if matches:
                    headers = ["Timestamp", "Total Score", "Volatility", "Structure", "Momentum", "Breadth", "Institutional", "Strategy", "Instrument"]
                    writer.writerow(headers)
                    
                    for match in matches:
                        writer.writerow([
                            match['timestamp'],
                            match['total_score'],
                            match['volatility'],
                            match['structure'],
                            match['momentum'],
                            match['breadth'],
                            match['institutional'],
                            match['strategy'],
                            match['instrument']
                        ])
                    
                    writer.writerow([])
                    writer.writerow(["Component Statistics"])
                    writer.writerow(["Component", "Min", "Average", "Max", "Std Dev"])
                    
                    for component, comp_stats in stats['component_stats'].items():
                        writer.writerow([
                            component.title(),
                            comp_stats['min'],
                            comp_stats['avg'],
                            comp_stats['max'],
                            comp_stats['std']
                        ])
                    
                    writer.writerow([])
                    writer.writerow(["Instrument Distribution"])
                    writer.writerow(["Instrument", "Count", "Percentage"])
                    
                    for instrument, count in stats['instrument_distribution'].items():
                        percentage = (count / stats['count']) * 100
                        writer.writerow([instrument, count, f"{percentage:.1f}%"])
            
            print(f"💾 Results exported to: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error exporting to CSV: {e}")
            print(f"❌ Error exporting to CSV: {e}")
    
    def run_backtest(self, strategy: str, min_score: float, start_date: str, 
                    end_date: str, component_filters: Dict[str, float], 
                    summary_only: bool = False, export_csv: bool = False) -> None:
        """
        Run the backtest simulation.
        
        Args:
            strategy: Strategy name to match
            min_score: Minimum total score threshold
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            component_filters: Component score filters
            summary_only: Whether to show summary only
            export_csv: Whether to export results to CSV
        """
        try:
            print(f"🚀 Starting backtest simulation...")
            print(f"   Strategy: {strategy}")
            print(f"   Min Score: {min_score}")
            print(f"   Date Range: {start_date} to {end_date}")
            
            if component_filters:
                print(f"   Component Filters: {component_filters}")
            
            # Query for matches
            matches = self.query_regime_matches(strategy, min_score, start_date, end_date, component_filters)
            
            # Calculate statistics
            stats = self.calculate_statistics(matches)
            
            # Display results
            if summary_only:
                self.display_summary(stats, strategy, min_score, start_date, end_date)
            else:
                self.display_detailed_results(matches, stats)
            
            # Export to CSV if requested
            if export_csv:
                self.export_to_csv(matches, stats, strategy, min_score, start_date, end_date)
            
            print(f"\n✅ Backtest simulation completed!")
            
        except Exception as e:
            logger.error(f"❌ Error in backtest simulation: {e}")
            print(f"❌ Error: {e}")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="MacroIntel Backtest Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backtest_simulator.py --strategy "Tier 1 Reversal" --min_score 70 --start 2024-01-01 --end 2024-01-31
  python backtest_simulator.py --strategy "Tier 2 Momentum" --min_score 80 --start 2024-01-01 --end 2024-01-31 --components "volatility>70,structure>60"
  python backtest_simulator.py --strategy "Tier 3 Range Trading" --min_score 50 --start 2024-01-01 --end 2024-01-31 --summary --export
        """
    )
    
    # Required arguments
    parser.add_argument('--strategy', type=str, required=True, 
                       help='Strategy name to match (e.g., "Tier 1 Reversal", "Tier 2 Momentum")')
    parser.add_argument('--min_score', type=float, required=True,
                       help='Minimum regime score threshold (0-100)')
    parser.add_argument('--start', type=str, required=True,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True,
                       help='End date (YYYY-MM-DD)')
    
    # Optional arguments
    parser.add_argument('--components', type=str, default='',
                       help='Component filters (e.g., "volatility>70,structure>60")')
    parser.add_argument('--summary', action='store_true',
                       help='Show summary statistics only')
    parser.add_argument('--export', action='store_true',
                       help='Export results to CSV file')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.min_score < 0 or args.min_score > 100:
        print("❌ Error: min_score must be between 0 and 100")
        sys.exit(1)
    
    try:
        datetime.strptime(args.start, "%Y-%m-%d")
        datetime.strptime(args.end, "%Y-%m-%d")
    except ValueError:
        print("❌ Error: start and end dates must be in YYYY-MM-DD format")
        sys.exit(1)
    
    if args.start > args.end:
        print("❌ Error: start date must be before end date")
        sys.exit(1)
    
    # Initialize simulator
    simulator = BacktestSimulator()
    
    # Parse component filters
    component_filters = simulator.parse_component_filters(args.components)
    
    # Run backtest
    try:
        simulator.run_backtest(
            strategy=args.strategy,
            min_score=args.min_score,
            start_date=args.start,
            end_date=args.end,
            component_filters=component_filters,
            summary_only=args.summary,
            export_csv=args.export
        )
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Backtest interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 