#!/usr/bin/env python3
"""
MacroIntel Dashboard - Real-time Streamlit Web Application
Displays live economic data, watchlists, charts, and news in a unified interface
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import requests
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import MacroIntel modules
try:
    from calendar_tracker import EconomicCalendarTracker
    from core.email_report import (
        generate_mini_ticker_cards, _fetch_ticker_data, load_regime_score_data,
        load_polygon_articles, load_latest_yahoo_futures
    )
    from agents.summarizer_agent import SummarizerAgent
    from core.enhanced_visualizations import EnhancedVisualizations
    from utils.api_clients import fetch_all_news
    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"MacroIntel modules not available: {e}")
    MODULES_AVAILABLE = False

# Optional desktop notifications
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

# Configure Streamlit page
st.set_page_config(
    page_title="MacroIntel Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for consistent styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin: 10px 0;
    }
    
    .ticker-card {
        background: rgba(255,255,255,0.1);
        border-left: 4px solid #27ae60;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
    }
    
    .news-card {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    
    .status-green { background-color: #28a745; }
    .status-red { background-color: #dc3545; }
    .status-yellow { background-color: #ffc107; }
    .status-gray { background-color: #6c757d; }
</style>
""", unsafe_allow_html=True)

class MacroIntelDashboard:
    """Main dashboard class for MacroIntel real-time data display."""
    
    def __init__(self):
        """Initialize the dashboard."""
        self.default_watchlist = ["SPY", "QQQ", "IWM", "GLD", "TLT", "^VIX", "AAPL", "TSLA", "NVDA", "MSFT", "BTC-USD", "^DXY"]
        self.last_update = None
        self.update_interval = 600  # 10 minutes
        self.data_cache = {}
        
        # Initialize session state
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
        if 'notifications_enabled' not in st.session_state:
            st.session_state.notifications_enabled = False
        if 'last_notification' not in st.session_state:
            st.session_state.last_notification = 0

    def show_header(self):
        """Display the main dashboard header."""
        st.markdown("""
        <div class="main-header">
            <h1>📊 MacroIntel Dashboard</h1>
            <p>Real-time financial intelligence and market analysis</p>
        </div>
        """, unsafe_allow_html=True)

    def show_sidebar(self):
        """Display the sidebar with controls and settings."""
        st.sidebar.title("⚙️ Dashboard Controls")
        
        # Auto-refresh toggle
        st.session_state.auto_refresh = st.sidebar.checkbox(
            "🔄 Auto Refresh (10 min)",
            value=st.session_state.auto_refresh,
            help="Automatically refresh data every 10 minutes"
        )
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Now", type="primary"):
            self.refresh_all_data()
            st.rerun()
        
        # Notifications toggle
        if NOTIFICATIONS_AVAILABLE:
            st.session_state.notifications_enabled = st.sidebar.checkbox(
                "🔔 Desktop Notifications",
                value=st.session_state.notifications_enabled,
                help="Enable desktop notifications for significant market moves"
            )
        
        st.sidebar.divider()
        
        # Watchlist customization
        st.sidebar.subheader("📋 Watchlist Settings")
        watchlist_input = st.sidebar.text_area(
            "Custom Watchlist (comma-separated)",
            value=",".join(self.default_watchlist),
            help="Enter ticker symbols separated by commas"
        )
        
        custom_watchlist = [symbol.strip().upper() for symbol in watchlist_input.split(",") if symbol.strip()]
        
        # Status indicators
        st.sidebar.divider()
        st.sidebar.subheader("📡 System Status")
        
        # API status
        self.show_api_status()
        
        # Last update time
        if self.last_update:
            st.sidebar.write(f"🕒 Last Update: {self.last_update.strftime('%H:%M:%S')}")
        
        return custom_watchlist

    def show_api_status(self):
        """Display API connection status indicators."""
        api_status = self.check_api_connectivity()
        
        for api_name, status in api_status.items():
            color = "green" if status else "red"
            st.sidebar.markdown(
                f'<span class="status-indicator status-{color}"></span>{api_name}',
                unsafe_allow_html=True
            )

    def check_api_connectivity(self) -> Dict[str, bool]:
        """Check connectivity to various APIs."""
        status = {}
        
        # FMP API
        try:
            fmp_key = os.getenv("FMP_API_KEY")
            if fmp_key:
                response = requests.get(
                    f"https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={fmp_key}",
                    timeout=5
                )
                status["FMP API"] = response.status_code == 200
            else:
                status["FMP API"] = False
        except:
            status["FMP API"] = False
        
        # yfinance (test with simple import)
        try:
            import yfinance as yf
            status["yfinance"] = True
        except:
            status["yfinance"] = False
        
        # Local modules
        status["MacroIntel Core"] = MODULES_AVAILABLE
        
        return status

    def refresh_all_data(self):
        """Refresh all dashboard data."""
        self.last_update = datetime.now()
        self.data_cache.clear()
        
        # Show refresh indicator
        with st.spinner("🔄 Refreshing dashboard data..."):
            time.sleep(1)  # Brief pause for UX
        
        # Send notification if enabled
        if (st.session_state.notifications_enabled and 
            NOTIFICATIONS_AVAILABLE and 
            time.time() - st.session_state.last_notification > 300):  # Max 1 notification per 5 min
            
            self.send_notification(
                "MacroIntel Dashboard",
                "Data refreshed successfully",
                timeout=3
            )
            st.session_state.last_notification = time.time()

    def send_notification(self, title: str, message: str, timeout: int = 5):
        """Send desktop notification."""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="MacroIntel",
                timeout=timeout
            )
        except Exception as e:
            st.sidebar.warning(f"Notification failed: {e}")

    def show_economic_calendar(self):
        """Display live economic calendar."""
        st.subheader("📅 Economic Calendar")
        
        try:
            if not MODULES_AVAILABLE:
                st.error("Economic calendar module not available")
                return
                
            # Use cached data if available and recent
            cache_key = "economic_calendar"
            if (cache_key in self.data_cache and 
                time.time() - self.data_cache[cache_key]['timestamp'] < 1800):  # 30 min cache
                events_data = self.data_cache[cache_key]['data']
            else:
                # Fetch fresh data
                with st.spinner("📅 Loading economic calendar..."):
                    calendar_tracker = EconomicCalendarTracker()
                    events = calendar_tracker.fetch_economic_events()
                    
                    if events:
                        # Convert to DataFrame for display
                        events_df = pd.DataFrame(events)
                        events_df['date'] = pd.to_datetime(events_df['date'])
                        
                        # Filter for next 7 days
                        end_date = datetime.now() + timedelta(days=7)
                        events_df = events_df[events_df['date'] <= end_date]
                        
                        # Sort by date and impact
                        impact_order = {'High': 3, 'Medium': 2, 'Low': 1}
                        events_df['impact_score'] = events_df['impact'].map(impact_order)
                        events_df = events_df.sort_values(['date', 'impact_score'], ascending=[True, False])
                        
                        events_data = events_df.head(20)  # Show top 20 events
                        
                        # Cache the data
                        self.data_cache[cache_key] = {
                            'data': events_data,
                            'timestamp': time.time()
                        }
                    else:
                        events_data = pd.DataFrame()
            
            if not events_data.empty:
                # Display events in a nice format
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    for _, event in events_data.iterrows():
                        impact_color = {
                            'High': '#dc3545',
                            'Medium': '#ffc107', 
                            'Low': '#28a745'
                        }.get(event['impact'], '#6c757d')
                        
                        st.markdown(f"""
                        <div style="background: white; border-left: 4px solid {impact_color}; padding: 10px; margin: 5px 0; border-radius: 5px;">
                            <strong>{event['event']}</strong><br>
                            <small>📅 {event['date'].strftime('%Y-%m-%d %H:%M')} | 
                            🌍 {event.get('country', 'N/A')} | 
                            📊 {event['impact']} Impact</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    # Impact distribution
                    impact_counts = events_data['impact'].value_counts()
                    fig = px.pie(
                        values=impact_counts.values,
                        names=impact_counts.index,
                        title="Impact Distribution",
                        color_discrete_map={
                            'High': '#dc3545',
                            'Medium': '#ffc107',
                            'Low': '#28a745'
                        }
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
            else:
                st.info("📅 No economic events available")
                
        except Exception as e:
            st.error(f"❌ Error loading economic calendar: {str(e)}")

    def show_watchlist_overview(self, watchlist: List[str]):
        """Display watchlist with live data."""
        st.subheader("📊 Live Watchlist")
        
        try:
            # Fetch ticker data
            ticker_data = {}
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, symbol in enumerate(watchlist):
                status_text.text(f"Fetching {symbol}...")
                progress_bar.progress((i + 1) / len(watchlist))
                
                try:
                    data = _fetch_ticker_data(symbol)
                    if data:
                        ticker_data[symbol] = data
                except Exception as e:
                    st.warning(f"❌ Failed to fetch {symbol}: {e}")
                    continue
            
            progress_bar.empty()
            status_text.empty()
            
            if ticker_data:
                # Create summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                # Calculate summary stats
                gains = sum(1 for data in ticker_data.values() if data['pct_change_5d'] > 0)
                losses = sum(1 for data in ticker_data.values() if data['pct_change_5d'] < 0)
                avg_change = sum(data['pct_change_5d'] for data in ticker_data.values()) / len(ticker_data)
                high_vol_count = sum(1 for data in ticker_data.values() if data['volatility_tag'] == 'High')
                
                with col1:
                    st.metric("📈 Gainers", gains, delta=f"{gains}/{len(ticker_data)}")
                
                with col2:
                    st.metric("📉 Losers", losses, delta=f"{losses}/{len(ticker_data)}")
                
                with col3:
                    st.metric("📊 Avg Change", f"{avg_change:.2f}%", delta="5-day")
                
                with col4:
                    st.metric("⚡ High Vol", high_vol_count, delta="assets")
                
                # Display individual ticker cards
                cols = st.columns(3)
                for i, (symbol, data) in enumerate(ticker_data.items()):
                    col_idx = i % 3
                    
                    with cols[col_idx]:
                        # Determine colors
                        change_color = "#28a745" if data['pct_change_5d'] > 0 else "#dc3545" if data['pct_change_5d'] < 0 else "#6c757d"
                        trend_icon = "📈" if data['trend_direction'] == "Up" else "📉" if data['trend_direction'] == "Down" else "➡️"
                        
                        # Determine sentiment (simplified)
                        sentiment = "Bullish" if data['pct_change_5d'] > 1 else "Bearish" if data['pct_change_5d'] < -1 else "Neutral"
                        
                        st.markdown(f"""
                        <div class="ticker-card">
                            <h4>{symbol} {trend_icon}</h4>
                            <h2 style="color: {change_color};">{data['pct_change_5d']:+.2f}%</h2>
                            <p><strong>Price:</strong> ${data['current_price']:.2f}</p>
                            <p><strong>Volatility:</strong> {data['volatility_tag']}</p>
                            <p><strong>Sentiment:</strong> {sentiment}</p>
                            <small>Source: {data.get('source', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Performance chart
                st.subheader("📈 Performance Overview")
                
                # Create performance chart
                symbols = list(ticker_data.keys())
                changes = [ticker_data[symbol]['pct_change_5d'] for symbol in symbols]
                colors = ['green' if change > 0 else 'red' if change < 0 else 'gray' for change in changes]
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=symbols,
                        y=changes,
                        marker_color=colors,
                        text=[f"{change:+.2f}%" for change in changes],
                        textposition='auto',
                    )
                ])
                
                fig.update_layout(
                    title="5-Day Performance (%)",
                    xaxis_title="Assets",
                    yaxis_title="% Change",
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning("⚠️ No ticker data available")
                
        except Exception as e:
            st.error(f"❌ Error loading watchlist: {str(e)}")

    def show_regime_analysis(self):
        """Display regime score and strategy recommendations."""
        st.subheader("🎯 Regime Analysis")
        
        try:
            # Load regime data
            regime_data = load_regime_score_data()
            
            if regime_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Regime score display
                    regime_score = regime_data.get('total_score', 50)
                    regime_classification = regime_data.get('regime_classification', 'Neutral')
                    
                    # Color based on score
                    if regime_score > 70:
                        color = "#28a745"  # Green
                    elif regime_score > 30:
                        color = "#ffc107"  # Yellow
                    else:
                        color = "#dc3545"  # Red
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>📊 Regime Score</h3>
                        <h1 style="color: {color};">{regime_score:.1f}</h1>
                        <p>{regime_classification}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Strategy recommendation
                    if regime_score > 70:
                        strategy = "Aggressive Growth"
                        tier = "Tier 3"
                    elif regime_score > 50:
                        strategy = "Moderate Growth"
                        tier = "Tier 2"
                    elif regime_score > 30:
                        strategy = "Conservative"
                        tier = "Tier 1"
                    else:
                        strategy = "Defensive"
                        tier = "Cash/Bonds"
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>🎯 Strategy Tier</h3>
                        <h2>{tier}</h2>
                        <p>{strategy}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Component breakdown chart
                    components = regime_data.get('component_breakdown', {})
                    if components:
                        component_names = []
                        component_scores = []
                        
                        for comp_name, comp_data in components.items():
                            if isinstance(comp_data, dict) and 'score' in comp_data:
                                component_names.append(comp_name.replace('_', ' ').title())
                                component_scores.append(comp_data['score'])
                        
                        if component_names:
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=component_names,
                                    y=component_scores,
                                    marker_color=['#28a745' if score > 0 else '#dc3545' for score in component_scores]
                                )
                            ])
                            
                            fig.update_layout(
                                title="Regime Components",
                                xaxis_title="Components",
                                yaxis_title="Score",
                                height=300
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                
                # Additional metrics
                col3, col4, col5 = st.columns(3)
                
                with col3:
                    fear_greed = regime_data.get('component_breakdown', {}).get('fear_greed', {}).get('raw_score', 50)
                    st.metric("😨 Fear & Greed", f"{fear_greed}")
                
                with col4:
                    vix = regime_data.get('component_breakdown', {}).get('volatility', {}).get('raw_score', 20)
                    st.metric("⚡ VIX Level", f"{vix:.1f}")
                
                with col5:
                    timestamp = regime_data.get('timestamp', '')
                    if timestamp:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        st.metric("🕒 Last Updated", dt.strftime('%m/%d %H:%M'))
                
            else:
                st.info("📊 Regime analysis data not available")
                
        except Exception as e:
            st.error(f"❌ Error loading regime analysis: {str(e)}")

    def show_live_charts(self, watchlist: List[str]):
        """Display live chart previews."""
        st.subheader("📈 Live Charts")
        
        try:
            # Chart type selector
            chart_type = st.selectbox(
                "Chart Type",
                ["Performance", "Volatility", "Correlation", "Volume"]
            )
            
            # Time period selector
            period = st.selectbox(
                "Time Period", 
                ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
            )
            
            if chart_type == "Performance":
                self.show_performance_chart(watchlist, period)
            elif chart_type == "Volatility":
                self.show_volatility_chart(watchlist, period)
            elif chart_type == "Correlation":
                self.show_correlation_chart(watchlist, period)
            elif chart_type == "Volume":
                self.show_volume_chart(watchlist, period)
                
        except Exception as e:
            st.error(f"❌ Error displaying charts: {str(e)}")

    def show_performance_chart(self, watchlist: List[str], period: str):
        """Show performance comparison chart."""
        try:
            import yfinance as yf
            
            # Fetch data for multiple symbols
            data = {}
            for symbol in watchlist[:6]:  # Limit to 6 for readability
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)
                    if not hist.empty:
                        # Calculate normalized performance
                        hist['normalized'] = (hist['Close'] / hist['Close'].iloc[0] - 1) * 100
                        data[symbol] = hist
                except:
                    continue
            
            if data:
                fig = go.Figure()
                
                for symbol, df in data.items():
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['normalized'],
                        mode='lines',
                        name=symbol,
                        line=dict(width=2)
                    ))
                
                fig.update_layout(
                    title=f"Performance Comparison ({period})",
                    xaxis_title="Date",
                    yaxis_title="Performance (%)",
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ No chart data available")
                
        except Exception as e:
            st.error(f"❌ Error creating performance chart: {e}")

    def show_volatility_chart(self, watchlist: List[str], period: str):
        """Show volatility comparison chart."""
        try:
            import yfinance as yf
            
            volatilities = {}
            for symbol in watchlist[:8]:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)
                    if not hist.empty and len(hist) > 1:
                        returns = hist['Close'].pct_change().dropna()
                        vol = returns.std() * 100  # Convert to percentage
                        volatilities[symbol] = vol
                except:
                    continue
            
            if volatilities:
                symbols = list(volatilities.keys())
                vols = list(volatilities.values())
                colors = ['red' if vol > 3 else 'orange' if vol > 1.5 else 'green' for vol in vols]
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=symbols,
                        y=vols,
                        marker_color=colors,
                        text=[f"{vol:.2f}%" for vol in vols],
                        textposition='auto',
                    )
                ])
                
                fig.update_layout(
                    title=f"Volatility Comparison ({period})",
                    xaxis_title="Assets",
                    yaxis_title="Daily Volatility (%)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ No volatility data available")
                
        except Exception as e:
            st.error(f"❌ Error creating volatility chart: {e}")

    def show_correlation_chart(self, watchlist: List[str], period: str):
        """Show correlation heatmap."""
        try:
            import yfinance as yf
            
            # Fetch price data
            price_data = {}
            for symbol in watchlist[:8]:  # Limit for performance
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)
                    if not hist.empty:
                        price_data[symbol] = hist['Close']
                except:
                    continue
            
            if len(price_data) > 1:
                df = pd.DataFrame(price_data)
                correlation_matrix = df.corr()
                
                fig = px.imshow(
                    correlation_matrix,
                    color_continuous_scale='RdBu_r',
                    aspect='auto',
                    title=f"Asset Correlation Matrix ({period})"
                )
                
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Insufficient data for correlation analysis")
                
        except Exception as e:
            st.error(f"❌ Error creating correlation chart: {e}")

    def show_volume_chart(self, watchlist: List[str], period: str):
        """Show volume analysis chart."""
        try:
            import yfinance as yf
            
            # Get volume data for a few key symbols
            volume_data = {}
            for symbol in watchlist[:4]:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)
                    if not hist.empty:
                        volume_data[symbol] = hist['Volume']
                except:
                    continue
            
            if volume_data:
                fig = make_subplots(
                    rows=len(volume_data), cols=1,
                    subplot_titles=list(volume_data.keys()),
                    shared_xaxes=True
                )
                
                for i, (symbol, volume) in enumerate(volume_data.items(), 1):
                    fig.add_trace(
                        go.Scatter(
                            x=volume.index,
                            y=volume,
                            name=symbol,
                            fill='tonexty' if i > 1 else 'tozeroy'
                        ),
                        row=i, col=1
                    )
                
                fig.update_layout(
                    title=f"Volume Analysis ({period})",
                    height=600,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ No volume data available")
                
        except Exception as e:
            st.error(f"❌ Error creating volume chart: {e}")

    def show_recent_news(self):
        """Display recent news articles."""
        st.subheader("📰 Recent News")
        
        try:
            # Load recent articles
            cache_key = "recent_news"
            if (cache_key in self.data_cache and 
                time.time() - self.data_cache[cache_key]['timestamp'] < 900):  # 15 min cache
                articles = self.data_cache[cache_key]['data']
            else:
                with st.spinner("📰 Loading recent news..."):
                    # Try to load from existing data first
                    polygon_articles = load_polygon_articles()
                    
                    if not polygon_articles:
                        # Fetch fresh news if no cached data
                        if MODULES_AVAILABLE:
                            try:
                                summarizer = SummarizerAgent()
                                news_result = summarizer.run()
                                articles = news_result.get('articles', [])[:10]
                            except:
                                articles = []
                        else:
                            articles = []
                    else:
                        articles = polygon_articles[:10]
                    
                    # Cache the articles
                    self.data_cache[cache_key] = {
                        'data': articles,
                        'timestamp': time.time()
                    }
            
            if articles:
                # News summary metrics
                col1, col2, col3 = st.columns(3)
                
                bullish_count = sum(1 for article in articles if article.get('tone', 'Neutral') == 'Bullish')
                bearish_count = sum(1 for article in articles if article.get('tone', 'Neutral') == 'Bearish')
                sources = set(article.get('source', 'Unknown') for article in articles)
                
                with col1:
                    st.metric("📈 Bullish", bullish_count)
                
                with col2:
                    st.metric("📉 Bearish", bearish_count)
                
                with col3:
                    st.metric("📡 Sources", len(sources))
                
                # Display articles
                for i, article in enumerate(articles):
                    sentiment = article.get('tone', 'Neutral')
                    sentiment_color = {
                        'Bullish': '#28a745',
                        'Bearish': '#dc3545',
                        'Neutral': '#6c757d'
                    }.get(sentiment, '#6c757d')
                    
                    source = article.get('source', 'Unknown').title()
                    timestamp = article.get('timestamp', '')
                    title = article.get('title', 'No title')
                    summary = article.get('summary', 'No summary available')
                    url = article.get('url', '#')
                    
                    # Parse timestamp for display
                    try:
                        if timestamp:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime('%m/%d %H:%M')
                        else:
                            time_str = 'Unknown'
                    except:
                        time_str = 'Unknown'
                    
                    st.markdown(f"""
                    <div class="news-card">
                        <h4><a href="{url}" target="_blank" style="text-decoration: none; color: #007bff;">{title}</a></h4>
                        <p>{summary[:200]}{'...' if len(summary) > 200 else ''}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                            <div>
                                <span style="background: {sentiment_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">
                                    {sentiment}
                                </span>
                                <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">
                                    {source}
                                </span>
                            </div>
                            <small style="color: #6c757d;">🕒 {time_str}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            else:
                st.info("📰 No recent news available")
                
        except Exception as e:
            st.error(f"❌ Error loading news: {str(e)}")

    def check_auto_refresh(self):
        """Check if auto-refresh should trigger."""
        if (st.session_state.auto_refresh and 
            self.last_update and 
            (datetime.now() - self.last_update).seconds > self.update_interval):
            
            self.refresh_all_data()
            st.rerun()

def main():
    """Main application entry point."""
    dashboard = MacroIntelDashboard()
    
    # Show header
    dashboard.show_header()
    
    # Show sidebar and get watchlist
    watchlist = dashboard.show_sidebar()
    
    # Check for auto-refresh
    dashboard.check_auto_refresh()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "📅 Calendar", 
        "📈 Charts", 
        "🎯 Regime", 
        "📰 News"
    ])
    
    with tab1:
        st.markdown("### 📊 Market Overview")
        dashboard.show_watchlist_overview(watchlist)
    
    with tab2:
        dashboard.show_economic_calendar()
    
    with tab3:
        dashboard.show_live_charts(watchlist)
    
    with tab4:
        dashboard.show_regime_analysis()
    
    with tab5:
        dashboard.show_recent_news()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #6c757d;'>"
        "📊 MacroIntel Dashboard | Real-time Financial Intelligence"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 