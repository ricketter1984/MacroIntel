#!/usr/bin/env python3
"""
CME Forex Futures Data Fetcher and Heatmap Generator

This module fetches 5-day performance data for major CME forex futures contracts
and generates a styled heatmap visualization showing:
- Currency pair symbols
- 5-day percent change
- Volatility rankings
- Volume metrics

Supported contracts:
- 6E=F (EUR/USD)
- 6J=F (JPY/USD) 
- 6B=F (GBP/USD)
- 6A=F (AUD/USD)
- 6C=F (CAD/USD)
- 6S=F (CHF/USD)
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime, timedelta
from pathlib import Path
import logging
import warnings

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
warnings.filterwarnings('ignore', category=FutureWarning, module='yfinance')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CMEForexFetcher:
    """CME Forex Futures data fetcher and visualizer."""
    
    def __init__(self):
        """Initialize the CME Forex Fetcher."""
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # CME Forex futures contracts
        self.forex_contracts = {
            '6E=F': {
                'name': 'EUR/USD',
                'description': 'Euro Futures',
                'multiplier': 125000
            },
            '6J=F': {
                'name': 'JPY/USD', 
                'description': 'Japanese Yen Futures',
                'multiplier': 12500000
            },
            '6B=F': {
                'name': 'GBP/USD',
                'description': 'British Pound Futures', 
                'multiplier': 62500
            },
            '6A=F': {
                'name': 'AUD/USD',
                'description': 'Australian Dollar Futures',
                'multiplier': 100000
            },
            '6C=F': {
                'name': 'CAD/USD',
                'description': 'Canadian Dollar Futures',
                'multiplier': 100000
            },
            '6S=F': {
                'name': 'CHF/USD',
                'description': 'Swiss Franc Futures',
                'multiplier': 125000
            }
        }
        
        logger.info(f"🏦 CME Forex Fetcher initialized for {len(self.forex_contracts)} contracts")
        logger.info(f"📁 Output directory: {os.path.abspath(self.output_dir)}")
    
    def fetch_forex_data(self):
        """
        Fetch 5-day performance data for all CME forex futures.
        
        Returns:
            Dict containing forex data with performance metrics
        """
        logger.info("📈 Fetching CME forex futures data...")
        
        forex_data = {}
        
        for symbol, contract_info in self.forex_contracts.items():
            try:
                logger.info(f"📊 Fetching {contract_info['name']} ({symbol})...")
                
                # Fetch data using yfinance
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="7d", interval="1d")  # Get extra days to ensure 5 trading days
                
                if not hist.empty and len(hist) >= 2:
                    # Calculate 5-day performance metrics
                    start_price = float(hist['Close'].iloc[0])
                    end_price = float(hist['Close'].iloc[-1])
                    pct_change_5d = ((end_price - start_price) / start_price) * 100
                    
                    # Calculate volatility (daily returns standard deviation)
                    returns = hist['Close'].pct_change().dropna()
                    daily_volatility = returns.std() * 100
                    
                    # Calculate average volume
                    avg_volume = hist['Volume'].mean() if 'Volume' in hist.columns else 0
                    
                    # Get high/low for the period
                    period_high = float(hist['High'].max())
                    period_low = float(hist['Low'].min())
                    price_range = ((period_high - period_low) / start_price) * 100
                    
                    forex_data[symbol] = {
                        'name': contract_info['name'],
                        'description': contract_info['description'],
                        'pct_change_5d': pct_change_5d,
                        'daily_volatility': daily_volatility,
                        'avg_volume': avg_volume,
                        'current_price': end_price,
                        'start_price': start_price,
                        'period_high': period_high,
                        'period_low': period_low,
                        'price_range': price_range,
                        'data_points': len(hist),
                        'source': 'yfinance'
                    }
                    
                    logger.info(f"✅ {contract_info['name']}: {pct_change_5d:+.2f}% (Vol: {daily_volatility:.2f}%)")
                    
                else:
                    logger.warning(f"⚠️ Insufficient data for {symbol}")
                    
            except Exception as e:
                logger.error(f"❌ Error fetching {symbol}: {str(e)}")
                continue
        
        if forex_data:
            # Calculate volatility rankings
            volatilities = [data['daily_volatility'] for data in forex_data.values()]
            vol_ranks = self._calculate_rankings(volatilities)
            
            # Add volatility rankings to data
            for i, symbol in enumerate(forex_data.keys()):
                forex_data[symbol]['volatility_rank'] = vol_ranks[i]
                
            logger.info(f"✅ Successfully fetched data for {len(forex_data)}/{len(self.forex_contracts)} forex contracts")
        else:
            logger.error("❌ No forex data could be fetched")
            
        return forex_data
    
    def _calculate_rankings(self, values):
        """Calculate rankings for a list of values (1 = highest)."""
        if not values:
            return []
            
        # Sort indices by values in descending order
        sorted_indices = np.argsort(values)[::-1]
        ranks = [0] * len(values)
        
        for rank, idx in enumerate(sorted_indices):
            ranks[idx] = rank + 1
            
        return ranks
    
    def generate_forex_heatmap(self, forex_data, output_filename="cme_fx_heatmap.png"):
        """
        Generate a heatmap-style visualization for CME forex futures.
        
        Args:
            forex_data: Dict containing forex performance data
            output_filename: Output filename for the chart
            
        Returns:
            Path to saved chart file or None if failed
        """
        if not forex_data:
            logger.error("❌ No forex data to visualize")
            return None
            
        logger.info(f"📊 Generating CME forex heatmap with {len(forex_data)} contracts...")
        
        try:
            # Prepare data for visualization
            symbols = list(forex_data.keys())
            pair_names = [forex_data[symbol]['name'] for symbol in symbols]
            pct_changes = [forex_data[symbol]['pct_change_5d'] for symbol in symbols]
            volatilities = [forex_data[symbol]['daily_volatility'] for symbol in symbols]
            vol_ranks = [forex_data[symbol]['volatility_rank'] for symbol in symbols]
            current_prices = [forex_data[symbol]['current_price'] for symbol in symbols]
            
            # Create figure with custom layout
            fig = plt.figure(figsize=(14, 10))
            
            # Main title
            fig.suptitle('CME Forex Futures - 5-Day Performance Heatmap', 
                        fontsize=18, fontweight='bold', y=0.95)
            
            # Create grid layout: heatmap on left, metrics on right
            gs = fig.add_gridspec(2, 2, width_ratios=[2, 1], height_ratios=[3, 1], 
                                hspace=0.3, wspace=0.3)
            
            # Main heatmap (top left)
            ax_heatmap = fig.add_subplot(gs[0, 0])
            self._create_performance_heatmap(ax_heatmap, symbols, pair_names, pct_changes)
            
            # Volatility ranking (top right)
            ax_vol = fig.add_subplot(gs[0, 1])
            self._create_volatility_ranking(ax_vol, pair_names, volatilities, vol_ranks)
            
            # Summary table (bottom, spanning both columns)
            ax_table = fig.add_subplot(gs[1, :])
            self._create_summary_table(ax_table, forex_data, symbols)
            
            # Add timestamp and data source
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
            fig.text(0.02, 0.02, f"Generated: {timestamp} | Source: yfinance (CME Futures)", 
                    fontsize=8, alpha=0.7)
            fig.text(0.98, 0.02, f"Contracts: {len(forex_data)}/6 active", 
                    fontsize=8, alpha=0.7, ha='right')
            
            # Save the chart
            output_path = os.path.join(self.output_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            logger.info(f"✅ CME forex heatmap saved to {output_path} ({file_size:,} bytes)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error generating forex heatmap: {str(e)}")
            return None
    
    def _create_performance_heatmap(self, ax, symbols, pair_names, pct_changes):
        """Create the main performance heatmap."""
        # Create heatmap data
        n_pairs = len(symbols)
        heatmap_data = np.array(pct_changes).reshape(1, n_pairs)
        
        # Color mapping: red for negative, green for positive
        vmin, vmax = min(pct_changes), max(pct_changes)
        abs_max = max(abs(vmin), abs(vmax))
        
        # Create heatmap
        im = ax.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', 
                      vmin=-abs_max, vmax=abs_max)
        
        # Customize appearance
        ax.set_xticks(range(n_pairs))
        ax.set_xticklabels(pair_names, rotation=45, ha='right')
        ax.set_yticks([])
        ax.set_title('5-Day Performance (%)', fontweight='bold', pad=20)
        
        # Add percentage labels on heatmap
        for i in range(n_pairs):
            color = 'white' if abs(pct_changes[i]) > abs_max * 0.5 else 'black'
            ax.text(i, 0, f'{pct_changes[i]:+.2f}%', 
                   ha='center', va='center', fontweight='bold', 
                   fontsize=12, color=color)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.1, shrink=0.8)
        cbar.set_label('5-Day % Change', fontweight='bold')
    
    def _create_volatility_ranking(self, ax, pair_names, volatilities, vol_ranks):
        """Create volatility ranking chart."""
        # Create horizontal bar chart
        y_pos = np.arange(len(pair_names))
        colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(pair_names)))
        
        bars = ax.barh(y_pos, volatilities, color=colors, alpha=0.8, edgecolor='black')
        
        # Customize appearance
        ax.set_yticks(y_pos)
        ax.set_yticklabels(pair_names)
        ax.set_xlabel('Daily Volatility (%)')
        ax.set_title('Volatility Ranking', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add volatility values and rankings
        for i, (bar, vol, rank) in enumerate(zip(bars, volatilities, vol_ranks)):
            width = bar.get_width()
            ax.text(width + 0.01, bar.get_y() + bar.get_height()/2, 
                   f'{vol:.2f}% (#{rank})', va='center', fontsize=10, fontweight='bold')
        
        ax.invert_yaxis()  # Highest volatility at top
    
    def _create_summary_table(self, ax, forex_data, symbols):
        """Create summary table with key metrics."""
        ax.axis('off')
        
        # Prepare table data
        table_data = []
        headers = ['Pair', 'Symbol', '5-Day %', 'Current Price', 'Vol Rank', 'Daily Vol %']
        
        for symbol in symbols:
            data = forex_data[symbol]
            table_data.append([
                data['name'],
                symbol.replace('=F', ''),
                f"{data['pct_change_5d']:+.2f}%",
                f"${data['current_price']:.4f}",
                f"#{data['volatility_rank']}",
                f"{data['daily_volatility']:.2f}%"
            ])
        
        # Create table
        table = ax.table(cellText=table_data, colLabels=headers, 
                        cellLoc='center', loc='center',
                        colWidths=[0.15, 0.12, 0.12, 0.18, 0.12, 0.12])
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        
        # Color header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#2c3e50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Color data rows based on performance
        for i, symbol in enumerate(symbols):
            pct_change = forex_data[symbol]['pct_change_5d']
            row_color = '#d4edda' if pct_change > 0 else '#f8d7da' if pct_change < 0 else '#e2e3e5'
            
            for j in range(len(headers)):
                table[(i + 1, j)].set_facecolor(row_color)
        
        ax.set_title('Summary Statistics', fontweight='bold', pad=20)
    
    def save_forex_data(self, forex_data, filename="cme_forex_data.json"):
        """
        Save forex data to JSON file for later use.
        
        Args:
            forex_data: Dict containing forex data
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        try:
            output_path = os.path.join(self.output_dir, filename)
            
            # Add timestamp to data
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'data_source': 'yfinance',
                'contracts_fetched': len(forex_data),
                'forex_data': forex_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ Forex data saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error saving forex data: {str(e)}")
            return None

def generate_cme_forex_heatmap():
    """
    Main function to generate CME forex heatmap.
    
    Returns:
        Path to generated heatmap file or None if failed
    """
    try:
        logger.info("🏦 Starting CME Forex Futures analysis...")
        
        # Initialize fetcher
        fetcher = CMEForexFetcher()
        
        # Fetch forex data
        forex_data = fetcher.fetch_forex_data()
        
        if not forex_data:
            logger.error("❌ No forex data available for heatmap generation")
            return None
        
        # Save data to JSON
        fetcher.save_forex_data(forex_data)
        
        # Generate heatmap
        heatmap_path = fetcher.generate_forex_heatmap(forex_data)
        
        if heatmap_path:
            logger.info("✅ CME forex heatmap generation completed successfully")
            
            # Log summary
            logger.info("📊 CME Forex Summary:")
            for symbol, data in forex_data.items():
                status = "📈" if data['pct_change_5d'] > 0 else "📉" if data['pct_change_5d'] < 0 else "➡️"
                logger.info(f"   {status} {data['name']}: {data['pct_change_5d']:+.2f}% (Rank #{data['volatility_rank']})")
        
        return heatmap_path
        
    except Exception as e:
        logger.error(f"❌ Error in CME forex heatmap generation: {str(e)}")
        return None

if __name__ == "__main__":
    """Test the CME forex fetcher."""
    print("🚀 Testing CME Forex Futures Fetcher...")
    
    heatmap_path = generate_cme_forex_heatmap()
    
    if heatmap_path:
        print(f"✅ Test completed successfully!")
        print(f"📊 Heatmap saved to: {heatmap_path}")
    else:
        print("❌ Test failed - check logs for details") 