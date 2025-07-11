#!/usr/bin/env python3
"""
Economic Calendar Tracker
Fetches macroeconomic events from FMP API and creates timeline visualizations
"""

import os
import json
import logging
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np

class EconomicCalendarTracker:
    """
    Tracks macroeconomic events and creates timeline visualizations with trade overlays.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the Economic Calendar Tracker.
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = output_dir
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.logger = self._setup_logger()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Event importance mapping
        self.importance_colors = {
            'High': '#e74c3c',      # Red
            'Medium': '#f39c12',    # Orange  
            'Low': '#3498db'        # Blue
        }
        
        # Trade type colors
        self.trade_colors = {
            'BUY': '#27ae60',       # Green
            'SELL': '#e74c3c',      # Red
            'CLOSE': '#95a5a6'      # Gray
        }
        
        self.logger.info("📅 Economic Calendar Tracker initialized")
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the calendar tracker."""
        logger = logging.getLogger('calendar_tracker')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def fetch_economic_events(self, days_back: int = 3, days_forward: int = 7) -> List[Dict]:
        """
        Fetch economic events from FMP Calendar API.
        
        Args:
            days_back: Number of days to look back for recent events
            days_forward: Number of days to look forward for upcoming events
            
        Returns:
            List of economic event dictionaries
        """
        if not self.fmp_api_key:
            self.logger.warning("⚠️ FMP API key not found - using simulated data")
            return self._generate_sample_events(days_back, days_forward)
        
        try:
            events = []
            today = datetime.now()
            
            # Fetch historical events (last 3 days)
            start_date = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
            
            self.logger.info(f"📈 Fetching historical events from {start_date} to {end_date}")
            historical_events = self._fetch_events_for_period(start_date, end_date)
            events.extend(historical_events)
            
            # Fetch upcoming events (next 7 days)
            start_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=days_forward)).strftime('%Y-%m-%d')
            
            self.logger.info(f"📅 Fetching upcoming events from {start_date} to {end_date}")
            upcoming_events = self._fetch_events_for_period(start_date, end_date)
            events.extend(upcoming_events)
            
            # Process and standardize events
            processed_events = self._process_events(events)
            
            self.logger.info(f"✅ Fetched {len(processed_events)} total economic events")
            return processed_events
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching economic events: {str(e)}")
            return self._generate_sample_events(days_back, days_forward)
    
    def _fetch_events_for_period(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch events for a specific date range from FMP API."""
        try:
            url = f"https://financialmodelingprep.com/api/v3/economic_calendar"
            params = {
                'from': start_date,
                'to': end_date,
                'apikey': self.fmp_api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list):
                self.logger.info(f"📊 Retrieved {len(data)} events for {start_date} to {end_date}")
                return data
            else:
                self.logger.warning(f"⚠️ Unexpected response format for {start_date} to {end_date}")
                return []
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API request failed for {start_date} to {end_date}: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error processing API response: {str(e)}")
            return []
    
    def _process_events(self, raw_events: List[Dict]) -> List[Dict]:
        """Process and standardize economic events."""
        processed_events = []
        
        for event in raw_events:
            try:
                # Parse date
                event_date = event.get('date', '')
                if not event_date:
                    continue
                    
                # Parse datetime - handle different formats
                try:
                    # Try full timestamp format first
                    if 'T' in event_date or ' ' in event_date:
                        # Handle ISO format or space-separated format
                        event_date_clean = event_date.split('T')[0].split(' ')[0]
                        parsed_date = datetime.strptime(event_date_clean, '%Y-%m-%d')
                    else:
                        # Handle date-only format
                        parsed_date = datetime.strptime(event_date, '%Y-%m-%d')
                except ValueError:
                    # Fallback - try to extract just the date part
                    import re
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', event_date)
                    if date_match:
                        parsed_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    else:
                        continue
                
                # Determine importance
                impact = event.get('impact', 'Low')
                if impact in ['High', 'Medium', 'Low']:
                    importance = impact
                else:
                    importance = 'Low'
                
                # Extract relevant fields
                processed_event = {
                    'date': parsed_date,
                    'time': event.get('time', ''),
                    'country': event.get('country', 'Unknown'),
                    'event': event.get('event', 'Economic Event'),
                    'currency': event.get('currency', ''),
                    'importance': importance,
                    'actual': event.get('actual', ''),
                    'estimate': event.get('estimate', ''),
                    'previous': event.get('previous', ''),
                    'change': event.get('change', ''),
                    'change_percentage': event.get('changePercentage', ''),
                    'unit': event.get('unit', ''),
                    'source': 'FMP'
                }
                
                processed_events.append(processed_event)
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error processing event: {str(e)}")
                continue
        
        # Sort by date
        processed_events.sort(key=lambda x: x['date'])
        
        return processed_events
    
    def _generate_sample_events(self, days_back: int, days_forward: int) -> List[Dict]:
        """Generate sample economic events for testing."""
        self.logger.info("📝 Generating sample economic events...")
        
        sample_events = []
        today = datetime.now()
        
        # Historical events
        historical_events = [
            {'days_offset': -2, 'event': 'US CPI Data Release', 'importance': 'High', 'country': 'US'},
            {'days_offset': -1, 'event': 'ECB Interest Rate Decision', 'importance': 'High', 'country': 'EU'},
            {'days_offset': 0, 'event': 'US Jobless Claims', 'importance': 'Medium', 'country': 'US'},
        ]
        
        # Upcoming events
        upcoming_events = [
            {'days_offset': 1, 'event': 'Fed FOMC Meeting', 'importance': 'High', 'country': 'US'},
            {'days_offset': 2, 'event': 'UK GDP Release', 'importance': 'Medium', 'country': 'UK'},
            {'days_offset': 3, 'event': 'US Retail Sales', 'importance': 'Medium', 'country': 'US'},
            {'days_offset': 4, 'event': 'Japan BOJ Decision', 'importance': 'High', 'country': 'JP'},
            {'days_offset': 5, 'event': 'US PMI Data', 'importance': 'Low', 'country': 'US'},
            {'days_offset': 6, 'event': 'EU Inflation Data', 'importance': 'Medium', 'country': 'EU'},
            {'days_offset': 7, 'event': 'China Trade Balance', 'importance': 'Medium', 'country': 'CN'},
        ]
        
        all_events = historical_events + upcoming_events
        
        for event_template in all_events:
            event_date = today + timedelta(days=event_template['days_offset'])
            
            sample_event = {
                'date': event_date,
                'time': '14:30' if event_template['importance'] == 'High' else '10:00',
                'country': event_template['country'],
                'event': event_template['event'],
                'currency': 'USD' if event_template['country'] == 'US' else 'EUR',
                'importance': event_template['importance'],
                'actual': '',
                'estimate': '',
                'previous': '',
                'change': '',
                'change_percentage': '',
                'unit': '',
                'source': 'Sample'
            }
            
            sample_events.append(sample_event)
        
        return sample_events
    
    def load_trade_log(self, trade_log_path: str = "logs/trade_log.json") -> List[Dict]:
        """
        Load user trade entries from local JSON file.
        
        Args:
            trade_log_path: Path to trade log JSON file
            
        Returns:
            List of trade dictionaries
        """
        try:
            if os.path.exists(trade_log_path):
                with open(trade_log_path, 'r') as f:
                    trades = json.load(f)
                    
                # Process trade dates
                processed_trades = []
                for trade in trades:
                    try:
                        # Parse trade date
                        trade_date_str = trade.get('date', trade.get('timestamp', ''))
                        if trade_date_str:
                            # Handle different date formats
                            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                                try:
                                    trade_date = datetime.strptime(trade_date_str.split('T')[0], '%Y-%m-%d')
                                    break
                                except ValueError:
                                    continue
                            else:
                                continue
                            
                            processed_trade = {
                                'date': trade_date,
                                'type': trade.get('type', trade.get('action', 'BUY')).upper(),
                                'symbol': trade.get('symbol', trade.get('ticker', 'Unknown')),
                                'quantity': trade.get('quantity', trade.get('size', 0)),
                                'price': trade.get('price', 0),
                                'description': trade.get('description', f"{trade.get('type', 'Trade')} {trade.get('symbol', '')}")
                            }
                            
                            processed_trades.append(processed_trade)
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error processing trade entry: {str(e)}")
                        continue
                
                self.logger.info(f"📊 Loaded {len(processed_trades)} trade entries from {trade_log_path}")
                return processed_trades
            else:
                self.logger.info(f"📝 No trade log found at {trade_log_path}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Error loading trade log: {str(e)}")
            return []
    
    def create_timeline_visualization(self, events: List[Dict], trades: List[Dict] = None, 
                                    output_filename: str = "economic_calendar_timeline.png") -> str:
        """
        Create horizontal timeline visualization of economic events and trades.
        
        Args:
            events: List of economic events
            trades: List of trade entries (optional)
            output_filename: Name of output file
            
        Returns:
            Path to saved visualization file
        """
        try:
            self.logger.info(f"📊 Creating timeline visualization with {len(events)} events...")
            
            if not events:
                self.logger.warning("⚠️ No events to visualize")
                return None
            
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(16, 10))
            
            # Prepare data
            event_dates = [event['date'] for event in events]
            min_date = min(event_dates) - timedelta(days=1)
            max_date = max(event_dates) + timedelta(days=1)
            
            # Set up timeline
            ax.set_xlim(min_date, max_date)
            ax.set_ylim(-1, 6)
            
            # Draw main timeline
            ax.axhline(y=0, color='black', linewidth=2, alpha=0.8)
            
            # Plot economic events
            self._plot_economic_events(ax, events)
            
            # Plot trades if provided
            if trades:
                self._plot_trades(ax, trades, min_date, max_date)
            
            # Format the chart
            self._format_timeline_chart(ax, fig, min_date, max_date)
            
            # Add legend
            self._add_timeline_legend(ax, bool(trades))
            
            # Save chart
            output_path = os.path.join(self.output_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            self.logger.info(f"✅ Timeline visualization saved to {output_path} ({file_size:,} bytes)")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ Error creating timeline visualization: {str(e)}")
            return None
    
    def _plot_economic_events(self, ax, events: List[Dict]):
        """Plot economic events on the timeline."""
        importance_levels = {'High': 3, 'Medium': 2, 'Low': 1}
        
        for i, event in enumerate(events):
            date = event['date']
            importance = event['importance']
            y_pos = importance_levels.get(importance, 1)
            color = self.importance_colors.get(importance, '#3498db')
            
            # Plot event marker
            ax.scatter(date, y_pos, s=120, c=color, alpha=0.8, 
                      edgecolors='black', linewidth=1, zorder=3)
            
            # Add event label
            event_text = f"{event['country']}: {event['event'][:30]}{'...' if len(event['event']) > 30 else ''}"
            
            # Alternate label positions to avoid overlap
            label_offset = 0.3 if i % 2 == 0 else -0.3
            
            ax.annotate(event_text, (date, y_pos), 
                       xytext=(0, 30 + label_offset * 20), textcoords='offset points',
                       ha='center', va='bottom', fontsize=8, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    def _plot_trades(self, ax, trades: List[Dict], min_date: datetime, max_date: datetime):
        """Plot trade entries on the timeline."""
        trade_y_positions = {'BUY': -0.5, 'SELL': -0.7, 'CLOSE': -0.3}
        
        # Filter trades within date range
        relevant_trades = [trade for trade in trades 
                          if min_date <= trade['date'] <= max_date]
        
        if not relevant_trades:
            return
        
        for trade in relevant_trades:
            date = trade['date']
            trade_type = trade['type']
            y_pos = trade_y_positions.get(trade_type, -0.5)
            color = self.trade_colors.get(trade_type, '#95a5a6')
            
            # Plot trade marker
            marker = '^' if trade_type == 'BUY' else 'v' if trade_type == 'SELL' else 's'
            ax.scatter(date, y_pos, s=100, c=color, marker=marker, 
                      alpha=0.9, edgecolors='black', linewidth=1, zorder=4)
            
            # Add trade label
            trade_text = f"{trade_type}: {trade['symbol']}"
            if trade.get('quantity'):
                trade_text += f" ({trade['quantity']})"
            
            ax.annotate(trade_text, (date, y_pos),
                       xytext=(0, -25), textcoords='offset points',
                       ha='center', va='top', fontsize=7,
                       bbox=dict(boxstyle="round,pad=0.2", facecolor=color, alpha=0.6))
    
    def _format_timeline_chart(self, ax, fig, min_date: datetime, max_date: datetime):
        """Format the timeline chart appearance."""
        # Set title
        fig.suptitle('📅 This Week in Macro - Economic Calendar & Trade Timeline', 
                    fontsize=18, fontweight='bold', y=0.95)
        
        # Configure x-axis (dates)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
        
        # Rotate date labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Configure y-axis
        ax.set_yticks([3, 2, 1, 0, -0.3, -0.5, -0.7])
        ax.set_yticklabels(['High Impact', 'Medium Impact', 'Low Impact', 
                           'Timeline', 'Close Trades', 'Buy/Sell', 'Sell Trades'])
        
        # Add gridlines
        ax.grid(True, alpha=0.3, axis='x')
        ax.grid(True, alpha=0.2, axis='y')
        
        # Add importance level lines
        for level, y_pos in [('High', 3), ('Medium', 2), ('Low', 1)]:
            ax.axhline(y=y_pos, color=self.importance_colors.get(level), 
                      alpha=0.2, linewidth=1, linestyle='--')
        
        # Style the chart
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_alpha(0.3)
        ax.spines['bottom'].set_alpha(0.3)
        
        # Add today marker
        today = datetime.now()
        if min_date <= today <= max_date:
            ax.axvline(x=today, color='red', linewidth=2, alpha=0.7, linestyle='-')
            ax.text(today, 4, 'TODAY', ha='center', va='bottom', 
                   fontweight='bold', color='red', fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor='red'))
    
    def _add_timeline_legend(self, ax, has_trades: bool):
        """Add legend to the timeline chart."""
        legend_elements = []
        
        # Economic event importance
        for importance, color in self.importance_colors.items():
            legend_elements.append(plt.scatter([], [], c=color, s=100, alpha=0.8, 
                                             edgecolors='black', linewidth=1,
                                             label=f'{importance} Impact Event'))
        
        # Trade types if trades are present
        if has_trades:
            for trade_type, color in self.trade_colors.items():
                marker = '^' if trade_type == 'BUY' else 'v' if trade_type == 'SELL' else 's'
                legend_elements.append(plt.scatter([], [], c=color, s=80, alpha=0.9,
                                                 marker=marker, edgecolors='black', linewidth=1,
                                                 label=f'{trade_type} Trade'))
        
        # Position legend
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.02, 0.98),
                 frameon=True, fancybox=True, shadow=True, fontsize=9)
    
    def save_events_to_json(self, events: List[Dict], filename: str = "economic_events.json"):
        """Save events to JSON file for debugging/analysis."""
        try:
            output_path = os.path.join(self.output_dir, filename)
            
            # Convert datetime objects to strings for JSON serialization
            serializable_events = []
            for event in events:
                serializable_event = event.copy()
                serializable_event['date'] = event['date'].isoformat()
                serializable_events.append(serializable_event)
            
            with open(output_path, 'w') as f:
                json.dump(serializable_events, f, indent=2)
            
            self.logger.info(f"📄 Saved {len(events)} events to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ Error saving events to JSON: {str(e)}")
            return None
    
    def generate_calendar_timeline(self, trade_log_path: str = "logs/trade_log.json") -> Optional[str]:
        """
        Main function to generate the complete economic calendar timeline.
        
        Args:
            trade_log_path: Path to trade log JSON file
            
        Returns:
            Path to generated timeline visualization
        """
        try:
            self.logger.info("🚀 Starting economic calendar timeline generation...")
            
            # Fetch economic events
            events = self.fetch_economic_events(days_back=3, days_forward=7)
            
            if not events:
                self.logger.error("❌ No economic events found")
                return None
            
            # Load trade log if available
            trades = self.load_trade_log(trade_log_path)
            
            # Save events for debugging
            self.save_events_to_json(events)
            
            # Create timeline visualization
            timeline_path = self.create_timeline_visualization(events, trades)
            
            if timeline_path:
                self.logger.info("✅ Economic calendar timeline generation completed successfully")
                
                # Log summary
                self.logger.info("📊 Timeline Summary:")
                self.logger.info(f"   📅 Events: {len(events)}")
                self.logger.info(f"   📈 Trades: {len(trades) if trades else 0}")
                
                # Log event breakdown by importance
                importance_counts = {}
                for event in events:
                    imp = event['importance']
                    importance_counts[imp] = importance_counts.get(imp, 0) + 1
                
                for importance, count in importance_counts.items():
                    self.logger.info(f"   {importance} Impact: {count} events")
                
                return timeline_path
            else:
                self.logger.error("❌ Failed to create timeline visualization")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error generating calendar timeline: {str(e)}")
            return None

def generate_economic_calendar_timeline(trade_log_path: str = "logs/trade_log.json") -> Optional[str]:
    """
    Convenience function to generate economic calendar timeline.
    
    Args:
        trade_log_path: Path to trade log JSON file
        
    Returns:
        Path to generated timeline visualization
    """
    tracker = EconomicCalendarTracker()
    return tracker.generate_calendar_timeline(trade_log_path)

def main():
    """Test the Economic Calendar Tracker."""
    
    print("🧪 Testing Economic Calendar Tracker")
    print("=" * 50)
    
    # Initialize tracker
    tracker = EconomicCalendarTracker()
    
    # Generate timeline
    timeline_path = tracker.generate_calendar_timeline()
    
    if timeline_path:
        print(f"✅ SUCCESS: Timeline generated at {timeline_path}")
        
        # Check file size
        if os.path.exists(timeline_path):
            file_size = os.path.getsize(timeline_path)
            print(f"📏 File size: {file_size:,} bytes")
    else:
        print("❌ FAILED: Timeline generation failed")

if __name__ == "__main__":
    main() 