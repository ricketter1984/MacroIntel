#!/usr/bin/env python3
"""
Chart Generator Agent for MacroIntel Swarm
Triggers visual_query_engine.py to create contextual market visualizations.
Supports command-line arguments for custom visual generation with conditional logic.
"""

import os
import sys
import json
import logging
import argparse
import re
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visual_query_engine import VisualQueryEngine, generate_comparison_chart, generate_extreme_fear_chart
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
            logger.error(f"❌ Error evaluating condition: {str(e)}")
            return True  # Default to generating chart
    
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
                    if self.custom_assets:
                        # Use custom assets for comparison
                        charts_needed.append({
                            "type": "custom_comparison",
                            "description": f"Custom asset comparison ({', '.join(self.custom_assets)})",
                            "priority": "high",
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
                "charts_needed": [],
                "custom_condition": self.custom_condition,
                "condition_met": None,
                "error": str(e)
            }
    
    def generate_chart(self, chart_type: str, context: str = "", chart_config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Generate a specific type of chart.
        
        Args:
            chart_type: Type of chart to generate
            context: Additional context for the chart
            chart_config: Additional configuration for the chart
            
        Returns:
            Dictionary with chart generation results
        """
        try:
            logger.info(f"📊 Generating {chart_type} chart...")
            
            if chart_type == "extreme_fear":
                # Generate extreme fear chart
                chart_path = generate_extreme_fear_chart()
                chart_description = "Asset performance analysis during extreme fear conditions"
                
            elif chart_type == "custom_comparison":
                # Generate custom asset comparison chart
                assets = chart_config.get("assets", self.custom_assets) if chart_config else self.custom_assets
                condition = chart_config.get("condition", self.custom_condition) if chart_config else self.custom_condition
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                filename = f"custom_comparison_{'_'.join(assets)}_{timestamp}.png"
                chart_path = generate_comparison_chart(
                    assets=assets,
                    output_path=os.path.join(self.output_dir, filename)
                )
                chart_description = f"Custom asset comparison: {', '.join(assets)}"
                if condition:
                    chart_description += f" (Condition: {condition})"
                
            elif chart_type == "asset_comparison":
                # Generate asset comparison chart
                assets = ["BTCUSD", "XAUUSD", "QQQ"]
                chart_path = generate_comparison_chart(
                    assets=assets,
                    output_path=os.path.join(self.output_dir, f"asset_comparison_{datetime.now().strftime('%Y%m%d_%H%M')}.png")
                )
                chart_description = "Multi-asset performance comparison"
                
            else:
                # Default to asset comparison
                assets = ["BTCUSD", "XAUUSD", "QQQ"]
                chart_path = generate_comparison_chart(
                    assets=assets,
                    output_path=os.path.join(self.output_dir, f"default_chart_{datetime.now().strftime('%Y%m%d_%H%M')}.png")
                )
                chart_description = "Default asset comparison chart"
            
            result = {
                "chart_type": chart_type,
                "file_path": chart_path,
                "description": chart_description,
                "context": context,
                "generated_at": datetime.now().isoformat(),
                "success": True
            }
            
            logger.info(f"✅ Chart generated: {chart_path}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating {chart_type} chart: {str(e)}")
            return {
                "chart_type": chart_type,
                "file_path": None,
                "description": f"Failed to generate {chart_type} chart",
                "context": context,
                "error": str(e),
                "success": False
            }
    
    def run(self, input_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Main execution method for the chart generator agent.
        
        Args:
            input_data: Optional input data from previous agent
            
        Returns:
            Dictionary with generated charts and analysis
        """
        logger.info("🚀 Starting Chart Generator Agent execution...")
        
        # Analyze market conditions
        market_analysis = self.analyze_market_conditions()
        
        # Generate charts based on conditions
        charts_generated = []
        
        for chart_config in market_analysis.get("charts_needed", []):
            chart_result = self.generate_chart(
                chart_type=chart_config["type"],
                context=chart_config["description"],
                chart_config=chart_config
            )
            charts_generated.append(chart_result)
        
        # Create analysis summary
        successful_charts = [c for c in charts_generated if c.get("success", False)]
        analysis_summary = f"Generated {len(successful_charts)} charts based on market conditions. Fear & Greed Index: {market_analysis.get('fear_greed_score', 'N/A')} ({market_analysis.get('fear_greed_rating', 'N/A')})"
        
        result = {
            "charts_generated": charts_generated,
            "analysis_summary": analysis_summary,
            "market_conditions": market_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("✅ Chart Generator Agent execution completed")
        return result

def main():
    """Main function for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Chart Generator Agent - Generate market visualizations with conditional logic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chart_generator_agent.py --assets BTCUSD,QQQ,XAUUSD --condition "fear < 30"
  python chart_generator_agent.py --assets SPY,GLD --condition "fear > 70"
  python chart_generator_agent.py --assets BTCUSD,ETHUSD
        """
    )
    
    parser.add_argument(
        "--assets",
        type=str,
        help="Comma-separated list of assets to analyze (e.g., BTCUSD,QQQ,XAUUSD)"
    )
    
    parser.add_argument(
        "--condition",
        type=str,
        help="Condition for chart generation (e.g., 'fear < 30', 'fear > 70')"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Parse assets
    custom_assets = None
    if args.assets:
        custom_assets = [asset.strip() for asset in args.assets.split(",")]
        logger.info(f"📊 Custom assets specified: {custom_assets}")
    
    # Create agent with custom parameters
    agent = ChartGeneratorAgent(
        custom_assets=custom_assets,
        custom_condition=args.condition
    )
    
    # Run the agent
    result = agent.run()
    
    # Print results
    print(json.dumps(result, indent=2))
    
    # Log chart paths for easy access
    successful_charts = [c for c in result.get("charts_generated", []) if c.get("success", False)]
    if successful_charts:
        print("\n📊 Generated Charts:")
        for chart in successful_charts:
            print(f"  • {chart.get('file_path', 'Unknown path')}")
    else:
        print("\n⚠️ No charts were generated (condition may not have been met)")

if __name__ == "__main__":
    main() 