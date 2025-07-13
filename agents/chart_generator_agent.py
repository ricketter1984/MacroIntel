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
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.visual_query_engine import VisualQueryEngine, generate_comparison_chart, generate_extreme_fear_chart
    _visual_engine_imported = True
except ImportError as e:
    print(f"⚠️ Visual query engine not available: {e}")
    VisualQueryEngine = None
    generate_comparison_chart = None
    generate_extreme_fear_chart = None
    _visual_engine_imported = False
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
        self.visual_engine: Any = None
        self.visual_engine_available = False
        if _visual_engine_imported and VisualQueryEngine is not None:
            try:
                self.visual_engine = VisualQueryEngine()
                self.visual_engine_available = True
            except Exception as e:
                print(f"⚠️ Visual query engine could not be instantiated: {e}")
                self.visual_engine = None
        else:
            self.visual_engine = None
            print("⚠️ Visual query engine not available - charts will be skipped")
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
                    "strategy_recommendation": "Tier 2 Mean Reversion",
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
                "strategy_recommendation": "Tier 2 Mean Reversion",
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
            if self.visual_engine_available and self.visual_engine is not None:
                fear_score, fear_rating = self.visual_engine.get_fear_greed_index()
            else:
                logger.warning("⚠️ Visual query engine not available - using default Fear & Greed Index")
                fear_score, fear_rating = 50, "Neutral"
            
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
    
    def analyze_regime_strength(self, regime_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze regime strength and provide detailed interpretation.
        
        Args:
            regime_data: Market regime analysis data
            
        Returns:
            Dictionary with regime strength analysis
        """
        try:
            total_score = regime_data.get('total_score', 50.0)
            classification = regime_data.get('regime_classification', 'Neutral')
            component_breakdown = regime_data.get('component_breakdown', {})
            
            # Determine regime strength
            if total_score >= 75:
                strength = "very strong"
                confidence = "high"
            elif total_score >= 60:
                strength = "strong"
                confidence = "moderate-high"
            elif total_score >= 40:
                strength = "neutral"
                confidence = "moderate"
            elif total_score >= 25:
                strength = "weak"
                confidence = "low-moderate"
            else:
                strength = "very weak"
                confidence = "low"
            
            # Analyze key components
            key_drivers = []
            weak_areas = []
            
            for component, data in component_breakdown.items():
                if isinstance(data, dict):
                    score = data.get('weighted_score', 0)
                    if score > 15:  # Strong component
                        key_drivers.append(component.replace('_', ' ').title())
                    elif score < 8:  # Weak component
                        weak_areas.append(component.replace('_', ' ').title())
            
            return {
                "score": total_score,
                "classification": classification,
                "strength": strength,
                "confidence": confidence,
                "key_drivers": key_drivers,
                "weak_areas": weak_areas,
                "is_bullish": total_score > 60,
                "is_bearish": total_score < 40,
                "is_extreme": total_score > 75 or total_score < 25
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error analyzing regime strength: {str(e)}")
            return {
                "score": 50.0,
                "classification": "Neutral",
                "strength": "neutral",
                "confidence": "low",
                "key_drivers": [],
                "weak_areas": [],
                "is_bullish": False,
                "is_bearish": False,
                "is_extreme": False
            }
    
    def determine_tier_logic(self, regime_analysis: Dict[str, Any], fear_greed_score: int) -> Dict[str, Any]:
        """
        Determine appropriate tier strategy based on regime and sentiment.
        
        Args:
            regime_analysis: Regime strength analysis
            fear_greed_score: Current Fear & Greed Index score
            
        Returns:
            Dictionary with tier strategy logic
        """
        try:
            regime_score = regime_analysis.get('score', 50.0)
            
            # Simplified tier logic - override any Tier 3 or 4 strategies
            if regime_score >= 65:
                tier = "Tier 1"
                strategy_type = "reversal"
                rationale = f"High regime score ({regime_score:.1f}) indicates reversal opportunity"
                risk_level = "high"
                time_horizon = "short-term"
            else:
                tier = "Tier 2"
                strategy_type = "momentum"
                rationale = f"Moderate regime score ({regime_score:.1f}) favors momentum strategy"
                risk_level = "moderate"
                time_horizon = "medium-term"
            
            return {
                "tier": tier,
                "strategy_type": strategy_type,
                "rationale": rationale,
                "risk_level": risk_level,
                "time_horizon": time_horizon
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error determining tier logic: {str(e)}")
            return {
                "tier": "Tier 2",
                "strategy_type": "momentum",
                "rationale": "Default to momentum strategy due to analysis error",
                "risk_level": "moderate",
                "time_horizon": "medium-term"
            }
    
    def analyze_perplexity_context(self, dominant_keywords: List[str], tags: List[str], topic: str | None = None) -> Dict[str, Any]:
        """
        Analyze Perplexity topic tags and keywords to understand market context.
        
        Args:
            dominant_keywords: List of dominant keywords from Perplexity
            tags: List of tags from Perplexity
            topic: Main topic string
            
        Returns:
            Dictionary with context analysis
        """
        try:
            # Market-relevant categories
            market_categories = {
                'monetary_policy': ['fed', 'interest', 'rates', 'inflation', 'monetary', 'policy', 'powell', 'fomc'],
                'geopolitical': ['war', 'conflict', 'china', 'russia', 'trade', 'tariffs', 'sanctions', 'geopolitical'],
                'earnings': ['earnings', 'revenue', 'profit', 'guidance', 'beat', 'miss', 'outlook'],
                'sector_rotation': ['sector', 'rotation', 'tech', 'energy', 'financials', 'healthcare', 'utilities'],
                'volatility': ['volatility', 'vix', 'options', 'hedge', 'risk', 'uncertainty'],
                'crypto': ['bitcoin', 'crypto', 'blockchain', 'ethereum', 'digital', 'currency'],
                'commodities': ['oil', 'gold', 'copper', 'commodities', 'energy', 'metals'],
                'economic_data': ['gdp', 'employment', 'jobless', 'unemployment', 'manufacturing', 'consumer']
            }
            
            # Analyze keywords and tags
            all_terms = [term.lower() for term in (dominant_keywords + tags + ([topic] if topic else []))]
            
            category_scores = {}
            for category, keywords in market_categories.items():
                score = sum(1 for term in all_terms for keyword in keywords if keyword in term)
                if score > 0:
                    category_scores[category] = score
            
            # Determine primary theme
            primary_theme = max(category_scores.keys(), key=lambda x: category_scores[x]) if category_scores else 'general_market'
            
            # Assess market impact
            high_impact_categories = ['monetary_policy', 'geopolitical', 'volatility']
            market_impact = 'high' if primary_theme in high_impact_categories else 'moderate'
            
            return {
                "primary_theme": primary_theme.replace('_', ' ').title(),
                "category_scores": category_scores,
                "market_impact": market_impact,
                "key_terms": dominant_keywords[:5],  # Top 5 keywords
                "relevant_tags": [tag for tag in tags if any(cat in tag.lower() for cat in market_categories.keys())][:3]
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error analyzing Perplexity context: {str(e)}")
            return {
                "primary_theme": "General Market",
                "category_scores": {},
                "market_impact": "moderate",
                "key_terms": dominant_keywords[:3] if dominant_keywords else [],
                "relevant_tags": tags[:2] if tags else []
            }
    
    def generate_intelligent_explanation(self, chart_result: Dict[str, Any], regime_analysis: Dict[str, Any], 
                                       tier_logic: Dict[str, Any], perplexity_context: Dict[str, Any], 
                                       fear_greed_score: int) -> str:
        """
        Generate sophisticated AI explanation for the chart.
        
        Args:
            chart_result: Chart generation result
            regime_analysis: Regime strength analysis
            tier_logic: Tier strategy logic
            perplexity_context: Perplexity context analysis
            fear_greed_score: Current Fear & Greed Index score
            
        Returns:
            Detailed AI explanation string
        """
        try:
            # Extract key information
            primary_instrument = chart_result.get("primary_instrument", "market instrument")
            secondary_instrument = chart_result.get("secondary_instrument", "secondary asset")
            regime_score = regime_analysis.get('score', 50.0)
            tier = tier_logic.get('tier', 'Tier 2')
            strategy_type = tier_logic.get('strategy_type', 'mean_reversion')
            theme = perplexity_context.get('primary_theme', 'Market Activity')
            key_terms = perplexity_context.get('key_terms', [])
            market_impact = perplexity_context.get('market_impact', 'moderate')
            
            # Build explanation sections
            sections = []
            
            # Context section
            if key_terms:
                terms_str = ', '.join(key_terms[:3])
                sections.append(f"📰 **News Context**: Recent coverage of {theme.lower()} ({terms_str}) is creating {market_impact} market impact.")
            else:
                sections.append(f"📰 **News Context**: Current {theme.lower()} developments are influencing market dynamics.")
            
            # Regime analysis section
            strength = regime_analysis.get('strength', 'neutral')
            confidence = regime_analysis.get('confidence', 'moderate')
            sections.append(f"📊 **Regime Analysis**: Market regime score of {regime_score:.1f} indicates {strength} conditions with {confidence} confidence.")
            
            # Key drivers
            key_drivers = regime_analysis.get('key_drivers', [])
            if key_drivers:
                drivers_str = ', '.join(key_drivers[:2])
                sections.append(f"🔑 **Key Drivers**: {drivers_str} are primary factors supporting current regime.")
            
            # Sentiment analysis
            if fear_greed_score < 25:
                sentiment_desc = "extreme fear creating potential mean reversion opportunities"
            elif fear_greed_score > 75:
                sentiment_desc = "extreme greed suggesting caution and potential reversal"
            elif fear_greed_score < 40:
                sentiment_desc = "fearful sentiment favoring defensive positioning"
            elif fear_greed_score > 60:
                sentiment_desc = "optimistic sentiment supporting trend continuation"
            else:
                sentiment_desc = "neutral sentiment allowing for tactical positioning"
            
            sections.append(f"😨 **Sentiment**: Fear & Greed at {fear_greed_score} indicates {sentiment_desc}.")
            
            # Strategy rationale
            rationale = tier_logic.get('rationale', 'Strategy based on current conditions')
            risk_level = tier_logic.get('risk_level', 'moderate')
            time_horizon = tier_logic.get('time_horizon', 'medium-term')
            
            sections.append(f"🎯 **{tier} Strategy**: {rationale}. This {risk_level}-risk, {time_horizon} approach focuses on {primary_instrument} with {secondary_instrument} as a hedge.")
            
            # Chart explanation
            if tier == "Tier 1":
                chart_purpose = f"This chart visualizes reversal opportunities in {primary_instrument}, designed for high-conviction positioning when regime signals indicate potential reversals."
            else:
                chart_purpose = f"This chart identifies momentum opportunities in {primary_instrument}, optimal for moderate risk positioning during trending market conditions."
            
            sections.append(f"📈 **Chart Purpose**: {chart_purpose}")
            
            # Trading logic explanation
            if strategy_type == "reversal":
                trading_logic = "Look for reversal confirmations with strong volume. Target counter-trend moves with disciplined risk management."
            else:  # momentum
                trading_logic = "Focus on trend continuation patterns. Scale in on pullbacks to moving averages and momentum signals."
            
            sections.append(f"⚙️ **Trading Logic**: {trading_logic}")
            
            # Combine all sections
            explanation = " ".join(sections)
            
            return explanation
            
        except Exception as e:
            logger.warning(f"⚠️ Error generating intelligent explanation: {str(e)}")
            return f"Chart analysis for current market conditions focusing on {chart_result.get('primary_instrument', 'market instrument')} using {tier_logic.get('tier', 'Tier 2')} strategy approach."
    
    def generate_intelligent_chart(self, regime_data: Dict[str, Any], fear_greed_score: int, dominant_keywords=None, tags=None, topic=None, headline=None) -> Dict[str, Any]:
        """
        Generate intelligent regime-aware chart with enhanced AI explanation.
        Args:
            regime_data: Market regime analysis data
            fear_greed_score: Current Fear & Greed Index score
            dominant_keywords: List of dominant keywords (from Perplexity)
            tags: List of tags (from Perplexity)
            topic: Main topic string (optional)
            headline: Example headline string (optional)
        Returns:
            Dictionary with chart information and sophisticated AI explanation
        """
        try:
            logger.info("🧠 Generating intelligent regime-aware chart with enhanced explanations...")
            
            # Ensure lists
            if dominant_keywords is None:
                dominant_keywords = []
            if tags is None:
                tags = []
            
            # Perform enhanced analysis
            regime_analysis = self.analyze_regime_strength(regime_data)
            tier_logic = self.determine_tier_logic(regime_analysis, fear_greed_score)
            perplexity_context = self.analyze_perplexity_context(dominant_keywords, tags, topic)
            
            logger.info(f"📊 Analysis complete: {tier_logic['tier']} strategy, {perplexity_context['primary_theme']} theme")
            
            # Generate the intelligent chart with determined tier
            chart_result = self.enhanced_viz.generate_intelligent_chart(
                regime_data=regime_data,
                fear_greed_score=fear_greed_score,
                dominant_keywords=dominant_keywords,
                tags=tags
            )
            
            # Check for either chart_path or file_path (different modules use different keys)
            chart_file_path = chart_result.get("chart_path") or chart_result.get("file_path") or chart_result.get("filename")
            
            if chart_result and chart_file_path:
                # Generate sophisticated AI explanation
                ai_explanation = self.generate_intelligent_explanation(
                    chart_result=chart_result,
                    regime_analysis=regime_analysis,
                    tier_logic=tier_logic,
                    perplexity_context=perplexity_context,
                    fear_greed_score=fear_greed_score
                )
                
                # Add enhanced analysis to chart result
                chart_result.update({
                    "ai_explanation": ai_explanation,
                    "tier_logic": tier_logic,
                    "regime_analysis": regime_analysis,
                    "perplexity_context": perplexity_context,
                    "enhanced_analysis": True
                })
                
                logger.info(f"✅ Generated {tier_logic['tier']} chart with enhanced explanation")
                
                return {
                    "success": True,
                    "chart_type": "intelligent_regime",
                    "file_path": chart_file_path,
                    "description": ai_explanation,
                    "context": f"Regime: {regime_analysis['classification']}, Strategy: {tier_logic['tier']} {tier_logic['strategy_type'].replace('_', ' ').title()}",
                    "regime": chart_result.get("regime", regime_analysis['classification']),
                    "strategy": tier_logic['tier'],
                    "primary_instrument": chart_result.get("primary_instrument", ""),
                    "secondary_instrument": chart_result.get("secondary_instrument", ""),
                    "ai_explanation": ai_explanation,
                    "tier_logic": tier_logic,
                    "market_theme": perplexity_context['primary_theme'],
                    "regime_strength": regime_analysis['strength']
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
                regime_data = chart_config.get("regime_data", {}) if chart_config else {}
                fear_greed_score = chart_config.get("fear_greed_score", 50) if chart_config else 50
                return self.generate_intelligent_chart(regime_data, fear_greed_score)
            
            elif chart_type == "extreme_fear":
                # Generate extreme fear chart
                if generate_extreme_fear_chart is not None:
                    chart_path = generate_extreme_fear_chart()
                else:
                    logger.warning("⚠️ Visual query engine not available - cannot generate extreme fear chart")
                    chart_path = None
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
                assets = chart_config.get("assets", ["BTCUSD", "XAUUSD", "QQQ"]) if chart_config else ["BTCUSD", "XAUUSD", "QQQ"]
                condition = chart_config.get("condition", "") if chart_config else ""
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(self.output_dir, f"asset_comparison_{timestamp}.png")
                
                if generate_comparison_chart is not None:
                    generate_comparison_chart(assets, condition=condition, output_path=output_path)
                else:
                    logger.warning("⚠️ Visual query engine not available - cannot generate asset comparison chart")
                    return {"success": False, "error": "Asset comparison chart generation failed"}
                
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