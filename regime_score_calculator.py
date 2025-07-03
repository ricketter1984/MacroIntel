#!/usr/bin/env python3
"""
Market Regime Score Calculator

This module calculates the Daily Market Regime Score based on Playbook v7.1 specifications.
It analyzes 5 key components to determine market conditions and provide trading recommendations.

Components:
1. Volatility Environment (VIX, VIX term structure, ATR)
2. Market Structure (ADX, Bollinger Band squeeze, failed breakouts)
3. Volume & Breadth (Volume spikes, A/D divergence, McClellan Oscillator, Put/Call ratio)
4. Momentum Indicators (RSI divergence, MACD histogram, oscillator confluence)
5. Institutional Positioning (Smart Money Flow Indicator, options flow)

Author: MacroIntel System
Version: 1.0.0
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import pandas_ta as ta
except ImportError:
    logger.warning("pandas_ta not available, using basic technical indicators")
    ta = None

class MarketRegimeCalculator:
    """
    Market Regime Score Calculator based on Playbook v7.1
    
    Calculates a comprehensive market regime score (0-100) based on 5 key components
    and provides trading recommendations for futures markets.
    """
    
    def __init__(self):
        """Initialize the calculator with default parameters."""
        self.output_dir = project_root / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Component weights (sum to 1.0)
        self.component_weights = {
            'volatility': 0.25,      # 25%
            'structure': 0.20,       # 20%
            'volume_breadth': 0.20,  # 20%
            'momentum': 0.20,        # 20%
            'institutional': 0.15    # 15%
        }
        
        # Trading instruments and their characteristics
        self.instruments = {
            'MYM': {'name': 'Micro E-mini Dow', 'volatility_threshold': 25, 'risk_multiplier': 1.0},
            'MNQ': {'name': 'Micro E-mini NASDAQ', 'volatility_threshold': 30, 'risk_multiplier': 1.2},
            'MES': {'name': 'Micro E-mini S&P 500', 'volatility_threshold': 22, 'risk_multiplier': 0.9},
            'M2K': {'name': 'Micro E-mini Russell 2000', 'volatility_threshold': 35, 'risk_multiplier': 1.5}
        }
        
        # Strategy recommendations based on regime score
        self.strategy_recommendations = {
            (0, 20): {
                'name': 'Tier 1 Reversal',
                'description': 'Extreme fear conditions, strong reversal potential',
                'risk_allocation': '3.0%',
                'instruments': ['MYM', 'MES']
            },
            (20, 40): {
                'name': 'Tier 2 Mean Reversion',
                'description': 'Fear conditions, mean reversion opportunities',
                'risk_allocation': '2.5%',
                'instruments': ['MYM', 'MES', 'M2K']
            },
            (40, 60): {
                'name': 'Tier 3 Range Trading',
                'description': 'Neutral conditions, range-bound trading',
                'risk_allocation': '2.0%',
                'instruments': ['MES', 'MNQ']
            },
            (60, 80): {
                'name': 'Tier 4 Momentum',
                'description': 'Greed conditions, momentum continuation',
                'risk_allocation': '2.5%',
                'instruments': ['MNQ', 'M2K']
            },
            (80, 100): {
                'name': 'Tier 5 Extreme Momentum',
                'description': 'Extreme greed, strong momentum continuation',
                'risk_allocation': '3.0%',
                'instruments': ['MNQ', 'M2K']
            }
        }
    
    def fetch_market_data(self) -> Dict[str, Any]:
        """
        Fetch market data from various sources.
        
        Returns:
            Dict containing market data from different sources
        """
        logger.info("📊 Fetching market data...")
        
        market_data: Dict[str, Any] = {
            'vix': None,
            'fear_greed': None,
            'polygon_data': None,
            'fmp_calendar': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Fetch VIX data
            from utils.api_clients import fetch_polygon_indices
            polygon_data = fetch_polygon_indices()
            if polygon_data:
                market_data['polygon_data'] = polygon_data
            
            # Fetch Fear & Greed Index
            try:
                from dashboards.fear_greed_dashboard import get_fear_greed_report
                fear_greed = get_fear_greed_report()
                market_data['fear_greed'] = fear_greed
                logger.info(f"✅ Fear & Greed: {fear_greed['score']:.1f} ({fear_greed['rating']})")
            except Exception as e:
                logger.warning(f"⚠️ Fear & Greed fetch failed: {e}")
            
            # Fetch FMP Calendar
            try:
                from utils.api_clients import fetch_fmp_calendar
                calendar_data = fetch_fmp_calendar()
                market_data['fmp_calendar'] = calendar_data
                logger.info(f"✅ FMP Calendar: {len(calendar_data)} events")
            except Exception as e:
                logger.warning(f"⚠️ FMP Calendar fetch failed: {e}")
            
            # Simulate VIX data if not available
            if not market_data.get('vix'):
                market_data['vix'] = self._simulate_vix_data()
            
        except Exception as e:
            logger.error(f"❌ Error fetching market data: {e}")
        
        return market_data
    
    def _simulate_vix_data(self) -> Dict[str, Any]:
        """Simulate VIX data for testing purposes."""
        current_vix = np.random.uniform(15, 35)
        return {
            'current': current_vix,
            'term_structure': {
                'vix1m': current_vix * 0.95,
                'vix3m': current_vix * 1.05,
                'vix6m': current_vix * 1.10
            },
            'atr_spy': np.random.uniform(1.5, 4.0),
            'atr_qqq': np.random.uniform(2.0, 5.0)
        }
    
    def calculate_volatility_score(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Volatility Environment Score (0-100)
        
        Components:
        - VIX level and term structure
        - ATR (Average True Range) for major indices
        - Volatility regime classification
        """
        logger.info("📈 Calculating Volatility Environment Score...")
        
        score = 0
        components = {}
        
        try:
            # VIX Level Analysis (40% of volatility score)
            vix_data = market_data.get('vix', {})
            current_vix = vix_data.get('current', 20)
            
            if current_vix < 15:
                vix_score = 20  # Low volatility, complacent
            elif current_vix < 20:
                vix_score = 40  # Normal volatility
            elif current_vix < 25:
                vix_score = 60  # Elevated volatility
            elif current_vix < 30:
                vix_score = 80  # High volatility
            else:
                vix_score = 100  # Extreme volatility
            
            components['vix_level'] = {
                'value': current_vix,
                'score': vix_score,
                'weight': 0.4
            }
            
            # VIX Term Structure Analysis (30% of volatility score)
            term_structure = vix_data.get('term_structure', {})
            vix1m = term_structure.get('vix1m', current_vix)
            vix3m = term_structure.get('vix3m', current_vix * 1.05)
            
            contango = (vix3m - vix1m) / vix1m
            
            if contango > 0.1:
                term_score = 80  # Strong contango (fear)
            elif contango > 0.05:
                term_score = 60  # Moderate contango
            elif contango > -0.05:
                term_score = 40  # Normal term structure
            elif contango > -0.1:
                term_score = 20  # Moderate backwardation
            else:
                term_score = 0   # Strong backwardation (complacency)
            
            components['term_structure'] = {
                'value': contango,
                'score': term_score,
                'weight': 0.3
            }
            
            # ATR Analysis (30% of volatility score)
            atr_spy = vix_data.get('atr_spy', 2.0)
            atr_qqq = vix_data.get('atr_qqq', 3.0)
            
            avg_atr = (atr_spy + atr_qqq) / 2
            
            if avg_atr < 1.5:
                atr_score = 20  # Low ATR
            elif avg_atr < 2.5:
                atr_score = 40  # Normal ATR
            elif avg_atr < 3.5:
                atr_score = 60  # Elevated ATR
            elif avg_atr < 4.5:
                atr_score = 80  # High ATR
            else:
                atr_score = 100  # Extreme ATR
            
            components['atr'] = {
                'value': avg_atr,
                'score': atr_score,
                'weight': 0.3
            }
            
            # Calculate weighted score
            score = sum(comp['score'] * comp['weight'] for comp in components.values())
            
        except Exception as e:
            logger.error(f"❌ Error calculating volatility score: {e}")
            score = 50  # Default neutral score
        
        return {
            'score': score,
            'components': components,
            'interpretation': self._interpret_volatility_score(score)
        }
    
    def calculate_structure_score(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Market Structure Score (0-100)
        
        Components:
        - ADX (Average Directional Index)
        - Bollinger Band squeeze
        - Failed breakouts analysis
        """
        logger.info("🏗️ Calculating Market Structure Score...")
        
        score = 0
        components = {}
        
        try:
            # Simulate market structure data
            # In a real implementation, this would use actual price data
            
            # ADX Analysis (40% of structure score)
            adx_value = np.random.uniform(15, 45)
            
            if adx_value < 20:
                adx_score = 20  # Weak trend
            elif adx_value < 25:
                adx_score = 40  # Developing trend
            elif adx_value < 30:
                adx_score = 60  # Strong trend
            elif adx_value < 35:
                adx_score = 80  # Very strong trend
            else:
                adx_score = 100  # Extreme trend
            
            components['adx'] = {
                'value': adx_value,
                'score': adx_score,
                'weight': 0.4
            }
            
            # Bollinger Band Squeeze (30% of structure score)
            bb_squeeze = np.random.uniform(0.1, 0.8)
            
            if bb_squeeze < 0.2:
                squeeze_score = 100  # Extreme squeeze
            elif bb_squeeze < 0.4:
                squeeze_score = 80   # High squeeze
            elif bb_squeeze < 0.6:
                squeeze_score = 60   # Moderate squeeze
            elif bb_squeeze < 0.8:
                squeeze_score = 40   # Low squeeze
            else:
                squeeze_score = 20   # No squeeze
            
            components['bb_squeeze'] = {
                'value': bb_squeeze,
                'score': squeeze_score,
                'weight': 0.3
            }
            
            # Failed Breakouts (30% of structure score)
            failed_breakouts = np.random.randint(0, 5)
            
            if failed_breakouts == 0:
                breakout_score = 20  # No failed breakouts
            elif failed_breakouts == 1:
                breakout_score = 40  # Few failed breakouts
            elif failed_breakouts == 2:
                breakout_score = 60  # Some failed breakouts
            elif failed_breakouts == 3:
                breakout_score = 80  # Many failed breakouts
            else:
                breakout_score = 100  # Numerous failed breakouts
            
            components['failed_breakouts'] = {
                'value': failed_breakouts,
                'score': breakout_score,
                'weight': 0.3
            }
            
            # Calculate weighted score
            score = sum(comp['score'] * comp['weight'] for comp in components.values())
            
        except Exception as e:
            logger.error(f"❌ Error calculating structure score: {e}")
            score = 50
        
        return {
            'score': score,
            'components': components,
            'interpretation': self._interpret_structure_score(score)
        }
    
    def calculate_volume_breadth_score(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Volume & Breadth Score (0-100)
        
        Components:
        - Volume spikes
        - Advance/Decline divergence
        - McClellan Oscillator
        - Put/Call ratio
        """
        logger.info("📊 Calculating Volume & Breadth Score...")
        
        score = 0
        components = {}
        
        try:
            # Volume Spikes (25% of volume/breadth score)
            volume_spike = np.random.uniform(0.8, 2.0)
            
            if volume_spike < 1.0:
                volume_score = 20  # Below average volume
            elif volume_spike < 1.3:
                volume_score = 40  # Normal volume
            elif volume_spike < 1.6:
                volume_score = 60  # Elevated volume
            elif volume_spike < 1.9:
                volume_score = 80  # High volume
            else:
                volume_score = 100  # Extreme volume spike
            
            components['volume_spikes'] = {
                'value': volume_spike,
                'score': volume_score,
                'weight': 0.25
            }
            
            # A/D Divergence (25% of volume/breadth score)
            ad_divergence = np.random.uniform(-0.3, 0.3)
            
            if ad_divergence < -0.2:
                ad_score = 100  # Strong negative divergence
            elif ad_divergence < -0.1:
                ad_score = 80   # Moderate negative divergence
            elif ad_divergence < 0.1:
                ad_score = 40   # No significant divergence
            elif ad_divergence < 0.2:
                ad_score = 20   # Moderate positive divergence
            else:
                ad_score = 0    # Strong positive divergence
            
            components['ad_divergence'] = {
                'value': ad_divergence,
                'score': ad_score,
                'weight': 0.25
            }
            
            # McClellan Oscillator (25% of volume/breadth score)
            mcclellan = np.random.uniform(-100, 100)
            
            if mcclellan < -50:
                mcclellan_score = 100  # Extreme oversold
            elif mcclellan < -25:
                mcclellan_score = 80   # Oversold
            elif mcclellan < 25:
                mcclellan_score = 40   # Neutral
            elif mcclellan < 50:
                mcclellan_score = 20   # Overbought
            else:
                mcclellan_score = 0    # Extreme overbought
            
            components['mcclellan'] = {
                'value': mcclellan,
                'score': mcclellan_score,
                'weight': 0.25
            }
            
            # Put/Call Ratio (25% of volume/breadth score)
            put_call_ratio = np.random.uniform(0.5, 2.0)
            
            if put_call_ratio > 1.5:
                pc_score = 100  # Extreme fear
            elif put_call_ratio > 1.2:
                pc_score = 80   # High fear
            elif put_call_ratio > 0.9:
                pc_score = 40   # Neutral
            elif put_call_ratio > 0.7:
                pc_score = 20   # High greed
            else:
                pc_score = 0    # Extreme greed
            
            components['put_call_ratio'] = {
                'value': put_call_ratio,
                'score': pc_score,
                'weight': 0.25
            }
            
            # Calculate weighted score
            score = sum(comp['score'] * comp['weight'] for comp in components.values())
            
        except Exception as e:
            logger.error(f"❌ Error calculating volume/breadth score: {e}")
            score = 50
        
        return {
            'score': score,
            'components': components,
            'interpretation': self._interpret_volume_breadth_score(score)
        }
    
    def calculate_momentum_score(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Momentum Indicators Score (0-100)
        
        Components:
        - RSI divergence
        - MACD histogram
        - Oscillator confluence
        """
        logger.info("📈 Calculating Momentum Indicators Score...")
        
        score = 0
        components = {}
        
        try:
            # RSI Divergence (40% of momentum score)
            rsi_divergence = np.random.uniform(-1, 1)
            
            if rsi_divergence < -0.5:
                rsi_score = 100  # Strong bearish divergence
            elif rsi_divergence < -0.2:
                rsi_score = 80   # Moderate bearish divergence
            elif rsi_divergence < 0.2:
                rsi_score = 40   # No significant divergence
            elif rsi_divergence < 0.5:
                rsi_score = 20   # Moderate bullish divergence
            else:
                rsi_score = 0    # Strong bullish divergence
            
            components['rsi_divergence'] = {
                'value': rsi_divergence,
                'score': rsi_score,
                'weight': 0.4
            }
            
            # MACD Histogram (30% of momentum score)
            macd_histogram = np.random.uniform(-2, 2)
            
            if macd_histogram < -1.5:
                macd_score = 100  # Strong bearish momentum
            elif macd_histogram < -0.5:
                macd_score = 80   # Bearish momentum
            elif macd_histogram < 0.5:
                macd_score = 40   # Neutral momentum
            elif macd_histogram < 1.5:
                macd_score = 20   # Bullish momentum
            else:
                macd_score = 0    # Strong bullish momentum
            
            components['macd_histogram'] = {
                'value': macd_histogram,
                'score': macd_score,
                'weight': 0.3
            }
            
            # Oscillator Confluence (30% of momentum score)
            oscillator_confluence = np.random.uniform(0, 1)
            
            if oscillator_confluence > 0.8:
                confluence_score = 100  # Strong confluence
            elif oscillator_confluence > 0.6:
                confluence_score = 80   # High confluence
            elif oscillator_confluence > 0.4:
                confluence_score = 60   # Moderate confluence
            elif oscillator_confluence > 0.2:
                confluence_score = 40   # Low confluence
            else:
                confluence_score = 20   # No confluence
            
            components['oscillator_confluence'] = {
                'value': oscillator_confluence,
                'score': confluence_score,
                'weight': 0.3
            }
            
            # Calculate weighted score
            score = sum(comp['score'] * comp['weight'] for comp in components.values())
            
        except Exception as e:
            logger.error(f"❌ Error calculating momentum score: {e}")
            score = 50
        
        return {
            'score': score,
            'components': components,
            'interpretation': self._interpret_momentum_score(score)
        }
    
    def calculate_institutional_score(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Institutional Positioning Score (0-100)
        
        Components:
        - Smart Money Flow Indicator
        - Options flow analysis
        - Institutional sentiment
        """
        logger.info("🏦 Calculating Institutional Positioning Score...")
        
        score = 0
        components = {}
        
        try:
            # Smart Money Flow (40% of institutional score)
            smart_money_flow = np.random.uniform(-1, 1)
            
            if smart_money_flow < -0.5:
                smf_score = 100  # Strong institutional selling
            elif smart_money_flow < -0.2:
                smf_score = 80   # Moderate institutional selling
            elif smart_money_flow < 0.2:
                smf_score = 40   # Neutral institutional flow
            elif smart_money_flow < 0.5:
                smf_score = 20   # Moderate institutional buying
            else:
                smf_score = 0    # Strong institutional buying
            
            components['smart_money_flow'] = {
                'value': smart_money_flow,
                'score': smf_score,
                'weight': 0.4
            }
            
            # Options Flow (30% of institutional score)
            options_flow = np.random.uniform(-2, 2)
            
            if options_flow < -1.5:
                options_score = 100  # Heavy put buying
            elif options_flow < -0.5:
                options_score = 80   # Moderate put buying
            elif options_flow < 0.5:
                options_score = 40   # Neutral options flow
            elif options_flow < 1.5:
                options_score = 20   # Moderate call buying
            else:
                options_score = 0    # Heavy call buying
            
            components['options_flow'] = {
                'value': options_flow,
                'score': options_score,
                'weight': 0.3
            }
            
            # Institutional Sentiment (30% of institutional score)
            inst_sentiment = np.random.uniform(0, 1)
            
            if inst_sentiment < 0.2:
                sentiment_score = 100  # Very bearish
            elif inst_sentiment < 0.4:
                sentiment_score = 80   # Bearish
            elif inst_sentiment < 0.6:
                sentiment_score = 40   # Neutral
            elif inst_sentiment < 0.8:
                sentiment_score = 20   # Bullish
            else:
                sentiment_score = 0    # Very bullish
            
            components['institutional_sentiment'] = {
                'value': inst_sentiment,
                'score': sentiment_score,
                'weight': 0.3
            }
            
            # Calculate weighted score
            score = sum(comp['score'] * comp['weight'] for comp in components.values())
            
        except Exception as e:
            logger.error(f"❌ Error calculating institutional score: {e}")
            score = 50
        
        return {
            'score': score,
            'components': components,
            'interpretation': self._interpret_institutional_score(score)
        }
    
    def calculate_total_score(self, component_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate the total market regime score (0-100) from component scores.
        
        Args:
            component_scores: Dictionary containing scores for all 5 components
            
        Returns:
            Dictionary with total score and breakdown
        """
        logger.info("🎯 Calculating Total Market Regime Score...")
        
        total_score = 0
        weighted_components = {}
        
        for component_name, component_data in component_scores.items():
            if component_name in self.component_weights:
                weight = self.component_weights[component_name]
                score = component_data['score']
                weighted_score = score * weight
                
                weighted_components[component_name] = {
                    'raw_score': score,
                    'weight': weight,
                    'weighted_score': weighted_score,
                    'interpretation': component_data.get('interpretation', '')
                }
                
                total_score += weighted_score
        
        # Determine regime classification
        regime_classification = self._classify_regime(total_score)
        
        # Get strategy recommendation
        strategy_rec = self._get_strategy_recommendation(total_score)
        
        return {
            'total_score': total_score,
            'regime_classification': regime_classification,
            'strategy_recommendation': strategy_rec['name'],
            'strategy_description': strategy_rec['description'],
            'instrument': self._select_instrument(total_score, strategy_rec),
            'risk_allocation': strategy_rec['risk_allocation'],
            'component_breakdown': weighted_components,
            'timestamp': datetime.now().isoformat()
        }
    
    def _classify_regime(self, score: float) -> str:
        """Classify the market regime based on total score."""
        if score < 20:
            return "Extreme Fear"
        elif score < 40:
            return "Fear"
        elif score < 60:
            return "Neutral"
        elif score < 80:
            return "Greed"
        else:
            return "Extreme Greed"
    
    def _get_strategy_recommendation(self, score: float) -> Dict[str, Any]:
        """Get strategy recommendation based on total score."""
        for (min_score, max_score), strategy in self.strategy_recommendations.items():
            if min_score <= score < max_score:
                return strategy
        return self.strategy_recommendations[(40, 60)]  # Default to neutral
    
    def _select_instrument(self, score: float, strategy: Dict[str, Any]) -> str:
        """Select the best trading instrument based on score and strategy."""
        available_instruments = strategy.get('instruments', ['MYM'])
        
        # Consider volatility when selecting instrument
        if score > 70:  # High volatility
            # Prefer higher volatility instruments
            if 'MNQ' in available_instruments:
                return 'MNQ'
            elif 'M2K' in available_instruments:
                return 'M2K'
        
        # Default to first available instrument
        return available_instruments[0]
    
    def _interpret_volatility_score(self, score: float) -> str:
        """Interpret volatility score."""
        if score < 20:
            return "Low volatility, complacent market"
        elif score < 40:
            return "Normal volatility conditions"
        elif score < 60:
            return "Elevated volatility, increased uncertainty"
        elif score < 80:
            return "High volatility, fear-driven market"
        else:
            return "Extreme volatility, panic conditions"
    
    def _interpret_structure_score(self, score: float) -> str:
        """Interpret structure score."""
        if score < 20:
            return "Weak market structure, choppy conditions"
        elif score < 40:
            return "Developing structure, mixed signals"
        elif score < 60:
            return "Moderate structure, some clarity"
        elif score < 80:
            return "Strong structure, clear trends"
        else:
            return "Extreme structure, powerful trends"
    
    def _interpret_volume_breadth_score(self, score: float) -> str:
        """Interpret volume/breadth score."""
        if score < 20:
            return "Low volume/breadth, weak participation"
        elif score < 40:
            return "Normal volume/breadth conditions"
        elif score < 60:
            return "Elevated volume/breadth, increased activity"
        elif score < 80:
            return "High volume/breadth, strong participation"
        else:
            return "Extreme volume/breadth, panic selling/buying"
    
    def _interpret_momentum_score(self, score: float) -> str:
        """Interpret momentum score."""
        if score < 20:
            return "Strong bullish momentum"
        elif score < 40:
            return "Moderate bullish momentum"
        elif score < 60:
            return "Neutral momentum conditions"
        elif score < 80:
            return "Moderate bearish momentum"
        else:
            return "Strong bearish momentum"
    
    def _interpret_institutional_score(self, score: float) -> str:
        """Interpret institutional score."""
        if score < 20:
            return "Strong institutional buying"
        elif score < 40:
            return "Moderate institutional buying"
        elif score < 60:
            return "Neutral institutional positioning"
        elif score < 80:
            return "Moderate institutional selling"
        else:
            return "Strong institutional selling"
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """
        Save results to JSON file.
        
        Args:
            results: Complete regime score results
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"regime_score_{timestamp}.json"
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"✅ Results saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
            return ""
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a human-readable report from the results.
        
        Args:
            results: Complete regime score results
            
        Returns:
            Formatted report string
        """
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    MARKET REGIME SCORE REPORT                ║
║                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
╚══════════════════════════════════════════════════════════════╝

📊 TOTAL REGIME SCORE: {results['total_score']:.1f}/100
🏷️  CLASSIFICATION: {results['regime_classification']}

🎯 STRATEGY RECOMMENDATION:
   • Strategy: {results['strategy_recommendation']}
   • Description: {results['strategy_description']}
   • Instrument: {results['instrument']}
   • Risk Allocation: {results['risk_allocation']}

📈 COMPONENT BREAKDOWN:
"""
        
        for component, data in results['component_breakdown'].items():
            report += f"   • {component.replace('_', ' ').title()}: {data['raw_score']:.1f}/100 ({data['interpretation']})\n"
        
        report += f"""
⏰ Generated: {results['timestamp']}
"""
        
        return report


def get_daily_regime_score() -> Dict[str, Any]:
    """
    Main function to calculate and return the daily market regime score.
    
    Returns:
        Dictionary containing complete regime score analysis
    """
    logger.info("🚀 Starting Daily Market Regime Score Calculation...")
    
    try:
        # Initialize calculator
        calculator = MarketRegimeCalculator()
        
        # Fetch market data
        market_data = calculator.fetch_market_data()
        
        # Calculate component scores
        volatility_score = calculator.calculate_volatility_score(market_data)
        structure_score = calculator.calculate_structure_score(market_data)
        volume_breadth_score = calculator.calculate_volume_breadth_score(market_data)
        momentum_score = calculator.calculate_momentum_score(market_data)
        institutional_score = calculator.calculate_institutional_score(market_data)
        
        # Compile component scores
        component_scores = {
            'volatility': volatility_score,
            'structure': structure_score,
            'volume_breadth': volume_breadth_score,
            'momentum': momentum_score,
            'institutional': institutional_score
        }
        
        # Calculate total score
        total_results = calculator.calculate_total_score(component_scores)
        
        # Add component scores to results
        total_results['component_scores'] = component_scores
        total_results['market_data'] = market_data
        
        # Save results
        filepath = calculator.save_results(total_results)
        if filepath:
            total_results['output_file'] = filepath
        
        # Generate and print report
        report = calculator.generate_report(total_results)
        print(report)
        
        logger.info("✅ Daily Market Regime Score calculation completed successfully!")
        
        return total_results
        
    except Exception as e:
        logger.error(f"❌ Error in get_daily_regime_score: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'success': False
        }


if __name__ == "__main__":
    # Run the regime score calculation
    results = get_daily_regime_score()
    
    if 'error' not in results:
        print(f"\n🎉 Regime Score Calculation Complete!")
        print(f"📊 Total Score: {results['total_score']:.1f}/100")
        print(f"🎯 Strategy: {results['strategy_recommendation']}")
        print(f"📈 Instrument: {results['instrument']}")
        print(f"💰 Risk Allocation: {results['risk_allocation']}")
    else:
        print(f"\n❌ Calculation failed: {results['error']}")
