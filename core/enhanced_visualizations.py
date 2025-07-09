#!/usr/bin/env python3
"""
Enhanced Visualization Engine for MacroIntel

This module generates advanced visualizations including:
- VIX over time with volatility analysis
- Multi-asset comparison charts
- Economic calendar impact visualization
- Fear & Greed correlation analysis
- Market regime indicators
- Intelligent regime-aware charts with AI explanations
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import warnings
import logging
import requests
from typing import Dict, Any

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

# Load environment variables
load_dotenv(dotenv_path="config/.env")

class EnhancedVisualizations:
    def __init__(self):
        """Initialize the enhanced visualization engine."""
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8')
        
        # Color schemes
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }
        
        # Regime-aware instrument mapping
        self.regime_instruments = {
            'BULLISH': {
                'primary': 'SPY',
                'secondary': 'QQQ',
                'macro_indicators': ['VIX', 'OIL', 'GOLD'],
                'description': 'Risk-on environment favoring growth assets'
            },
            'NEUTRAL': {
                'primary': 'GLD',
                'secondary': 'TLT',
                'macro_indicators': ['VIX', 'OIL', 'USD'],
                'description': 'Balanced environment with defensive positioning'
            },
            'BEARISH': {
                'primary': 'VIX',
                'secondary': 'GLD',
                'macro_indicators': ['VIX', 'OIL', 'USD', 'GOLD'],
                'description': 'Risk-off environment with defensive assets'
            }
        }
        
        # Strategy-based chart types
        self.strategy_charts = {
            'Tier 1': 'momentum_breakout',
            'Tier 2': 'mean_reversion',
            'Tier 5': 'extreme_momentum'
        }
        
        self.logger.info("🎨 Enhanced Visualization Engine initialized")
        self.logger.info(f"📁 Output directory: {os.path.abspath(self.output_dir)}")
    
    def create_vix_analysis_chart(self, vix_data, output_filename="vix_analysis.png"):
        """Create comprehensive VIX analysis chart."""
        self.logger.info("📊 Creating VIX analysis chart...")
        
        # Validate input data
        if vix_data is None:
            self.logger.error("❌ VIX data is None - skipping VIX chart")
            return None
            
        if not isinstance(vix_data, pd.DataFrame):
            self.logger.error(f"❌ VIX data is not a DataFrame (type: {type(vix_data)}) - skipping VIX chart")
            return None
            
        if vix_data.empty:
            self.logger.error("❌ VIX data is empty - skipping VIX chart")
            return None
            
        if 'close' not in vix_data.columns:
            self.logger.error(f"❌ VIX data missing 'close' column. Available columns: {list(vix_data.columns)} - skipping VIX chart")
            return None
            
        self.logger.info(f"✅ VIX data validated: {len(vix_data)} rows, columns: {list(vix_data.columns)}")
        
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('VIX Volatility Index Analysis', fontsize=16, fontweight='bold')
            
            # Main VIX chart
            ax1.plot(vix_data.index, vix_data['close'], color=self.colors['primary'], linewidth=2)
            ax1.axhline(y=20, color=self.colors['warning'], linestyle='--', alpha=0.7, label='Normal Volatility (20)')
            ax1.axhline(y=30, color=self.colors['danger'], linestyle='--', alpha=0.7, label='High Volatility (30)')
            ax1.fill_between(vix_data.index, vix_data['close'], alpha=0.3, color=self.colors['primary'])
            ax1.set_title('VIX Index Over Time')
            ax1.set_ylabel('VIX Level')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # VIX distribution
            ax2.hist(vix_data['close'], bins=30, color=self.colors['secondary'], alpha=0.7, edgecolor='black')
            ax2.axvline(vix_data['close'].mean(), color=self.colors['danger'], linestyle='--', label=f'Mean: {vix_data["close"].mean():.1f}')
            ax2.axvline(vix_data['close'].median(), color=self.colors['success'], linestyle='--', label=f'Median: {vix_data["close"].median():.1f}')
            ax2.set_title('VIX Distribution')
            ax2.set_xlabel('VIX Level')
            ax2.set_ylabel('Frequency')
            ax2.legend()
            
            # VIX rolling volatility
            rolling_std = vix_data['close'].rolling(window=20).std()
            ax3.plot(vix_data.index, rolling_std, color=self.colors['info'], linewidth=2)
            ax3.set_title('VIX Rolling Volatility (20-day)')
            ax3.set_ylabel('Volatility of VIX')
            ax3.grid(True, alpha=0.3)
            
            # VIX vs S&P 500 correlation (if available)
            if 'sp500' in vix_data.columns:
                correlation = vix_data['close'].corr(vix_data['sp500'])
                ax4.scatter(vix_data['close'], vix_data['sp500'], alpha=0.6, color=self.colors['primary'])
                ax4.set_xlabel('VIX Level')
                ax4.set_ylabel('S&P 500 Level')
                ax4.set_title(f'VIX vs S&P 500 (Correlation: {correlation:.3f})')
                ax4.grid(True, alpha=0.3)
            else:
                # VIX momentum
                vix_momentum = vix_data['close'].pct_change(periods=5)
                ax4.plot(vix_data.index, vix_momentum, color=self.colors['warning'], linewidth=2)
                ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                ax4.set_title('VIX 5-Day Momentum')
                ax4.set_ylabel('5-Day Change (%)')
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save chart
            output_path = os.path.join(self.output_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"✅ VIX analysis chart saved to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ Error creating VIX analysis chart: {str(e)}")
            return None
    
    def create_multi_asset_comparison(self, asset_data, output_filename="multi_asset_comparison.png"):
        """Create multi-asset comparison chart."""
        self.logger.info("📈 Creating multi-asset comparison chart...")
        
        # Validate input data
        if asset_data is None:
            self.logger.error("❌ Asset data is None - skipping multi-asset chart")
            return None
            
        if not isinstance(asset_data, dict):
            self.logger.error(f"❌ Asset data is not a dictionary (type: {type(asset_data)}) - skipping multi-asset chart")
            return None
            
        if not asset_data:
            self.logger.error("❌ Asset data is empty - skipping multi-asset chart")
            return None
            
        # Check if we have valid data for at least one asset
        valid_assets = []
        for symbol, data in asset_data.items():
            if data is not None and isinstance(data, pd.DataFrame) and not data.empty and 'close' in data.columns:
                valid_assets.append(symbol)
            else:
                self.logger.warning(f"⚠️ Invalid data for {symbol}: {type(data)}")
                
        if not valid_assets:
            self.logger.error("❌ No valid asset data found - skipping multi-asset chart")
            return None
            
        self.logger.info(f"✅ Multi-asset data validated: {len(valid_assets)} valid assets: {valid_assets}")
        
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Multi-Asset Market Analysis', fontsize=16, fontweight='bold')
            
            # Normalized price comparison
            for symbol, data in asset_data.items():
                if data is not None and len(data) > 0:
                    normalized = data['close'] / data['close'].iloc[0] * 100
                    ax1.plot(data.index, normalized, label=symbol, linewidth=2)
            
            ax1.set_title('Normalized Asset Performance (Base = 100)')
            ax1.set_ylabel('Normalized Price')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Correlation heatmap
            if len(asset_data) > 1:
                # Create correlation matrix
                price_data = pd.DataFrame()
                for symbol, data in asset_data.items():
                    if data is not None and len(data) > 0:
                        price_data[symbol] = data['close']
                
                if len(price_data.columns) > 1:
                    correlation_matrix = price_data.corr()
                    
                    im = ax2.imshow(correlation_matrix, cmap='RdYlBu', aspect='auto')
                    ax2.set_xticks(range(len(correlation_matrix.columns)))
                    ax2.set_yticks(range(len(correlation_matrix.columns)))
                    ax2.set_xticklabels(correlation_matrix.columns, rotation=45)
                    ax2.set_yticklabels(correlation_matrix.columns)
                    
                    # Add correlation values
                    for i in range(len(correlation_matrix.columns)):
                        for j in range(len(correlation_matrix.columns)):
                            text = ax2.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                                          ha="center", va="center", color="black", fontsize=8)
                    
                    ax2.set_title('Asset Correlation Matrix')
                    plt.colorbar(im, ax=ax2)
            
            # Volatility comparison
            volatilities = {}
            for symbol, data in asset_data.items():
                if data is not None and len(data) > 10:
                    returns = data['close'].pct_change().dropna()
                    volatilities[symbol] = returns.std() * np.sqrt(252) * 100  # Annualized
            
            if volatilities:
                symbols = list(volatilities.keys())
                vol_values = list(volatilities.values())
                bars = ax3.bar(symbols, vol_values, color=[self.colors['primary'], self.colors['secondary'], 
                                                         self.colors['success'], self.colors['warning']][:len(symbols)])
                ax3.set_title('Annualized Volatility Comparison')
                ax3.set_ylabel('Volatility (%)')
                ax3.tick_params(axis='x', rotation=45)
                
                # Add value labels on bars
                for bar, value in zip(bars, vol_values):
                    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                            f'{value:.1f}%', ha='center', va='bottom')
            
            # Risk-return scatter plot
            risk_return_data = []
            for symbol, data in asset_data.items():
                if data is not None and len(data) > 10:
                    returns = data['close'].pct_change().dropna()
                    volatility = returns.std() * np.sqrt(252) * 100
                    annual_return = ((data['close'].iloc[-1] / data['close'].iloc[0]) ** (252/len(data)) - 1) * 100
                    risk_return_data.append((symbol, volatility, annual_return))
            
            if risk_return_data:
                symbols, volatilities, returns = zip(*risk_return_data)
                scatter = ax4.scatter(volatilities, returns, s=100, alpha=0.7, 
                                    c=range(len(symbols)), cmap='viridis')
                
                # Add labels
                for i, symbol in enumerate(symbols):
                    ax4.annotate(symbol, (volatilities[i], returns[i]), 
                               xytext=(5, 5), textcoords='offset points', fontsize=8)
                
                ax4.set_xlabel('Volatility (%)')
                ax4.set_ylabel('Annual Return (%)')
                ax4.set_title('Risk-Return Profile')
                ax4.grid(True, alpha=0.3)
                ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                ax4.axvline(x=0, color='black', linestyle='-', alpha=0.5)
            
            plt.tight_layout()
            
            # Save chart
            output_path = os.path.join(self.output_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Multi-asset comparison chart saved to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error creating multi-asset comparison chart: {str(e)}")
            return None
    
    def create_economic_calendar_impact(self, calendar_data, market_data, output_filename="economic_calendar_impact.png"):
        """Create economic calendar impact visualization."""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Economic Calendar Market Impact Analysis', fontsize=16, fontweight='bold')
            
            # Economic events timeline
            if calendar_data and 'events_by_date' in calendar_data:
                event_dates = []
                event_impacts = []
                event_names = []
                
                for date, events in calendar_data['events_by_date'].items():
                    for event in events:
                        event_dates.append(pd.to_datetime(date))
                        impact_map = {"High": 3, "Medium": 2, "Low": 1}
                        event_impacts.append(impact_map.get(event.get('impact', 'Low'), 1))
                        event_names.append(event.get('event', 'Unknown'))
                
                if event_dates:
                    # Create impact timeline
                    ax1.scatter(event_dates, event_impacts, s=[50 if imp == 3 else 30 if imp == 2 else 15 for imp in event_impacts],
                              c=event_impacts, cmap='RdYlBu', alpha=0.7)
                    ax1.set_title('Economic Events by Impact Level')
                    ax1.set_ylabel('Impact Level (1=Low, 2=Medium, 3=High)')
                    ax1.set_xlabel('Date')
                    ax1.grid(True, alpha=0.3)
                    
                    # Add some event labels
                    for i, (date, name) in enumerate(zip(event_dates, event_names)):
                        if event_impacts[i] == 3:  # High impact events
                            ax1.annotate(name[:20] + '...' if len(name) > 20 else name,
                                       (date, event_impacts[i]), xytext=(5, 5),
                                       textcoords='offset points', fontsize=6, rotation=45)
            
            # Market performance around events
            if market_data and len(market_data) > 0:
                # Show market performance
                market_symbol = list(market_data.keys())[0] if market_data else None
                if market_symbol and market_data[market_symbol] is not None:
                    data = market_data[market_symbol]
                    ax2.plot(data.index, data['close'], color=self.colors['primary'], linewidth=2)
                    ax2.set_title(f'{market_symbol} Price Performance')
                    ax2.set_ylabel('Price')
                    ax2.grid(True, alpha=0.3)
            
            # Impact distribution
            if calendar_data and 'high_impact_events' in calendar_data:
                impact_counts = {
                    'High': len(calendar_data.get('high_impact_events', [])),
                    'Medium': len(calendar_data.get('medium_impact_events', [])),
                    'Low': len(calendar_data.get('low_impact_events', []))
                }
                
                impacts = list(impact_counts.keys())
                counts = list(impact_counts.values())
                colors = [self.colors['danger'], self.colors['warning'], self.colors['success']]
                
                bars = ax3.bar(impacts, counts, color=colors, alpha=0.7)
                ax3.set_title('Economic Events by Impact Level')
                ax3.set_ylabel('Number of Events')
                
                # Add value labels
                for bar, count in zip(bars, counts):
                    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                            str(count), ha='center', va='bottom')
            
            # Market sentiment correlation
            if calendar_data and market_data:
                # Create a simple sentiment indicator based on event count
                event_dates = []
                if 'events_by_date' in calendar_data:
                    for date in calendar_data['events_by_date'].keys():
                        event_dates.append(pd.to_datetime(date))
                
                if event_dates and market_data:
                    market_symbol = list(market_data.keys())[0]
                    if market_data[market_symbol] is not None:
                        data = market_data[market_symbol]
                        
                        # Calculate daily returns
                        returns = data['close'].pct_change().dropna()
                        
                        # Mark days with events
                        event_days = []
                        event_returns = []
                        non_event_returns = []
                        
                        for date in returns.index:
                            if date.date() in [d.date() for d in event_dates]:
                                event_days.append(date)
                                event_returns.append(returns[date])
                            else:
                                non_event_returns.append(returns[date])
                        
                        if event_returns and non_event_returns:
                            ax4.hist(non_event_returns, bins=30, alpha=0.5, label='Non-Event Days', 
                                   color=self.colors['primary'])
                            ax4.hist(event_returns, bins=30, alpha=0.7, label='Event Days', 
                                   color=self.colors['danger'])
                            ax4.set_title('Market Returns: Event vs Non-Event Days')
                            ax4.set_xlabel('Daily Returns')
                            ax4.set_ylabel('Frequency')
                            ax4.legend()
                            ax4.axvline(x=0, color='black', linestyle='--', alpha=0.5)
            
            plt.tight_layout()
            
            # Save chart
            output_path = os.path.join(self.output_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Economic calendar impact chart saved to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error creating economic calendar impact chart: {str(e)}")
            return None
    
    def create_fear_greed_analysis(self, fear_greed_data, market_data, output_filename="fear_greed_analysis.png"):
        """Create Fear & Greed index analysis chart."""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Fear & Greed Index Market Analysis', fontsize=16, fontweight='bold')
            
            # Fear & Greed index over time
            if fear_greed_data is not None and len(fear_greed_data) > 0:
                ax1.plot(fear_greed_data.index, fear_greed_data.values, color=self.colors['warning'], linewidth=2)
                ax1.axhline(y=50, color='black', linestyle='--', alpha=0.5, label='Neutral (50)')
                ax1.axhline(y=25, color=self.colors['danger'], linestyle='--', alpha=0.7, label='Extreme Fear (25)')
                ax1.axhline(y=75, color=self.colors['success'], linestyle='--', alpha=0.7, label='Extreme Greed (75)')
                ax1.fill_between(fear_greed_data.index, fear_greed_data.values, alpha=0.3, color=self.colors['warning'])
                ax1.set_title('Fear & Greed Index Over Time')
                ax1.set_ylabel('Fear & Greed Score')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
            
            # Market performance vs Fear & Greed
            if fear_greed_data is not None and market_data:
                market_symbol = list(market_data.keys())[0] if market_data else None
                if market_symbol and market_data[market_symbol] is not None:
                    data = market_data[market_symbol]
                    
                    # Align data
                    common_dates = fear_greed_data.index.intersection(data.index)
                    if len(common_dates) > 0:
                        fear_greed_aligned = fear_greed_data.loc[common_dates]
                        market_aligned = data.loc[common_dates]
                        
                        # Calculate correlation
                        correlation = fear_greed_aligned.corr(market_aligned['close'])
                        
                        ax2.scatter(fear_greed_aligned, market_aligned['close'], alpha=0.6, color=self.colors['primary'])
                        ax2.set_xlabel('Fear & Greed Score')
                        ax2.set_ylabel(f'{market_symbol} Price')
                        ax2.set_title(f'Market vs Fear & Greed (Correlation: {correlation:.3f})')
                        ax2.grid(True, alpha=0.3)
            
            # Fear & Greed distribution
            if fear_greed_data is not None:
                ax3.hist(fear_greed_data.values, bins=20, color=self.colors['secondary'], alpha=0.7, edgecolor='black')
                ax3.axvline(fear_greed_data.mean(), color=self.colors['danger'], linestyle='--', 
                           label=f'Mean: {fear_greed_data.mean():.1f}')
                ax3.set_title('Fear & Greed Score Distribution')
                ax3.set_xlabel('Fear & Greed Score')
                ax3.set_ylabel('Frequency')
                ax3.legend()
            
            # Market regime analysis
            if fear_greed_data is not None and market_data:
                market_symbol = list(market_data.keys())[0] if market_data else None
                if market_symbol and market_data[market_symbol] is not None:
                    data = market_data[market_symbol]
                    
                    # Align data
                    common_dates = fear_greed_data.index.intersection(data.index)
                    if len(common_dates) > 0:
                        fear_greed_aligned = fear_greed_data.loc[common_dates]
                        market_aligned = data.loc[common_dates]
                        
                        # Categorize by fear/greed levels
                        extreme_fear = fear_greed_aligned < 25
                        fear = (fear_greed_aligned >= 25) & (fear_greed_aligned < 45)
                        neutral = (fear_greed_aligned >= 45) & (fear_greed_aligned < 55)
                        greed = (fear_greed_aligned >= 55) & (fear_greed_aligned < 75)
                        extreme_greed = fear_greed_aligned >= 75
                        
                        # Calculate returns for each regime
                        returns = market_aligned['close'].pct_change().dropna()
                        regimes = {
                            'Extreme Fear': returns[extreme_fear[1:]] if len(extreme_fear) > 1 else pd.Series(),
                            'Fear': returns[fear[1:]] if len(fear) > 1 else pd.Series(),
                            'Neutral': returns[neutral[1:]] if len(neutral) > 1 else pd.Series(),
                            'Greed': returns[greed[1:]] if len(greed) > 1 else pd.Series(),
                            'Extreme Greed': returns[extreme_greed[1:]] if len(extreme_greed) > 1 else pd.Series()
                        }
                        
                        regime_means = {k: v.mean() * 100 for k, v in regimes.items() if len(v) > 0}
                        
                        if regime_means:
                            regimes_list = list(regime_means.keys())
                            means_list = list(regime_means.values())
                            colors = [self.colors['danger'], self.colors['warning'], self.colors['info'], 
                                     self.colors['secondary'], self.colors['success']]
                            
                            bars = ax4.bar(regimes_list, means_list, color=colors[:len(regimes_list)], alpha=0.7)
                            ax4.set_title('Average Daily Returns by Market Sentiment')
                            ax4.set_ylabel('Average Daily Return (%)')
                            ax4.tick_params(axis='x', rotation=45)
                            
                            # Add value labels
                            for bar, value in zip(bars, means_list):
                                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                                        f'{value:.2f}%', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Save chart
            output_path = os.path.join(self.output_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Fear & Greed analysis chart saved to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error creating Fear & Greed analysis chart: {str(e)}")
            return None
    
    def create_vix_strategic_chart(self, vix_data=None, fear_greed_data=None, regime_data=None, output_filename=None):
        """
        Create a high-quality two-panel strategic VIX chart.
        
        Args:
            vix_data: DataFrame with VIX data (Date, close columns)
            fear_greed_data: DataFrame with Fear & Greed data (Date, score columns)
            regime_data: DataFrame with Regime Score data (Date, total_score columns)
            output_filename: Optional custom filename
            
        Returns:
            str: Path to saved chart file
        """
        self.logger.info("📊 Creating VIX Strategic Chart...")
        
        # Generate timestamp for filename if not provided
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"vix_regime_analysis_{timestamp}.png"
        
        try:
            # Fetch VIX data if not provided
            if vix_data is None:
                vix_data = self._fetch_vix_data()
            
            # Fetch Fear & Greed data if not provided
            if fear_greed_data is None:
                fear_greed_data = self._fetch_fear_greed_data()
            
            # Fetch Regime Score data if not provided
            if regime_data is None:
                regime_data = self._fetch_regime_data()
            
            # Validate data
            if vix_data is None or vix_data.empty:
                self.logger.error("❌ No VIX data available")
                return None
            
            # Create figure with two panels
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
            fig.suptitle('VIX Strategic Analysis', fontsize=20, fontweight='bold', y=0.95)
            
            # Panel 1: VIX Over Time with Zones
            self._create_vix_panel(ax1, vix_data)
            
            # Panel 2: VIX vs Fear & Greed vs Regime Score
            self._create_comparison_panel(ax2, vix_data, fear_greed_data, regime_data)
            
            # Adjust layout
            plt.tight_layout()
            plt.subplots_adjust(top=0.92, hspace=0.3)
            
            # Save chart
            output_path = os.path.join(self.output_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            self.logger.info(f"✅ VIX Strategic Chart saved to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ Error creating VIX Strategic Chart: {str(e)}")
            return None
    
    def generate_intelligent_chart(self, regime_data: Dict[str, Any], fear_greed_score: int, 
                                 market_data: Dict[str, Any] | None = None, 
                                 dominant_keywords: list = None, tags: list = None) -> Dict[str, Any]:
        """
        Generate intelligent chart based on current regime, strategy, and dominant keywords.
        Args:
            regime_data: Market regime analysis data
            fear_greed_score: Current Fear & Greed Index score
            market_data: Additional market data
            dominant_keywords: List of dominant keywords from Perplexity
            tags: List of tags from Perplexity
        Returns:
            Dictionary with chart information and AI explanation
        """
        self.logger.info("🧠 Generating intelligent regime-aware chart...")
        try:
            # Extract regime information
            regime = regime_data.get('regime_classification', 'Neutral')
            strategy = regime_data.get('strategy_recommendation', 'Tier 2 Mean Reversion')
            instrument = regime_data.get('instrument', 'MES')
            total_score = regime_data.get('total_score', 50)

            # Asset selection logic using dominant_keywords and tags
            assets = None
            if dominant_keywords is None:
                dominant_keywords = []
            if tags is None:
                tags = []
            # Lowercase for matching
            dom_kw = [k.lower() for k in dominant_keywords]
            tags_lc = [t.lower() for t in tags]
            if "oil" in dom_kw or "middle east" in tags_lc:
                assets = ['MCL', 'MGC', 'MYM']
                topic = "oil"
            elif "inflation" in dom_kw:
                assets = ['MYM', 'MGC', 'MES']
                topic = "inflation"
            elif "ai stocks" in dom_kw:
                assets = ['NVDA', 'QQQ', 'MNQ']
                topic = "AI stocks"
            else:
                assets = ['MYM', 'MES', 'MCL']
                topic = "general"
            main_asset = assets[0]

            # Generate appropriate chart based on strategy
            chart_type = self._determine_chart_type(strategy, regime, fear_greed_score)

            # Generate filename as specified
            tier = (strategy.split()[1] if 'Tier' in strategy else 'unknown').lower()
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"regime_chart_{tier}_{topic}_{main_asset}_{date_str}.png"
            output_path = os.path.join(self.output_dir, filename)

            # Create the chart (reuse _create_regime_chart, but pass selected assets)
            chart_result = self._create_regime_chart(
                chart_type=chart_type,
                primary_instrument=assets[0],
                secondary_instrument=assets[1],
                macro_indicators=assets[2:],
                regime_data=regime_data,
                fear_greed_score=fear_greed_score,
                market_data=market_data
            )
            # Overwrite path with our filename
            if chart_result:
                chart_result["path"] = output_path

            # Generate AI explanation (to be updated in chart_generator_agent)
            ai_explanation = ""

            result = {
                "chart_path": output_path,
                "chart_type": chart_type,
                "regime": regime,
                "strategy": strategy,
                "primary_instrument": assets[0],
                "secondary_instrument": assets[1],
                "macro_indicators": assets[2:],
                "ai_explanation": ai_explanation,
                "fear_greed_score": fear_greed_score,
                "regime_score": total_score,
                "topic": topic,
                "main_asset": main_asset,
                "tier": tier,
                "timestamp": datetime.now().isoformat()
            }
            self.logger.info(f"✅ Intelligent chart generated: {chart_type} for {regime} regime with assets {assets}")
            return result
        except Exception as e:
            self.logger.error(f"❌ Error generating intelligent chart: {str(e)}")
            return {
                "error": str(e),
                "chart_type": "fallback",
                "ai_explanation": "Chart generation failed due to technical error."
            }
    
    def _determine_chart_type(self, strategy: str, regime: str, fear_greed_score: int) -> str:
        """Determine the best chart type based on strategy and regime."""
        
        # Extract strategy tier
        if 'Tier 1' in strategy:
            return 'momentum_breakout'
        elif 'Tier 2' in strategy:
            return 'mean_reversion'

        elif 'Tier 5' in strategy:
            return 'extreme_momentum'
        
        # Fallback based on regime and fear/greed
        if regime == 'BULLISH' and fear_greed_score > 60:
            return 'momentum_continuation'
        elif regime == 'BEARISH' and fear_greed_score < 40:
            return 'mean_reversion'
        else:
            return 'range_trading'
    
    def _create_regime_chart(self, chart_type: str, primary_instrument: str, 
                           secondary_instrument: str, macro_indicators: list,
                           regime_data: Dict[str, Any], fear_greed_score: int,
                           market_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Create the actual chart based on regime analysis."""
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"regime_chart_{chart_type}_{timestamp}.png"
            output_path = os.path.join(self.output_dir, filename)
            
            # Create figure
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'Macro Regime Analysis: {regime_data.get("regime_classification", "Unknown")} Environment', 
                        fontsize=16, fontweight='bold')
            
            # Panel 1: Primary instrument performance
            self._create_instrument_panel(ax1, primary_instrument, "Primary Instrument", 
                                        regime_data, fear_greed_score)
            
            # Panel 2: Secondary instrument performance
            self._create_instrument_panel(ax2, secondary_instrument, "Secondary Instrument", 
                                        regime_data, fear_greed_score)
            
            # Panel 3: Macro indicators correlation
            self._create_macro_correlation_panel(ax3, macro_indicators, regime_data)
            
            # Panel 4: Regime score breakdown
            self._create_regime_breakdown_panel(ax4, regime_data)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return {"path": output_path, "success": True}
            
        except Exception as e:
            self.logger.error(f"❌ Error creating regime chart: {str(e)}")
            return {"path": None, "success": False, "error": str(e)}
    
    def _validate_price_data(self, prices: list, instrument: str) -> bool:
        """
        Validate price data for reasonable values and detect anomalies.
        
        Args:
            prices: List of price values
            instrument: Instrument name for logging
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if not prices or len(prices) == 0:
                self.logger.warning(f"⚠️ Empty price data for {instrument}")
                return False
            
            # Convert to numpy array for easier processing
            price_array = np.array(prices)
            
            # Check for NaN or infinite values
            if np.any(np.isnan(price_array)) or np.any(np.isinf(price_array)):
                self.logger.warning(f"⚠️ NaN or infinite values detected for {instrument}")
                return False
            
            # Check for extreme values (1e27 scale or larger)
            if np.any(price_array > 1e20) or np.any(price_array < -1e20):
                self.logger.error(f"❌ Extreme price values detected for {instrument} (1e27-scale) - skipping chart")
                return False
            
            # Check for all zero or negative values
            if np.all(price_array <= 0):
                self.logger.warning(f"⚠️ All non-positive values for {instrument}")
                return False
            
            # Check for reasonable price ranges based on instrument type
            if instrument == 'SPY':
                if np.any(price_array < 10) or np.any(price_array > 10000):
                    self.logger.warning(f"⚠️ SPY prices outside reasonable range (10-10000): {np.min(price_array):.2f} to {np.max(price_array):.2f}")
                    return False
            elif instrument == 'QQQ':
                if np.any(price_array < 10) or np.any(price_array > 10000):
                    self.logger.warning(f"⚠️ QQQ prices outside reasonable range (10-10000): {np.min(price_array):.2f} to {np.max(price_array):.2f}")
                    return False
            elif instrument == 'GLD':
                if np.any(price_array < 50) or np.any(price_array > 5000):
                    self.logger.warning(f"⚠️ GLD prices outside reasonable range (50-5000): {np.min(price_array):.2f} to {np.max(price_array):.2f}")
                    return False
            elif instrument == 'VIX':
                if np.any(price_array < 0) or np.any(price_array > 200):
                    self.logger.warning(f"⚠️ VIX values outside reasonable range (0-200): {np.min(price_array):.2f} to {np.max(price_array):.2f}")
                    return False
            
            # Check for excessive volatility (price changes > 100% in single period)
            if len(price_array) > 1:
                price_changes = np.abs(np.diff(price_array) / price_array[:-1])
                if np.any(price_changes > 1.0):  # > 100% change
                    self.logger.warning(f"⚠️ Excessive volatility detected for {instrument} - single period changes > 100%")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error validating price data for {instrument}: {str(e)}")
            return False
    
    def _normalize_price_data(self, prices: list, instrument: str) -> list:
        """
        Normalize price data to handle missing or malformed values.
        
        Args:
            prices: List of price values
            instrument: Instrument name for logging
            
        Returns:
            Normalized list of prices
        """
        try:
            if not prices or len(prices) == 0:
                self.logger.warning(f"⚠️ Empty price data for {instrument} - using default values")
                # Generate reasonable default data
                dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
                if instrument == 'SPY':
                    return list(np.random.normal(400, 10, len(dates)) + 380)
                elif instrument == 'QQQ':
                    return list(np.random.normal(350, 15, len(dates)) + 330)
                elif instrument == 'GLD':
                    return list(np.random.normal(180, 5, len(dates)) + 175)
                elif instrument == 'VIX':
                    return list(np.random.normal(20, 5, len(dates)) + 15)
                else:
                    return list(np.random.normal(100, 10, len(dates)) + 90)
            
            # Convert to numpy array
            price_array = np.array(prices)
            
            # Handle NaN values by forward fill, then backward fill
            price_array = pd.Series(price_array).fillna(method='ffill').fillna(method='bfill').values
            
            # If still have NaN values, replace with reasonable defaults
            if np.any(np.isnan(price_array)):
                self.logger.warning(f"⚠️ NaN values in {instrument} data - replacing with defaults")
                if instrument == 'SPY':
                    default_price = 400
                elif instrument == 'QQQ':
                    default_price = 350
                elif instrument == 'GLD':
                    default_price = 180
                elif instrument == 'VIX':
                    default_price = 20
                else:
                    default_price = 100
                
                price_array = np.where(np.isnan(price_array), default_price, price_array)
            
            # Handle infinite values
            if np.any(np.isinf(price_array)):
                self.logger.warning(f"⚠️ Infinite values in {instrument} data - replacing with defaults")
                if instrument == 'SPY':
                    default_price = 400
                elif instrument == 'QQQ':
                    default_price = 350
                elif instrument == 'GLD':
                    default_price = 180
                elif instrument == 'VIX':
                    default_price = 20
                else:
                    default_price = 100
                
                price_array = np.where(np.isinf(price_array), default_price, price_array)
            
            # Handle extreme values
            if np.any(price_array > 1e20) or np.any(price_array < -1e20):
                self.logger.error(f"❌ Invalid price data detected for {instrument} – skipping chart")
                return []
            
            # Handle negative values for instruments that shouldn't be negative
            if instrument in ['SPY', 'QQQ', 'GLD'] and np.any(price_array < 0):
                self.logger.warning(f"⚠️ Negative values in {instrument} data - replacing with absolute values")
                price_array = np.abs(price_array)
            
            # Ensure all values are finite
            if not np.all(np.isfinite(price_array)):
                self.logger.error(f"❌ Non-finite values in {instrument} data after normalization")
                return []
            
            return list(price_array)
            
        except Exception as e:
            self.logger.error(f"❌ Error normalizing price data for {instrument}: {str(e)}")
            return []
    
    def _create_data_unavailable_panel(self, ax, instrument: str, reason: str = "Data unavailable"):
        """Create a placeholder panel when data is unavailable."""
        try:
            ax.text(0.5, 0.5, f'{instrument}\n{reason}', 
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
            ax.set_title(f'{instrument} - Data Unavailable')
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error creating data unavailable panel for {instrument}: {str(e)}")

    def _create_instrument_panel(self, ax, instrument: str, title: str, 
                               regime_data: Dict[str, Any], fear_greed_score: int):
        """Create instrument performance panel with robust data validation."""
        try:
            # Simulate instrument data (in real implementation, fetch from API)
            dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
            
            # Generate realistic data based on instrument type
            if instrument == 'SPY':
                base_price = 400
                volatility = 0.02
            elif instrument == 'QQQ':
                base_price = 350
                volatility = 0.025
            elif instrument == 'GLD':
                base_price = 180
                volatility = 0.015
            elif instrument == 'VIX':
                base_price = 20
                volatility = 0.1
            else:
                base_price = 100
                volatility = 0.02
            
            # Generate price data with regime influence
            regime_score = regime_data.get('total_score', 50)
            trend_factor = (regime_score - 50) / 50  # -1 to 1
            
            prices = []
            current_price = base_price
            for i in range(len(dates)):
                # Add trend based on regime
                trend = trend_factor * 0.001 * i
                # Add volatility
                noise = np.random.normal(0, volatility)
                current_price *= (1 + trend + noise)
                prices.append(current_price)
            
            # Normalize and validate the generated data
            normalized_prices = self._normalize_price_data(prices, instrument)
            
            if not normalized_prices:
                self._create_data_unavailable_panel(ax, instrument, "Invalid price data")
                return
            
            if not self._validate_price_data(normalized_prices, instrument):
                self._create_data_unavailable_panel(ax, instrument, "Data validation failed")
                return
            
            # Plot the validated data
            ax.plot(dates, normalized_prices, color=self.colors['primary'], linewidth=2)
            ax.set_title(f'{title}: {instrument}')
            ax.set_ylabel('Price')
            ax.grid(True, alpha=0.3)
            
            # Add regime annotation
            regime = regime_data.get('regime_classification', 'Unknown')
            ax.text(0.02, 0.98, f'Regime: {regime}\nF&G: {fear_greed_score}', 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error creating instrument panel for {instrument}: {str(e)}")
            self._create_data_unavailable_panel(ax, instrument, f"Error: {str(e)}")
    
    def _create_macro_correlation_panel(self, ax, macro_indicators: list, regime_data: Dict[str, Any]):
        """Create macro indicators correlation panel with data validation."""
        try:
            # Simulate macro indicator data
            indicators = macro_indicators[:3]  # Limit to 3 indicators
            dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
            
            valid_indicators = []
            
            # Generate data for each indicator with validation
            for i, indicator in enumerate(indicators):
                if indicator == 'VIX':
                    values = np.random.normal(20, 5, len(dates)) + 15
                elif indicator == 'OIL':
                    values = np.random.normal(70, 10, len(dates)) + 60
                elif indicator == 'GOLD':
                    values = np.random.normal(1800, 50, len(dates)) + 1750
                elif indicator == 'USD':
                    values = np.random.normal(100, 2, len(dates)) + 98
                else:
                    values = np.random.normal(50, 10, len(dates)) + 45
                
                # Normalize and validate the data
                normalized_values = self._normalize_price_data(list(values), indicator)
                
                if normalized_values and self._validate_price_data(normalized_values, indicator):
                    ax.plot(dates, normalized_values, label=indicator, linewidth=2)
                    valid_indicators.append(indicator)
                else:
                    self.logger.warning(f"⚠️ Invalid data for macro indicator {indicator} - skipping")
            
            if valid_indicators:
                ax.set_title('Macro Indicators Correlation')
                ax.set_ylabel('Value')
                ax.legend()
                ax.grid(True, alpha=0.3)
            else:
                self._create_data_unavailable_panel(ax, "Macro Indicators", "No valid data available")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error creating macro correlation panel: {str(e)}")
            self._create_data_unavailable_panel(ax, "Macro Indicators", f"Error: {str(e)}")
    
    def _create_regime_breakdown_panel(self, ax, regime_data: Dict[str, Any]):
        """Create regime score breakdown panel with data validation."""
        try:
            # Extract component breakdown
            breakdown = regime_data.get('component_breakdown', {})
            
            if breakdown:
                components = list(breakdown.keys())
                scores = []
                valid_components = []
                
                # Validate each component score
                for comp in components:
                    comp_data = breakdown.get(comp, {})
                    score = comp_data.get('weighted_score', 0)
                    
                    # Check for reasonable score values
                    if isinstance(score, (int, float)) and 0 <= score <= 100:
                        scores.append(score)
                        valid_components.append(comp)
                    else:
                        self.logger.warning(f"⚠️ Invalid score for component {comp}: {score}")
                
                if valid_components and scores:
                    # Create bar chart
                    bars = ax.bar(valid_components, scores, color=self.colors['info'], alpha=0.7)
                    ax.set_title('Regime Score Breakdown')
                    ax.set_ylabel('Weighted Score')
                    ax.set_xticklabels(valid_components, rotation=45, ha='right')
                    
                    # Add value labels on bars
                    for bar, score in zip(bars, scores):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{score:.1f}', ha='center', va='bottom')
                    
                    # Add total score
                    total_score = regime_data.get('total_score', 0)
                    if isinstance(total_score, (int, float)) and 0 <= total_score <= 100:
                        ax.text(0.02, 0.98, f'Total Score: {total_score:.1f}', 
                               transform=ax.transAxes, verticalalignment='top',
                               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                    else:
                        ax.text(0.02, 0.98, 'Total Score: Invalid', 
                               transform=ax.transAxes, verticalalignment='top',
                               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                else:
                    self._create_data_unavailable_panel(ax, "Regime Breakdown", "No valid component data")
            else:
                self._create_data_unavailable_panel(ax, "Regime Breakdown", "Breakdown data unavailable")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error creating regime breakdown panel: {str(e)}")
            self._create_data_unavailable_panel(ax, "Regime Breakdown", f"Error: {str(e)}")
    
    def _generate_chart_explanation(self, chart_type: str, regime: str, strategy: str,
                                  instrument: str, fear_greed_score: int, total_score: float,
                                  primary_instrument: str, secondary_instrument: str) -> str:
        """Generate AI-powered explanation for the chart."""
        
        try:
            # Create explanation based on chart type and regime
            explanations = {
                'momentum_breakout': f"This chart shows momentum breakout patterns in a {regime.lower()} market environment. The {primary_instrument} is positioned as the primary instrument due to strong trend following characteristics, while {secondary_instrument} provides diversification. With a Fear & Greed score of {fear_greed_score} and regime score of {total_score:.1f}, the market shows {self._interpret_score(total_score)} conditions.",
                
                'mean_reversion': f"This mean reversion analysis is tailored for {regime.lower()} market conditions. {primary_instrument} is highlighted as it typically exhibits mean reversion properties during {regime.lower()} periods. The Fear & Greed score of {fear_greed_score} indicates {self._interpret_fear_greed(fear_greed_score)} sentiment, supporting mean reversion strategies.",
                
                'range_trading': f"This range trading visualization reflects the current {regime.lower()} market regime. {primary_instrument} and {secondary_instrument} are selected for their range-bound characteristics. With a regime score of {total_score:.1f} and Fear & Greed at {fear_greed_score}, the market appears to be in {self._interpret_score(total_score)} territory, ideal for range trading strategies.",
                
                'momentum_continuation': f"This momentum continuation chart is designed for {regime.lower()} market conditions. {primary_instrument} leads as the momentum instrument, supported by {secondary_instrument}. The Fear & Greed score of {fear_greed_score} and regime score of {total_score:.1f} suggest {self._interpret_score(total_score)} momentum conditions.",
                
                'extreme_momentum': f"This extreme momentum analysis captures the current {regime.lower()} market environment. {primary_instrument} is positioned for extreme momentum plays, with {secondary_instrument} providing balance. The Fear & Greed score of {fear_greed_score} indicates {self._interpret_fear_greed(fear_greed_score)} sentiment, supporting extreme momentum strategies."
            }
            
            base_explanation = explanations.get(chart_type, explanations['range_trading'])
            
            # Add strategy-specific insights
            strategy_insights = {
                'Tier 1': "This Tier 1 strategy focuses on aggressive momentum plays with high conviction setups.",
                'Tier 2': "This Tier 2 approach emphasizes mean reversion opportunities in volatile conditions.",
                'Tier 5': "This Tier 5 strategy capitalizes on extreme momentum with maximum risk allocation."
            }
            
            strategy_insight = strategy_insights.get(strategy.split()[0], "This strategy adapts to current market conditions.")
            
            # Add instrument-specific commentary
            instrument_commentary = f"The selected instruments ({primary_instrument}, {secondary_instrument}) are optimized for the current {regime.lower()} regime and {strategy} strategy."
            
            full_explanation = f"{base_explanation} {strategy_insight} {instrument_commentary}"
            
            return full_explanation
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error generating chart explanation: {str(e)}")
            return f"Chart analysis for {regime} regime with {strategy} strategy. Fear & Greed: {fear_greed_score}, Regime Score: {total_score:.1f}."
    
    def _interpret_score(self, score: float) -> str:
        """Interpret regime score."""
        if score < 20:
            return "extreme fear"
        elif score < 40:
            return "fear"
        elif score < 60:
            return "neutral"
        elif score < 80:
            return "greed"
        else:
            return "extreme greed"
    
    def _interpret_fear_greed(self, score: int) -> str:
        """Interpret Fear & Greed score."""
        if score < 25:
            return "extreme fear"
        elif score < 45:
            return "fear"
        elif score < 55:
            return "neutral"
        elif score < 75:
            return "greed"
        else:
            return "extreme greed"
    
    def _fetch_vix_data(self):
        """Fetch VIX data using the dedicated FMP API function."""
        try:
            from utils.api_clients import fetch_vix_data
            
            # Use the dedicated VIX fetching function
            vix_df = fetch_vix_data(days=365)
            
            if vix_df is not None and not vix_df.empty:
                self.logger.info(f"✅ Fetched VIX data from FMP: {len(vix_df)} records")
                return vix_df
            else:
                self.logger.warning("⚠️ No VIX data returned from FMP API - using simulated data")
                return self._simulate_vix_data()
                
        except Exception as e:
            self.logger.error(f"❌ Error in VIX data fetch: {e}")
            return self._simulate_vix_data()
    
    def _fetch_fear_greed_data(self):
        """Fetch Fear & Greed data."""
        try:
            import requests
            
            api_key = os.getenv("FEAR_GREED_API_KEY")
            if not api_key:
                self.logger.warning("⚠️ FEAR_GREED_API_KEY not found - using simulated data")
                return self._simulate_fear_greed_data()
            
            url = "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/index"
            headers = {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "cnn-fear-and-greed-index.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("fear_and_greed", {}).get("score", 50)
                
                # Create a simple DataFrame with current score
                df = pd.DataFrame({
                    'Fear_Greed': [score]
                }, index=[datetime.now()])
                
                self.logger.info(f"✅ Fetched Fear & Greed data: {score}")
                return df
            else:
                self.logger.warning(f"⚠️ Fear & Greed API error: {response.status_code} - using simulated data")
                return self._simulate_fear_greed_data()
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error fetching Fear & Greed data: {str(e)} - using simulated data")
            return self._simulate_fear_greed_data()
    
    def _fetch_regime_data(self):
        """Fetch Regime Score data."""
        try:
            # Try to get latest regime score from database or files
            from pathlib import Path
            import json
            
            output_dir = Path("output")
            regime_files = list(output_dir.glob("regime_score_*.json"))
            
            if regime_files:
                # Get the most recent file
                latest_file = max(regime_files, key=lambda x: x.stat().st_mtime)
                
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                
                # Create DataFrame with regime score
                df = pd.DataFrame({
                    'Regime_Score': [data.get('total_score', 50)]
                }, index=[datetime.now()])
                
                self.logger.info(f"✅ Fetched Regime Score data: {data.get('total_score', 50)}")
                return df
            else:
                self.logger.warning("⚠️ No regime score files found - using simulated data")
                return self._simulate_regime_data()
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error fetching Regime Score data: {str(e)} - using simulated data")
            return self._simulate_regime_data()
    
    def _simulate_fear_greed_data(self):
        """Simulate Fear & Greed data for testing."""
        dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
        scores = np.random.normal(50, 15, len(dates))
        scores = np.clip(scores, 0, 100)
        
        df = pd.DataFrame({
            'Fear_Greed': scores
        }, index=pd.DatetimeIndex(dates))
        
        return df
    
    def _simulate_regime_data(self):
        """Simulate Regime Score data for testing."""
        dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
        scores = np.random.normal(50, 20, len(dates))
        scores = np.clip(scores, 0, 100)
        
        df = pd.DataFrame({
            'Regime_Score': scores
        }, index=pd.DatetimeIndex(dates))
        
        return df
    
    def _simulate_vix_data(self):
        """Simulate VIX data for testing."""
        dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
        vix_values = np.random.normal(20, 8, len(dates))
        vix_values = np.clip(vix_values, 10, 50)  # Keep VIX in reasonable range
        
        df = pd.DataFrame({
            'VIX': vix_values
        }, index=pd.DatetimeIndex(dates))
        
        return df
    
    def _create_vix_panel(self, ax, vix_data):
        """Create Panel 1: VIX Over Time with Zones."""
        # Plot VIX line
        ax.plot(vix_data.index, vix_data['VIX'], color=self.colors['primary'], linewidth=2, label='VIX')
        
        # Define zones
        zones = [
            {'min': 0.0, 'max': 15.0, 'color': '#f0f0f0', 'label': 'Low Vol (< 15)'},
            {'min': 15.0, 'max': 20.0, 'color': '#90EE90', 'label': 'Watch Zone (15-20)'},
            {'min': 20.0, 'max': 30.0, 'color': '#FFA500', 'label': 'Reversal-Friendly (20-30)'},
            {'min': 30.0, 'max': 100.0, 'color': '#FF6B6B', 'label': 'Chaos (> 30)'}
        ]
        
        # Add shaded zones
        for zone in zones:
            ax.axhspan(zone['min'], zone['max'], alpha=0.3, color=zone['color'], label=zone['label'])
        
        # Add zone labels
        for zone in zones:
            mid_point = float(zone['min'] + zone['max']) / 2.0
            ax.text(vix_data.index[-1], mid_point, zone['label'], 
                   ha='right', va='center', fontsize=10, fontweight='bold',
                   bbox={'boxstyle': "round,pad=0.3", 'facecolor': 'white', 'alpha': 0.8})
        
        # Customize panel
        ax.set_title('VIX Over Time', fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel('VIX Level', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=10)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _create_comparison_panel(self, ax, vix_data, fear_greed_data, regime_data):
        """Create Panel 2: VIX vs Fear & Greed vs Regime Score."""
        # Plot VIX (blue line)
        ax.plot(vix_data.index, vix_data['VIX'], color=self.colors['primary'], linewidth=2, label='VIX')
        
        # Plot Fear & Greed (green line) - scale to VIX range
        if fear_greed_data is not None and not fear_greed_data.empty:
            # Scale Fear & Greed (0-100) to VIX range (0-50)
            scaled_fg = fear_greed_data['Fear_Greed'] * 0.5
            ax.plot(fear_greed_data.index, scaled_fg, color=self.colors['success'], linewidth=2, label='Fear & Greed (scaled)')
        
        # Plot Regime Score (red dashed line) - scale to VIX range
        if regime_data is not None and not regime_data.empty:
            # Scale Regime Score (0-100) to VIX range (0-50)
            scaled_regime = regime_data['Regime_Score'] * 0.5
            ax.plot(regime_data.index, scaled_regime, color=self.colors['danger'], 
                   linewidth=2, linestyle='--', label='Regime Score (scaled)')
        
        # Add strategy markers
        if regime_data is not None and not regime_data.empty and vix_data is not None and not vix_data.empty:
            self._add_strategy_markers(ax, vix_data, regime_data)
        
        # Customize panel
        ax.set_title('VIX vs Fear & Greed vs Regime Score', fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel('Scaled Values', fontsize=12, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=10)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _add_strategy_markers(self, ax, vix_data, regime_data):
        """Add vertical markers for strategy setups."""
        try:
            # Find days where regime score > 70 and VIX > 25
            if len(regime_data) > 1:  # Need more than one data point for comparison
                # For simplicity, we'll mark recent high regime scores
                recent_regime = regime_data.iloc[-1]['Regime_Score'] if len(regime_data) > 0 else 50
                recent_vix = vix_data.iloc[-1]['VIX'] if len(vix_data) > 0 else 20
                
                # Ensure values are scalar
                if hasattr(recent_regime, 'item'):
                    recent_regime = recent_regime.item()
                elif hasattr(recent_regime, 'iloc'):
                    recent_regime = recent_regime.iloc[0]
                if hasattr(recent_vix, 'item'):
                    recent_vix = recent_vix.item()
                elif hasattr(recent_vix, 'iloc'):
                    recent_vix = recent_vix.iloc[0]
                
                if recent_regime > 70 and recent_vix > 25:
                    # Add vertical line and annotation
                    ax.axvline(x=vix_data.index[-1], color='red', linestyle=':', linewidth=2, alpha=0.7)
                    ax.annotate('Tier 1 Setup', 
                               xy=(vix_data.index[-1], recent_vix),
                               xytext=(10, 10), textcoords='offset points',
                               fontsize=12, fontweight='bold', color='red',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8),
                               arrowprops=dict(arrowstyle='->', color='red', alpha=0.7))
        except Exception as e:
            self.logger.warning(f"Overlay condition failed to apply: {e}")

    def generate_all_visualizations(self, data_sources):
        """Generate all enhanced visualizations."""
        self.logger.info("🎨 Generating enhanced visualizations...")
        
        # Log available data sources
        self.logger.info(f"📊 Available data sources: {list(data_sources.keys()) if data_sources else 'None'}")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "charts_generated": [],
            "charts_skipped": [],
            "errors": []
        }
        
        # Generate VIX analysis
        self.logger.info("🔍 Checking VIX data availability...")
        if 'vix_data' in data_sources and data_sources['vix_data'] is not None:
            self.logger.info("✅ VIX data found, generating chart...")
            try:
                vix_chart = self.create_vix_analysis_chart(data_sources['vix_data'])
                if vix_chart:
                    results["charts_generated"].append({
                        "type": "vix_analysis",
                        "path": vix_chart
                    })
                    self.logger.info("✅ VIX chart generated successfully")
                else:
                    results["charts_skipped"].append("vix_analysis")
                    self.logger.warning("⚠️ VIX chart generation failed")
            except Exception as e:
                results["errors"].append(f"VIX chart error: {str(e)}")
                self.logger.error(f"❌ VIX chart error: {str(e)}")
        else:
            results["charts_skipped"].append("vix_analysis")
            self.logger.warning("⚠️ VIX data not available - skipping VIX chart")
        
        # Generate multi-asset comparison
        self.logger.info("🔍 Checking asset data availability...")
        if 'asset_data' in data_sources and data_sources['asset_data']:
            self.logger.info("✅ Asset data found, generating chart...")
            try:
                asset_chart = self.create_multi_asset_comparison(data_sources['asset_data'])
                if asset_chart:
                    results["charts_generated"].append({
                        "type": "multi_asset_comparison",
                        "path": asset_chart
                    })
                    self.logger.info("✅ Multi-asset chart generated successfully")
                else:
                    results["charts_skipped"].append("multi_asset_comparison")
                    self.logger.warning("⚠️ Multi-asset chart generation failed")
            except Exception as e:
                results["errors"].append(f"Multi-asset chart error: {str(e)}")
                self.logger.error(f"❌ Multi-asset chart error: {str(e)}")
        else:
            results["charts_skipped"].append("multi_asset_comparison")
            self.logger.warning("⚠️ Asset data not available - skipping multi-asset chart")
        
        # Generate economic calendar impact
        self.logger.info("🔍 Checking economic calendar data availability...")
        if 'calendar_data' in data_sources and 'market_data' in data_sources:
            self.logger.info("✅ Calendar and market data found, generating chart...")
            try:
                calendar_chart = self.create_economic_calendar_impact(
                    data_sources['calendar_data'], 
                    data_sources['market_data']
                )
                if calendar_chart:
                    results["charts_generated"].append({
                        "type": "economic_calendar_impact",
                        "path": calendar_chart
                    })
                    self.logger.info("✅ Economic calendar chart generated successfully")
                else:
                    results["charts_skipped"].append("economic_calendar_impact")
                    self.logger.warning("⚠️ Economic calendar chart generation failed")
            except Exception as e:
                results["errors"].append(f"Economic calendar chart error: {str(e)}")
                self.logger.error(f"❌ Economic calendar chart error: {str(e)}")
        else:
            results["charts_skipped"].append("economic_calendar_impact")
            self.logger.warning("⚠️ Calendar or market data not available - skipping economic calendar chart")
        
        # Generate Fear & Greed analysis
        self.logger.info("🔍 Checking Fear & Greed data availability...")
        if 'fear_greed_data' in data_sources and 'market_data' in data_sources:
            self.logger.info("✅ Fear & Greed and market data found, generating chart...")
            try:
                fear_greed_chart = self.create_fear_greed_analysis(
                    data_sources['fear_greed_data'],
                    data_sources['market_data']
                )
                if fear_greed_chart:
                    results["charts_generated"].append({
                        "type": "fear_greed_analysis",
                        "path": fear_greed_chart
                    })
                    self.logger.info("✅ Fear & Greed chart generated successfully")
                else:
                    results["charts_skipped"].append("fear_greed_analysis")
                    self.logger.warning("⚠️ Fear & Greed chart generation failed")
            except Exception as e:
                results["errors"].append(f"Fear & Greed chart error: {str(e)}")
                self.logger.error(f"❌ Fear & Greed chart error: {str(e)}")
        else:
            results["charts_skipped"].append("fear_greed_analysis")
            self.logger.warning("⚠️ Fear & Greed or market data not available - skipping Fear & Greed chart")
        
        # Generate Intelligent Chart
        self.logger.info("🔍 Checking Regime and Fear & Greed data for intelligent chart...")
        if 'regime_data' in data_sources and 'fear_greed_data' in data_sources and 'market_data' in data_sources:
            self.logger.info("✅ Regime, Fear & Greed, and market data found, generating intelligent chart...")
            try:
                intelligent_chart_result = self.generate_intelligent_chart(
                    data_sources['regime_data'],
                    data_sources['fear_greed_data']['Fear_Greed'].iloc[-1] if 'Fear_Greed' in data_sources['fear_greed_data'] else 50,
                    data_sources['market_data']
                )
                if intelligent_chart_result.get("chart_path"):
                    results["charts_generated"].append({
                        "type": "intelligent_regime_chart",
                        "path": intelligent_chart_result["chart_path"]
                    })
                    self.logger.info(f"✅ Intelligent chart generated: {intelligent_chart_result['chart_type']}")
                else:
                    results["charts_skipped"].append("intelligent_regime_chart")
                    self.logger.warning("⚠️ Intelligent chart generation failed")
            except Exception as e:
                results["errors"].append(f"Intelligent chart error: {str(e)}")
                self.logger.error(f"❌ Intelligent chart error: {str(e)}")
        else:
            results["charts_skipped"].append("intelligent_regime_chart")
            self.logger.warning("⚠️ Regime, Fear & Greed, or market data not available - skipping intelligent chart")
        
        # Summary
        total_charts = len(results["charts_generated"])
        total_skipped = len(results["charts_skipped"])
        total_errors = len(results["errors"])
        
        self.logger.info(f"📊 Visualization Summary:")
        self.logger.info(f"   ✅ Charts generated: {total_charts}")
        self.logger.info(f"   ⚠️ Charts skipped: {total_skipped}")
        self.logger.info(f"   ❌ Errors: {total_errors}")
        
        if results["charts_skipped"]:
            self.logger.info(f"   📋 Skipped charts: {', '.join(results['charts_skipped'])}")
        
        if results["errors"]:
            self.logger.info(f"   🚨 Errors: {', '.join(results['errors'])}")
        
        return results

def main():
    """Test function for the enhanced visualization engine."""
    viz_engine = EnhancedVisualizations()
    
    # Create sample data for testing
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    # Sample VIX data
    vix_data = pd.DataFrame({
        'close': np.random.normal(20, 5, len(dates)) + 15,
        'sp500': np.random.normal(4000, 100, len(dates)) + 3800
    }, index=dates)
    
    # Sample asset data
    asset_data = {
        'SPY': pd.DataFrame({'close': np.random.normal(400, 10, len(dates)) + 380}, index=dates),
        'QQQ': pd.DataFrame({'close': np.random.normal(350, 15, len(dates)) + 330}, index=dates),
        'GLD': pd.DataFrame({'close': np.random.normal(180, 5, len(dates)) + 175}, index=dates),
        'TLT': pd.DataFrame({'close': np.random.normal(90, 3, len(dates)) + 87}, index=dates)
    }
    
    # Sample Fear & Greed data
    fear_greed_data = pd.Series(np.random.normal(50, 15, len(dates)), index=dates)
    
    # Test visualizations
    data_sources = {
        'vix_data': vix_data,
        'asset_data': asset_data,
        'fear_greed_data': fear_greed_data,
        'market_data': asset_data
    }
    
    results = viz_engine.generate_all_visualizations(data_sources)
    print(f"Generated charts: {results['charts_generated']}")

if __name__ == "__main__":
    main() 