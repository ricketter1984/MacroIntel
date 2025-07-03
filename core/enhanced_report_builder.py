#!/usr/bin/env python3
"""
Enhanced Report Builder for MacroIntel

This module integrates all data sources and generates comprehensive reports with:
- Multi-source data aggregation
- Strategy recommendations based on playbook logic
- Market regime analysis
- Risk assessment
- Visual insights
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import glob
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import Dict, List, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

# Import local modules
from core.enhanced_visualizations import EnhancedVisualizations

class EnhancedReportBuilder:
    def __init__(self):
        """Initialize the enhanced report builder."""
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize visualization engine
        self.viz_engine = EnhancedVisualizations()
        
        # Market regime thresholds
        self.regime_thresholds = {
            'vix_high': 30,
            'vix_low': 15,
            'fear_greed_extreme_fear': 25,
            'fear_greed_extreme_greed': 75,
            'market_volatility_high': 0.03,  # 3% daily volatility
            'market_volatility_low': 0.01    # 1% daily volatility
        }
        
        # Strategy playbook
        self.strategy_playbook = {
            'trend_following': {
                'conditions': ['bullish_trend', 'low_volatility', 'neutral_sentiment'],
                'description': 'Follow established trends with tight risk management',
                'risk_level': 'Medium',
                'position_sizing': 'Normal'
            },
            'mean_reversion': {
                'conditions': ['oversold_conditions', 'high_volatility', 'extreme_fear'],
                'description': 'Contrarian approach during extreme conditions',
                'risk_level': 'High',
                'position_sizing': 'Reduced'
            },
            'momentum': {
                'conditions': ['strong_momentum', 'low_volatility', 'greed_sentiment'],
                'description': 'Ride momentum with trailing stops',
                'risk_level': 'Medium-High',
                'position_sizing': 'Normal'
            },
            'defensive': {
                'conditions': ['bearish_trend', 'high_volatility', 'extreme_greed'],
                'description': 'Defensive positioning with hedges',
                'risk_level': 'Low',
                'position_sizing': 'Reduced'
            },
            'opportunistic': {
                'conditions': ['mixed_signals', 'moderate_volatility', 'neutral_sentiment'],
                'description': 'Selective opportunities with strict criteria',
                'risk_level': 'Medium',
                'position_sizing': 'Normal'
            }
        }
        
        print("📊 Enhanced Report Builder initialized")
    
    def load_regime_score_data(self) -> Optional[Dict[str, Any]]:
        """
        Load the most recent regime score data from output directory.
        
        Returns:
            Dict containing regime score data or None if not found
        """
        try:
            # Look for regime score files in output directory
            output_dir = Path("output")
            if not output_dir.exists():
                return None
            
            # Find all regime score files
            regime_files = list(output_dir.glob("regime_score_*.json"))
            if not regime_files:
                return None
            
            # Get the most recent file
            latest_file = max(regime_files, key=lambda x: x.stat().st_mtime)
            
            # Load and parse the JSON data
            with open(latest_file, 'r', encoding='utf-8') as f:
                regime_data = json.load(f)
            
            print(f"✅ Loaded regime score data from: {latest_file}")
            return regime_data
            
        except Exception as e:
            print(f"⚠️ Error loading regime score data: {e}")
            return None
    
    def analyze_market_regime(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current market regime using multiple indicators."""
        regime_analysis = {
            'timestamp': datetime.now().isoformat(),
            'overall_regime': 'Unknown',
            'confidence': 0.0,
            'indicators': {},
            'signals': []
        }
        
        # VIX Analysis
        if 'vix_data' in data_sources and data_sources['vix_data'] is not None:
            vix_data = data_sources['vix_data']
            if len(vix_data) > 0:
                current_vix = vix_data['close'].iloc[-1] if 'close' in vix_data.columns else vix_data.iloc[-1]
                avg_vix = vix_data['close'].mean() if 'close' in vix_data.columns else vix_data.mean()
                
                regime_analysis['indicators']['vix'] = {
                    'current': current_vix,
                    'average': avg_vix,
                    'status': 'High' if current_vix > self.regime_thresholds['vix_high'] else 
                             'Low' if current_vix < self.regime_thresholds['vix_low'] else 'Normal'
                }
                
                if current_vix > self.regime_thresholds['vix_high']:
                    regime_analysis['signals'].append('High volatility - defensive positioning recommended')
                elif current_vix < self.regime_thresholds['vix_low']:
                    regime_analysis['signals'].append('Low volatility - trend following favorable')
        
        # Fear & Greed Analysis
        if 'fear_greed_data' in data_sources and data_sources['fear_greed_data'] is not None:
            fg_data = data_sources['fear_greed_data']
            if len(fg_data) > 0:
                current_fg = fg_data.iloc[-1]
                
                regime_analysis['indicators']['fear_greed'] = {
                    'current': current_fg,
                    'status': 'Extreme Fear' if current_fg < self.regime_thresholds['fear_greed_extreme_fear'] else
                             'Extreme Greed' if current_fg > self.regime_thresholds['fear_greed_extreme_greed'] else
                             'Fear' if current_fg < 45 else 'Greed' if current_fg > 55 else 'Neutral'
                }
                
                if current_fg < self.regime_thresholds['fear_greed_extreme_fear']:
                    regime_analysis['signals'].append('Extreme fear - contrarian opportunities')
                elif current_fg > self.regime_thresholds['fear_greed_extreme_greed']:
                    regime_analysis['signals'].append('Extreme greed - risk reduction advised')
        
        # Market Trend Analysis
        if 'asset_data' in data_sources and data_sources['asset_data']:
            asset_data = data_sources['asset_data']
            trend_signals = []
            
            for symbol, data in asset_data.items():
                if data is not None and len(data) > 20:
                    # Calculate trend indicators
                    current_price = data['close'].iloc[-1]
                    sma_20 = data['close'].rolling(20).mean().iloc[-1]
                    sma_50 = data['close'].rolling(50).mean().iloc[-1] if len(data) > 50 else sma_20
                    
                    # Determine trend
                    if current_price > sma_20 > sma_50:
                        trend = 'Strong Bullish'
                    elif current_price > sma_20 and sma_20 < sma_50:
                        trend = 'Weak Bullish'
                    elif current_price < sma_20 < sma_50:
                        trend = 'Strong Bearish'
                    elif current_price < sma_20 and sma_20 > sma_50:
                        trend = 'Weak Bearish'
                    else:
                        trend = 'Sideways'
                    
                    trend_signals.append(f"{symbol}: {trend}")
            
            regime_analysis['indicators']['market_trends'] = trend_signals
        
        # Economic Calendar Impact
        if 'calendar_data' in data_sources and data_sources['calendar_data']:
            calendar_data = data_sources['calendar_data']
            if calendar_data.get('success'):
                high_impact_count = len(calendar_data.get('high_impact_events', []))
                medium_impact_count = len(calendar_data.get('medium_impact_events', []))
                
                regime_analysis['indicators']['economic_events'] = {
                    'high_impact': high_impact_count,
                    'medium_impact': medium_impact_count,
                    'total_events': calendar_data.get('total_events', 0)
                }
                
                if high_impact_count > 3:
                    regime_analysis['signals'].append('High economic event density - increased volatility expected')
        
        # Determine overall regime
        regime_score = 0
        total_indicators = 0
        
        # VIX contribution
        if 'vix' in regime_analysis['indicators']:
            vix_status = regime_analysis['indicators']['vix']['status']
            if vix_status == 'High':
                regime_score -= 2
            elif vix_status == 'Low':
                regime_score += 1
            total_indicators += 1
        
        # Fear & Greed contribution
        if 'fear_greed' in regime_analysis['indicators']:
            fg_status = regime_analysis['indicators']['fear_greed']['status']
            if 'Extreme Fear' in fg_status:
                regime_score += 2  # Contrarian bullish signal
            elif 'Extreme Greed' in fg_status:
                regime_score -= 2  # Contrarian bearish signal
            elif 'Fear' in fg_status:
                regime_score += 1
            elif 'Greed' in fg_status:
                regime_score -= 1
            total_indicators += 1
        
        # Market trends contribution
        if 'market_trends' in regime_analysis['indicators']:
            bullish_count = sum(1 for signal in regime_analysis['indicators']['market_trends'] if 'Bullish' in signal)
            bearish_count = sum(1 for signal in regime_analysis['indicators']['market_trends'] if 'Bearish' in signal)
            
            if bullish_count > bearish_count:
                regime_score += 1
            elif bearish_count > bullish_count:
                regime_score -= 1
            total_indicators += 1
        
        # Calculate overall regime
        if total_indicators > 0:
            avg_score = regime_score / total_indicators
            
            if avg_score >= 1.5:
                regime_analysis['overall_regime'] = 'Bullish'
                regime_analysis['confidence'] = min(abs(avg_score) * 0.3, 1.0)
            elif avg_score <= -1.5:
                regime_analysis['overall_regime'] = 'Bearish'
                regime_analysis['confidence'] = min(abs(avg_score) * 0.3, 1.0)
            else:
                regime_analysis['overall_regime'] = 'Neutral'
                regime_analysis['confidence'] = 0.5
        
        return regime_analysis
    
    def generate_strategy_recommendations(self, regime_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategy recommendations based on market regime analysis."""
        recommendations = {
            'timestamp': datetime.now().isoformat(),
            'primary_strategy': None,
            'secondary_strategy': None,
            'risk_level': 'Medium',
            'position_sizing': 'Normal',
            'key_considerations': [],
            'strategies': []
        }
        
        regime = regime_analysis['overall_regime']
        confidence = regime_analysis['confidence']
        
        # Determine primary strategy based on regime
        if regime == 'Bullish' and confidence > 0.6:
            if 'Low' in regime_analysis['indicators'].get('vix', {}).get('status', ''):
                recommendations['primary_strategy'] = 'trend_following'
            else:
                recommendations['primary_strategy'] = 'momentum'
        elif regime == 'Bearish' and confidence > 0.6:
            if 'Extreme Fear' in regime_analysis['indicators'].get('fear_greed', {}).get('status', ''):
                recommendations['primary_strategy'] = 'mean_reversion'
            else:
                recommendations['primary_strategy'] = 'defensive'
        else:
            recommendations['primary_strategy'] = 'opportunistic'
        
        # Set secondary strategy
        if recommendations['primary_strategy'] == 'trend_following':
            recommendations['secondary_strategy'] = 'momentum'
        elif recommendations['primary_strategy'] == 'mean_reversion':
            recommendations['secondary_strategy'] = 'defensive'
        elif recommendations['primary_strategy'] == 'defensive':
            recommendations['secondary_strategy'] = 'opportunistic'
        else:
            recommendations['secondary_strategy'] = 'trend_following'
        
        # Get strategy details
        primary_details = self.strategy_playbook.get(recommendations['primary_strategy'], {})
        secondary_details = self.strategy_playbook.get(recommendations['secondary_strategy'], {})
        
        recommendations['risk_level'] = primary_details.get('risk_level', 'Medium')
        recommendations['position_sizing'] = primary_details.get('position_sizing', 'Normal')
        
        # Add key considerations
        recommendations['key_considerations'].extend(regime_analysis['signals'])
        
        # Add strategy descriptions
        recommendations['strategies'] = [
            {
                'name': recommendations['primary_strategy'],
                'type': 'Primary',
                'description': primary_details.get('description', ''),
                'risk_level': primary_details.get('risk_level', 'Medium'),
                'conditions': primary_details.get('conditions', [])
            },
            {
                'name': recommendations['secondary_strategy'],
                'type': 'Secondary',
                'description': secondary_details.get('description', ''),
                'risk_level': secondary_details.get('risk_level', 'Medium'),
                'conditions': secondary_details.get('conditions', [])
            }
        ]
        
        return recommendations
    
    def generate_risk_assessment(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive risk assessment."""
        risk_assessment = {
            'timestamp': datetime.now().isoformat(),
            'overall_risk_level': 'Medium',
            'risk_factors': [],
            'risk_score': 50,
            'mitigation_strategies': []
        }
        
        risk_score = 50  # Base score
        
        # VIX-based risk
        if 'vix_data' in data_sources and data_sources['vix_data'] is not None:
            vix_data = data_sources['vix_data']
            if len(vix_data) > 0:
                current_vix = vix_data['close'].iloc[-1] if 'close' in vix_data.columns else vix_data.iloc[-1]
                
                if current_vix > 30:
                    risk_score += 20
                    risk_assessment['risk_factors'].append(f'High VIX ({current_vix:.1f}) - elevated volatility risk')
                elif current_vix > 25:
                    risk_score += 10
                    risk_assessment['risk_factors'].append(f'Moderate VIX ({current_vix:.1f}) - increased volatility')
                elif current_vix < 15:
                    risk_score -= 10
                    risk_assessment['risk_factors'].append(f'Low VIX ({current_vix:.1f}) - complacency risk')
        
        # Fear & Greed risk
        if 'fear_greed_data' in data_sources and data_sources['fear_greed_data'] is not None:
            fg_data = data_sources['fear_greed_data']
            if len(fg_data) > 0:
                current_fg = fg_data.iloc[-1]
                
                if current_fg < 25:
                    risk_score += 15
                    risk_assessment['risk_factors'].append(f'Extreme fear ({current_fg:.1f}) - panic selling risk')
                elif current_fg > 75:
                    risk_score += 15
                    risk_assessment['risk_factors'].append(f'Extreme greed ({current_fg:.1f}) - bubble risk')
        
        # Economic event risk
        if 'calendar_data' in data_sources and data_sources['calendar_data']:
            calendar_data = data_sources['calendar_data']
            if calendar_data.get('success'):
                high_impact_count = len(calendar_data.get('high_impact_events', []))
                
                if high_impact_count > 5:
                    risk_score += 15
                    risk_assessment['risk_factors'].append(f'High economic event density ({high_impact_count} events)')
                elif high_impact_count > 2:
                    risk_score += 10
                    risk_assessment['risk_factors'].append(f'Moderate economic event density ({high_impact_count} events)')
        
        # Market trend risk
        if 'asset_data' in data_sources and data_sources['asset_data']:
            asset_data = data_sources['asset_data']
            bearish_count = 0
            
            for symbol, data in asset_data.items():
                if data is not None and len(data) > 20:
                    current_price = data['close'].iloc[-1]
                    sma_20 = data['close'].rolling(20).mean().iloc[-1]
                    
                    if current_price < sma_20:
                        bearish_count += 1
            
            if bearish_count > len(asset_data) * 0.7:
                risk_score += 15
                risk_assessment['risk_factors'].append(f'Majority of assets in downtrend ({bearish_count}/{len(asset_data)})')
        
        # Determine overall risk level
        risk_score = max(0, min(100, risk_score))
        risk_assessment['risk_score'] = risk_score
        
        if risk_score >= 70:
            risk_assessment['overall_risk_level'] = 'High'
        elif risk_score >= 40:
            risk_assessment['overall_risk_level'] = 'Medium'
        else:
            risk_assessment['overall_risk_level'] = 'Low'
        
        # Generate mitigation strategies
        if risk_score >= 70:
            risk_assessment['mitigation_strategies'].extend([
                'Reduce position sizes by 50%',
                'Increase stop-loss distances',
                'Add defensive hedges',
                'Focus on high-quality assets only'
            ])
        elif risk_score >= 50:
            risk_assessment['mitigation_strategies'].extend([
                'Reduce position sizes by 25%',
                'Tighten stop-losses',
                'Diversify across asset classes',
                'Monitor key support/resistance levels'
            ])
        else:
            risk_assessment['mitigation_strategies'].extend([
                'Normal position sizing',
                'Standard risk management',
                'Regular portfolio rebalancing',
                'Monitor for complacency signals'
            ])
        
        return risk_assessment
    
    def build_comprehensive_report(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive market intelligence report."""
        print("📊 Building comprehensive market intelligence report...")
        
        # Load regime score data
        regime_score_data = self.load_regime_score_data()
        
        # Generate all analyses
        regime_analysis = self.analyze_market_regime(data_sources)
        strategy_recommendations = self.generate_strategy_recommendations(regime_analysis)
        risk_assessment = self.generate_risk_assessment(data_sources)
        
        # Generate visualizations
        print(f"🔍 Data sources being passed to visualization engine:")
        print(f"   Available keys: {list(data_sources.keys()) if data_sources else 'None'}")
        
        # Debug data structure
        for key, value in data_sources.items():
            if value is not None:
                if isinstance(value, pd.DataFrame):
                    print(f"   {key}: DataFrame with {len(value)} rows, columns: {list(value.columns)}")
                elif isinstance(value, dict):
                    print(f"   {key}: Dictionary with keys: {list(value.keys())}")
                elif isinstance(value, pd.Series):
                    print(f"   {key}: Series with {len(value)} values")
                else:
                    print(f"   {key}: {type(value)} - {str(value)[:100]}...")
            else:
                print(f"   {key}: None")
        
        viz_results = self.viz_engine.generate_all_visualizations(data_sources)
        
        # Compile comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'report_type': 'comprehensive_market_intelligence',
            'executive_summary': {
                'market_regime': regime_analysis['overall_regime'],
                'confidence': regime_analysis['confidence'],
                'primary_strategy': strategy_recommendations['primary_strategy'],
                'risk_level': risk_assessment['overall_risk_level'],
                'key_insights': regime_analysis['signals'][:3]  # Top 3 signals
            },
            'market_regime_analysis': regime_analysis,
            'strategy_recommendations': strategy_recommendations,
            'risk_assessment': risk_assessment,
            'regime_score_data': regime_score_data,  # Add regime score data
            'data_sources_summary': {
                'sources_available': list(data_sources.keys()),
                'data_quality': 'High' if len(data_sources) >= 3 else 'Medium' if len(data_sources) >= 2 else 'Low'
            },
            'visualizations': viz_results,
            'detailed_analysis': {
                'market_indicators': regime_analysis['indicators'],
                'risk_factors': risk_assessment['risk_factors'],
                'mitigation_strategies': risk_assessment['mitigation_strategies']
            }
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        report_filename = f"comprehensive_report_{timestamp}.json"
        report_path = os.path.join(self.output_dir, report_filename)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"✅ Comprehensive report saved to {report_path}")
        print(f"📊 Report Summary:")
        print(f"   Market Regime: {report['executive_summary']['market_regime']}")
        print(f"   Confidence: {report['executive_summary']['confidence']:.1%}")
        print(f"   Primary Strategy: {report['executive_summary']['primary_strategy']}")
        print(f"   Risk Level: {report['executive_summary']['risk_level']}")
        print(f"   Charts Generated: {len(viz_results['charts_generated'])}")
        
        return report

def main():
    """Test function for the enhanced report builder."""
    report_builder = EnhancedReportBuilder()
    
    # Create sample data for testing
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    # Sample data sources
    data_sources = {
        'vix_data': pd.DataFrame({
            'close': np.random.normal(20, 5, len(dates)) + 15
        }, index=dates),
        'fear_greed_data': pd.Series(np.random.normal(50, 15, len(dates)), index=dates),
        'asset_data': {
            'SPY': pd.DataFrame({'close': np.random.normal(400, 10, len(dates)) + 380}, index=dates),
            'QQQ': pd.DataFrame({'close': np.random.normal(350, 15, len(dates)) + 330}, index=dates),
            'GLD': pd.DataFrame({'close': np.random.normal(180, 5, len(dates)) + 175}, index=dates)
        },
        'calendar_data': {
            'success': True,
            'high_impact_events': [{'event': 'FOMC Meeting', 'date': '2024-01-15'}],
            'medium_impact_events': [{'event': 'CPI Release', 'date': '2024-01-10'}],
            'total_events': 2
        }
    }
    
    # Generate comprehensive report
    report = report_builder.build_comprehensive_report(data_sources)
    print(f"Report generated successfully: {report['executive_summary']}")

if __name__ == "__main__":
    main() 