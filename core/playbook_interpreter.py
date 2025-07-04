#!/usr/bin/env python3
"""
Trading Playbook Interpreter for MacroIntel
Evaluates market conditions and selects viable strategies based on Trading Playbook rules.
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PlaybookInterpreter:
    """Interprets market conditions based on Trading Playbook rules."""
    
    def __init__(self):
        """Initialize the playbook interpreter with API keys and configuration."""
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.fear_greed_api_key = os.getenv("FEAR_GREED_API_KEY")
        
        # Strategy tiers and their conditions
        self.strategy_tiers = {
            "Tier 1 Reversal Ignition": {
                "conditions": {
                    "vix_max": 25,
                    "fear_greed_min": 20,
                    "fear_greed_max": 80,
                    "volatility_required": True,
                    "momentum_required": False
                },
                "description": "High-probability reversal setups in volatile conditions"
            },
            "Tier 2 Momentum Reload": {
                "conditions": {
                    "vix_max": 20,
                    "fear_greed_min": 30,
                    "fear_greed_max": 70,
                    "volatility_required": False,
                    "momentum_required": True
                },
                "description": "Momentum continuation in stable market conditions"
            },
            "Tier 3 Breakout Acceleration": {
                "conditions": {
                    "vix_max": 18,
                    "fear_greed_min": 40,
                    "fear_greed_max": 60,
                    "volatility_required": False,
                    "momentum_required": True
                },
                "description": "Breakout plays in low volatility, trending markets"
            },
            "Tier 4 Mean Reversion": {
                "conditions": {
                    "vix_max": 30,
                    "fear_greed_min": 10,
                    "fear_greed_max": 90,
                    "volatility_required": True,
                    "momentum_required": False
                },
                "description": "Mean reversion plays in extreme conditions"
            },
            "Tier 5 Defensive Hedge": {
                "conditions": {
                    "vix_min": 25,
                    "fear_greed_max": 30,
                    "volatility_required": True,
                    "momentum_required": False
                },
                "description": "Defensive strategies in high fear/volatility"
            }
        }
        
        # Disqualifier conditions
        self.disqualifiers = {
            "vix_extreme_high": 35,
            "vix_extreme_low": 12,
            "fear_greed_extreme_fear": 15,
            "fear_greed_extreme_greed": 85,
            "conflicting_signals": True
        }
        
        logging.info("Playbook Interpreter initialized")
    
    def get_fear_greed_index(self):
        """Fetch current Fear & Greed Index from CNN API."""
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
            from utils.api_clients import fetch_vix_data
            
            vix_df = fetch_vix_data(days=30)
            
            if vix_df is not None and not vix_df.empty:
                latest_vix = float(vix_df['VIX'].iloc[-1])
                avg_vix = float(vix_df['VIX'].mean())
                vix_change = ((latest_vix - avg_vix) / avg_vix) * 100 if avg_vix > 0 else 0
                return latest_vix, avg_vix, vix_change
            else:
                return 20, 20, 0  # Default values
                
        except Exception as e:
            logging.error(f"Error fetching VIX data: {str(e)}")
            return 20, 20, 0
    
    def get_sp500_momentum(self):
        """Calculate S&P 500 momentum indicators."""
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
                    
                    # Calculate momentum indicators
                    momentum_20 = ((current_price - sma_20) / sma_20) * 100 if sma_20 > 0 else 0
                    momentum_50 = ((current_price - sma_50) / sma_50) * 100 if sma_50 > 0 else 0
                    
                    # Determine trend strength
                    if current_price > sma_20 > sma_50:
                        trend = "Strong Uptrend"
                    elif current_price > sma_20 and sma_20 < sma_50:
                        trend = "Weak Uptrend"
                    elif current_price < sma_20 < sma_50:
                        trend = "Strong Downtrend"
                    elif current_price < sma_20 and sma_20 > sma_50:
                        trend = "Weak Downtrend"
                    else:
                        trend = "Sideways"
                    
                    return {
                        "current_price": current_price,
                        "sma_20": sma_20,
                        "sma_50": sma_50,
                        "momentum_20": momentum_20,
                        "momentum_50": momentum_50,
                        "trend": trend
                    }
            return None
            
        except Exception as e:
            logging.error(f"Error fetching S&P 500 data: {str(e)}")
            return None
    
    def get_macro_indicators(self):
        """Fetch macro indicators (Gold, BTC, Dollar, Oil)."""
        try:
            indicators = {}
            symbols = {
                "GOLD": "GLD",
                "BTC": "BTCUSD", 
                "DOLLAR": "UUP",
                "OIL": "USO"
            }
            
            for name, symbol in symbols.items():
                url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
                params = {
                    "apikey": self.fmp_api_key,
                    "from": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "to": datetime.now().strftime("%Y-%m-%d")
                }
                
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if "historical" in data and data["historical"]:
                        prices = [float(d["close"]) for d in data["historical"][:5]]
                        if len(prices) >= 2:
                            change_pct = ((prices[0] - prices[-1]) / prices[-1]) * 100
                            indicators[name] = {
                                "current": prices[0],
                                "change_5d": change_pct,
                                "trend": "Bullish" if change_pct > 2 else "Bearish" if change_pct < -2 else "Neutral"
                            }
            
            return indicators
            
        except Exception as e:
            logging.error(f"Error fetching macro indicators: {str(e)}")
            return {}
    
    def determine_market_regime(self, fear_greed_score, vix_current, sp500_data):
        """Determine market regime based on Fear & Greed and VIX."""
        try:
            # Risk-On conditions
            if (fear_greed_score > 60 and vix_current < 20 and 
                sp500_data and sp500_data["trend"] in ["Strong Uptrend", "Weak Uptrend"]):
                return "Risk-On"
            
            # Risk-Off conditions
            elif (fear_greed_score < 30 and vix_current > 25 and 
                  sp500_data and sp500_data["trend"] in ["Strong Downtrend", "Weak Downtrend"]):
                return "Risk-Off"
            
            # Neutral conditions
            else:
                return "Neutral"
                
        except Exception as e:
            logging.error(f"Error determining market regime: {str(e)}")
            return "Neutral"
    
    def evaluate_strategy_viability(self, strategy_name, strategy_config, market_data):
        """Evaluate if a strategy is viable given current market conditions."""
        try:
            conditions = strategy_config["conditions"]
            viable = True
            reasons = []
            
            # Check VIX conditions
            if "vix_max" in conditions and market_data["vix_current"] > conditions["vix_max"]:
                viable = False
                reasons.append(f"VIX too high ({market_data['vix_current']:.1f} > {conditions['vix_max']})")
            
            if "vix_min" in conditions and market_data["vix_current"] < conditions["vix_min"]:
                viable = False
                reasons.append(f"VIX too low ({market_data['vix_current']:.1f} < {conditions['vix_min']})")
            
            # Check Fear & Greed conditions
            if "fear_greed_min" in conditions and market_data["fear_greed_score"] < conditions["fear_greed_min"]:
                viable = False
                reasons.append(f"Fear too high ({market_data['fear_greed_score']} < {conditions['fear_greed_min']})")
            
            if "fear_greed_max" in conditions and market_data["fear_greed_score"] > conditions["fear_greed_max"]:
                viable = False
                reasons.append(f"Greed too high ({market_data['fear_greed_score']} > {conditions['fear_greed_max']})")
            
            # Check volatility requirements
            if conditions.get("volatility_required", False):
                vix_ratio = market_data["vix_current"] / market_data["vix_avg"] if market_data["vix_avg"] > 0 else 1
                if vix_ratio < 1.2:
                    viable = False
                    reasons.append("Insufficient volatility")
            
            # Check momentum requirements
            if conditions.get("momentum_required", False) and market_data.get("sp500_data"):
                if market_data["sp500_data"]["momentum_20"] < 1:
                    viable = False
                    reasons.append("Insufficient momentum")
            
            return viable, reasons
            
        except Exception as e:
            logging.error(f"Error evaluating strategy viability: {str(e)}")
            return False, ["Evaluation error"]
    
    def check_disqualifiers(self, market_data):
        """Check for market disqualifiers."""
        try:
            disqualifiers = []
            
            # VIX extreme conditions
            if market_data["vix_current"] > self.disqualifiers["vix_extreme_high"]:
                disqualifiers.append(f"VIX extremely high ({market_data['vix_current']:.1f})")
            
            if market_data["vix_current"] < self.disqualifiers["vix_extreme_low"]:
                disqualifiers.append(f"VIX extremely low ({market_data['vix_current']:.1f})")
            
            # Fear & Greed extreme conditions
            if market_data["fear_greed_score"] < self.disqualifiers["fear_greed_extreme_fear"]:
                disqualifiers.append(f"Extreme fear ({market_data['fear_greed_score']})")
            
            if market_data["fear_greed_score"] > self.disqualifiers["fear_greed_extreme_greed"]:
                disqualifiers.append(f"Extreme greed ({market_data['fear_greed_score']})")
            
            # Conflicting signals
            if market_data.get("sp500_data"):
                sp500_trend = market_data["sp500_data"]["trend"]
                fear_greed = market_data["fear_greed_score"]
                
                if (sp500_trend in ["Strong Uptrend", "Weak Uptrend"] and fear_greed < 30):
                    disqualifiers.append("Conflicting signals: Bullish trend with high fear")
                elif (sp500_trend in ["Strong Downtrend", "Weak Downtrend"] and fear_greed > 70):
                    disqualifiers.append("Conflicting signals: Bearish trend with high greed")
            
            return disqualifiers
            
        except Exception as e:
            logging.error(f"Error checking disqualifiers: {str(e)}")
            return ["Error checking disqualifiers"]
    
    def generate_macro_notes(self, macro_indicators, market_data):
        """Generate macro analysis notes."""
        try:
            notes = []
            
            # Analyze Gold behavior
            if "GOLD" in macro_indicators:
                gold_data = macro_indicators["GOLD"]
                if gold_data["trend"] == "Bullish" and market_data["fear_greed_score"] < 40:
                    notes.append("Gold surging as safe haven during market stress")
                elif gold_data["trend"] == "Bullish" and market_data["fear_greed_score"] > 60:
                    notes.append("Gold rising alongside risk assets - inflation hedge")
            
            # Analyze Bitcoin behavior
            if "BTC" in macro_indicators:
                btc_data = macro_indicators["BTC"]
                if btc_data["trend"] == "Bullish" and market_data["fear_greed_score"] > 60:
                    notes.append("Bitcoin showing risk-on characteristics")
                elif btc_data["trend"] == "Bullish" and market_data["fear_greed_score"] < 40:
                    notes.append("Bitcoin acting as digital gold during stress")
            
            # Analyze Dollar behavior
            if "DOLLAR" in macro_indicators:
                dollar_data = macro_indicators["DOLLAR"]
                if dollar_data["trend"] == "Bullish" and market_data["fear_greed_score"] < 40:
                    notes.append("Dollar strengthening as flight-to-quality asset")
                elif dollar_data["trend"] == "Bearish" and market_data["fear_greed_score"] > 60:
                    notes.append("Dollar weakening as risk appetite increases")
            
            # Analyze Oil behavior
            if "OIL" in macro_indicators:
                oil_data = macro_indicators["OIL"]
                if oil_data["trend"] == "Bullish" and market_data["fear_greed_score"] > 60:
                    notes.append("Oil rising with economic optimism")
                elif oil_data["trend"] == "Bearish" and market_data["fear_greed_score"] < 40:
                    notes.append("Oil declining on growth concerns")
            
            # Market regime summary
            if market_data["regime"] == "Risk-On":
                notes.append("Risk-on environment favors high beta assets and momentum strategies")
            elif market_data["regime"] == "Risk-Off":
                notes.append("Risk-off environment favors defensive assets and reversal strategies")
            else:
                notes.append("Neutral environment - mixed signals suggest selective positioning")
            
            return notes
            
        except Exception as e:
            logging.error(f"Error generating macro notes: {str(e)}")
            return ["Error generating macro analysis"]
    
    def interpret_market_conditions(self):
        """Main function to interpret market conditions based on Trading Playbook rules."""
        try:
            logging.info("Starting market condition interpretation...")
            
            # Gather market data
            fear_greed_score, fear_greed_rating = self.get_fear_greed_index()
            vix_current, vix_avg, vix_change = self.get_vix_data()
            sp500_data = self.get_sp500_momentum()
            macro_indicators = self.get_macro_indicators()
            
            # Determine market regime
            regime = self.determine_market_regime(fear_greed_score, vix_current, sp500_data)
            
            # Compile market data
            market_data = {
                "fear_greed_score": fear_greed_score,
                "fear_greed_rating": fear_greed_rating,
                "vix_current": vix_current,
                "vix_avg": vix_avg,
                "vix_change": vix_change,
                "sp500_data": sp500_data,
                "regime": regime,
                "macro_indicators": macro_indicators
            }
            
            # Evaluate strategy viability
            viable_strategies = []
            avoid_strategies = []
            
            for strategy_name, strategy_config in self.strategy_tiers.items():
                viable, reasons = self.evaluate_strategy_viability(strategy_name, strategy_config, market_data)
                
                if viable:
                    viable_strategies.append(strategy_name)
                else:
                    avoid_strategies.append(f"{strategy_name} ({', '.join(reasons)})")
            
            # Check disqualifiers
            disqualifiers = self.check_disqualifiers(market_data)
            
            # Generate macro notes
            macro_notes = self.generate_macro_notes(macro_indicators, market_data)
            
            # Compile results
            result = {
                "regime": regime,
                "viable_strategies": viable_strategies,
                "avoid": avoid_strategies,
                "disqualifiers": disqualifiers,
                "macro_notes": macro_notes,
                "market_data": {
                    "fear_greed": {"score": fear_greed_score, "rating": fear_greed_rating},
                    "vix": {"current": vix_current, "average": vix_avg, "change": vix_change},
                    "sp500": sp500_data,
                    "macro_indicators": macro_indicators
                }
            }
            
            logging.info(f"Market interpretation complete: {regime} regime with {len(viable_strategies)} viable strategies")
            return result
            
        except Exception as e:
            logging.error(f"Error interpreting market conditions: {str(e)}")
            return {
                "regime": "Unknown",
                "viable_strategies": [],
                "avoid": ["All strategies (interpretation error)"],
                "disqualifiers": ["System error"],
                "macro_notes": ["Unable to analyze market conditions"],
                "market_data": {}
            }

def main():
    """Main function for testing the playbook interpreter."""
    try:
        interpreter = PlaybookInterpreter()
        result = interpreter.interpret_market_conditions()
        
        print("\n" + "="*60)
        print("📊 TRADING PLAYBOOK INTERPRETATION")
        print("="*60)
        
        print(f"\n🎯 Market Regime: {result['regime']}")
        
        print(f"\n✅ Viable Strategies ({len(result['viable_strategies'])}):")
        for strategy in result['viable_strategies']:
            print(f"   • {strategy}")
        
        if result['avoid']:
            print(f"\n❌ Avoid ({len(result['avoid'])}):")
            for avoid in result['avoid']:
                print(f"   • {avoid}")
        
        if result['disqualifiers']:
            print(f"\n🚫 Disqualifiers ({len(result['disqualifiers'])}):")
            for dq in result['disqualifiers']:
                print(f"   • {dq}")
        
        print(f"\n📈 Macro Notes ({len(result['macro_notes'])}):")
        for note in result['macro_notes']:
            print(f"   • {note}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Error in main: {str(e)}")

if __name__ == "__main__":
    main() 