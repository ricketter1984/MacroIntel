import os
import smtplib
import requests
import json
import glob
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from dotenv import load_dotenv
from email.utils import formataddr
from pathlib import Path

# Load environment variables at the top
load_dotenv(dotenv_path="config/.env")

# Import visual query engine
try:
    from visual_query_engine import generate_extreme_fear_chart
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
    """Generate Fear & Greed index using real API or fallback to placeholder"""
    fear_greed_api_key = os.getenv("FEAR_GREED_API_KEY")
    fear_greed_api_host = "cnn-fear-and-greed-index.p.rapidapi.com"  # Fixed host
    
    if not fear_greed_api_key:
        print("⚠️ FEAR_GREED_API_KEY not found in environment variables")
        return "Fear & Greed Index: 65 (Greed) - Market showing moderate optimism [API Key Missing]"
    
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
            return "Fear & Greed Index: 65 (Greed) - Market showing moderate optimism [API Error]"
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Fear & Greed API request failed: {str(e)}")
        return "Fear & Greed Index: 65 (Greed) - Market showing moderate optimism [API Unavailable]"
    except Exception as e:
        print(f"⚠️ Fear & Greed API error: {str(e)}")
        return "Fear & Greed Index: 65 (Greed) - Market showing moderate optimism [API Error]"

def generate_sector_heatmap_placeholder():
    """Generate a placeholder for sector heatmap"""
    sectors = {
        "Technology": "🔥 Hot",
        "Financial": "📈 Bullish", 
        "Energy": "⚡ Volatile",
        "Healthcare": "🩺 Stable",
        "Consumer": "🛒 Mixed"
    }
    
    heatmap_html = "<h3>📊 Sector Heatmap</h3><ul>"
    for sector, status in sectors.items():
        heatmap_html += f"<li><strong>{sector}:</strong> {status}</li>"
    heatmap_html += "</ul>"
    
    return heatmap_html

def generate_sentiment_gauge_placeholder():
    """Generate a placeholder for sentiment gauge"""
    # Placeholder sentiment analysis
    sentiment_score = 65  # 0-100 scale
    sentiment_label = "Moderately Bullish"
    
    gauge_html = f"""
    <h3>📊 Market Sentiment</h3>
    <div style="background: #f0f0f0; padding: 10px; border-radius: 5px;">
        <strong>Sentiment Score:</strong> {sentiment_score}/100 ({sentiment_label})<br>
        <div style="background: linear-gradient(to right, #ff4444, #ffff44, #44ff44); 
                    height: 20px; border-radius: 10px; position: relative;">
            <div style="background: #333; width: 4px; height: 20px; 
                        position: absolute; left: {sentiment_score}%; border-radius: 2px;"></div>
        </div>
        <small>Bearish ← → Bullish</small>
    </div>
    """
    
    return gauge_html

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
    Load the most recent Barchart.com Most Active Futures data from output directory.
    Returns a list of futures contracts or empty list if not found.
    """
    try:
        output_dir = Path("output")
        if not output_dir.exists():
            return []
        futures_files = list(output_dir.glob("barchart_futures_*.json"))
        if not futures_files:
            return []
        latest_file = max(futures_files, key=lambda x: x.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"⚠️ Error loading Barchart Futures data: {e}")
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
        articles: List of summarized articles
        limit: Maximum articles to include
    
    Returns:
        HTML string for email body
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
    
    # Check for extreme fear chart
    extreme_fear_chart_html = ""
    if VISUAL_ENGINE_AVAILABLE:
        try:
            chart_path = generate_extreme_fear_chart()
            if chart_path and os.path.exists(chart_path):
                extreme_fear_chart_html = f"""
                <div style="margin: 20px 0; padding: 15px; background: #2c3e50; border-radius: 5px;">
                    <h3>😱 Extreme Fear Alert - Asset Performance Analysis</h3>
                    <p>Market fear detected! Here's how key assets are performing during this period:</p>
                    <img src="cid:fear_chart" style="width: 100%; max-width: 600px; height: auto; border-radius: 5px;">
                    <p><small>Chart shows 1-year performance comparison of BTC, Gold, and QQQ</small></p>
                </div>
                """
        except Exception as e:
            print(f"⚠️ Error generating extreme fear chart: {str(e)}")
    
    # Load Yahoo Futures data
    yahoo_futures_data = load_latest_yahoo_futures()
    barchart_futures_data = load_latest_barchart_futures()
    yahoo_futures_html = generate_futures_table_html(yahoo_futures_data, "Yahoo Futures Screener")
    barchart_futures_html = generate_futures_table_html(barchart_futures_data, "Barchart Most Active Futures")
    # Start HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
            .article {{ border-left: 4px solid #3498db; margin: 15px 0; padding: 10px; background: #f8f9fa; }}
            .title {{ font-weight: bold; color: #2c3e50; margin-bottom: 5px; }}
            .summary {{ color: #555; margin: 5px 0; }}
            .tickers {{ color: #e74c3c; font-weight: bold; }}
            .tone {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 12px; }}
            .tone-bullish {{ background: #d4edda; color: #155724; }}
            .tone-bearish {{ background: #f8d7da; color: #721c24; }}
            .tone-neutral {{ background: #d1ecf1; color: #0c5460; }}
            .tone-volatile {{ background: #fff3cd; color: #856404; }}
            .visuals {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ margin-top: 30px; padding: 15px; background: #95a5a6; color: white; border-radius: 5px; }}
            .source-header {{ background: #34495e; color: white; padding: 8px 15px; margin: 20px 0 10px 0; border-radius: 5px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📰 MacroIntel Daily News Report</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>📊 {len(articles_to_include)} relevant articles from your watchlist</p>
            <p>📈 Sources: {', '.join([f'{source} ({count})' for source, count in source_counts.items()])}</p>
        </div>
        
        {regime_summary_html}
        
        {agent_results_html}
        
        <div class="visuals">
            <h2>📈 Market Overview</h2>
            <p><strong>{fear_greed}</strong></p>
            {sector_heatmap}
            {sentiment_gauge}
        </div>
        
        {yahoo_futures_html}
        {barchart_futures_html}
        {extreme_fear_chart_html}
        
        <h2>📰 Relevant Headlines</h2>
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
        <div class="source-header">
            📈 Source: {source_display_name} ({len(source_articles)} articles)
        </div>
        """
        
        # Add articles for this source
        for article in source_articles:
            title = article.get("title", "No title")
            url = article.get("url", "#")
            summary = article.get("summary", "No summary available")
            tickers = article.get("affected_tickers", "")
            tone = article.get("tone", "Neutral")
            
            # Determine tone class
            tone_class = f"tone-{tone.lower()}"
            
            html_content += f"""
            <div class="article">
                <div class="title">
                    <a href="{url}" style="color: #2c3e50; text-decoration: none;">{article_counter}. {title}</a>
                </div>
                <div class="summary">{summary}</div>
                <div style="margin-top: 5px;">
                    <span class="tickers">📈 {tickers}</span> | 
                    <span class="tone {tone_class}">{tone}</span> | 
                    <small>Source: {source_display_name}</small>
                </div>
            </div>
            """
            article_counter += 1
    
    # Add footer
    html_content += f"""
        <div class="footer">
            <p><strong>MacroIntel News Scanner</strong></p>
            <p>This report contains {len(articles_to_include)} articles relevant to your watchlist.</p>
            <p>Generated automatically - click article titles to read full stories.</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_daily_report(html_content, attachments=None):
    """
    Send the daily report email with the provided HTML content as the body.
    Args:
        html_content: The full HTML string to use as the email body.
        attachments: List of file paths to attach (optional)
    Returns:
        True if sent successfully, False otherwise.
    """
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
        print("[ERROR] Missing required email credentials. Please check your .env file for:")
        print("  - SMTP_USER")
        print("  - SMTP_PASSWORD") 
        print("  - EMAIL_RECIPIENT")
        print("  - EMAIL_SENDER")
        print("  - EMAIL_SENDER_NAME")
        print("  - SMTP_SERVER")
        return False

    # Ensure all required fields are strings
    smtp_user = str(smtp_user)
    smtp_password = str(smtp_password)
    email_recipient = str(email_recipient)
    sender_email = str(sender_email)
    sender_name = str(sender_name)
    smtp_server = str(smtp_server)

    print(f"[INFO] Sending email to {email_recipient}")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = formataddr((sender_name, sender_email))
    msg['To'] = email_recipient

    # Attach the HTML content
    msg.attach(MIMEText(html_content, 'html'))

    # Add attachments if provided
    if attachments:
        for attachment_path in attachments:
            try:
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEImage(f.read())
                    attachment.add_header('Content-Disposition', 'attachment', 
                                        filename=os.path.basename(attachment_path))
                    msg.attach(attachment)
                print(f"[INFO] Attached: {os.path.basename(attachment_path)}")
            except Exception as e:
                print(f"[WARNING] Failed to attach {attachment_path}: {e}")

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, email_recipient, msg.as_string())
        print("[SUCCESS] Email sent successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False

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