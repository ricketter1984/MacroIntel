"""
MacroIntel Multi-Agent System using LangGraph

This module implements a three-agent pipeline for macro analysis:
1. NewsAnalyzerAgent - Analyzes news headlines and returns summaries with impact scores
2. StrategyMatchAgent - Matches market conditions to strategy tiers
3. InstrumentSelectorAgent - Selects appropriate futures instruments based on analysis
"""

import logging
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NewsAnalysis:
    """Data structure for news analysis results"""
    headlines: List[str]
    summaries: List[str]
    impact_scores: List[float]
    overall_sentiment: str
    key_themes: List[str]
    timestamp: datetime


@dataclass
class StrategyRecommendation:
    """Data structure for strategy recommendations"""
    regime_score: float
    vix_level: float
    fear_greed_score: int
    recommended_tier: str
    confidence: float
    reasoning: str
    timestamp: datetime


@dataclass
class InstrumentSelection:
    """Data structure for instrument selection results"""
    selected_instruments: List[str]
    allocation_weights: Dict[str, float]
    risk_level: str
    reasoning: str
    macro_factors: Dict[str, Any]
    timestamp: datetime


class AgentState(TypedDict):
    """State object passed between agents"""
    news_headlines: List[str]
    news_analysis: Optional[NewsAnalysis]
    regime_score: float
    vix_level: float
    fear_greed_score: int
    strategy_recommendation: Optional[StrategyRecommendation]
    instrument_selection: Optional[InstrumentSelection]
    metadata: Dict[str, Any]


class NewsAnalyzerAgent:
    """Agent responsible for analyzing news headlines and extracting insights"""
    
    def __init__(self):
        self.name = "NewsAnalyzerAgent"
        logger.info(f"Initialized {self.name}")
    
    def analyze_headlines(self, headlines: List[str]) -> NewsAnalysis:
        """
        Analyze news headlines and return structured analysis
        
        Args:
            headlines: List of news headlines to analyze
            
        Returns:
            NewsAnalysis object with summaries, impact scores, and insights
        """
        logger.info(f"{self.name}: Analyzing {len(headlines)} headlines")
        
        # Placeholder logic - replace with GPT calls later
        summaries = []
        impact_scores = []
        key_themes = []
        
        for headline in headlines:
            # Placeholder: Generate summary (replace with GPT)
            summary = f"Analysis of: {headline[:50]}..."
            summaries.append(summary)
            
            # Placeholder: Calculate impact score (replace with sentiment analysis)
            impact_score = 0.5  # Neutral default
            if any(word in headline.lower() for word in ['fed', 'inflation', 'jobs']):
                impact_score = 0.8  # High impact
            elif any(word in headline.lower() for word in ['earnings', 'guidance']):
                impact_score = 0.6  # Medium impact
            impact_scores.append(impact_score)
        
        # Placeholder: Extract key themes (replace with GPT)
        key_themes = ['monetary_policy', 'economic_data', 'market_sentiment']
        
        # Placeholder: Overall sentiment (replace with GPT)
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0.5
        overall_sentiment = "bullish" if avg_impact > 0.6 else "bearish" if avg_impact < 0.4 else "neutral"
        
        analysis = NewsAnalysis(
            headlines=headlines,
            summaries=summaries,
            impact_scores=impact_scores,
            overall_sentiment=overall_sentiment,
            key_themes=key_themes,
            timestamp=datetime.now()
        )
        
        logger.info(f"{self.name}: Analysis complete - {overall_sentiment} sentiment")
        return analysis
    
    def run(self, state: AgentState) -> AgentState:
        """Run the news analyzer agent"""
        headlines = state.get('news_headlines', [])
        if not headlines:
            logger.warning(f"{self.name}: No headlines provided")
            return state
        
        analysis = self.analyze_headlines(headlines)
        state['news_analysis'] = analysis
        return state


class StrategyMatchAgent:
    """Agent responsible for matching market conditions to strategy tiers"""
    
    def __init__(self):
        self.name = "StrategyMatchAgent"
        self.strategy_tiers = {
            'conservative': {'min_regime': 0.0, 'max_regime': 0.3, 'max_vix': 25, 'min_fg': 0},
            'moderate': {'min_regime': 0.2, 'max_regime': 0.7, 'max_vix': 35, 'min_fg': 20},
            'aggressive': {'min_regime': 0.5, 'max_regime': 1.0, 'max_vix': 50, 'min_fg': 40},
            'defensive': {'min_regime': 0.0, 'max_regime': 0.4, 'max_vix': 40, 'min_fg': 0}
        }
        logger.info(f"Initialized {self.name}")
    
    def match_strategy(self, regime_score: float, vix_level: float, fear_greed_score: int) -> StrategyRecommendation:
        """
        Match market conditions to appropriate strategy tier
        
        Args:
            regime_score: Current regime score (0-1)
            vix_level: Current VIX level
            fear_greed_score: Fear & Greed index (0-100)
            
        Returns:
            StrategyRecommendation object
        """
        logger.info(f"{self.name}: Matching strategy for regime={regime_score:.2f}, VIX={vix_level:.1f}, F&G={fear_greed_score}")
        
        # Placeholder logic - replace with more sophisticated matching later
        recommended_tier = "moderate"  # Default
        confidence = 0.7
        reasoning = []
        
        # Simple rule-based matching
        if regime_score > 0.7 and vix_level < 25 and fear_greed_score > 60:
            recommended_tier = "aggressive"
            reasoning.append("Strong regime with low volatility and high greed")
        elif regime_score < 0.3 or vix_level > 35:
            recommended_tier = "defensive"
            reasoning.append("Weak regime or high volatility")
        elif regime_score < 0.5 and fear_greed_score < 30:
            recommended_tier = "conservative"
            reasoning.append("Weak regime with fear sentiment")
        
        reasoning_str = "; ".join(reasoning) if reasoning else "Default moderate strategy"
        
        recommendation = StrategyRecommendation(
            regime_score=regime_score,
            vix_level=vix_level,
            fear_greed_score=fear_greed_score,
            recommended_tier=recommended_tier,
            confidence=confidence,
            reasoning=reasoning_str,
            timestamp=datetime.now()
        )
        
        logger.info(f"{self.name}: Recommended {recommended_tier} strategy")
        return recommendation
    
    def run(self, state: AgentState) -> AgentState:
        """Run the strategy match agent"""
        regime_score = state.get('regime_score', 0.5)
        vix_level = state.get('vix_level', 20.0)
        fear_greed_score = state.get('fear_greed_score', 50)
        
        recommendation = self.match_strategy(regime_score, vix_level, fear_greed_score)
        state['strategy_recommendation'] = recommendation
        return state


class InstrumentSelectorAgent:
    """Agent responsible for selecting appropriate futures instruments"""
    
    def __init__(self):
        self.name = "InstrumentSelectorAgent"
        self.instruments = {
            'MYM': {'name': 'Micro E-mini Dow Jones', 'volatility': 'low', 'suitable_for': ['conservative', 'moderate']},
            'MNQ': {'name': 'Micro E-mini NASDAQ-100', 'volatility': 'high', 'suitable_for': ['aggressive', 'moderate']},
            'MES': {'name': 'Micro E-mini S&P 500', 'volatility': 'medium', 'suitable_for': ['moderate', 'conservative']}
        }
        logger.info(f"Initialized {self.name}")
    
    def select_instruments(self, 
                          strategy_tier: str, 
                          news_analysis: Optional[NewsAnalysis] = None,
                          macro_factors: Optional[Dict[str, Any]] = None) -> InstrumentSelection:
        """
        Select appropriate futures instruments based on strategy and macro factors
        
        Args:
            strategy_tier: Recommended strategy tier
            news_analysis: Optional news analysis results
            macro_factors: Optional macro economic factors
            
        Returns:
            InstrumentSelection object
        """
        logger.info(f"{self.name}: Selecting instruments for {strategy_tier} strategy")
        
        # Placeholder logic - replace with more sophisticated selection later
        selected_instruments = []
        allocation_weights = {}
        reasoning = []
        
        # Basic instrument selection based on strategy tier
        if strategy_tier == "conservative":
            selected_instruments = ["MES", "MYM"]
            allocation_weights = {"MES": 0.6, "MYM": 0.4}
            reasoning.append("Conservative strategy favors lower volatility instruments")
        elif strategy_tier == "moderate":
            selected_instruments = ["MES", "MNQ", "MYM"]
            allocation_weights = {"MES": 0.4, "MNQ": 0.4, "MYM": 0.2}
            reasoning.append("Moderate strategy balances risk across instruments")
        elif strategy_tier == "aggressive":
            selected_instruments = ["MNQ", "MES"]
            allocation_weights = {"MNQ": 0.7, "MES": 0.3}
            reasoning.append("Aggressive strategy favors higher volatility instruments")
        elif strategy_tier == "defensive":
            selected_instruments = ["MYM"]
            allocation_weights = {"MYM": 1.0}
            reasoning.append("Defensive strategy uses lowest volatility instrument")
        
        # Adjust based on news sentiment if available
        if news_analysis and news_analysis.overall_sentiment == "bearish":
            # Reduce exposure to high-volatility instruments
            if "MNQ" in allocation_weights and allocation_weights["MNQ"] > 0.3:
                allocation_weights["MNQ"] *= 0.7
                allocation_weights["MES"] = allocation_weights.get("MES", 0) + 0.1
                reasoning.append("Bearish sentiment reduces high-volatility exposure")
        
        # Normalize weights
        total_weight = sum(allocation_weights.values())
        if total_weight > 0:
            allocation_weights = {k: v/total_weight for k, v in allocation_weights.items()}
        
        risk_level = strategy_tier  # Simple mapping for now
        
        selection = InstrumentSelection(
            selected_instruments=selected_instruments,
            allocation_weights=allocation_weights,
            risk_level=risk_level,
            reasoning="; ".join(reasoning),
            macro_factors=macro_factors or {},
            timestamp=datetime.now()
        )
        
        logger.info(f"{self.name}: Selected {len(selected_instruments)} instruments")
        return selection
    
    def run(self, state: AgentState) -> AgentState:
        """Run the instrument selector agent"""
        strategy_recommendation = state.get('strategy_recommendation')
        if not strategy_recommendation:
            logger.warning(f"{self.name}: No strategy recommendation available")
            return state
        
        news_analysis = state.get('news_analysis')
        macro_factors = state.get('metadata', {})
        
        selection = self.select_instruments(
            strategy_recommendation.recommended_tier,
            news_analysis,
            macro_factors
        )
        state['instrument_selection'] = selection
        return state


def run_agents_pipeline(news_headlines: List[str], 
                       regime_score: float = 0.5,
                       vix_level: float = 20.0,
                       fear_greed_score: int = 50,
                       macro_factors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute the complete three-agent pipeline
    
    Args:
        news_headlines: List of news headlines to analyze
        regime_score: Current regime score (0-1)
        vix_level: Current VIX level
        fear_greed_score: Fear & Greed index (0-100)
        macro_factors: Optional macro economic factors
        
    Returns:
        Dictionary containing results from all three agents
    """
    logger.info("Starting MacroIntel agents pipeline")
    
    # Initialize agents
    news_analyzer = NewsAnalyzerAgent()
    strategy_matcher = StrategyMatchAgent()
    instrument_selector = InstrumentSelectorAgent()
    
    # Initialize state
    state: AgentState = {
        'news_headlines': news_headlines,
        'news_analysis': None,
        'regime_score': regime_score,
        'vix_level': vix_level,
        'fear_greed_score': fear_greed_score,
        'strategy_recommendation': None,
        'instrument_selection': None,
        'metadata': macro_factors or {}
    }
    
    try:
        # Step 1: Analyze news
        logger.info("Step 1: Running NewsAnalyzerAgent")
        state = news_analyzer.run(state)
        
        # Step 2: Match strategy
        logger.info("Step 2: Running StrategyMatchAgent")
        state = strategy_matcher.run(state)
        
        # Step 3: Select instruments
        logger.info("Step 3: Running InstrumentSelectorAgent")
        state = instrument_selector.run(state)
        
        # Prepare results
        results = {
            'news_analysis': state['news_analysis'],
            'strategy_recommendation': state['strategy_recommendation'],
            'instrument_selection': state['instrument_selection'],
            'pipeline_completed': True,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("MacroIntel agents pipeline completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Error in agents pipeline: {str(e)}")
        return {
            'error': str(e),
            'pipeline_completed': False,
            'timestamp': datetime.now().isoformat()
        }


def print_pipeline_results(results: Dict[str, Any]) -> None:
    """Pretty print the pipeline results"""
    print("\n" + "="*60)
    print("MACROINTEL AGENTS PIPELINE RESULTS")
    print("="*60)
    
    if results.get('error'):
        print(f"❌ Pipeline failed: {results['error']}")
        return
    
    # News Analysis
    if results.get('news_analysis'):
        na = results['news_analysis']
        print(f"\n📰 NEWS ANALYSIS")
        print(f"   Sentiment: {na.overall_sentiment.upper()}")
        print(f"   Headlines analyzed: {len(na.headlines)}")
        print(f"   Key themes: {', '.join(na.key_themes)}")
        print(f"   Average impact score: {sum(na.impact_scores)/len(na.impact_scores):.2f}")
    
    # Strategy Recommendation
    if results.get('strategy_recommendation'):
        sr = results['strategy_recommendation']
        print(f"\n🎯 STRATEGY RECOMMENDATION")
        print(f"   Tier: {sr.recommended_tier.upper()}")
        print(f"   Confidence: {sr.confidence:.1%}")
        print(f"   Reasoning: {sr.reasoning}")
        print(f"   Regime: {sr.regime_score:.2f} | VIX: {sr.vix_level:.1f} | F&G: {sr.fear_greed_score}")
    
    # Instrument Selection
    if results.get('instrument_selection'):
        isel = results['instrument_selection']
        print(f"\n📊 INSTRUMENT SELECTION")
        print(f"   Risk level: {isel.risk_level.upper()}")
        print(f"   Selected: {', '.join(isel.selected_instruments)}")
        print(f"   Allocation: {dict(isel.allocation_weights)}")
        print(f"   Reasoning: {isel.reasoning}")
    
    print(f"\n⏰ Completed: {results['timestamp']}")
    print("="*60)


if __name__ == "__main__":
    # Example usage
    sample_headlines = [
        "Fed signals potential rate cuts in 2024",
        "Inflation data comes in below expectations",
        "Tech earnings beat estimates across the board"
    ]
    
    results = run_agents_pipeline(
        news_headlines=sample_headlines,
        regime_score=0.6,
        vix_level=18.5,
        fear_greed_score=65,
        macro_factors={'gdp_growth': 2.1, 'unemployment': 3.8}
    )
    
    print_pipeline_results(results) 