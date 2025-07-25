import os
import smtplib
import requests
import json
import glob
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from dotenv import load_dotenv
from email.utils import formataddr
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

# Import chart generation capabilities
try:
    from agents.chart_generator_agent import ChartGeneratorAgent
    from core.enhanced_visualizations import EnhancedVisualizations
    CHART_GENERATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Chart generation not available: {e}")
    ChartGeneratorAgent = None
    EnhancedVisualizations = None
    CHART_GENERATION_AVAILABLE = False

# Load environment variables at the top
load_dotenv(dotenv_path="config/.env")

# Import visual query engine
try:
    from core.visual_query_engine import generate_extreme_fear_chart
    VISUAL_ENGINE_AVAILABLE = True
except ImportError:
    print("⚠️ Visual query engine not available - charts will be skipped")
    VISUAL_ENGINE_AVAILABLE = False

# Import agent pipeline
try:
    from macrointel_agents import run_agents_pipeline
    AGENT_PIPELINE_AVAILABLE = True
except ImportError:
    print("⚠️ Agent pipeline not available - agent results will be skipped")
    AGENT_PIPELINE_AVAILABLE = False

def sanitize_email_text(text: str) -> str:
    """
    Sanitize email text content by converting emojis, replacing line breaks,
    and stripping illegal Unicode characters that break SMTP clients.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text safe for email transmission
    """
    if not text:
        return text
    
    # Convert to string if needed
    text = str(text)
    
    # Convert emojis to text equivalents
    emoji_mappings = {
        '📈': 'UP',
        '📉': 'DOWN', 
        '➡️': 'FLAT',
        '✅': 'SUCCESS',
        '❌': 'ERROR',
        '⚠️': 'WARNING',
        '🔄': 'RETRY',
        '📊': 'CHART',
        '📰': 'NEWS',
        '🏦': 'BANK',
        '🤖': 'AI',
        '📅': 'CALENDAR',
        '🎯': 'TARGET',
        '💡': 'IDEA',
        '🚀': 'LAUNCH',
        '🔥': 'HOT',
        '💎': 'DIAMOND',
        '🎪': 'CIRCUS',
        '🎭': 'THEATER',
        '🎨': 'ART',
        '🎬': 'MOVIE',
        '🎵': 'MUSIC',
        '🎮': 'GAME',
        '🎲': 'DICE',
        '📋': 'LIST',
        '🔗': 'LINK',
        '📱': 'MOBILE',
        '💻': 'COMPUTER',
        '🌐': 'WEB',
        '📞': 'PHONE',
        '📧': 'EMAIL',
        '📨': 'MAIL',
        '📩': 'INBOX',
        '📤': 'SEND',
        '📥': 'RECEIVE',
        '🔍': 'SEARCH',
        '🔎': 'FIND',
        '📝': 'NOTE',
        '✏️': 'EDIT',
        '🗑️': 'DELETE',
        '🔄': 'REFRESH',
        '⚙️': 'SETTINGS',
        '🔧': 'TOOLS',
        '🛠️': 'REPAIR',
        '🔨': 'HAMMER',
        '🔩': 'NUT',
        '⚡': 'FAST',
        '🚫': 'BLOCKED',
        '⏸️': 'PAUSE',
        '▶️': 'PLAY',
        '⏹️': 'STOP',
        '⏭️': 'NEXT',
        '⏮️': 'PREVIOUS',
        '🔀': 'SHUFFLE',
        '🔁': 'REPEAT',
        '🔂': 'REPEAT_ONE',
        '🔊': 'VOLUME_UP',
        '🔉': 'VOLUME_DOWN',
        '🔇': 'MUTE',
        '🔈': 'VOLUME_LOW',
        '🔉': 'VOLUME_MEDIUM',
        '🔊': 'VOLUME_HIGH',
        '📢': 'ANNOUNCEMENT',
        '📣': 'MEGAPHONE',
        '🔔': 'BELL',
        '🔕': 'BELL_OFF',
        '⏰': 'ALARM',
        '⏱️': 'STOPWATCH',
        '⏲️': 'TIMER',
        '🕐': 'TIME',
        '🕑': 'TIME_2',
        '🕒': 'TIME_3',
        '🕓': 'TIME_4',
        '🕔': 'TIME_5',
        '🕕': 'TIME_6',
        '🕖': 'TIME_7',
        '🕗': 'TIME_8',
        '🕘': 'TIME_9',
        '🕙': 'TIME_10',
        '🕚': 'TIME_11',
        '🕛': 'TIME_12'
    }
    
    # Replace emojis with text equivalents
    for emoji, replacement in emoji_mappings.items():
        text = text.replace(emoji, replacement)
    
    # Strip non-ASCII characters that might cause encoding issues
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    # Replace line breaks with HTML <br/> tags as requested
    text = text.replace("\\n", "<br/>").replace("\n", "<br/>").replace("\\r", "<br/>")
    
    # Normalize whitespace and strip illegal Unicode characters
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = text.strip()
    
    # Strip illegal Unicode characters that break SMTP clients
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    # Ensure proper UTF-8 encoding
    try:
        text = text.encode('utf-8').decode('utf-8')
    except UnicodeError:
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
    
    return text


def load_regime_score_data():
    """
    Load the most recent regime score data from output directory.
    
    Returns:
        Dict containing regime score data or None if not found
    """
    try:
        # Look for regime score files in output directory
        output_dir = Path("output")
        if not output_dir.exists():
            return None
        
        # Find all regime score files
        regime_files = list(output_dir.glob("regime_score_*.json"))
        if not regime_files:
            return None
        
        # Get the most recent file
        latest_file = max(regime_files, key=lambda x: x.stat().st_mtime)
        
        # Load and parse the JSON data
        with open(latest_file, 'r', encoding='utf-8') as f:
            regime_data = json.load(f)
        
        print(f"✅ Loaded regime score data from: {latest_file}")
        return regime_data
        
    except Exception as e:
        print(f"⚠️ Error loading regime score data: {e}")
        return None

def generate_regime_summary_html(regime_data):
    """
    Generate HTML for the market regime summary section.
    
    Args:
        regime_data: Dict containing regime score data
        
    Returns:
        HTML string for regime summary section
    """
    if not regime_data:
        return """
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #6c757d;">
            <h3>📊 Market Regime Summary</h3>
            <p><em>Regime score data not available</em></p>
        </div>
        """
    
    try:
        total_score = regime_data.get('total_score', 0)
        strategy = regime_data.get('strategy_recommendation', 'Unknown')
        instrument = regime_data.get('instrument', 'Unknown')
        risk_allocation = regime_data.get('risk_allocation', 'Unknown')
        classification = regime_data.get('regime_classification', 'Unknown')
        timestamp = regime_data.get('timestamp', 'Unknown')
        
        # Get component scores
        component_breakdown = regime_data.get('component_breakdown', {})
        
        # Determine score color based on classification
        score_color = {
            'Extreme Fear': '#dc3545',
            'Fear': '#fd7e14', 
            'Neutral': '#6c757d',
            'Greed': '#28a745',
            'Extreme Greed': '#20c997'
        }.get(classification, '#6c757d')
        
        html = f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {score_color};">
            <h3 style="margin-top: 0; color: #2c3e50;">📊 Market Regime Summary</h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                <div style="background: white; padding: 15px; border-radius: 5px;">
                    <h4 style="margin-top: 0; color: #2c3e50;">🎯 Strategy</h4>
                    <p style="font-size: 18px; font-weight: bold; color: {score_color}; margin: 5px 0;">{strategy}</p>
                    <p style="margin: 5px 0;"><strong>Instrument:</strong> {instrument}</p>
                    <p style="margin: 5px 0;"><strong>Risk Allocation:</strong> {risk_allocation}</p>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 5px;">
                    <h4 style="margin-top: 0; color: #2c3e50;">📈 Score Overview</h4>
                    <p style="font-size: 24px; font-weight: bold; color: {score_color}; margin: 5px 0;">{total_score:.1f}/100</p>
                    <p style="margin: 5px 0;"><strong>Classification:</strong> {classification}</p>
                    <p style="margin: 5px 0; font-size: 12px; color: #6c757d;">{timestamp}</p>
                </div>
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 5px;">
                <h4 style="margin-top: 0; color: #2c3e50;">🔍 Component Breakdown</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
        """
        
        # Add component scores
        for component, data in component_breakdown.items():
            if isinstance(data, dict):
                raw_score = data.get('raw_score', 0)
                interpretation = data.get('interpretation', '')
                
                # Determine component color
                if raw_score < 30:
                    comp_color = '#dc3545'  # Red for low scores
                elif raw_score < 50:
                    comp_color = '#fd7e14'  # Orange for moderate scores
                elif raw_score < 70:
                    comp_color = '#6c757d'  # Gray for neutral scores
                elif raw_score < 85:
                    comp_color = '#28a745'  # Green for good scores
                else:
                    comp_color = '#20c997'  # Teal for excellent scores
                
                component_name = component.replace('_', ' ').title()
                html += f"""
                    <div style="border-left: 3px solid {comp_color}; padding-left: 10px;">
                        <strong>{component_name}:</strong> {raw_score:.1f}/100<br>
                        <small style="color: #6c757d;">{interpretation}</small>
                    </div>
                """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        return html
        
    except Exception as e:
        print(f"⚠️ Error generating regime summary HTML: {e}")
        return """
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #6c757d;">
            <h3>📊 Market Regime Summary</h3>
            <p><em>Error loading regime score data</em></p>
        </div>
        """

def generate_fear_greed_placeholder():
    """Generate Fear & Greed index using real API or return data unavailable message"""
    fear_greed_api_key = os.getenv("FEAR_GREED_API_KEY")
    fear_greed_api_host = "cnn-fear-and-greed-index.p.rapidapi.com"  # Fixed host
    
    if not fear_greed_api_key:
        print("⚠️ FEAR_GREED_API_KEY not found in environment variables")
        return "Fear & Greed Index: Data Unavailable [API Key Missing]"
    
    try:
        url = "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/index"
        headers = {
            "x-rapidapi-key": fear_greed_api_key,  # Fixed header key
            "x-rapidapi-host": fear_greed_api_host  # Fixed header key
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            score = data.get("fear_and_greed", {}).get("score", 50)
            classification = data.get("fear_and_greed", {}).get("rating", "Neutral")
            
            # Map classification to emoji and description
            classification_map = {
                "extreme fear": "😱",
                "fear": "😨", 
                "neutral": "😐",
                "greed": "😏",
                "extreme greed": "🤑"
            }
            
            emoji = classification_map.get(classification.lower(), "📊")
            
            return f"Fear & Greed Index: {score} ({classification.title()}) {emoji} - Market showing {classification} sentiment"
        else:
            print(f"⚠️ Fear & Greed API error: {response.status_code}")
            return "Fear & Greed Index: Data Unavailable [API Error]"
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Fear & Greed API request failed: {str(e)}")
        return "Fear & Greed Index: Data Unavailable [API Unavailable]"
    except Exception as e:
        print(f"⚠️ Fear & Greed API error: {str(e)}")
        return "Fear & Greed Index: Data Unavailable [API Error]"

def generate_sector_heatmap_placeholder():
    """Generate a placeholder for sector heatmap"""
    heatmap_html = "<h3>📊 Sector Heatmap</h3><p>Data Unavailable - Sector performance data could not be fetched</p>"
    
    return heatmap_html

def generate_sentiment_gauge_placeholder():
    """Generate a placeholder for sentiment gauge"""
    gauge_html = """
    <h3>📊 Market Sentiment</h3>
    <div style="background: #f0f0f0; padding: 10px; border-radius: 5px;">
        <strong>Sentiment Score:</strong> Data Unavailable<br>
        <p>Market sentiment data could not be fetched</p>
    </div>
    """
    
    return gauge_html

def generate_mini_ticker_cards(watchlist=None, fear_greed_score=50):
    """
    Generate compact HTML ticker cards for watchlist assets.
    
    Args:
        watchlist: List of ticker symbols (default: common ETFs and stocks)
        fear_greed_score: Current Fear & Greed Index score for sentiment fallback
        
    Returns:
        HTML string containing ticker cards in a grid layout
    """
    # Default watchlist if none provided
    if not watchlist:
        watchlist = ["SPY", "QQQ", "IWM", "GLD", "TLT", "^VIX", "AAPL", "TSLA", "NVDA", "MSFT", "BTC-USD", "^DXY"]
    
    print(f"📋 Generating mini ticker cards for {len(watchlist)} symbols...")
    
    ticker_data = {}
    
    # Fetch data for each ticker
    for symbol in watchlist:
        try:
            ticker_info = _fetch_ticker_data(symbol)
            if ticker_info:
                ticker_data[symbol] = ticker_info
                print(f"✅ {symbol}: {ticker_info['pct_change_5d']:+.2f}% ({ticker_info['trend_direction']})")
            else:
                print(f"❌ Failed to fetch data for {symbol}")
                
        except Exception as e:
            print(f"⚠️ Error fetching {symbol}: {str(e)}")
            continue
    
    if not ticker_data:
        return """
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #6c757d;">
            <h3>📋 Market Snapshot - Ticker Cards</h3>
            <p><em>Ticker data not available</em></p>
        </div>
        """
    
    # Generate HTML cards
    cards_html = f"""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: white;">📋 Market Snapshot - Ticker Cards</h3>
        <p style="margin-bottom: 20px; opacity: 0.9;">Real-time performance overview with 5-day trends, volatility metrics, and sentiment analysis</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px;">
    """
    
    for symbol, data in ticker_data.items():
        card_html = _generate_single_ticker_card(symbol, data, fear_greed_score)
        cards_html += card_html
    
    cards_html += """
        </div>
        
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2); font-size: 12px; opacity: 0.8;">
            <p style="margin: 0;"><strong>Data Sources:</strong> yfinance, FMP API | <strong>Updated:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M UTC') + """</p>
        </div>
    </div>
    """
    
    print(f"✅ Generated {len(ticker_data)} ticker cards successfully")
    return cards_html

def _fetch_ticker_data(symbol):
    """
    Fetch 5-day performance and volatility data for a single ticker.
    
    Args:
        symbol: Ticker symbol to fetch
        
    Returns:
        Dict with performance metrics or None if failed
    """
    try:
        # Try yfinance first
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d", interval="1d")
            
            if not hist.empty and len(hist) >= 2:
                # Calculate 5-day performance
                start_price = float(hist['Close'].iloc[0])
                end_price = float(hist['Close'].iloc[-1])
                pct_change_5d = ((end_price - start_price) / start_price) * 100
                
                # Calculate volatility (daily returns standard deviation)
                returns = hist['Close'].pct_change().dropna()
                daily_vol = returns.std() * 100
                
                # Determine trend direction
                if pct_change_5d > 0.5:
                    trend_direction = "Up"
                elif pct_change_5d < -0.5:
                    trend_direction = "Down"
                else:
                    trend_direction = "Flat"
                
                # Determine volatility category
                if daily_vol < 1.0:
                    volatility_tag = "Low"
                elif daily_vol < 2.5:
                    volatility_tag = "Moderate"
                else:
                    volatility_tag = "High"
                
                return {
                    'pct_change_5d': pct_change_5d,
                    'trend_direction': trend_direction,
                    'volatility_tag': volatility_tag,
                    'daily_volatility': daily_vol,
                    'current_price': end_price,
                    'source': 'yfinance'
                }
                
        except Exception as e:
            print(f"⚠️ yfinance failed for {symbol}: {e}")
        
        # Try FMP as fallback
        try:
            api_key = os.getenv("FMP_API_KEY")
            if api_key:
                from datetime import datetime, timedelta
                
                # FMP symbol mapping for special cases
                fmp_symbol_map = {
                    'BTC-USD': 'BTCUSD',
                    'DXY': 'DXY',
                    '^VIX': 'VIX',
                    'VIX': 'VIX'
                }
                
                fmp_symbol = fmp_symbol_map.get(symbol, symbol)
                url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{fmp_symbol}"
                params = {
                    "apikey": api_key,
                    "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    "to": datetime.now().strftime("%Y-%m-%d")
                }
                
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if "historical" in data and data["historical"]:
                        import pandas as pd
                        df = pd.DataFrame(data["historical"])
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date').sort_index()
                        
                        if len(df) >= 2:
                            start_price = float(df['close'].iloc[0])
                            end_price = float(df['close'].iloc[-1])
                            pct_change_5d = ((end_price - start_price) / start_price) * 100
                            
                            returns = df['close'].pct_change().dropna()
                            daily_vol = returns.std() * 100
                            
                            # Determine trend and volatility
                            if pct_change_5d > 0.5:
                                trend_direction = "Up"
                            elif pct_change_5d < -0.5:
                                trend_direction = "Down"
                            else:
                                trend_direction = "Flat"
                            
                            if daily_vol < 1.0:
                                volatility_tag = "Low"
                            elif daily_vol < 2.5:
                                volatility_tag = "Moderate"
                            else:
                                volatility_tag = "High"
                            
                            return {
                                'pct_change_5d': pct_change_5d,
                                'trend_direction': trend_direction,
                                'volatility_tag': volatility_tag,
                                'daily_volatility': daily_vol,
                                'current_price': end_price,
                                'source': 'fmp'
                            }
                            
        except Exception as e:
            print(f"⚠️ FMP failed for {symbol}: {e}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error fetching ticker data for {symbol}: {str(e)}")
        return None

def _generate_single_ticker_card(symbol, data, fear_greed_score):
    """
    Generate HTML for a single ticker card.
    
    Args:
        symbol: Ticker symbol
        data: Ticker performance data dict
        fear_greed_score: Fear & Greed score for sentiment fallback
        
    Returns:
        HTML string for the ticker card
    """
    pct_change = data['pct_change_5d']
    trend_direction = data['trend_direction']
    volatility_tag = data['volatility_tag']
    current_price = data['current_price']
    
    # Determine sentiment based on performance and Fear & Greed
    sentiment_label = _determine_sentiment(pct_change, trend_direction, fear_greed_score)
    
    # Color coding based on performance
    if trend_direction == "Up":
        trend_color = "#27ae60"  # Green
        trend_icon = "📈"
    elif trend_direction == "Down":
        trend_color = "#e74c3c"  # Red
        trend_icon = "📉"
    else:
        trend_color = "#95a5a6"  # Gray
        trend_icon = "➡️"
    
    # Volatility color coding
    vol_colors = {
        "Low": "#3498db",      # Blue
        "Moderate": "#f39c12", # Orange
        "High": "#e67e22"      # Dark Orange
    }
    vol_color = vol_colors.get(volatility_tag, "#95a5a6")
    
    # Sentiment color coding
    sentiment_colors = {
        "Bullish": "#27ae60",   # Green
        "Bearish": "#e74c3c",   # Red
        "Neutral": "#95a5a6"    # Gray
    }
    sentiment_color = sentiment_colors.get(sentiment_label, "#95a5a6")
    
    card_html = f"""
    <div style="background: rgba(255,255,255,0.1); border-radius: 8px; padding: 15px; border-left: 4px solid {trend_color}; backdrop-filter: blur(10px);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h4 style="margin: 0; color: white; font-size: 18px; font-weight: bold;">{symbol}</h4>
            <span style="font-size: 20px;">{trend_icon}</span>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
            <div>
                <div style="font-size: 24px; font-weight: bold; color: {trend_color}; margin-bottom: 2px;">
                    {pct_change:+.2f}%
                </div>
                <div style="font-size: 11px; opacity: 0.8;">5-Day Change</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 16px; font-weight: bold; color: white; margin-bottom: 2px;">
                    ${current_price:.2f}
                </div>
                <div style="font-size: 11px; opacity: 0.8;">Current Price</div>
            </div>
        </div>
        
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span style="background: {trend_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">
                {trend_direction}
            </span>
            <span style="background: {vol_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">
                {volatility_tag} Vol
            </span>
            <span style="background: {sentiment_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">
                {sentiment_label}
            </span>
        </div>
    </div>
    """
    
    return card_html

def _determine_sentiment(pct_change, trend_direction, fear_greed_score):
    """
    Determine sentiment label based on performance and market conditions.
    
    Args:
        pct_change: 5-day percent change
        trend_direction: Trend direction (Up/Down/Flat)
        fear_greed_score: Current Fear & Greed Index score
        
    Returns:
        Sentiment label (Bullish/Bearish/Neutral)
    """
    # Base sentiment on performance
    if trend_direction == "Up" and pct_change > 2.0:
        base_sentiment = "Bullish"
    elif trend_direction == "Down" and pct_change < -2.0:
        base_sentiment = "Bearish"
    elif abs(pct_change) < 1.0:
        base_sentiment = "Neutral"
    else:
        # Moderate moves - use Fear & Greed to determine
        if fear_greed_score > 60:
            base_sentiment = "Bullish" if pct_change > 0 else "Neutral"
        elif fear_greed_score < 40:
            base_sentiment = "Bearish" if pct_change < 0 else "Neutral"
        else:
            base_sentiment = "Neutral"
    
    return base_sentiment

def generate_geopolitical_section_html(geopolitical_articles):
    """
    Generate HTML section for Trade War & Geopolitical Tensions.
    
    Args:
        geopolitical_articles: List of articles with geopolitical content
        
    Returns:
        HTML string for geopolitical tensions section
    """
    if not geopolitical_articles:
        return ""
    
    # Filter for high-impact geopolitical articles
    high_impact_articles = [
        article for article in geopolitical_articles 
        if article.get("geopolitical", {}).get("impact_level") == "high"
    ]
    
    # If no high-impact, include medium-impact articles
    if not high_impact_articles:
        high_impact_articles = [
            article for article in geopolitical_articles 
            if article.get("geopolitical", {}).get("impact_level") in ["high", "medium"]
        ]
    
    # Limit to top 5 most relevant articles
    display_articles = high_impact_articles[:5]
    
    if not display_articles:
        return ""
    
    html_content = f"""
    <div style="margin: 20px 0; padding: 15px; background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); border-radius: 8px; color: white;">
        <h3 style="margin-top: 0; color: white;">🌍 Trade War & Geopolitical Tensions</h3>
        <p style="margin-bottom: 15px;">High-impact headlines related to trade policies, geopolitical developments, and supply chain disruptions:</p>
        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px;">
    """
    
    for i, article in enumerate(display_articles, 1):
        geopolitical_data = article.get("geopolitical", {})
        categories = geopolitical_data.get("categories", [])
        keywords_found = geopolitical_data.get("keywords_found", [])
        impact_level = geopolitical_data.get("impact_level", "low")
        
        # Create category badges
        category_badges = []
        category_colors = {
            'tariffs': '#ffc107',      # Yellow
            'china': '#dc3545',        # Red
            'sanctions': '#6f42c1',    # Purple
            'trade': '#17a2b8',        # Teal
            'supply_chains': '#28a745' # Green
        }
        
        for category in categories:
            color = category_colors.get(category, '#6c757d')
            category_display = category.replace('_', ' ').title()
            category_badges.append(f'<span style="background: {color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-right: 5px;">{category_display}</span>')
        
        # Impact level indicator
        impact_color = {
            'high': '#dc3545',    # Red
            'medium': '#ffc107',  # Yellow
            'low': '#6c757d'      # Gray
        }.get(impact_level, '#6c757d')
        
        impact_indicator = f'<span style="background: {impact_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">{impact_level.upper()}</span>'
        
        html_content += f"""
        <div style="margin-bottom: 15px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 5px; border-left: 4px solid white;">
            <div style="font-weight: bold; margin-bottom: 5px;">
                <a href="{article.get('url', '#')}" style="color: white; text-decoration: none;">{i}. {article.get('title', 'Untitled')}</a>
            </div>
            <div style="font-size: 14px; margin-bottom: 8px; opacity: 0.9;">
                {article.get('summary', 'No summary available')[:150]}{'...' if len(article.get('summary', '')) > 150 else ''}
            </div>
            <div style="margin-bottom: 5px;">
                {impact_indicator}
                {''.join(category_badges)}
            </div>
            <div style="font-size: 12px; opacity: 0.8;">
                <strong>Keywords:</strong> {', '.join(keywords_found[:5])} | 
                <strong>Source:</strong> {article.get('source', 'Unknown')} | 
                <strong>Sentiment:</strong> {article.get('sentiment', 'Neutral')}
            </div>
        </div>
        """
    
    html_content += f"""
        </div>
        <p style="margin: 10px 0 5px 0; font-size: 14px;"><strong>Impact Analysis:</strong> {len(display_articles)} high-priority geopolitical developments detected</p>
        <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">Articles analyzed for: tariffs, China relations, sanctions, trade flows, and supply chain disruptions. Impact levels determined by keyword density and cross-category coverage.</p>
    </div>
    """
    
    return html_content

def generate_agent_results_html(agent_results):
    """
    Generate HTML for the agent pipeline results section.
    
    Args:
        agent_results: Dict containing results from run_agents_pipeline()
        
    Returns:
        HTML string for agent results section
    """
    if not agent_results or not agent_results.get('pipeline_completed'):
        return """
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #6c757d;">
            <h3>🤖 AI Agent Analysis</h3>
            <p><em>Agent pipeline results not available</em></p>
        </div>
        """
    
    try:
        html = """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: white;">🤖 AI Agent Analysis</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        """
        
        # News Analysis Section
        if agent_results.get('news_analysis'):
            na = agent_results['news_analysis']
            sentiment_color = {
                'bullish': '#28a745',
                'bearish': '#dc3545',
                'neutral': '#6c757d'
            }.get(na.overall_sentiment, '#6c757d')
            
            # Safely handle potential Series objects
            headlines_count = len(na.headlines) if hasattr(na.headlines, '__len__') else 0
            key_themes_str = ', '.join(na.key_themes) if hasattr(na.key_themes, '__iter__') else 'None'
            
            # Safely calculate average impact score
            if hasattr(na.impact_scores, '__iter__') and len(na.impact_scores) > 0:
                avg_impact = sum(na.impact_scores) / len(na.impact_scores)
            else:
                avg_impact = 0.0
            
            html += f"""
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px;">
                    <h4 style="margin-top: 0; color: white;">📰 News Sentiment</h4>
                    <p style="font-size: 18px; font-weight: bold; color: {sentiment_color}; margin: 5px 0;">
                        {na.overall_sentiment.upper()}
                    </p>
                    <p style="margin: 5px 0;"><strong>Headlines Analyzed:</strong> {headlines_count}</p>
                    <p style="margin: 5px 0;"><strong>Key Themes:</strong> {key_themes_str}</p>
                    <p style="margin: 5px 0;"><strong>Avg Impact:</strong> {avg_impact:.2f}</p>
                </div>
            """
        
        # Strategy Recommendation Section
        if agent_results.get('strategy_recommendation'):
            sr = agent_results['strategy_recommendation']
            tier_color = {
                'conservative': '#28a745',
                'moderate': '#ffc107',
                'aggressive': '#dc3545',
                'defensive': '#17a2b8'
            }.get(sr.recommended_tier, '#6c757d')
            
            html += f"""
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px;">
                    <h4 style="margin-top: 0; color: white;">🎯 Strategy Tier</h4>
                    <p style="font-size: 18px; font-weight: bold; color: {tier_color}; margin: 5px 0;">
                        {sr.recommended_tier.upper()}
                    </p>
                    <p style="margin: 5px 0;"><strong>Confidence:</strong> {sr.confidence:.1%}</p>
                    <p style="margin: 5px 0;"><strong>Regime:</strong> {sr.regime_score:.2f}</p>
                    <p style="margin: 5px 0;"><strong>VIX:</strong> {sr.vix_level:.1f}</p>
                    <p style="margin: 5px 0;"><strong>F&G:</strong> {sr.fear_greed_score}</p>
                </div>
            """
        
        html += """
            </div>
        """
        
        # Instrument Selection Section
        if agent_results.get('instrument_selection'):
            isel = agent_results['instrument_selection']
            html += f"""
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px; margin-top: 15px;">
                <h4 style="margin-top: 0; color: white;">📊 Recommended Instruments</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
            """
            
            # Safely handle allocation weights (could be Series or dict)
            allocation_weights = isel.allocation_weights
            if hasattr(allocation_weights, 'items'):
                # It's a dictionary-like object
                for instrument, weight in allocation_weights.items():
                    percentage = weight * 100
                    html += f"""
                        <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; text-align: center;">
                            <strong>{instrument}</strong><br>
                            <span style="font-size: 16px; font-weight: bold;">{percentage:.0f}%</span>
                        </div>
                    """
            else:
                # Fallback if it's not a dictionary-like object
                html += """
                    <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; text-align: center;">
                        <strong>No allocation data</strong><br>
                        <span style="font-size: 16px; font-weight: bold;">N/A</span>
                    </div>
                """
            
            html += f"""
                </div>
                <p style="margin-top: 10px; margin-bottom: 5px;"><strong>Risk Level:</strong> {isel.risk_level.upper()}</p>
                <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">{isel.reasoning}</p>
            </div>
            """
        
        html += """
        </div>
        """
        
        return html
        
    except Exception as e:
        print(f"⚠️ Error generating agent results HTML: {e}")
        return """
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #6c757d;">
            <h3>🤖 AI Agent Analysis</h3>
            <p><em>Error processing agent results</em></p>
        </div>
        """

def load_polygon_articles():
    """
    Load Polygon articles from the latest swarm execution log.
    
    Returns:
        List of Polygon articles or empty list if not found
    """
    try:
        # Look for swarm execution logs in logs directory
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return []
        
        # Find all swarm execution log files
        log_files = list(logs_dir.glob("swarm_execution_*.json"))
        if not log_files:
            return []
        
        # Get the most recent file
        latest_file = max(log_files, key=lambda x: x.stat().st_mtime)
        
        # Load and parse the JSON data
        with open(latest_file, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        # Extract articles from summarizer agent results
        summarizer_data = log_data.get("agents", {}).get("summarizer", {})
        all_articles = summarizer_data.get("articles", [])
        
        # Filter for Polygon articles
        polygon_articles = []
        for article in all_articles:
            if article.get("source") == "polygon":
                # Convert to standard format
                polygon_articles.append({
                    "title": article.get("title", ""),
                    "summary": article.get("summary", ""),
                    "url": article.get("url", ""),
                    "timestamp": article.get("timestamp", ""),
                    "source": "polygon",
                    "tone": article.get("sentiment", "Neutral"),
                    "affected_tickers": article.get("affected_tickers", "")
                })
        
        print(f"✅ Loaded {len(polygon_articles)} Polygon articles from: {latest_file}")
        return polygon_articles
        
    except Exception as e:
        print(f"⚠️ Error loading Polygon articles: {e}")
        return []

def deduplicate_articles(articles):
    """
    Remove duplicate articles based on title similarity.
    
    Args:
        articles: List of articles to deduplicate
        
    Returns:
        List of deduplicated articles
    """
    if not articles:
        return []
    
    # Create a dictionary to track unique articles by normalized title
    unique_articles = {}
    
    for article in articles:
        # Normalize title for comparison (lowercase, remove extra spaces)
        normalized_title = " ".join(article.get("title", "").lower().split())
        
        # If we haven't seen this title before, add it
        if normalized_title not in unique_articles:
            unique_articles[normalized_title] = article
        else:
            # If we have seen it, keep the one with more content (longer summary)
            existing = unique_articles[normalized_title]
            if len(article.get("summary", "")) > len(existing.get("summary", "")):
                unique_articles[normalized_title] = article
    
    return list(unique_articles.values())

def load_latest_yahoo_futures():
    """
    Load the most recent Yahoo Futures data from output directory (yfinance format).
    Returns a list of futures contracts or empty list if not found.
    """
    try:
        output_dir = Path("output")
        if not output_dir.exists():
            return []
        futures_files = list(output_dir.glob("yahoo_futures_*.json"))
        if not futures_files:
            return []
        latest_file = max(futures_files, key=lambda x: x.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"⚠️ Error loading Yahoo Futures data: {e}")
        return []

def load_latest_barchart_futures():
    """
    Load the most recent Yahoo Top Movers data from output directory (formerly Barchart).
    Now fetches top movers by 24h percent change using Yahoo Finance/yfinance.
    Returns a list of top movers or empty list if not found.
    """
    try:
        output_dir = Path("output")
        if not output_dir.exists():
            return []
        # Check for both old and new filenames for backward compatibility
        futures_files = list(output_dir.glob("barchart_futures_*.json")) + list(output_dir.glob("yahoo_top_movers_*.json"))
        if not futures_files:
            return []
        latest_file = max(futures_files, key=lambda x: x.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"⚠️ Error loading Yahoo Top Movers data: {e}")
        return []

def generate_futures_table_html(futures_data, title):
    """
    Generate an HTML table for a list of futures contracts with a given title.
    """
    if not futures_data:
        return f"""
        <div style='background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #6c757d;'>
            <h3>{title}</h3>
            <p><em>No futures data available.</em></p>
        </div>
        """
    html = f"""
    <div style='background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #007bff;'>
        <h3 style='margin-top: 0; color: #2c3e50;'>{title}</h3>
        <table style='width: 100%; border-collapse: collapse; background: white;'>
            <thead>
                <tr style='background: #e9ecef;'>
                    <th style='padding: 8px; border-bottom: 1px solid #dee2e6;'>Symbol</th>
                    <th style='padding: 8px; border-bottom: 1px solid #dee2e6;'>Name</th>
                    <th style='padding: 8px; border-bottom: 1px solid #dee2e6;'>Price</th>
                    <th style='padding: 8px; border-bottom: 1px solid #dee2e6;'>% Change</th>
                    <th style='padding: 8px; border-bottom: 1px solid #dee2e6;'>Volume</th>
                </tr>
            </thead>
            <tbody>
    """
    for fut in futures_data:
        symbol = fut.get("symbol", "")
        name = fut.get("name", "")
        price = fut.get("last_price", fut.get("price", ""))
        percent_change = fut.get("percent_change", "")
        volume = fut.get("volume", "")
        # Color code change based on percent_change
        try:
            if percent_change and '(' in percent_change and ')' in percent_change:
                pct_str = percent_change.strip('()').replace('%', '')
                change_val = float(pct_str)
                color = '#28a745' if change_val > 0 else ('#dc3545' if change_val < 0 else '#6c757d')
                change_str = f"<span style='color: {color};'>{change_val:+.2f}%</span>"
            else:
                change_str = f"<span style='color: #6c757d;'>{percent_change}</span>"
        except Exception:
            change_str = f"<span style='color: #6c757d;'>{percent_change}</span>"
        html += f"""
            <tr>
                <td style='padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;'>{symbol}</td>
                <td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>{name}</td>
                <td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>{price}</td>
                <td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>{change_str}</td>
                <td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>{volume}</td>
            </tr>
        """
    html += """
            </tbody>
        </table>
    </div>
    """
    return html

def generate_email_content(articles, limit=25):
    """
    Generate HTML email content with articles, summaries, and visuals
    
    Args:
        articles: List of summarized articles or result dictionary with geopolitical data
        limit: Maximum articles to include
    
    Returns:
        HTML string for email body
    """
    # Handle both legacy format (list) and new format (dict with geopolitical data)
    if isinstance(articles, dict):
        # New format from SummarizerAgent with geopolitical detection
        all_articles = articles.get("articles", [])
        geopolitical_articles = articles.get("geopolitical_articles", [])
    else:
        # Legacy format - just a list of articles
        all_articles = articles
        geopolitical_articles = []
    
    # Load Polygon articles and combine with existing articles
    polygon_articles = load_polygon_articles()
    all_articles = all_articles + polygon_articles
    
    # Deduplicate articles
    deduplicated_articles = deduplicate_articles(all_articles)
    
    # Limit articles
    articles_to_include = deduplicated_articles[:limit]
    
    # Count articles by source
    source_counts = {}
    for article in articles_to_include:
        source = article.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Load regime score data
    regime_data = load_regime_score_data()
    regime_summary_html = generate_regime_summary_html(regime_data)
    
    # Generate agent results if available
    agent_results_html = ""
    if AGENT_PIPELINE_AVAILABLE:
        try:
            # Extract headlines from articles for agent analysis
            headlines = [article.get("title", "") for article in articles_to_include if article.get("title")]
            
            # Get regime metrics for agent pipeline
            regime_score = 0.5  # Default
            vix_level = 20.0    # Default
            fear_greed_score = 50  # Default
            
            if regime_data:
                regime_score = regime_data.get('total_score', 50) / 100.0  # Convert to 0-1 scale
                # Try to extract VIX and F&G from regime data if available
                component_breakdown = regime_data.get('component_breakdown', {})
                if 'volatility' in component_breakdown:
                    vix_level = component_breakdown['volatility'].get('raw_score', 20.0)
                if 'fear_greed' in component_breakdown:
                    fear_greed_score = component_breakdown['fear_greed'].get('raw_score', 50)
            
            # Run agent pipeline
            agent_results = run_agents_pipeline(
                news_headlines=headlines,
                regime_score=regime_score,
                vix_level=vix_level,
                fear_greed_score=fear_greed_score,
                macro_factors={'articles_analyzed': len(headlines)}
            )
            
            agent_results_html = generate_agent_results_html(agent_results)
            print(f"✅ Agent pipeline completed - {len(headlines)} headlines analyzed")
            
        except Exception as e:
            print(f"⚠️ Error running agent pipeline: {e}")
            agent_results_html = """
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #6c757d;">
                <h3>🤖 AI Agent Analysis</h3>
                <p><em>Agent pipeline failed to run</em></p>
            </div>
            """
    else:
        print("⚠️ Agent pipeline not available - skipping agent analysis")
    
    # Generate visual placeholders
    fear_greed = generate_fear_greed_placeholder()
    sector_heatmap = generate_sector_heatmap_placeholder()
    sentiment_gauge = generate_sentiment_gauge_placeholder()
    
    # Generate geopolitical tensions section
    geopolitical_section_html = ""
    try:
        if geopolitical_articles:
            geopolitical_section_html = generate_geopolitical_section_html(geopolitical_articles)
            print(f"✅ Generated geopolitical section with {len(geopolitical_articles)} articles")
        else:
            print("ℹ️ No geopolitical articles detected")
    except Exception as e:
        print(f"❌ Error generating geopolitical section: {str(e)}")
    
    # Extract Fear & Greed score for ticker cards sentiment analysis
    fear_greed_score = 50  # Default fallback
    try:
        # Extract score from fear_greed string (format: "Fear & Greed Index: 65 (Greed)")
        import re
        score_match = re.search(r'Fear & Greed Index: (\d+)', fear_greed)
        if score_match:
            fear_greed_score = int(score_match.group(1))
            print(f"✅ Extracted Fear & Greed score: {fear_greed_score}")
    except Exception as e:
        print(f"⚠️ Could not extract Fear & Greed score, using default: {e}")
    
    # Generate Mini Ticker Cards
    ticker_cards_html = ""
    try:
        # Check if ticker cards are enabled (can be controlled via env var)
        ticker_cards_enabled = os.getenv("TICKER_CARDS_ENABLED", "true").lower() == "true"
        
        if ticker_cards_enabled:
            # Default watchlist - can be customized based on preferences
            watchlist = ["SPY", "QQQ", "IWM", "GLD", "TLT", "AAPL", "TSLA", "NVDA"]
            ticker_cards_html = generate_mini_ticker_cards(watchlist, fear_greed_score)
            print(f"✅ Generated ticker cards for watchlist")
        else:
            print(f"ℹ️ Ticker cards disabled via configuration")
    except Exception as e:
        print(f"❌ Error generating ticker cards: {str(e)}")
    
    # Check for extreme fear chart
    extreme_fear_chart_html = ""
    if VISUAL_ENGINE_AVAILABLE:
        try:
            chart_path = generate_extreme_fear_chart()
            if chart_path and os.path.exists(chart_path):
                extreme_fear_chart_html = f"""
                <div style="padding: 12px;">
                    <img src="cid:fear_chart" style="width: 100%; border-radius: 10px;" />
                </div>
                """
        except Exception as e:
            print(f"⚠️ Error generating extreme fear chart: {str(e)}")
    
    # Load Yahoo Futures data and Top Movers
    yahoo_futures_data = load_latest_yahoo_futures()
    top_movers_data = load_latest_barchart_futures()
    yahoo_futures_html = generate_futures_table_html(yahoo_futures_data, "Yahoo Futures Screener")
    top_movers_html = generate_futures_table_html(top_movers_data, "Yahoo Top Movers (24h % Change)")
    
    # Generate Fear & Greed trend chart - ALWAYS include this chart
    fear_greed_trend_chart_html = ""
    fear_greed_chart_path = None
    
    try:
        # Always generate the Fear & Greed chart using enhanced visualizations
        fear_greed_chart_path = generate_fear_greed_trend_chart()
        if fear_greed_chart_path and os.path.exists(fear_greed_chart_path):
            fear_greed_trend_chart_html = f"""
            <div style="padding: 12px;">
                <img src="cid:fear_greed_trend_chart" style="width: 100%; border-radius: 10px;" />
            </div>
            """
            print(f"✅ Fear & Greed trend chart generated and HTML created")
        else:
            # Generate placeholder HTML if chart generation failed
            fear_greed_trend_chart_html = f"""
            <div style="margin: 20px 0; padding: 15px; background: #dc3545; border-radius: 5px; color: white;">
                <h3>📊 Fear & Greed Index Trend (14 Days)</h3>
                <p>⚠️ Fear & Greed data unavailable - please check API configuration</p>
                <div style="text-align: center; margin: 15px 0; padding: 40px; background: rgba(255,255,255,0.1); border-radius: 5px;">
                    <h4>Fear & Greed Data Unavailable</h4>
                    <p>Unable to fetch CNN Fear & Greed Index data</p>
                </div>
                <p><small>The chart will be included once API access is restored.</small></p>
            </div>
            """
            print(f"⚠️ Fear & Greed chart failed - using placeholder HTML")
    except Exception as e:
        print(f"❌ Error generating Fear & Greed trend chart: {str(e)}")
        fear_greed_trend_chart_html = f"""
        <div style="margin: 20px 0; padding: 15px; background: #dc3545; border-radius: 5px; color: white;">
            <h3>📊 Fear & Greed Index Trend (14 Days)</h3>
            <p>❌ Error generating Fear & Greed chart: {str(e)}</p>
        </div>
        """
    
    # Generate Enhanced Charts with AI Explanations
    enhanced_charts_html = ""
    chart_attachments = []
    
    if CHART_GENERATION_AVAILABLE and regime_data:
        try:
            # Extract headlines for context
            headlines = [article.get("title", "") for article in articles_to_include if article.get("title")]
            
            # Get fear & greed score from generated data
            current_fear_greed = 50  # Default
            try:
                from agents.chart_generator_agent import ChartGeneratorAgent
                temp_agent = ChartGeneratorAgent()
                if temp_agent.visual_engine_available and temp_agent.visual_engine:
                    current_fear_greed, _ = temp_agent.visual_engine.get_fear_greed_index()
                    if current_fear_greed is None:
                        current_fear_greed = 50
            except:
                current_fear_greed = 50
            
            # Generate enhanced charts
            enhanced_charts = generate_enhanced_charts_with_explanations(
                regime_data=regime_data,
                fear_greed_score=current_fear_greed,
                headlines=headlines
            )
            
            if enhanced_charts:
                enhanced_charts_html += """
                <div style="margin: 30px 0;">
                    <h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">🤖 AI-Enhanced Market Analysis</h2>
                    <p style="color: #6c757d; margin-bottom: 20px;">Advanced chart analysis with intelligent explanations based on current market regime and sentiment data.</p>
                </div>
                """
                
                # Add each enhanced chart
                chart_counter = 1
                for chart_key, chart_data in enhanced_charts.items():
                    chart_path = chart_data.get("path")
                    if chart_path and isinstance(chart_path, str) and os.path.exists(chart_path):
                        chart_names = {
                            "intelligent_regime": "Intelligent Regime Analysis",
                            "vix_strategic": "VIX Strategic Overview", 
                            "multi_asset": "Multi-Asset Comparison"
                        }
                        
                        chart_name = chart_names.get(chart_key, f"Chart {chart_counter}")
                        chart_id = f"enhanced_chart_{chart_counter}"
                        
                        enhanced_charts_html += create_chart_html_section(
                            chart_name=chart_name,
                            chart_data=chart_data,
                            chart_id=chart_id
                        )
                        
                        chart_attachments.append({
                            "path": chart_data["path"],
                            "cid": chart_id
                        })
                        
                        chart_counter += 1
                
                print(f"✅ Generated {len(enhanced_charts)} enhanced charts for email")
            else:
                print("⚠️ No enhanced charts generated")
                
        except Exception as e:
            print(f"⚠️ Error generating enhanced charts: {str(e)}")
    
    # Generate Macro Volatility Stack Chart
    macro_volatility_chart_html = ""
    macro_volatility_chart_path = None
    
    try:
        if EnhancedVisualizations is not None:
            viz_engine = EnhancedVisualizations()
            macro_volatility_chart_path = viz_engine.create_macro_volatility_trend_chart()
            
            if macro_volatility_chart_path and os.path.exists(macro_volatility_chart_path):
                macro_volatility_chart_html = """
                <div style="padding: 12px;">
                    <img src="cid:macro_volatility_chart" style="width: 100%; border-radius: 10px;" />
                </div>
                """
                print(f"✅ Macro volatility chart generated and HTML created")
            else:
                print(f"⚠️ Macro volatility chart generation failed")
        else:
            print(f"⚠️ Enhanced visualizations not available for macro volatility chart")
    except Exception as e:
        print(f"❌ Error generating macro volatility chart: {str(e)}")

    # Generate Equity Futures Overview Chart
    equity_futures_chart_html = ""
    equity_futures_chart_path = None
    
    try:
        if EnhancedVisualizations is not None:
            viz_engine = EnhancedVisualizations()
            equity_futures_chart_path = viz_engine.create_equity_index_matrix_chart()
            
            if equity_futures_chart_path and os.path.exists(equity_futures_chart_path):
                equity_futures_chart_html = """
                <div style="padding: 12px;">
                    <img src="cid:equity_futures_chart" style="width: 100%; border-radius: 10px;" />
                </div>
                """
                print(f"✅ Equity futures chart generated and HTML created")
            else:
                print(f"⚠️ Equity futures chart generation failed")
        else:
            print(f"⚠️ Enhanced visualizations not available for equity futures chart")
    except Exception as e:
        print(f"❌ Error generating equity futures chart: {str(e)}")

    # Generate Timeline Panel Charts
    timeline_panels_html = ""
    timeline_panel_paths = []
    
    try:
        # Define default asset list for timeline panels - can be customized based on regime or preferences
        timeline_asset_list = ["SPY", "QQQ", "IWM", "GLD"]  # Major ETFs representing key market segments
        
        # Check if timeline panel generation is enabled (can be controlled via env var)
        timeline_enabled = os.getenv("TIMELINE_PANELS_ENABLED", "true").lower() == "true"
        
        if timeline_enabled and EnhancedVisualizations is not None:
            viz_engine = EnhancedVisualizations()
            timeline_panel_paths = viz_engine.generate_timeline_panels(timeline_asset_list, enabled=True)
            
            if timeline_panel_paths:
                timeline_panels_html = f"""
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 15px; margin: 15px 0;">
                """
                
                # Add each timeline panel chart
                for i, chart_path in enumerate(timeline_panel_paths):
                    if os.path.exists(chart_path):
                        # Extract symbol from filename (e.g., "SPY_multi_timeframe.png" -> "SPY")
                        symbol = os.path.basename(chart_path).replace("_multi_timeframe.png", "")
                        cid = f"timeline_{symbol.lower()}"
                        
                        timeline_panels_html += f"""
                        <div style="text-align: center; padding: 12px;">
                            <img src="cid:{cid}" style="width: 100%; border-radius: 10px;" />
                        </div>
                        """
                
                timeline_panels_html += """
                    </div>
                """
                print(f"✅ Generated {len(timeline_panel_paths)} timeline panel charts and HTML created")
            else:
                print(f"⚠️ Timeline panel chart generation failed")
        else:
            if not timeline_enabled:
                print(f"ℹ️ Timeline panels disabled via configuration")
            else:
                print(f"⚠️ Enhanced visualizations not available for timeline panels")
    except Exception as e:
        print(f"❌ Error generating timeline panel charts: {str(e)}")

    # Generate CME Forex Heatmap
    cme_forex_chart_html = ""
    cme_forex_chart_path = None
    
    try:
        # Check if CME forex generation is enabled (can be controlled via env var)
        cme_forex_enabled = os.getenv("CME_FOREX_ENABLED", "true").lower() == "true"
        
        if cme_forex_enabled:
            from fetch_forex_cme import generate_cme_forex_heatmap
            cme_forex_chart_path = generate_cme_forex_heatmap()
            
            if cme_forex_chart_path and os.path.exists(cme_forex_chart_path):
                cme_forex_chart_html = """
                <div style="padding: 12px;">
                    <img src="cid:cme_forex_chart" style="width: 100%; border-radius: 10px;" />
                </div>
                """
                print(f"✅ CME forex heatmap generated and HTML created")
            else:
                print(f"⚠️ CME forex heatmap generation failed")
        else:
            print(f"ℹ️ CME forex disabled via configuration")
    except Exception as e:
        print(f"❌ Error generating CME forex heatmap: {str(e)}")

    # Generate Macro vs Futures Comparison Chart
    macro_vs_futures_chart_html = ""
    macro_vs_futures_chart_path = None
    
    try:
        # Check if macro vs futures generation is enabled (can be controlled via env var)
        macro_vs_futures_enabled = os.getenv("MACRO_VS_FUTURES_ENABLED", "true").lower() == "true"
        
        if macro_vs_futures_enabled and EnhancedVisualizations is not None:
            viz_engine = EnhancedVisualizations()
            macro_vs_futures_chart_path = viz_engine.create_macro_vs_futures_chart()
            
            if macro_vs_futures_chart_path and os.path.exists(macro_vs_futures_chart_path):
                macro_vs_futures_chart_html = """
                <div style="padding: 12px;">
                    <img src="cid:macro_vs_futures_chart" style="width: 100%; border-radius: 10px;" />
                </div>
                """
                print(f"✅ Macro vs futures chart generated and HTML created")
            else:
                print(f"⚠️ Macro vs futures chart generation failed")
        else:
            if not macro_vs_futures_enabled:
                print(f"ℹ️ Macro vs futures disabled via configuration")
            else:
                print(f"⚠️ Enhanced visualizations not available for macro vs futures chart")
    except Exception as e:
        print(f"❌ Error generating macro vs futures chart: {str(e)}")

    # Generate Economic Calendar Timeline
    economic_calendar_html = ""
    economic_calendar_chart_path = None
    
    try:
        # Check if economic calendar is enabled (can be controlled via env var)
        economic_calendar_enabled = os.getenv("ECONOMIC_CALENDAR_ENABLED", "true").lower() == "true"
        
        if economic_calendar_enabled:
            from calendar_tracker import generate_economic_calendar_timeline
            economic_calendar_chart_path = generate_economic_calendar_timeline()
            
            if economic_calendar_chart_path and os.path.exists(economic_calendar_chart_path):
                economic_calendar_html = """
                <div style="padding: 12px;">
                    <img src="cid:economic_calendar_chart" style="width: 100%; border-radius: 10px;" />
                </div>
                """
                print(f"✅ Economic calendar timeline generated and HTML created")
            else:
                print(f"⚠️ Economic calendar timeline generation failed")
        else:
            print(f"ℹ️ Economic calendar disabled via configuration")
    except Exception as e:
        print(f"❌ Error generating economic calendar timeline: {str(e)}")

    # Start HTML content with proper structure
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📰 MacroIntel Daily News Report</h2>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>📊 {len(articles_to_include)} relevant articles from your watchlist</p>
            <p>📈 Sources: {', '.join([f'{source} ({count})' for source, count in source_counts.items()])}</p>
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📊 Market Regime Summary</h2>
            {regime_summary_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">🤖 AI Agent Analysis</h2>
            {agent_results_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">🌍 Geopolitical Analysis</h2>
            {geopolitical_section_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📅 Economic Calendar</h2>
            {economic_calendar_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📈 Market Overview</h2>
            <p><strong>{fear_greed}</strong></p>
            {sector_heatmap}
            {sentiment_gauge}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📊 Ticker Cards</h2>
            {ticker_cards_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📊 Macro Volatility Chart</h2>
            {macro_volatility_chart_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">🎯 Equity Futures Overview</h2>
            {equity_futures_chart_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">🏦 CME Forex Watchlist</h2>
            {cme_forex_chart_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">⚖️ Macro vs Equity Futures Analysis</h2>
            {macro_vs_futures_chart_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📊 Multi-Timeframe Analysis Panels</h2>
            {timeline_panels_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📈 Yahoo Futures Screener</h2>
            {yahoo_futures_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📈 Yahoo Top Movers</h2>
            {top_movers_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">😱 Extreme Fear Alert</h2>
            {extreme_fear_chart_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📊 Fear & Greed Index Trend</h2>
            {fear_greed_trend_chart_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">🤖 AI-Enhanced Market Analysis</h2>
            {enhanced_charts_html}
        </div>
        
        <div style="padding:12px; margin-bottom:20px;">
            <h2 style="color:#333;">📰 Relevant Headlines</h2>
        </div>
    """
    
    # Group articles by source for better organization
    articles_by_source = {}
    for article in articles_to_include:
        source = article.get("source", "unknown")
        if source not in articles_by_source:
            articles_by_source[source] = []
        articles_by_source[source].append(article)
    
    # Add articles grouped by source
    article_counter = 1
    for source, source_articles in articles_by_source.items():
        # Add source header
        source_display_name = {
            "fmp": "Financial Modeling Prep",
            "polygon": "Polygon.io",
            "perplexity": "Perplexity AI",
            "messari": "Messari",
            "benzinga": "Benzinga"
        }.get(source, source.title())
        
        html_content += f"""
        <div style="padding:12px; margin-bottom:20px;">
            <h3 style="color:#333;">📈 Source: {source_display_name} ({len(source_articles)} articles)</h3>
        </div>
        """
        
        # Add articles for this source
        for article in source_articles:
            title = article.get("title", "No title")
            url = article.get("url", "#")
            summary = article.get("summary", "No summary available")
            tickers = article.get("affected_tickers", "")
            tone = article.get("tone", "Neutral")
            
            # Sanitize all dynamic content for email compatibility
            title = sanitize_email_text(title)
            summary = sanitize_email_text(summary)
            tickers = sanitize_email_text(tickers)
            tone = sanitize_email_text(tone)
            
            # Determine tone style
            tone_style = "background: #d4edda; color: #155724;" if tone.lower() == "bullish" else \
                        "background: #f8d7da; color: #721c24;" if tone.lower() == "bearish" else \
                        "background: #fff3cd; color: #856404;" if tone.lower() == "volatile" else \
                        "background: #d1ecf1; color: #0c5460;"
            
            html_content += f"""
            <div style="border-left: 4px solid #3498db; margin: 15px 0; padding: 10px; background: #f8f9fa;">
                <div style="font-weight: bold; color: #2c3e50; margin-bottom: 5px;">
                    <a href="{url}" style="color: #2c3e50; text-decoration: none;">{article_counter}. {title}</a>
                </div>
                <div style="color: #555; margin: 5px 0;">{summary}</div>
                <div style="margin-top: 5px;">
                    <span style="color: #e74c3c; font-weight: bold;">📈 {tickers}</span> | 
                    <span style="display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 12px; {tone_style}">{tone}</span> | 
                    <small>Source: {source_display_name}</small>
                </div>
            </div>
            """
            article_counter += 1
    
    # Add footer
    html_content += f"""
        <div style="margin-top: 30px; padding: 15px; background: #95a5a6; color: white; border-radius: 5px;">
            <p><strong>MacroIntel News Scanner</strong></p>
            <p>This report contains {len(articles_to_include)} articles relevant to your watchlist.</p>
            <p>Generated automatically - click article titles to read full stories.</p>
        </div>
    </body>
    </html>
    """
    
    # Always include Fear & Greed chart in attachments if it was generated
    if fear_greed_chart_path and os.path.exists(fear_greed_chart_path):
        chart_attachments.append({
            "path": fear_greed_chart_path,
            "cid": "fear_greed_trend_chart"
        })
        print(f"✅ Added Fear & Greed chart to email attachments")
    else:
        print(f"⚠️ Fear & Greed chart file missing: {fear_greed_chart_path}")
    
    # Include Macro Volatility chart in attachments if it was generated
    if macro_volatility_chart_path and os.path.exists(macro_volatility_chart_path):
        chart_attachments.append({
            "path": macro_volatility_chart_path,
            "cid": "macro_volatility_chart"
        })
        print(f"✅ Added Macro Volatility chart to email attachments")
    else:
        print(f"⚠️ Macro Volatility chart file missing: {macro_volatility_chart_path}")
    
    # Include Equity Futures chart in attachments if it was generated
    if equity_futures_chart_path and os.path.exists(equity_futures_chart_path):
        chart_attachments.append({
            "path": equity_futures_chart_path,
            "cid": "equity_futures_chart"
        })
        print(f"✅ Added Equity Futures chart to email attachments")
    else:
        print(f"⚠️ Equity Futures chart file missing: {equity_futures_chart_path}")
    
    # Include Timeline Panel charts in attachments if they were generated
    if timeline_panel_paths:
        added_timeline_charts = 0
        for chart_path in timeline_panel_paths:
            if os.path.exists(chart_path):
                # Extract symbol from filename (e.g., "SPY_multi_timeframe.png" -> "SPY")
                symbol = os.path.basename(chart_path).replace("_multi_timeframe.png", "")
                cid = f"timeline_{symbol.lower()}"
                
                chart_attachments.append({
                    "path": chart_path,
                    "cid": cid
                })
                added_timeline_charts += 1
            else:
                print(f"⚠️ Timeline Panel chart file missing: {chart_path}")
        print(f"✅ Added {added_timeline_charts}/{len(timeline_panel_paths)} Timeline Panel charts to email attachments")
    
    # Include CME Forex chart in attachments if it was generated
    if cme_forex_chart_path and os.path.exists(cme_forex_chart_path):
        chart_attachments.append({
            "path": cme_forex_chart_path,
            "cid": "cme_forex_chart"
        })
        print(f"✅ Added CME Forex chart to email attachments")
    else:
        print(f"⚠️ CME Forex chart file missing: {cme_forex_chart_path}")
    
    # Include Macro vs Futures chart in attachments if it was generated
    if macro_vs_futures_chart_path and os.path.exists(macro_vs_futures_chart_path):
        chart_attachments.append({
            "path": macro_vs_futures_chart_path,
            "cid": "macro_vs_futures_chart"
        })
        print(f"✅ Added Macro vs Futures chart to email attachments")
    else:
        print(f"⚠️ Macro vs Futures chart file missing: {macro_vs_futures_chart_path}")
    
    # Include Economic Calendar chart in attachments if it was generated
    if economic_calendar_chart_path and os.path.exists(economic_calendar_chart_path):
        chart_attachments.append({
            "path": economic_calendar_chart_path,
            "cid": "economic_calendar_chart"
        })
        print(f"✅ Added Economic Calendar timeline to email attachments")
    else:
        print(f"⚠️ Economic Calendar chart file missing: {economic_calendar_chart_path}")
    
    print(f"📧 Email generation complete: {len(chart_attachments)} total chart attachments")
    
    return html_content, chart_attachments

def send_daily_report(html_content, attachments=None, inline_charts=None):
    """
    Send the daily report email with the provided HTML content as the body.
    Args:
        html_content: The full HTML string to use as the email body.
        attachments: List of file paths to attach (optional)
        inline_charts: List of inline chart dictionaries with 'path' and 'cid' keys (optional)
    Returns:
        True if sent successfully, False otherwise.
    """
    import base64
    import re
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Use the global sanitize_email_text function
    
    def clean_text_content(text):
        """Clean problematic characters and emojis from text content."""
        if not text:
            return text
        
        # Convert to string if needed
        text = str(text)
        
        # Remove or replace problematic emojis and characters
        problematic_chars = {
            '📈': 'UP',
            '📉': 'DOWN', 
            '➡️': 'FLAT',
            '✅': 'SUCCESS',
            '❌': 'ERROR',
            '⚠️': 'WARNING',
            '🔄': 'RETRY',
            '📊': 'CHART',
            '📰': 'NEWS',
            '🏦': 'BANK',
            '🤖': 'AI',
            '📅': 'CALENDAR',
            '🎯': 'TARGET',
            '💡': 'IDEA',
            '🚀': 'LAUNCH',
            '🔥': 'HOT',
            '💎': 'DIAMOND',
            '🎪': 'CIRCUS',
            '🎭': 'THEATER',
            '🎨': 'ART',
            '🎬': 'MOVIE',
            '🎵': 'MUSIC',
            '🎮': 'GAME',
            '🎲': 'DICE',
            '🎯': 'TARGET',
            '🎪': 'CIRCUS',
            '🎭': 'THEATER',
            '🎨': 'ART',
            '🎬': 'MOVIE',
            '🎵': 'MUSIC',
            '🎮': 'GAME',
            '🎲': 'DICE'
        }
        
        # Replace problematic characters
        for emoji, replacement in problematic_chars.items():
            text = text.replace(emoji, replacement)
        
        # Remove other non-ASCII characters that might cause issues
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        # Ensure proper UTF-8 encoding
        try:
            text = text.encode('utf-8').decode('utf-8')
        except UnicodeError:
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        return text
    
    def save_report_locally(html_content, error_note=""):
        """Save report locally as fallback when email fails."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            filename = f"email_report_fallback_{timestamp}.html"
            filepath = output_dir / filename
            
            # Add error note to the HTML content
            error_html = f"""
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <h3>⚠️ Email Delivery Failed</h3>
                <p><strong>Error:</strong> {error_note}</p>
                <p><strong>Time:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>This report was saved locally because email delivery failed.</p>
            </div>
            """
            
            # Insert error note at the beginning of the HTML content
            full_html = error_html + html_content
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            logger.info(f"✅ Report saved locally: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Failed to save report locally: {e}")
            return None
    
    # Load credentials using standardized environment variables
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_recipient = os.getenv("EMAIL_RECIPIENT")
    
    # Additional email settings
    sender_email = os.getenv("EMAIL_SENDER")
    sender_name = os.getenv("EMAIL_SENDER_NAME")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    subject = os.getenv("EMAIL_SUBJECT", "MacroIntel Daily News Report")

    # Validate required credentials
    if not all([smtp_user, smtp_password, email_recipient, sender_email, sender_name, smtp_server]):
        error_msg = "Missing required email credentials"
        logger.error(f"❌ {error_msg}")
        print("[ERROR] Missing required email credentials. Please check your .env file for:")
        print("  - SMTP_USER")
        print("  - SMTP_PASSWORD") 
        print("  - EMAIL_RECIPIENT")
        print("  - EMAIL_SENDER")
        print("  - EMAIL_SENDER_NAME")
        print("  - SMTP_SERVER")
        
        # Save report locally as fallback
        save_report_locally(html_content, error_msg)
        return False

    # Ensure all required fields are strings and clean them
    smtp_user = clean_text_content(str(smtp_user))
    smtp_password = str(smtp_password)  # Don't clean passwords
    email_recipient = clean_text_content(str(email_recipient))
    sender_email = clean_text_content(str(sender_email))
    sender_name = clean_text_content(str(sender_name))
    smtp_server = clean_text_content(str(smtp_server))
    subject = clean_text_content(subject)

    logger.info(f"📧 Sending email to {email_recipient}")

    # Clean the HTML content with enhanced sanitization
    html_content = sanitize_email_text(html_content)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = formataddr((sender_name, sender_email))
    msg['To'] = email_recipient

    # Attach the HTML content with UTF-8 encoding
    try:
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        logger.info("✅ HTML content attached successfully with UTF-8 encoding")
    except UnicodeEncodeError as e:
        logger.warning(f"⚠️ UnicodeEncodeError in HTML content, cleaning and retrying: {e}")
        try:
            # Clean the HTML content more aggressively
            cleaned_html = clean_text_content(html_content)
            html_part = MIMEText(cleaned_html, 'html', 'utf-8')
            msg.attach(html_part)
            logger.info("✅ HTML content attached successfully after cleaning")
        except Exception as retry_e:
            logger.error(f"❌ Failed to attach HTML content after UnicodeEncodeError: {retry_e}")
            save_report_locally(html_content, f"HTML encoding error after UnicodeEncodeError: {retry_e}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to attach HTML content: {e}")
        save_report_locally(html_content, f"HTML encoding error: {e}")
        return False

    # Add inline charts if provided
    if inline_charts:
        for chart in inline_charts:
            try:
                chart_path = chart.get("path")
                chart_cid = chart.get("cid")
                
                if chart_path and chart_cid and os.path.exists(chart_path):
                    # Open image in binary mode and encode as base64
                    with open(chart_path, 'rb') as f:
                        image_data = f.read()
                        chart_img = MIMEImage(image_data)
                        chart_img.add_header('Content-ID', f'<{chart_cid}>')
                        
                        # Clean filename to prevent UnicodeEncodeError
                        safe_filename = clean_text_content(os.path.basename(chart_path))
                        chart_img.add_header('Content-Disposition', 'inline', 
                                           filename=safe_filename)
                        msg.attach(chart_img)
                    logger.info(f"✅ Embedded inline chart: {safe_filename} (CID: {chart_cid})")
                else:
                    logger.warning(f"⚠️ Invalid chart data: {chart}")
            except UnicodeEncodeError as e:
                logger.warning(f"⚠️ UnicodeEncodeError in chart filename, using cleaned name: {e}")
                try:
                    # Retry with cleaned filename
                    chart_path = chart.get("path")
                    chart_cid = chart.get("cid")
                    
                    if chart_path and chart_cid and os.path.exists(chart_path):
                        with open(chart_path, 'rb') as f:
                            image_data = f.read()
                            chart_img = MIMEImage(image_data)
                            chart_img.add_header('Content-ID', f'<{chart_cid}>')
                            
                            # Use a safe fallback filename
                            safe_filename = f"chart_{chart_cid}.png"
                            chart_img.add_header('Content-Disposition', 'inline', 
                                               filename=safe_filename)
                            msg.attach(chart_img)
                        logger.info(f"✅ Embedded inline chart with safe filename: {safe_filename} (CID: {chart_cid})")
                except Exception as retry_e:
                    logger.error(f"❌ Failed to embed chart after UnicodeEncodeError: {retry_e}")
            except Exception as e:
                logger.error(f"❌ Failed to embed chart {chart.get('path', 'unknown')}: {e}")

    # Add attachments if provided
    if attachments:
        for attachment_path in attachments:
            try:
                # Open attachment in binary mode
                with open(attachment_path, 'rb') as f:
                    attachment_data = f.read()
                    attachment = MIMEImage(attachment_data)
                    
                    # Clean filename to prevent UnicodeEncodeError
                    safe_filename = clean_text_content(os.path.basename(attachment_path))
                    attachment.add_header('Content-Disposition', 'attachment', 
                                        filename=safe_filename)
                    msg.attach(attachment)
                logger.info(f"✅ Attached: {safe_filename}")
            except UnicodeEncodeError as e:
                logger.warning(f"⚠️ UnicodeEncodeError in attachment filename, using cleaned name: {e}")
                try:
                    # Retry with cleaned filename
                    with open(attachment_path, 'rb') as f:
                        attachment_data = f.read()
                        attachment = MIMEImage(attachment_data)
                        
                        # Use a safe fallback filename
                        safe_filename = f"attachment_{os.path.splitext(os.path.basename(attachment_path))[0]}.png"
                        attachment.add_header('Content-Disposition', 'attachment', 
                                            filename=safe_filename)
                        msg.attach(attachment)
                    logger.info(f"✅ Attached with safe filename: {safe_filename}")
                except Exception as retry_e:
                    logger.error(f"❌ Failed to attach after UnicodeEncodeError: {retry_e}")
            except Exception as e:
                logger.error(f"❌ Failed to attach {attachment_path}: {e}")

    # Send email with detailed error handling
    try:
        logger.info(f"🔗 Connecting to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            logger.info("🔐 Starting TLS encryption...")
            server.starttls()
            
            logger.info(f"👤 Logging in as: {smtp_user}")
            server.login(smtp_user, smtp_password)
            
            logger.info("📤 Sending email...")
            server.sendmail(sender_email, email_recipient, msg.as_string())
            
        logger.info("✅ Email sent successfully")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed: {e}"
        logger.error(f"❌ {error_msg}")
        save_report_locally(html_content, error_msg)
        return False
        
    except smtplib.SMTPConnectError as e:
        error_msg = f"SMTP connection failed: {e}"
        logger.error(f"❌ {error_msg}")
        save_report_locally(html_content, error_msg)
        return False
        
    except smtplib.SMTPRecipientsRefused as e:
        error_msg = f"SMTP recipient refused: {e}"
        logger.error(f"❌ {error_msg}")
        save_report_locally(html_content, error_msg)
        return False
        
    except smtplib.SMTPServerDisconnected as e:
        error_msg = f"SMTP server disconnected: {e}"
        logger.error(f"❌ {error_msg}")
        save_report_locally(html_content, error_msg)
        return False
        
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {e}"
        logger.error(f"❌ {error_msg}")
        save_report_locally(html_content, error_msg)
        return False
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(f"❌ {error_msg}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Enhanced fallback with detailed logging
        fallback_path = save_report_locally(html_content, error_msg)
        if fallback_path:
            logger.info(f"✅ Fallback HTML report saved to: {fallback_path}")
        else:
            logger.error("❌ Failed to save fallback report")
        
        return False

def generate_fear_greed_trend_chart():
    """
    Generate a 14-day Fear & Greed Index trend chart using enhanced visualizations.
    Always saves as output/fear_greed_trend.png.
    Returns the path to the saved chart file, or None if failed.
    """
    try:
        print("📊 Generating 14-day Fear & Greed Index trend chart...")
        
        # Use the enhanced visualizations engine
        if EnhancedVisualizations is None:
            print("❌ Enhanced visualizations not available")
            return None
            
        viz_engine = EnhancedVisualizations()
        chart_path = viz_engine.generate_fear_greed_trend_chart()
        
        if chart_path:
            print(f"✅ Fear & Greed trend chart saved to: {chart_path}")
            return chart_path
        else:
            print("⚠️ Failed to generate Fear & Greed trend chart")
            return None
            
    except Exception as e:
        print(f"❌ Error generating Fear & Greed trend chart: {str(e)}")
        return None

def generate_enhanced_charts_with_explanations(regime_data, fear_greed_score, headlines=None):
    """
    Generate enhanced visual charts with AI explanations.
    
    Args:
        regime_data: Market regime analysis data
        fear_greed_score: Current Fear & Greed Index score
        headlines: List of news headlines for context
        
    Returns:
        Dictionary with chart paths and explanations
    """
    if not CHART_GENERATION_AVAILABLE:
        print("⚠️ Chart generation not available - skipping enhanced charts")
        return {}
    
    try:
        print("📊 Generating enhanced charts with AI explanations...")
        
        # Initialize chart generator and visualization engine
        if ChartGeneratorAgent is None or EnhancedVisualizations is None:
            print("❌ Chart generation classes not available")
            return {}
            
        chart_agent = ChartGeneratorAgent()
        viz_engine = EnhancedVisualizations()
        
        # Extract dominant keywords from headlines for Perplexity context
        dominant_keywords = []
        if headlines:
            # Simple keyword extraction from headlines
            all_text = ' '.join(headlines).lower()
            market_keywords = ['inflation', 'fed', 'rates', 'oil', 'china', 'earnings', 'ai', 'tech', 'energy']
            dominant_keywords = [keyword for keyword in market_keywords if keyword in all_text]
        
        charts_generated = {}
        
        # 1. Generate Intelligent Regime Chart
        print("🧠 Generating intelligent regime chart...")
        intelligent_chart_result = chart_agent.generate_intelligent_chart(
            regime_data=regime_data,
            fear_greed_score=fear_greed_score,
            dominant_keywords=dominant_keywords,
            tags=dominant_keywords  # Use same keywords as tags
        )
        
        if intelligent_chart_result.get("success"):
            charts_generated["intelligent_regime"] = {
                "path": intelligent_chart_result.get("file_path"),
                "explanation": intelligent_chart_result.get("ai_explanation", ""),
                "strategy": intelligent_chart_result.get("strategy", "Tier 2"),
                "regime": intelligent_chart_result.get("regime", "Neutral"),
                "market_theme": intelligent_chart_result.get("market_theme", "General Market"),
                "sentiment_data": {
                    "fear_greed_score": fear_greed_score,
                    "regime_score": regime_data.get('total_score', 50),
                    "regime_strength": intelligent_chart_result.get("regime_strength", "neutral")
                }
            }
        
        # 2. Generate VIX Strategic Chart
        print("📈 Generating VIX strategic chart...")
        vix_chart_path = viz_engine.create_vix_strategic_chart()
        
        if vix_chart_path:
            # Generate explanation for VIX chart
            vix_explanation = f"""
            This VIX strategic analysis shows current volatility conditions with regime context. 
            With Fear & Greed at {fear_greed_score} and regime score of {regime_data.get('total_score', 50):.1f}, 
            the market is displaying {regime_data.get('regime_classification', 'neutral').lower()} characteristics. 
            VIX levels above 30 indicate chaos conditions suitable for volatility trading strategies, 
            while levels below 15 suggest complacent markets requiring breakout positioning.
            """
            
            charts_generated["vix_strategic"] = {
                "path": vix_chart_path,
                "explanation": vix_explanation.strip(),
                "strategy": "Volatility-based positioning",
                "regime": regime_data.get('regime_classification', 'Neutral'),
                "market_theme": "Volatility Analysis",
                "sentiment_data": {
                    "fear_greed_score": fear_greed_score,
                    "regime_score": regime_data.get('total_score', 50),
                    "vix_interpretation": "Chaos" if fear_greed_score > 75 else "Normal" if fear_greed_score > 25 else "Complacent"
                }
            }
        
        # 3. Generate Multi-Asset Comparison (if data available)
        print("📊 Generating multi-asset comparison...")
        try:
            # Create sample asset data for demonstration
            sample_asset_data = {
                'SPY': {'name': 'S&P 500 ETF', 'price': 450.0, 'change': 1.2},
                'QQQ': {'name': 'NASDAQ ETF', 'price': 380.0, 'change': 0.8},
                'GLD': {'name': 'Gold ETF', 'price': 180.0, 'change': -0.5}
            }
            
            multi_asset_chart = viz_engine.create_multi_asset_comparison(sample_asset_data)
            
            if multi_asset_chart:
                asset_explanation = f"""
                Multi-asset comparison reveals cross-asset relationships in the current {regime_data.get('regime_classification', 'neutral').lower()} regime. 
                With regime score at {regime_data.get('total_score', 50):.1f}, asset correlation patterns suggest 
                {"risk-on sentiment" if regime_data.get('total_score', 50) > 60 else "risk-off behavior" if regime_data.get('total_score', 50) < 40 else "neutral positioning"}. 
                This analysis helps identify relative value opportunities across major asset classes.
                """
                
                charts_generated["multi_asset"] = {
                    "path": multi_asset_chart,
                    "explanation": asset_explanation.strip(),
                    "strategy": "Cross-asset rotation",
                    "regime": regime_data.get('regime_classification', 'Neutral'),
                    "market_theme": "Asset Allocation",
                    "sentiment_data": {
                        "fear_greed_score": fear_greed_score,
                        "regime_score": regime_data.get('total_score', 50),
                        "correlation_regime": "High" if regime_data.get('total_score', 50) > 70 else "Low"
                    }
                }
        except Exception as e:
            print(f"⚠️ Multi-asset chart generation failed: {e}")
        
        print(f"✅ Generated {len(charts_generated)} enhanced charts with explanations")
        return charts_generated
        
    except Exception as e:
        print(f"❌ Error generating enhanced charts: {str(e)}")
        return {}

def create_chart_html_section(chart_name, chart_data, chart_id):
    """
    Create HTML section for a chart with explanation and sentiment data.
    
    Args:
        chart_name: Display name for the chart
        chart_data: Dictionary containing chart path, explanation, strategy, etc.
        chart_id: Unique ID for the chart (for email attachment)
        
    Returns:
        HTML string for the chart section
    """
    if not chart_data or not chart_data.get("path"):
        return ""
    
    explanation = chart_data.get("explanation", "Chart analysis not available.")
    strategy = chart_data.get("strategy", "Strategy TBD")
    regime = chart_data.get("regime", "Neutral")
    market_theme = chart_data.get("market_theme", "General")
    sentiment_data = chart_data.get("sentiment_data", {})
    
    # Create sentiment data display
    sentiment_html = ""
    if sentiment_data:
        sentiment_items = []
        for key, value in sentiment_data.items():
            if isinstance(value, (int, float)):
                sentiment_items.append(f"{key.replace('_', ' ').title()}: {value:.1f}")
            else:
                sentiment_items.append(f"{key.replace('_', ' ').title()}: {value}")
        sentiment_html = " | ".join(sentiment_items)
    
    # Determine background color based on regime
    regime_colors = {
        "Bullish": "#d4edda",
        "Bearish": "#f8d7da", 
        "Neutral": "#e2e3e5",
        "Volatile": "#fff3cd"
    }
    bg_color = regime_colors.get(regime, "#e2e3e5")
    
    html = f"""
    <div style="margin: 20px 0; padding: 20px; background: {bg_color}; border-radius: 8px; border-left: 5px solid #007bff;">
        <h3 style="color: #2c3e50; margin-bottom: 15px;">📊 {chart_name}</h3>
        
        <div style="text-align: center; margin: 15px 0;">
            <img src="cid:{chart_id}" style="width: 100%; max-width: 800px; height: auto; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        </div>
        
        <div style="background: #ffffff; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h4 style="color: #495057; margin-bottom: 10px;">🤖 AI Analysis</h4>
            <p style="color: #6c757d; line-height: 1.6; margin: 0;">{explanation}</p>
        </div>
        
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
            <div style="background: #f8f9fa; padding: 8px 12px; border-radius: 4px; border: 1px solid #dee2e6;">
                <strong>🎯 Strategy:</strong> {strategy}
            </div>
            <div style="background: #f8f9fa; padding: 8px 12px; border-radius: 4px; border: 1px solid #dee2e6;">
                <strong>📈 Regime:</strong> {regime}
            </div>
            <div style="background: #f8f9fa; padding: 8px 12px; border-radius: 4px; border: 1px solid #dee2e6;">
                <strong>🎨 Theme:</strong> {market_theme}
            </div>
        </div>
        
        {f'<div style="background: #f1f3f4; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 0.9em; color: #495057;"><strong>📊 Sentiment Data:</strong> {sentiment_html}</div>' if sentiment_html else ''}
    </div>
    """
    
    return html

def generate_text_report(articles, limit=25):
    """
    Generate plain text version of the report (fallback)
    
    Args:
        articles: List of summarized articles
        limit: Maximum articles to include
    
    Returns:
        Plain text string
    """
    # Load Polygon articles and combine with existing articles
    polygon_articles = load_polygon_articles()
    all_articles = articles + polygon_articles
    
    # Deduplicate articles
    deduplicated_articles = deduplicate_articles(all_articles)
    
    # Limit articles
    articles_to_include = deduplicated_articles[:limit]
    
    # Count articles by source
    source_counts = {}
    for article in articles_to_include:
        source = article.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    
    text_content = f"""
📰 MacroIntel Daily News Report
Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
📊 {len(articles_to_include)} relevant articles from your watchlist
📈 Sources: {', '.join([f'{source} ({count})' for source, count in source_counts.items()])}

📈 Market Overview:
{generate_fear_greed_placeholder()}

📰 Relevant Headlines:
"""
    
    # Group articles by source for better organization
    articles_by_source = {}
    for article in articles_to_include:
        source = article.get("source", "unknown")
        if source not in articles_by_source:
            articles_by_source[source] = []
        articles_by_source[source].append(article)
    
    # Add articles grouped by source
    article_counter = 1
    for source, source_articles in articles_by_source.items():
        # Add source header
        source_display_name = {
            "fmp": "Financial Modeling Prep",
            "polygon": "Polygon.io",
            "perplexity": "Perplexity AI",
            "messari": "Messari",
            "benzinga": "Benzinga"
        }.get(source, source.title())
        
        text_content += f"""
📈 Source: {source_display_name} ({len(source_articles)} articles)
"""
        
        # Add articles for this source
        for article in source_articles:
            title = article.get("title", "No title")
            url = article.get("url", "#")
            summary = article.get("summary", "No summary available")
            tickers = article.get("affected_tickers", "")
            tone = article.get("tone", "Neutral")
            
            text_content += f"""
{article_counter}. {title}
   URL: {url}
   Summary: {summary}
   Tickers: {tickers}
   Tone: {tone} | Source: {source_display_name}
"""
            article_counter += 1
    
    text_content += f"""
---
MacroIntel News Scanner
This report contains {len(articles_to_include)} articles relevant to your watchlist.
Generated automatically.
"""
    
    return text_content

# Test mode
if __name__ == "__main__":
    test_html = "<h1>Test Email</h1><p>This is a test email from MacroIntel.</p>"
    send_daily_report(test_html, attachments=[]) 