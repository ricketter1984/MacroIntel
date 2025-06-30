import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from dotenv import load_dotenv

# Import visual query engine
try:
    from visual_query_engine import generate_extreme_fear_chart
    VISUAL_ENGINE_AVAILABLE = True
except ImportError:
    print("⚠️ Visual query engine not available - charts will be skipped")
    VISUAL_ENGINE_AVAILABLE = False

load_dotenv()

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

def send_daily_report(articles, limit=25):
    """
    Send daily email report with relevant news
    
    Args:
        articles: List of summarized articles
        limit: Maximum articles to include in report
    """
    # Email configuration
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    receiver_email = os.getenv("EMAIL_RECEIVER")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    
    if not all([sender_email, sender_password, receiver_email]):
        print("⚠️ Email configuration incomplete. Check EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER in .env")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📰 MacroIntel Daily Report - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = str(sender_email)  # Ensure it's a string
        msg['To'] = str(receiver_email)  # Ensure it's a string
        
        # Generate HTML content
        html_content = generate_email_content(articles, limit)
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Check for extreme fear chart and attach if available
        if VISUAL_ENGINE_AVAILABLE:
            try:
                chart_path = generate_extreme_fear_chart()
                if chart_path and os.path.exists(chart_path):
                    with open(chart_path, 'rb') as f:
                        img_data = f.read()
                        image = MIMEImage(img_data)
                        image.add_header('Content-ID', '<fear_chart>')
                        msg.attach(image)
                        print(f"📊 Attached extreme fear chart: {chart_path}")
            except Exception as e:
                print(f"⚠️ Error attaching extreme fear chart: {str(e)}")
        
        # Send email
        print(f"📧 Sending daily report to {receiver_email}...")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(str(sender_email), str(sender_password))  # Ensure they're strings
            server.send_message(msg)
        
        print("✅ Daily report sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
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