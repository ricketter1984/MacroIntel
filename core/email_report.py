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

# Import visual query engine
try:
    from visual_query_engine import generate_extreme_fear_chart
    VISUAL_ENGINE_AVAILABLE = True
except ImportError:
    print("⚠️ Visual query engine not available - charts will be skipped")
    VISUAL_ENGINE_AVAILABLE = False

load_dotenv(dotenv_path="config/.env")

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

def generate_email_content(articles, limit=25):
    """
    Generate HTML email content with articles, summaries, and visuals
    
    Args:
        articles: List of summarized articles
        limit: Maximum articles to include
    
    Returns:
        HTML string for email body
    """
    # Limit articles
    articles_to_include = articles[:limit]
    
    # Load regime score data
    regime_data = load_regime_score_data()
    regime_summary_html = generate_regime_summary_html(regime_data)
    
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
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📰 MacroIntel Daily News Report</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>📊 {len(articles_to_include)} relevant articles from your watchlist</p>
        </div>
        
        {regime_summary_html}
        
        <div class="visuals">
            <h2>📈 Market Overview</h2>
            <p><strong>{fear_greed}</strong></p>
            {sector_heatmap}
            {sentiment_gauge}
        </div>
        
        {extreme_fear_chart_html}
        
        <h2>📰 Relevant Headlines</h2>
    """
    
    # Add articles
    for i, article in enumerate(articles_to_include, 1):
        title = article.get("title", "No title")
        url = article.get("url", "#")
        summary = article.get("summary", "No summary available")
        tickers = article.get("affected_tickers", "")
        tone = article.get("tone", "Neutral")
        source = article.get("source", "unknown")
        
        # Determine tone class
        tone_class = f"tone-{tone.lower()}"
        
        html_content += f"""
        <div class="article">
            <div class="title">
                <a href="{url}" style="color: #2c3e50; text-decoration: none;">{i}. {title}</a>
            </div>
            <div class="summary">{summary}</div>
            <div style="margin-top: 5px;">
                <span class="tickers">📈 {tickers}</span> | 
                <span class="tone {tone_class}">{tone}</span> | 
                <small>Source: {source}</small>
            </div>
        </div>
        """
    
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
    # Load credentials using os.getenv()
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("EMAIL_TO")
    
    # Additional email settings
    sender_email = os.getenv("EMAIL_SENDER")
    sender_name = os.getenv("EMAIL_SENDER_NAME", "MacroIntel Bot")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    subject = os.getenv("EMAIL_SUBJECT", "MacroIntel Daily News Report")

    # Validate required credentials
    if not all([smtp_user, smtp_password, email_to]):
        print("[ERROR] Missing required email credentials: SMTP_USER, SMTP_PASSWORD, or EMAIL_TO")
        return False

    # Ensure all required fields are strings
    smtp_user = str(smtp_user)
    smtp_password = str(smtp_password)
    email_to = str(email_to)
    sender_email = str(sender_email) if sender_email else "noreply@macrointel.com"
    smtp_server = str(smtp_server) if smtp_server else "smtp.gmail.com"

    print(f"[INFO] Sending email to {email_to}")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = formataddr((sender_name, sender_email))
    msg['To'] = email_to

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
            server.sendmail(sender_email, email_to, msg.as_string())
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
    articles_to_include = articles[:limit]
    
    text_content = f"""
📰 MacroIntel Daily News Report
Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
📊 {len(articles_to_include)} relevant articles from your watchlist

📈 Market Overview:
{generate_fear_greed_placeholder()}

📰 Relevant Headlines:
"""
    
    for i, article in enumerate(articles_to_include, 1):
        title = article.get("title", "No title")
        url = article.get("url", "#")
        summary = article.get("summary", "No summary available")
        tickers = article.get("affected_tickers", "")
        tone = article.get("tone", "Neutral")
        source = article.get("source", "unknown")
        
        text_content += f"""
{i}. {title}
   URL: {url}
   Summary: {summary}
   Tickers: {tickers}
   Tone: {tone} | Source: {source}
"""
    
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