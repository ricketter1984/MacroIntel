#!/usr/bin/env python3
"""
Playbook Strategist Agent for MacroIntel Swarm
Runs playbook_interpreter and selects daily trading strategies.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playbook_interpreter import PlaybookInterpreter
from playbook_loader import get_playbook_loader, PlaybookConfigError
from utils.api_clients import init_env

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlaybookStrategistAgent:
    """Agent responsible for analyzing market conditions and selecting trading strategies."""
    
    def __init__(self):
        """Initialize the playbook strategist agent."""
        init_env()
        self.playbook = PlaybookInterpreter()
        
        # Initialize playbook loader
        try:
            self.playbook_loader = get_playbook_loader()
            logger.info("📘 Playbook Strategist Agent initialized with configuration loader")
        except PlaybookConfigError as e:
            logger.warning(f"⚠️ Could not load playbook configuration: {e}")
            self.playbook_loader = None
        
        logger.info("📘 Playbook Strategist Agent initialized")
    
    def analyze_market_regime(self) -> Dict[str, Any]:
        """
        Analyze current market regime using playbook interpreter.
        
        Returns:
            Dictionary with market regime analysis
        """
        try:
            logger.info("🔍 Analyzing market regime...")
            
            # Get market interpretation from playbook
            interpretation = self.playbook.interpret_market_conditions()
            
            # Extract key components
            if isinstance(interpretation, dict):
                market_regime = interpretation.get("regime", "NEUTRAL")
                selected_strategies = interpretation.get("viable_strategies", [])
                avoid_list = interpretation.get("avoid", [])
                macro_notes = interpretation.get("macro_notes", [])
            else:
                market_regime = "NEUTRAL"
                selected_strategies = []
                avoid_list = []
                macro_notes = []
            
            # Format strategies for output
            formatted_strategies = []
            for strategy in selected_strategies:
                if isinstance(strategy, str):
                    formatted_strategy = {
                        "name": strategy,
                        "description": f"Strategy: {strategy}",
                        "confidence": 0.7,
                        "conditions": {}
                    }
                else:
                    formatted_strategy = {
                        "name": strategy.get("name", ""),
                        "description": strategy.get("description", ""),
                        "confidence": strategy.get("confidence", 0.0),
                        "conditions": strategy.get("conditions", {})
                    }
                formatted_strategies.append(formatted_strategy)
            
            result = {
                "market_regime": market_regime,
                "selected_strategies": formatted_strategies,
                "avoid_list": avoid_list,
                "macro_notes": macro_notes,
                "raw_interpretation": interpretation,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📊 Market regime analysis complete: {market_regime} regime with {len(formatted_strategies)} strategies")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing market regime: {str(e)}")
            return {
                "market_regime": "NEUTRAL",
                "selected_strategies": [],
                "avoid_list": [],
                "macro_notes": f"Analysis failed: {str(e)}",
                "error": str(e)
            }
    
    def select_strategies(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Select appropriate strategies based on market conditions.
        
        Args:
            market_data: Market analysis data
            
        Returns:
            List of selected strategies with confidence scores
        """
        try:
            logger.info("🎯 Selecting trading strategies...")
            
            # Use the strategies already selected by the playbook interpreter
            strategies = market_data.get("selected_strategies", [])
            
            # Enhance strategies with playbook configuration if available
            if self.playbook_loader:
                enhanced_strategies = []
                for strategy in strategies:
                    strategy_name = strategy.get("name", "")
                    
                    # Get configuration from playbook loader
                    try:
                        strategy_config = self.playbook_loader.get_strategy_config(strategy_name)
                        enhanced_strategy = {
                            "name": strategy_name,
                            "description": strategy_config.get("description", strategy.get("description", "")),
                            "confidence": strategy.get("confidence", 0.7),
                            "conditions": strategy_config.get("conditions", {}),
                            "regime_score_threshold": strategy_config.get("regime_score_threshold", 50),
                            "risk_allocation": strategy_config.get("risk_allocation", "5%"),
                            "instruments": strategy_config.get("instruments", []),
                            "entry_rules": strategy_config.get("entry_rules", {})
                        }
                        enhanced_strategies.append(enhanced_strategy)
                    except PlaybookConfigError:
                        # Fallback to original strategy if not found in config
                        enhanced_strategies.append(strategy)
                
                strategies = enhanced_strategies
            else:
                # Fallback to original logic if playbook loader not available
                for strategy in strategies:
                    if "confidence" not in strategy:
                        # Calculate confidence based on market conditions
                        confidence = 0.7  # Default confidence
                        
                        # Adjust based on market regime
                        regime = market_data.get("market_regime", "NEUTRAL")
                        if regime == "BULLISH":
                            confidence += 0.1
                        elif regime == "BEARISH":
                            confidence -= 0.1
                        
                        strategy["confidence"] = min(1.0, max(0.0, confidence))
            
            logger.info(f"✅ Selected {len(strategies)} strategies")
            return strategies
            
        except Exception as e:
            logger.error(f"❌ Error selecting strategies: {str(e)}")
            return []
    
    def check_disqualifiers(self, market_data: Dict[str, Any]) -> List[str]:
        """
        Check for strategy disqualifiers based on market conditions.
        
        Args:
            market_data: Market analysis data
            
        Returns:
            List of disqualifying conditions
        """
        try:
            logger.info("🚫 Checking strategy disqualifiers...")
            
            # Get avoid list from playbook analysis
            avoid_list = market_data.get("avoid_list", [])
            
            # Add additional disqualifiers based on conditions
            additional_disqualifiers = []
            
            # Check for extreme conditions
            fear_greed_score = market_data.get("raw_interpretation", {}).get("fear_greed_score", 50)
            vix_current = market_data.get("raw_interpretation", {}).get("vix_current", 20)
            
            if fear_greed_score < 10:
                additional_disqualifiers.append("Extreme fear conditions - avoid momentum strategies")
            elif fear_greed_score > 90:
                additional_disqualifiers.append("Extreme greed conditions - avoid reversal strategies")
            
            if vix_current > 35:
                additional_disqualifiers.append("Extreme volatility - reduce position sizes")
            
            # Combine all disqualifiers
            all_disqualifiers = avoid_list + additional_disqualifiers
            
            logger.info(f"🚫 Found {len(all_disqualifiers)} disqualifying conditions")
            return all_disqualifiers
            
        except Exception as e:
            logger.error(f"❌ Error checking disqualifiers: {str(e)}")
            return [f"Error checking disqualifiers: {str(e)}"]
    
    def run(self, input_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Main execution method for the playbook strategist agent.
        
        Args:
            input_data: Optional input data from previous agent
            
        Returns:
            Dictionary with strategy analysis and recommendations
        """
        logger.info("🚀 Starting Playbook Strategist Agent execution...")
        
        # Analyze market regime
        market_analysis = self.analyze_market_regime()
        
        # Select strategies
        selected_strategies = self.select_strategies(market_analysis)
        
        # Check disqualifiers
        disqualifiers = self.check_disqualifiers(market_analysis)
        
        # Update market analysis with refined data
        market_analysis["selected_strategies"] = selected_strategies
        market_analysis["avoid_list"] = disqualifiers
        
        result = {
            "market_regime": market_analysis["market_regime"],
            "selected_strategies": selected_strategies,
            "avoid_list": disqualifiers,
            "macro_notes": market_analysis["macro_notes"],
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        logger.info("✅ Playbook Strategist Agent execution completed")
        return result

def main():
    """Main function for standalone execution."""
    agent = PlaybookStrategistAgent()
    result = agent.run()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 