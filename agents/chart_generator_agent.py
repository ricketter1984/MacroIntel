#!/usr/bin/env python3
"""
Chart Generator Agent for MacroIntel Swarm
Triggers visual_query_engine.py to create contextual market visualizations.
Supports command-line arguments for custom visual generation with conditional logic.
Now includes intelligent regime-aware chart generation with AI explanations.
"""

import os
import sys
import json
import logging
import argparse
import re
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.visual_query_engine import VisualQueryEngine, generate_comparison_chart, generate_extreme_fear_chart
from core.enhanced_visualizations import EnhancedVisualizations
from utils.api_clients import init_env

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChartGeneratorAgent:
    """Agent responsible for generating contextual market visualizations."""
    
    def __init__(self, custom_assets: List[str] | None = None, custom_condition: str | None = None):
        """
        Initialize the chart generator agent.
        
        Args:
            custom_assets: List of custom assets to analyze
            custom_condition: Custom condition string (e.g., "fear < 30")
        """
        init_env()
        self.visual_engine = VisualQueryEngine()
        self.enhanced_viz = EnhancedVisualizations()
        self.output_dir = "output"
        self.custom_assets = custom_assets or ["BTCUSD", "XAUUSD", "QQQ"]
        self.custom_condition = custom_condition
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("📈 Chart Generator Agent initialized")
        if custom_condition:
            logger.info(f"🎯 Custom condition: {custom_condition}")
        if custom_assets:
            logger.info(f"📊 Custom assets: {', '.join(custom_assets)}")
    
    def parse_condition(self, condition_str: str) -> Dict[str, Any] | None:
        """
        Parse condition string (e.g., "fear < 30") into structured format.
        
        Args:
            condition_str: Condition string to parse
            
        Returns:
            Dictionary with parsed condition components
        """
        try:
            # Pattern to match: metric operator value
            pattern = r'(\w+)\s*([<>=!]+)\s*(\d+(?:\.\d+)?)'
            match = re.match(pattern, condition_str.strip())
            
            if match:
                metric, operator, value = match.groups()
                return {
                    "metric": metric.lower(),
                    "operator": operator,
                    "value": float(value),
                    "original": condition_str
                }
            else:
                logger.warning(f"⚠️ Could not parse condition: {condition_str}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error parsing condition '{condition_str}': {str(e)}")
            return None
    
    def evaluate_condition(self, condition: Dict[str, Any], fear_greed_score: float) -> bool:
        """
        Evaluate if the condition is met based on current market data.
        
        Args:
            condition: Parsed condition dictionary
            fear_greed_score: Current Fear & Greed Index score
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            if not condition:
                return True  # No condition means always generate
            
            metric = condition.get("metric")
            operator = condition.get("operator")
            value = condition.get("value")
            
            if metric == "fear":
                current_value = fear_greed_score
            else:
                logger.warning(f"⚠️ Unknown metric: {metric}")
                return True  # Default to generating chart
            
            # Check if value is valid
            if value is None:
                logger.warning("⚠️ Invalid condition value")
                return True  # Default to generating chart
            
            # Evaluate condition
            if operator == "<":
                result = current_value < value
            elif operator == "<=":
                result = current_value <= value
            elif operator == ">":
                result = current_value > value
            elif operator == ">=":
                result = current_value >= value
            elif operator == "==" or operator == "=":
                result = current_value == value
            elif operator == "!=":
                result = current_value != value
            else:
                logger.warning(f"⚠️ Unknown operator: {operator}")
                return True  # Default to generating chart
            
            logger.info(f"🔍 Condition evaluation: {current_value} {operator} {value} = {result}")
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Overlay condition failed to apply: {e}")
            return True  # Default to generating chart
    
    def get_regime_data(self) -> Dict[str, Any]:
        """
        Get current market regime data.
        
        Returns:
            Dictionary with regime analysis data
        """
        try:
            logger.info("🔍 Fetching market regime data...")
            
            # Try to load latest regime score file
            regime_files = []
            for file in os.listdir("output"):
                if file.startswith("regime_score_") and file.endswith(".json"):
                    regime_files.append(file)
            
            if regime_files:
                # Get the most recent file
                latest_file = sorted(regime_files)[-1]
                regime_path = os.path.join("output", latest_file)
                
                with open(regime_path, 'r') as f:
                    regime_data = json.load(f)
                
                logger.info(f"✅ Loaded regime data from {latest_file}")
                return regime_data
            else:
                logger.warning("⚠️ No regime data files found, using default")
                return {
                    "total_score": 50.0,
                    "regime_classification": "Neutral",
                    "strategy_recommendation": "Tier 3 Range Trading",
                    "instrument": "MES",
                    "component_breakdown": {
                        "volatility": {"weighted_score": 12.5},
                        "structure": {"weighted_score": 10.0},
                        "volume_breadth": {"weighted_score": 10.0},
                        "momentum": {"weighted_score": 10.0},
                        "institutional": {"weighted_score": 7.5}
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Error fetching regime data: {str(e)}")
            return {
                "total_score": 50.0,
                "regime_classification": "Neutral",
                "strategy_recommendation": "Tier 3 Range Trading",
                "instrument": "MES",
                "component_breakdown": {}
            }
    
    def analyze_market_conditions(self) -> Dict[str, Any]:
        """
        Analyze current market conditions to determine chart needs.
        
        Returns:
            Dictionary with market analysis data
        """
        try:
            logger.info("🔍 Analyzing market conditions...")
            
            # Get Fear & Greed Index
            fear_score, fear_rating = self.visual_engine.get_fear_greed_index()
            
            # Get regime data
            regime_data = self.get_regime_data()
            
            # Parse custom condition if provided
            parsed_condition = None
            if self.custom_condition:
                parsed_condition = self.parse_condition(self.custom_condition)
                if parsed_condition:
                    logger.info(f"🎯 Parsed condition: {parsed_condition}")
            
            # Determine chart requirements based on conditions
            charts_needed = []
            condition_met = None
            
            if fear_score is not None:
                # Check if custom condition is met
                if parsed_condition:
                    condition_met = self.evaluate_condition(parsed_condition, fear_score)
                else:
                    condition_met = True  # No condition means always generate
                
                if condition_met:
                    # Always generate intelligent regime chart
                    charts_needed.append({
                        "type": "intelligent_regime",
                        "description": "Intelligent regime-aware chart with AI explanation",
                        "priority": "high",
                        "regime_data": regime_data,
                        "fear_greed_score": fear_score
                    })
                    
                    if self.custom_assets:
                        # Use custom assets for comparison
                        charts_needed.append({
                            "type": "custom_comparison",
                            "description": f"Custom asset comparison ({', '.join(self.custom_assets)})",
                            "priority": "medium",
                            "assets": self.custom_assets,
                            "condition": self.custom_condition
                        })
                    else:
                        # Use default logic
                        if fear_score < 25:  # Extreme Fear
                            charts_needed.append({
                                "type": "extreme_fear",
                                "description": "Asset performance during extreme fear",
                                "priority": "high"
                            })
                        elif fear_score > 75:  # Extreme Greed
                            charts_needed.append({
                                "type": "asset_comparison",
                                "description": "Asset performance during extreme greed",
                                "priority": "medium"
                            })
                        
                        # Always include basic asset comparison
                        charts_needed.append({
                            "type": "asset_comparison",
                            "description": "General asset performance comparison",
                            "priority": "normal"
                        })
                else:
                    logger.info(f"⚠️ Condition not met: {self.custom_condition} (Fear & Greed: {fear_score})")
            
            market_data = {
                "fear_greed_score": fear_score,
                "fear_greed_rating": fear_rating,
                "regime_data": regime_data,
                "charts_needed": charts_needed,
                "custom_condition": self.custom_condition,
                "condition_met": condition_met if fear_score is not None else None,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📊 Market analysis complete: {len(charts_needed)} charts needed")
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Error analyzing market conditions: {str(e)}")
            return {
                "fear_greed_score": 50,
                "fear_greed_rating": "Neutral",
                "regime_data": self.get_regime_data(),
                "charts_needed": [],
                "custom_condition": self.custom_condition,
                "condition_met": None,
                "error": str(e)
            }
    
    def generate_intelligent_chart(self, regime_data: Dict[str, Any], fear_greed_score: int) -> Dict[str, Any]:
        """
        Generate intelligent regime-aware chart with AI explanation.
        
        Args:
            regime_data: Market regime analysis data
            fear_greed_score: Current Fear & Greed Index score
            
        Returns:
            Dictionary with chart information and AI explanation
        """
        try:
            logger.info("🧠 Generating intelligent regime-aware chart...")
            
            # Generate the intelligent chart
            chart_result = self.enhanced_viz.generate_intelligent_chart(
                regime_data=regime_data,
                fear_greed_score=fear_greed_score
            )
            
            if chart_result and chart_result.get("chart_path"):
                logger.info(f"✅ Intelligent chart generated: {chart_result.get('chart_type', 'unknown')}")
                return {
                    "success": True,
                    "chart_type": "intelligent_regime",
                    "file_path": chart_result.get("chart_path", ""),
                    "description": chart_result.get("ai_explanation", ""),
                    "context": f"Regime: {chart_result.get('regime', 'Unknown')}, Strategy: {chart_result.get('strategy', 'Unknown')}",
                    "regime": chart_result.get("regime", "Unknown"),
                    "strategy": chart_result.get("strategy", "Unknown"),
                    "primary_instrument": chart_result.get("primary_instrument", ""),
                    "secondary_instrument": chart_result.get("secondary_instrument", ""),
                    "ai_explanation": chart_result.get("ai_explanation", "")
                }
            else:
                logger.warning("⚠️ Intelligent chart generation failed")
                return {
                    "success": False,
                    "error": "Chart generation failed"
                }
                
        except Exception as e:
            logger.error(f"❌ Error generating intelligent chart: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_chart(self, chart_type: str, context: str = "", chart_config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Generate a specific type of chart.
        
        Args:
            chart_type: Type of chart to generate
            context: Context information for the chart
            chart_config: Configuration for the chart
            
        Returns:
            Dictionary with chart generation results
        """
        try:
            logger.info(f"📈 Generating {chart_type} chart...")
            
            if chart_type == "intelligent_regime":
                # Generate intelligent regime chart
                regime_data = chart_config.get("regime_data", {})
                fear_greed_score = chart_config.get("fear_greed_score", 50)
                return self.generate_intelligent_chart(regime_data, fear_greed_score)
            
            elif chart_type == "extreme_fear":
                # Generate extreme fear chart
                chart_path = generate_extreme_fear_chart()
                if chart_path:
                    return {
                        "success": True,
                        "chart_type": "extreme_fear",
                        "file_path": chart_path,
                        "description": "Asset performance during extreme fear conditions",
                        "context": context
                    }
                else:
                    return {"success": False, "error": "Extreme fear chart generation failed"}
            
            elif chart_type in ["asset_comparison", "custom_comparison"]:
                # Generate asset comparison chart
                assets = chart_config.get("assets", ["BTCUSD", "XAUUSD", "QQQ"])
                condition = chart_config.get("condition", "")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(self.output_dir, f"asset_comparison_{timestamp}.png")
                
                generate_comparison_chart(assets, condition=condition, output_path=output_path)
                
                return {
                    "success": True,
                    "chart_type": "asset_comparison",
                    "file_path": output_path,
                    "description": f"Asset comparison: {', '.join(assets)}",
                    "context": context
                }
            
            else:
                logger.warning(f"⚠️ Unknown chart type: {chart_type}")
                return {"success": False, "error": f"Unknown chart type: {chart_type}"}
                
        except Exception as e:
            logger.error(f"❌ Error generating {chart_type} chart: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def run(self, input_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run the chart generator agent.
        
        Args:
            input_data: Optional input data from other agents
            
        Returns:
            Dictionary with chart generation results
        """
        try:
            logger.info("🚀 Starting Chart Generator Agent...")
            
            # Analyze market conditions
            market_conditions = self.analyze_market_conditions()
            
            # Generate charts
            charts_generated = []
            charts_failed = []
            
            for chart_config in market_conditions.get("charts_needed", []):
                try:
                    chart_result = self.generate_chart(
                        chart_type=chart_config["type"],
                        context=chart_config.get("description", ""),
                        chart_config=chart_config
                    )
                    
                    if chart_result.get("success", False):
                        charts_generated.append(chart_result)
                        logger.info(f"✅ Generated {chart_config['type']} chart")
                    else:
                        charts_failed.append({
                            "type": chart_config["type"],
                            "error": chart_result.get("error", "Unknown error")
                        })
                        logger.warning(f"⚠️ Failed to generate {chart_config['type']} chart")
                        
                except Exception as e:
                    charts_failed.append({
                        "type": chart_config["type"],
                        "error": str(e)
                    })
                    logger.error(f"❌ Error generating {chart_config['type']} chart: {str(e)}")
            
            # Compile results
            results = {
                "status": "success",
                "charts_generated": charts_generated,
                "charts_failed": charts_failed,
                "total_charts": len(charts_generated),
                "failed_charts": len(charts_failed),
                "market_conditions": market_conditions,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Chart Generator completed: {len(charts_generated)} charts generated, {len(charts_failed)} failed")
            return results
            
        except Exception as e:
            logger.error(f"❌ Chart Generator failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "charts_generated": [],
                "charts_failed": [],
                "timestamp": datetime.now().isoformat()
            }

def main():
    """Main function for running the chart generator agent."""
    parser = argparse.ArgumentParser(description="Chart Generator Agent")
    parser.add_argument('--assets', nargs='+', help='Assets to compare')
    parser.add_argument('--condition', help='Condition for chart generation (e.g., "fear < 30")')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = ChartGeneratorAgent(
        custom_assets=args.assets,
        custom_condition=args.condition
    )
    
    # Run agent
    results = agent.run()
    
    # Print results
    if results.get("status") == "success":
        print(f"\n✅ Chart Generator completed successfully!")
        print(f"📊 Charts generated: {results['total_charts']}")
        print(f"❌ Charts failed: {results['failed_charts']}")
        
        for chart in results["charts_generated"]:
            print(f"   📈 {chart['chart_type']}: {chart['file_path']}")
            if chart.get('ai_explanation'):
                print(f"      💡 {chart['ai_explanation'][:100]}...")
    else:
        print(f"❌ Chart Generator failed: {results.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    main() 