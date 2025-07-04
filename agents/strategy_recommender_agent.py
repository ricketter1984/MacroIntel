#!/usr/bin/env python3
"""
Strategy Recommender Agent for MacroIntel Swarm
Uses GPT/Claude reasoning and playbook_interpreter.py to recommend trading strategies.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from playbook_interpreter import PlaybookInterpreter
from utils.api_clients import init_env

# Load .env if present
load_dotenv(dotenv_path="config/.env")
init_env()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyRecommenderAgent:
    """Agent responsible for recommending trading strategies using GPT/Claude reasoning."""
    
    def __init__(self, ai_engine: str = "gpt"):
        self.playbook = PlaybookInterpreter()
        self.ai_engine = ai_engine
        self.openai_client = None
        if ai_engine == "gpt" and OpenAI:
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info(f"🧠 Strategy Recommender Agent initialized (engine: {ai_engine})")
    
    def get_market_context(self, asset: str, fear_level: Optional[int] = None, 
                          macro_conditions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Gather comprehensive market context for strategy analysis.
        
        Args:
            asset: Asset symbol (e.g., BTCUSD, M2K)
            fear_level: Optional fear/greed level override
            macro_conditions: List of macro conditions
            
        Returns:
            Dictionary with market context data
        """
        try:
            logger.info(f"🔍 Gathering market context for {asset}...")
            
            # Get current market data
            fear_score, fear_rating = self.playbook.get_fear_greed_index()
            vix_current, vix_avg, vix_change = self.playbook.get_vix_data()
            sp500_data = self.playbook.get_sp500_momentum()
            macro_indicators = self.playbook.get_macro_indicators()
            
            # Use provided fear level if available
            if fear_level is not None:
                fear_score = fear_level
                fear_rating = self._get_fear_rating(fear_level)
            
            # Get market regime
            market_regime = self.playbook.determine_market_regime(fear_score, vix_current, sp500_data)
            
            # Check for disqualifiers
            market_data = {
                "fear_greed_score": fear_score,
                "fear_greed_rating": fear_rating,
                "vix_current": vix_current,
                "vix_avg": vix_avg,
                "vix_change": vix_change,
                "sp500_data": sp500_data,
                "macro_indicators": macro_indicators,
                "market_regime": market_regime
            }
            
            disqualifiers = self.playbook.check_disqualifiers(market_data)
            
            context = {
                "asset": asset,
                "market_data": market_data,
                "disqualifiers": disqualifiers,
                "macro_conditions": macro_conditions or [],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📊 Market context gathered: {len(disqualifiers)} disqualifiers found")
            return context
            
        except Exception as e:
            logger.error(f"❌ Error gathering market context: {str(e)}")
            return {
                "asset": asset,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_fear_rating(self, score: int) -> str:
        """Convert fear/greed score to rating."""
        if score <= 25:
            return "Extreme Fear"
        elif score <= 45:
            return "Fear"
        elif score <= 55:
            return "Neutral"
        elif score <= 75:
            return "Greed"
        else:
            return "Extreme Greed"
    
    def evaluate_strategies(self, market_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate all available strategies against current market conditions.
        
        Args:
            market_context: Market context data
            
        Returns:
            List of evaluated strategies with viability scores
        """
        try:
            logger.info("🎯 Evaluating strategies against market conditions...")
            
            evaluated_strategies = []
            
            for strategy_name, strategy_config in self.playbook.strategy_tiers.items():
                viability = self.playbook.evaluate_strategy_viability(
                    strategy_name, strategy_config, market_context["market_data"]
                )
                
                # Accept both dict and tuple returns for backward compatibility
                if isinstance(viability, dict):
                    is_viable = viability.get("viable", False)
                elif isinstance(viability, tuple):
                    is_viable = viability[0]
                    viability = viability[1] if len(viability) > 1 and isinstance(viability[1], dict) else {}
                else:
                    is_viable = False
                
                if is_viable:
                    evaluated_strategies.append({
                        "strategy_name": strategy_name,
                        "tier_level": strategy_name.split()[1],  # Extract tier number
                        "setup_conditions": strategy_config["conditions"],
                        "description": strategy_config["description"],
                        "viability_score": viability.get("score", 0),
                        "confidence_factors": viability.get("confidence_factors", []),
                        "risk_level": self._determine_risk_level(strategy_name, market_context),
                        "disqualifiers": viability.get("disqualifiers", [])
                    })
            
            # Sort by viability score (highest first)
            evaluated_strategies.sort(key=lambda x: x["viability_score"], reverse=True)
            
            logger.info(f"✅ Evaluated {len(evaluated_strategies)} viable strategies")
            return evaluated_strategies
            
        except Exception as e:
            logger.error(f"❌ Error evaluating strategies: {str(e)}")
            return []
    
    def _determine_risk_level(self, strategy_name: str, market_context: Dict[str, Any]) -> str:
        """Determine risk level based on strategy and market conditions."""
        fear_score = market_context["market_data"]["fear_greed_score"]
        vix_current = market_context["market_data"]["vix_current"]
        
        # High risk: extreme conditions or high VIX
        if fear_score <= 20 or fear_score >= 80 or vix_current >= 30:
            return "High"
        # Medium risk: moderate conditions
        elif fear_score <= 35 or fear_score >= 65 or vix_current >= 20:
            return "Medium"
        # Low risk: stable conditions
        else:
            return "Low"
    
    def generate_gpt_justification(self, asset: str, market_context: Dict[str, Any], top_strategy: Dict[str, Any]) -> str:
        """Generate the why_this_setup justification using GPT/Claude."""
        if self.ai_engine == "gpt" and self.openai_client:
            try:
                market_data = market_context["market_data"]
                prompt = f"""
You are an expert trading strategist. Given the following market context and recommended strategy, explain in 2-3 sentences why this setup is optimal.

Asset: {asset}
Market Regime: {market_data['market_regime']}
Fear & Greed Index: {market_data['fear_greed_score']} ({market_data['fear_greed_rating']})
VIX: {market_data['vix_current']:.1f}
Macro: {', '.join(market_context['macro_conditions']) if market_context['macro_conditions'] else 'None'}
Strategy: {top_strategy['strategy_name']} (Tier {top_strategy['tier_level']})
Setup Conditions: {top_strategy['setup_conditions']}
Disqualifiers: {top_strategy['disqualifiers']}

Justification (2-3 sentences):
"""
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert trading strategist."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"GPT justification failed: {e}")
                return "[GPT error: could not generate justification]"
        # Claude or fallback
        return "[AI justification not available: GPT/Claude integration required]"
    
    def run(self, asset: Optional[str], fear_level: Optional[int], macro_conditions: Optional[List[str]], trend_state: Optional[str]) -> Dict[str, Any]:
        errors = []
        if not asset:
            errors.append("Missing required argument: --asset (e.g., BTCUSD, QQQ)")
        if errors:
            return {"error": " | ".join(errors)}
        market_context = self.get_market_context(asset, fear_level, macro_conditions)
        if "error" in market_context:
            return {"error": market_context["error"]}
        evaluated_strategies = self.evaluate_strategies(market_context)
        if not evaluated_strategies:
            return {"error": "No viable strategies found for the given context."}
        top_strategy = evaluated_strategies[0]
        justification = self.generate_gpt_justification(asset, market_context, top_strategy)
        summary = {
            "strategy_name": top_strategy["strategy_name"],
            "setup_conditions": top_strategy["setup_conditions"],
            "tier_level": top_strategy["tier_level"],
            "confidence_score": top_strategy["viability_score"],
            "key_disqualifiers": top_strategy["disqualifiers"],
            "why_this_setup": justification
        }
        result = {
            "asset": asset,
            "market_context": market_context,
            "summary": summary,
            "all_strategies": evaluated_strategies,
            "timestamp": datetime.now().isoformat()
        }
        return result

def print_markdown_summary(result: Dict[str, Any]):
    if "error" in result:
        print(f"\n**❌ Error:** {result['error']}\n")
        return
    summary = result["summary"]
    print("\n---\n")
    print(f"### 🧠 Strategy Recommendation for `{result['asset']}`\n")
    print(f"| Field              | Value |")
    print(f"|--------------------|-------|")
    print(f"| **Strategy Name**  | {summary['strategy_name']} |")
    print(f"| **Tier Level**     | {summary['tier_level']} |")
    print(f"| **Confidence**     | {summary['confidence_score']} |")
    print(f"| **Setup Conditions** | `{summary['setup_conditions']}` |")
    print(f"| **Key Disqualifiers** | `{', '.join(summary['key_disqualifiers']) if summary['key_disqualifiers'] else 'None'}` |\n")
    print(f"**Justification:**\n\n> {summary['why_this_setup']}\n")
    print("---\n")

def main():
    parser = argparse.ArgumentParser(
        description="Strategy Recommender Agent - Generate trading strategy recommendations using GPT/Claude reasoning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python strategy_recommender_agent.py --asset BTCUSD --fear 21 --macro "dollar falling"
  python strategy_recommender_agent.py --asset M2K --macro "inflation rising" "fed hawkish"
  python strategy_recommender_agent.py --asset QQQ
        """
    )
    parser.add_argument("--asset", type=str, help="Asset symbol to analyze (e.g., BTCUSD, M2K, QQQ)")
    parser.add_argument("--fear", type=int, help="Override fear/greed level (0-100)")
    parser.add_argument("--macro", nargs="+", help="Macro conditions (e.g., 'dollar falling', 'inflation rising')")
    parser.add_argument("--trend", type=str, help="Trend state context")
    parser.add_argument("--engine", type=str, choices=["gpt", "claude"], default="gpt", help="AI engine for justification (default: gpt)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    agent = StrategyRecommenderAgent(ai_engine=args.engine)
    result = agent.run(
        asset=args.asset,
        fear_level=args.fear,
        macro_conditions=args.macro,
        trend_state=args.trend
    )
    print_markdown_summary(result)
    print("\n[Full Output as dict]\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
