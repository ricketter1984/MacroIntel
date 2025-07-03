#!/usr/bin/env python3
"""
Enhanced Visualization Engine for MacroIntel

This module generates advanced visualizations including:
- VIX over time with volatility analysis
- Multi-asset comparison charts
- Economic calendar impact visualization
- Fear & Greed correlation analysis
- Market regime indicators
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