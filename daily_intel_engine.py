#!/usr/bin/env python3
"""
DEPRECATED: Daily Intelligence Engine for MacroIntel
This file has been deprecated and replaced by agents/swarm_orchestrator.py

The new Claude Flow agent swarm provides enhanced functionality:
- Better error handling and recovery
- Modular agent architecture
- Improved logging and monitoring
- Enhanced report generation

Please use the new execution engine:
python agents/swarm_orchestrator.py

This file is kept for reference only and will be removed in a future version.
"""

import os
import sys
import schedule
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import requests
import json

# Create logs directory first
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_intel.log'),
        logging.StreamHandler()
    ]
)

# Import existing modules
from utils.api_clients import fetch_all_news, init_env
from visual_query_engine import generate_extreme_fear_chart, VisualQueryEngine
from email_report import send_daily_report, generate_email_content
from news_scanner.news_insight_feed import scan_relevant_news
from playbook_interpreter import PlaybookInterpreter

# Load environment variables
load_dotenv(dotenv_path="config/.env")

class MarketRegimeAnalyzer:
    """Analyzes market regime using Trading Playbook v7.0 criteria."""
    
    def __init__(self):
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.fear_greed_api_key = os.getenv("FEAR_GREED_API_KEY")
        
    def get_fear_and_greed(self):
        """Fetch Fear & Greed Index from CNN API."""
        try:
            url = "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/index"
            headers = {
                "x-rapidapi-key": self.fear_greed_api_key,
                "x-rapidapi-host": "cnn-fear-and-greed-index.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("fear_and_greed", {}).get("score", 50)
                rating = data.get("fear_and_greed", {}).get("rating", "Neutral")
                return score, rating
            else:
                logging.warning(f"Fear & Greed API error: {response.status_code}")
                return 50, "Neutral"
                
        except Exception as e:
            logging.error(f"Error fetching Fear & Greed Index: {str(e)}")
            return 50, "Neutral"
    
    def get_vix_data(self):
        """Fetch VIX data for volatility analysis."""
        try:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/VIX"
            params = {
                "apikey": self.fmp_api_key,
                "from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if "historical" in data and data["historical"]:
                    latest_vix = float(data["historical"][0]["close"])
                    avg_vix = np.mean([float(d["close"]) for d in data["historical"][:20]])
                    return latest_vix, avg_vix
            return 20, 20  # Default values
            
        except Exception as e:
            logging.error(f"Error fetching VIX data: {str(e)}")
            return 20, 20
    
    def get_sp500_data(self):
        """Fetch S&P 500 data for trend analysis."""
        try:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/SPY"
            params = {
                "apikey": self.fmp_api_key,
                "from": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if "historical" in data and data["historical"]:
                    prices = [float(d["close"]) for d in data["historical"]]
                    current_price = prices[0]
                    sma_20 = np.mean(prices[:20])
                    sma_50 = np.mean(prices[:50])
                    return current_price, sma_20, sma_50
            return 400, 400, 400  # Default values
            
        except Exception as e:
            logging.error(f"Error fetching S&P 500 data: {str(e)}")
            return 400, 400, 400
    
    def calculate_market_regime_score(self):
        """Calculate Market Regime Score using Trading Playbook v7.0 criteria."""
        try:
            # Get market data
            fear_score, fear_rating = self.get_fear_and_greed()
            vix_current, vix_avg = self.get_vix_data()
            sp_current, sp_sma20, sp_sma50 = self.get_sp500_data()
            
            # Initialize score components
            regime_score = 0
            regime_factors = {}
            
            # 1. Fear & Greed Index (0-100 scale)
            if fear_score < 25:
                regime_score += 25  # Extreme Fear - Bullish
                regime_factors["fear_greed"] = "Extreme Fear (Bullish)"
            elif fear_score < 45:
                regime_score += 15  # Fear - Moderately Bullish
                regime_factors["fear_greed"] = "Fear (Moderately Bullish)"
            elif fear_score > 75:
                regime_score -= 25  # Extreme Greed - Bearish
                regime_factors["fear_greed"] = "Extreme Greed (Bearish)"
            elif fear_score > 55:
                regime_score -= 15  # Greed - Moderately Bearish
                regime_factors["fear_greed"] = "Greed (Moderately Bearish)"
            else:
                regime_factors["fear_greed"] = "Neutral"
            
            # 2. VIX Analysis (Volatility)
            vix_ratio = vix_current / vix_avg if vix_avg > 0 else 1
            if vix_ratio > 1.5:
                regime_score += 20  # High volatility - potential reversal
                regime_factors["volatility"] = f"High VIX ({vix_current:.1f} vs {vix_avg:.1f} avg)"
            elif vix_ratio < 0.7:
                regime_score -= 15  # Low volatility - complacency
                regime_factors["volatility"] = f"Low VIX ({vix_current:.1f} vs {vix_avg:.1f} avg)"
            else:
                regime_factors["volatility"] = f"Normal VIX ({vix_current:.1f})"
            
            # 3. S&P 500 Trend Analysis
            if sp_current > sp_sma20 > sp_sma50:
                regime_score += 20  # Strong uptrend
                regime_factors["trend"] = "Strong Uptrend"
            elif sp_current > sp_sma20 and sp_sma20 < sp_sma50:
                regime_score += 10  # Weak uptrend
                regime_factors["trend"] = "Weak Uptrend"
            elif sp_current < sp_sma20 < sp_sma50:
                regime_score -= 20  # Strong downtrend
                regime_factors["trend"] = "Strong Downtrend"
            elif sp_current < sp_sma20 and sp_sma20 > sp_sma50:
                regime_score -= 10  # Weak downtrend
                regime_factors["trend"] = "Weak Downtrend"
            else:
                regime_factors["trend"] = "Sideways"
            
            # 4. Market Breadth (simplified)
            # Using Fear & Greed as proxy for market breadth
            if fear_score < 30:
                regime_score += 15  # Oversold conditions
                regime_factors["breadth"] = "Oversold"
            elif fear_score > 70:
                regime_score -= 15  # Overbought conditions
                regime_factors["breadth"] = "Overbought"
            else:
                regime_factors["breadth"] = "Normal"
            
            # Normalize score to 0-100 range
            regime_score = max(0, min(100, 50 + regime_score))
            
            # Determine regime
            if regime_score >= 70:
                regime = "BULLISH"
            elif regime_score >= 40:
                regime = "NEUTRAL"
            else:
                regime = "BEARISH"
            
            return {
                "score": regime_score,
                "regime": regime,
                "factors": regime_factors,
                "data": {
                    "fear_greed": {"score": fear_score, "rating": fear_rating},
                    "vix": {"current": vix_current, "average": vix_avg},
                    "sp500": {"current": sp_current, "sma20": sp_sma20, "sma50": sp_sma50}
                }
            }
            
        except Exception as e:
            logging.error(f"Error calculating market regime: {str(e)}")
            return {
                "score": 50,
                "regime": "NEUTRAL",
                "factors": {"error": "Calculation failed"},
                "data": {}
            }

class StrategySelector:
    """Selects optimal strategy and instruments based on market regime."""
    
    def __init__(self):
        self.strategies = {
            "BULLISH": {
                "primary": "Momentum Long",
                "secondary": "Breakout Trading",
                "instruments": ["SPY", "QQQ", "IWM", "BTC"],
                "risk_level": "Moderate"
            },
            "NEUTRAL": {
                "primary": "Mean Reversion",
                "secondary": "Range Trading",
                "instruments": ["SPY", "GLD", "TLT", "VIX"],
                "risk_level": "Low"
            },
            "BEARISH": {
                "primary": "Defensive",
                "secondary": "Short Momentum",
                "instruments": ["VIX", "GLD", "TLT", "SHY"],
                "risk_level": "High"
            }
        }
    
    def select_strategy(self, regime_analysis):
        """Select strategy based on market regime analysis."""
        regime = regime_analysis["regime"]
        strategy_info = self.strategies.get(regime, self.strategies["NEUTRAL"])
        
        # Select primary instrument based on regime
        if regime == "BULLISH":
            primary_instrument = "SPY"  # S&P 500 ETF
        elif regime == "NEUTRAL":
            primary_instrument = "GLD"  # Gold ETF
        else:  # BEARISH
            primary_instrument = "VIX"  # Volatility Index
        
        return {
            "regime": regime,
            "primary_strategy": strategy_info["primary"],
            "secondary_strategy": strategy_info["secondary"],
            "primary_instrument": primary_instrument,
            "recommended_instruments": strategy_info["instruments"],
            "risk_level": strategy_info["risk_level"],
            "confidence": regime_analysis["score"] / 100
        }

class CrossAssetAnalyzer:
    """Analyzes cross-asset correlations and insights."""
    
    def __init__(self):
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.assets = {
            "OIL": "USO",      # Oil ETF
            "GOLD": "GLD",     # Gold ETF
            "DOLLAR": "UUP",   # Dollar ETF
            "BTC": "BTCUSD",   # Bitcoin
            "BONDS": "TLT"     # Long-term bonds
        }
    
    def get_asset_correlations(self):
        """Calculate correlations between major assets."""
        try:
            correlations = {}
            
            # Fetch recent data for correlation analysis
            for asset_name, symbol in self.assets.items():
                url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
                params = {
                    "apikey": self.fmp_api_key,
                    "from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "to": datetime.now().strftime("%Y-%m-%d")
                }
                
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if "historical" in data and data["historical"]:
                        prices = [float(d["close"]) for d in data["historical"][:20]]
                        correlations[asset_name] = prices
            
            # Calculate correlation matrix
            if len(correlations) >= 3:
                df = pd.DataFrame(correlations)
                corr_matrix = df.corr()
                
                # Find key insights
                insights = []
                
                # Oil vs Dollar correlation
                if "OIL" in corr_matrix.index and "DOLLAR" in corr_matrix.columns:
                    oil_dollar_corr = corr_matrix.loc["OIL", "DOLLAR"]
                    if oil_dollar_corr < -0.7:
                        insights.append("Strong negative correlation between Oil and Dollar")
                    elif oil_dollar_corr > 0.7:
                        insights.append("Strong positive correlation between Oil and Dollar")
                
                # Gold vs Dollar correlation
                if "GOLD" in corr_matrix.index and "DOLLAR" in corr_matrix.columns:
                    gold_dollar_corr = corr_matrix.loc["GOLD", "DOLLAR"]
                    if gold_dollar_corr < -0.7:
                        insights.append("Gold acting as dollar hedge")
                    elif gold_dollar_corr > 0.7:
                        insights.append("Gold and Dollar moving together")
                
                # BTC vs traditional assets
                if "BTC" in corr_matrix.index:
                    btc_correlations = corr_matrix.loc["BTC"]
                    if btc_correlations["GOLD"] > 0.5:
                        insights.append("Bitcoin showing safe-haven characteristics")
                    elif btc_correlations["OIL"] > 0.5:
                        insights.append("Bitcoin correlated with risk assets")
                
                return {
                    "correlation_matrix": corr_matrix.to_dict(),
                    "insights": insights,
                    "status": "success"
                }
            
            return {
                "correlation_matrix": {},
                "insights": ["Insufficient data for correlation analysis"],
                "status": "partial"
            }
            
        except Exception as e:
            logging.error(f"Error in cross-asset analysis: {str(e)}")
            return {
                "correlation_matrix": {},
                "insights": ["Analysis failed"],
                "status": "error"
            }

class DailyIntelEngine:
    """Main engine for daily market intelligence."""
    
    def __init__(self):
        self.regime_analyzer = MarketRegimeAnalyzer()
        self.strategy_selector = StrategySelector()
        self.cross_asset_analyzer = CrossAssetAnalyzer()
        self.visual_engine = VisualQueryEngine()
        self.playbook_interpreter = PlaybookInterpreter()
        
        # Create necessary directories
        os.makedirs("logs", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        
        logging.info("Daily Intelligence Engine initialized")
    
    def generate_insight_visuals(self):
        """Generate market insight visuals."""
        try:
            # Generate extreme fear chart if conditions are met
            fear_chart_path = generate_extreme_fear_chart()
            
            # Additional visual generation can be added here
            visuals = {
                "fear_chart": fear_chart_path,
                "generated_at": datetime.now().isoformat()
            }
            
            return visuals
            
        except Exception as e:
            logging.error(f"Error generating visuals: {str(e)}")
            return {"error": str(e)}
    
    def build_html_report(self, regime_analysis, strategy_selection, cross_asset_insights, playbook_analysis, news_articles, visuals):
        """Build comprehensive HTML report."""
        try:
            # Generate base email content
            html_content = generate_email_content(news_articles, limit=15)
            
            # Add market regime section
            regime_section = f"""
            <div style="background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h2>📊 Market Regime Analysis</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h3>Regime Score: {regime_analysis['score']:.1f}/100</h3>
                        <h4>Current Regime: {regime_analysis['regime']}</h4>
                        <ul>
                            <li>Fear & Greed: {regime_analysis['factors'].get('fear_greed', 'N/A')}</li>
                            <li>Volatility: {regime_analysis['factors'].get('volatility', 'N/A')}</li>
                            <li>Trend: {regime_analysis['factors'].get('trend', 'N/A')}</li>
                            <li>Breadth: {regime_analysis['factors'].get('breadth', 'N/A')}</li>
                        </ul>
                    </div>
                    <div>
                        <h3>Strategy Selection</h3>
                        <ul>
                            <li><strong>Primary:</strong> {strategy_selection['primary_strategy']}</li>
                            <li><strong>Secondary:</strong> {strategy_selection['secondary_strategy']}</li>
                            <li><strong>Instrument:</strong> {strategy_selection['primary_instrument']}</li>
                            <li><strong>Risk Level:</strong> {strategy_selection['risk_level']}</li>
                        </ul>
                    </div>
                </div>
            </div>
            """
            
            # Add cross-asset insights section
            cross_asset_section = f"""
            <div style="background: #34495e; color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h2>🔄 Cross-Asset Insights</h2>
                <ul>
                    {''.join([f'<li>{insight}</li>' for insight in cross_asset_insights['insights']])}
                </ul>
            </div>
            """
            
            # Add playbook outlook section
            playbook_section = f"""
            <div style="background: #8e44ad; color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h2>📘 Playbook Outlook</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h3>Market Regime: {playbook_analysis['regime']}</h3>
                        <h4>✅ Strategies to Use Today ({len(playbook_analysis['viable_strategies'])}):</h4>
                        <ul>
                            {''.join([f'<li>{strategy}</li>' for strategy in playbook_analysis['viable_strategies']])}
                        </ul>
                    </div>
                    <div>
                        <h4>❌ What to Avoid ({len(playbook_analysis['avoid'])}):</h4>
                        <ul>
                            {''.join([f'<li>{avoid}</li>' for avoid in playbook_analysis['avoid']])}
                        </ul>
                        {f'<h4>🚫 Disqualifiers ({len(playbook_analysis["disqualifiers"])}):</h4><ul>{chr(10).join([f"<li>{dq}</li>" for dq in playbook_analysis["disqualifiers"]])}</ul>' if playbook_analysis['disqualifiers'] else ''}
                    </div>
                </div>
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.3);">
                    <h4>📈 Macro Notes ({len(playbook_analysis['macro_notes'])}):</h4>
                    <ul>
                        {''.join([f'<li>{note}</li>' for note in playbook_analysis['macro_notes']])}
                    </ul>
                </div>
            </div>
            """
            
            # Insert custom sections into the HTML content
            # Find the position after the visuals section
            insert_pos = html_content.find('<h2>📰 Relevant Headlines</h2>')
            
            if insert_pos != -1:
                custom_sections = regime_section + cross_asset_section + playbook_section
                html_content = html_content[:insert_pos] + custom_sections + html_content[insert_pos:]
            
            return html_content
            
        except Exception as e:
            logging.error(f"Error building HTML report: {str(e)}")
            return generate_email_content(news_articles, limit=15)  # Fallback to basic report
    
    def run_daily_analysis(self):
        """Main function to run daily market analysis."""
        try:
            logging.info("Starting daily market analysis...")
            
            # 1. Calculate Market Regime Score
            logging.info("Calculating market regime...")
            regime_analysis = self.regime_analyzer.calculate_market_regime_score()
            
            # 2. Select Strategy
            logging.info("Selecting strategy...")
            strategy_selection = self.strategy_selector.select_strategy(regime_analysis)
            
            # 3. Cross-Asset Analysis
            logging.info("Analyzing cross-asset correlations...")
            cross_asset_insights = self.cross_asset_analyzer.get_asset_correlations()
            
            # 4. Playbook Interpretation
            logging.info("Interpreting market conditions with playbook...")
            playbook_analysis = self.playbook_interpreter.interpret_market_conditions()
            
            # 5. Fetch News
            logging.info("Fetching market news...")
            all_news = fetch_all_news()
            relevant_articles = scan_relevant_news(limit=15, engine='gpt')
            
            # 6. Generate Visuals
            logging.info("Generating market visuals...")
            visuals = self.generate_insight_visuals()
            
            # 7. Build Report
            logging.info("Building HTML report...")
            html_report = self.build_html_report(
                regime_analysis, 
                strategy_selection, 
                cross_asset_insights, 
                playbook_analysis,
                relevant_articles, 
                visuals
            )
            
            # 8. Send Email
            logging.info("Sending daily report...")
            success = send_daily_report(html_report)
            
            if success:
                logging.info("Daily analysis completed successfully!")
                return {
                    "status": "success",
                    "regime": regime_analysis,
                    "strategy": strategy_selection,
                    "playbook": playbook_analysis,
                    "articles_processed": len(relevant_articles)
                }
            else:
                logging.error("Failed to send daily report")
                return {"status": "error", "message": "Email sending failed"}
                
        except Exception as e:
            logging.error(f"Error in daily analysis: {str(e)}")
            return {"status": "error", "message": str(e)}

def schedule_daily_run():
    """Schedule the daily run at 7:15 AM."""
    engine = DailyIntelEngine()
    
    def daily_job():
        logging.info("Executing scheduled daily analysis...")
        result = engine.run_daily_analysis()
        logging.info(f"Daily analysis result: {result}")
    
    # Schedule for 7:15 AM daily
    schedule.every().day.at("07:15").do(daily_job)
    
    logging.info("Daily Intelligence Engine scheduled for 7:15 AM")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def main():
    """Main function for manual execution or scheduling."""
    # Initialize environment
    init_env()
    
    # Create engine
    engine = DailyIntelEngine()
    
    # Check if running manually or scheduled
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        schedule_daily_run()
    else:
        # Run immediately
        logging.info("Running daily analysis manually...")
        result = engine.run_daily_analysis()
        print(f"Analysis result: {result}")

if __name__ == "__main__":
    main() 