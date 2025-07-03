#!/usr/bin/env python3
"""
Enhanced MacroIntel System

This is the main entry point for the MacroIntel system, now with enhanced capabilities:
- Multi-source data integration (Benzinga, Polygon, FMP, Messari, Twelve Data, Fear & Greed)
- Enhanced visualizations (VIX analysis, multi-asset comparison, economic calendar impact)
- Strategy recommendations based on playbook logic
- Comprehensive risk assessment
- Automated report generation
"""

import os
import sys
import json
import logging
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

# Import local modules
from api_dispatcher import dispatch_api_task
from core.enhanced_report_builder import EnhancedReportBuilder
from core.enhanced_visualizations import EnhancedVisualizations

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_macrointel.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedMacroIntel:
    def __init__(self):
        """Initialize the enhanced MacroIntel system."""
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Initialize components
        self.report_builder = EnhancedReportBuilder()
        self.viz_engine = EnhancedVisualizations()
        
        # Data sources configuration
        self.data_sources = {
            'benzinga': 'scripts/fetch_benzinga_news.py',
            'polygon': 'scripts/fetch_polygon_indices.py',
            'fmp_calendar': 'scripts/fetch_fmp_calendar.py',
            'messari': 'scripts/fetch_messari_intel.py',
            'twelve_data': 'scripts/fetch_twelve_data.py'
        }
        
        logger.info("🚀 Enhanced MacroIntel System initialized")
    
    def fetch_benzinga_news(self):
        """Fetch news from Benzinga API."""
        logger.info("📰 Fetching Benzinga news...")
        try:
            result = dispatch_api_task("benzinga", self.data_sources['benzinga'])
            if result['success']:
                logger.info(f"✅ Benzinga: {len(result.get('data', {}).get('articles', []))} articles")
            else:
                logger.error(f"❌ Benzinga fetch failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"❌ Benzinga fetch error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def fetch_polygon_indices(self):
        """Fetch market indices from Polygon API."""
        logger.info("📊 Fetching Polygon market indices...")
        try:
            result = dispatch_api_task("polygon", self.data_sources['polygon'])
            if result['success']:
                market_data = result.get('data', {})
                logger.info(f"✅ Polygon: {market_data.get('market_summary', {}).get('total_symbols', 0)} symbols")
            else:
                logger.error(f"❌ Polygon fetch failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"❌ Polygon fetch error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def fetch_fmp_calendar(self):
        """Fetch economic calendar from FMP API."""
        logger.info("📅 Fetching FMP economic calendar...")
        try:
            result = dispatch_api_task("fmp", self.data_sources['fmp_calendar'])
            if result['success']:
                calendar_data = result.get('data', {})
                logger.info(f"✅ FMP Calendar: {calendar_data.get('total_events', 0)} events")
            else:
                logger.error(f"❌ FMP Calendar fetch failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"❌ FMP Calendar fetch error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def fetch_messari_intel(self):
        """Fetch crypto intelligence from Messari API."""
        logger.info("🪙 Fetching Messari crypto intelligence...")
        try:
            result = dispatch_api_task("messari", self.data_sources['messari'])
            if result['success']:
                crypto_data = result.get('data', {})
                logger.info(f"✅ Messari: {crypto_data.get('market_summary', {}).get('total_assets', 0)} assets")
            else:
                logger.error(f"❌ Messari fetch failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"❌ Messari fetch error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def fetch_twelve_data(self):
        """Fetch forex/equity data from Twelve Data API."""
        logger.info("📈 Fetching Twelve Data charts...")
        try:
            result = dispatch_api_task("twelve_data", self.data_sources['twelve_data'])
            if result['success']:
                chart_data = result.get('data', {})
                logger.info(f"✅ Twelve Data: {chart_data.get('market_summary', {}).get('total_symbols', 0)} symbols")
            else:
                logger.error(f"❌ Twelve Data fetch failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"❌ Twelve Data fetch error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def fetch_fear_greed_index(self):
        """Fetch Fear & Greed Index."""
        logger.info("😨 Fetching Fear & Greed Index...")
        try:
            import requests
            
            api_key = os.getenv("FEAR_GREED_API_KEY")
            if not api_key:
                raise ValueError("FEAR_GREED_API_KEY not found")
            
            url = "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/index"
            headers = {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "cnn-fear-and-greed-index.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("fear_and_greed", {}).get("score", 50)
                rating = data.get("fear_and_greed", {}).get("rating", "Neutral")
                
                result = {
                    'success': True,
                    'data': {
                        'score': score,
                        'rating': rating,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
                logger.info(f"✅ Fear & Greed: {score} ({rating})")
                return result
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Fear & Greed fetch error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def fetch_vix_data(self):
        """Fetch VIX data from FMP API."""
        logger.info("📊 Fetching VIX data...")
        try:
            import requests
            import pandas as pd
            
            api_key = os.getenv("FMP_API_KEY")
            if not api_key:
                raise ValueError("FMP_API_KEY not found")
            
            url = "https://financialmodelingprep.com/api/v3/historical-price-full/VIX"
            params = {
                "apikey": api_key,
                "from": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if "historical" in data and data["historical"]:
                    df = pd.DataFrame(data["historical"])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date').sort_index()
                    
                    result = {
                        'success': True,
                        'data': df[['close']].rename(columns={'close': 'VIX'})
                    }
                    
                    logger.info(f"✅ VIX: {len(df)} data points")
                    return result
                else:
                    raise Exception("No VIX data available")
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ VIX fetch error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def aggregate_data_sources(self):
        """Aggregate data from all sources."""
        logger.info("🔄 Aggregating data from all sources...")
        
        aggregated_data = {
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        # Fetch from all sources
        sources_to_fetch = [
            ('benzinga', self.fetch_benzinga_news),
            ('polygon', self.fetch_polygon_indices),
            ('fmp_calendar', self.fetch_fmp_calendar),
            ('messari', self.fetch_messari_intel),
            ('twelve_data', self.fetch_twelve_data),
            ('fear_greed', self.fetch_fear_greed_index),
            ('vix', self.fetch_vix_data)
        ]
        
        for source_name, fetch_func in sources_to_fetch:
            try:
                result = fetch_func()
                aggregated_data['sources'][source_name] = result
                
                if result['success']:
                    logger.info(f"✅ {source_name}: Data fetched successfully")
                else:
                    logger.warning(f"⚠️  {source_name}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ {source_name}: Fetch error - {str(e)}")
                aggregated_data['sources'][source_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Save aggregated data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"aggregated_data_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(aggregated_data, f, indent=2, default=str)
        
        logger.info(f"💾 Aggregated data saved to {filepath}")
        return aggregated_data
    
    def prepare_data_for_reporting(self, aggregated_data):
        """Prepare aggregated data for report generation."""
        logger.info("📋 Preparing data for report generation...")
        
        data_sources = {}
        
        # Extract and format data for reporting
        sources = aggregated_data.get('sources', {})
        
        # VIX data
        if sources.get('vix', {}).get('success'):
            vix_data = sources.get('vix', {}).get('data')
            if vix_data is not None:
                data_sources['vix_data'] = vix_data
        
        # Fear & Greed data
        if sources.get('fear_greed', {}).get('success'):
            fg_data = sources['fear_greed'].get('data', {})
            if fg_data and 'score' in fg_data:
                # Create a simple time series for visualization
                import pandas as pd
                fear_greed_series = pd.Series([fg_data['score']], index=[pd.Timestamp.now()])
                data_sources['fear_greed_data'] = fear_greed_series
        
        # Asset data from Twelve Data
        if sources.get('twelve_data', {}).get('success'):
            twelve_data = sources['twelve_data'].get('data', {})
            chart_data = twelve_data.get('chart_data', {})
            if chart_data:
                # Convert to DataFrame format for visualization
                asset_data = {}
                for symbol, data in chart_data.items():
                    if isinstance(data, dict) and 'current_price' in data:
                        # Create simple price series for visualization
                        import pandas as pd
                        price_series = pd.Series([data['current_price']], index=[pd.Timestamp.now()])
                        asset_data[symbol] = pd.DataFrame({'close': price_series})
                if asset_data:
                    data_sources['asset_data'] = asset_data
        
        # Economic calendar data
        if sources.get('fmp_calendar', {}).get('success'):
            fmp_data = sources['fmp_calendar'].get('data', {})
            if fmp_data:
                data_sources['calendar_data'] = fmp_data
        
        # Market data (use Polygon as primary)
        if sources.get('polygon', {}).get('success'):
            polygon_data = sources['polygon'].get('data', {})
            market_data = polygon_data.get('market_data', {})
            if market_data:
                data_sources['market_data'] = market_data
        
        logger.info(f"📊 Prepared {len(data_sources)} data sources for reporting")
        logger.info(f"   Available sources: {list(data_sources.keys())}")
        return data_sources
    
    def generate_comprehensive_report(self):
        """Generate comprehensive market intelligence report."""
        logger.info("📊 Generating comprehensive market intelligence report...")
        
        try:
            # Aggregate data from all sources
            aggregated_data = self.aggregate_data_sources()
            
            # Prepare data for reporting
            data_sources = self.prepare_data_for_reporting(aggregated_data)
            
            # Generate comprehensive report
            report = self.report_builder.build_comprehensive_report(data_sources)
            
            logger.info("✅ Comprehensive report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"❌ Report generation error: {str(e)}")
            return None
    
    def run_daily_report(self):
        """Run daily comprehensive report generation."""
        logger.info("🌅 Starting daily comprehensive report generation...")
        
        try:
            report = self.generate_comprehensive_report()
            
            if report:
                logger.info("✅ Daily report completed successfully")
                
                # Log summary
                summary = report.get('executive_summary', {})
                logger.info(f"📊 Daily Summary:")
                logger.info(f"   Market Regime: {summary.get('market_regime', 'Unknown')}")
                logger.info(f"   Primary Strategy: {summary.get('primary_strategy', 'Unknown')}")
                logger.info(f"   Risk Level: {summary.get('risk_level', 'Unknown')}")
                
                return True
            else:
                logger.error("❌ Daily report generation failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Daily report error: {str(e)}")
            return False
    
    def run_market_analysis(self):
        """Run focused market analysis."""
        logger.info("📈 Running focused market analysis...")
        
        try:
            # Fetch key market data
            polygon_result = self.fetch_polygon_indices()
            fear_greed_result = self.fetch_fear_greed_index()
            vix_result = self.fetch_vix_data()
            
            # Quick analysis
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'market_status': 'Unknown',
                'key_indicators': {},
                'recommendations': []
            }
            
            # Analyze market data
            if polygon_result['success']:
                market_summary = polygon_result['data'].get('market_summary', {})
                analysis['key_indicators']['market_sentiment'] = market_summary.get('market_sentiment', 'Unknown')
                analysis['key_indicators']['advancing'] = market_summary.get('advancing', 0)
                analysis['key_indicators']['declining'] = market_summary.get('declining', 0)
            
            if fear_greed_result['success']:
                fg_data = fear_greed_result['data']
                analysis['key_indicators']['fear_greed_score'] = fg_data.get('score', 50)
                analysis['key_indicators']['fear_greed_rating'] = fg_data.get('rating', 'Neutral')
            
            if vix_result['success']:
                vix_data = vix_result['data']
                current_vix = vix_data['VIX'].iloc[-1] if len(vix_data) > 0 else 20
                analysis['key_indicators']['vix_level'] = current_vix
                
                if current_vix > 30:
                    analysis['recommendations'].append('High VIX - Consider defensive positioning')
                elif current_vix < 15:
                    analysis['recommendations'].append('Low VIX - Watch for complacency')
            
            # Determine overall market status
            if analysis['key_indicators'].get('market_sentiment') == 'Bullish':
                analysis['market_status'] = 'Bullish'
            elif analysis['key_indicators'].get('market_sentiment') == 'Bearish':
                analysis['market_status'] = 'Bearish'
            else:
                analysis['market_status'] = 'Neutral'
            
            logger.info(f"📊 Market Analysis Complete:")
            logger.info(f"   Status: {analysis['market_status']}")
            logger.info(f"   VIX: {analysis['key_indicators'].get('vix_level', 'N/A')}")
            logger.info(f"   Fear & Greed: {analysis['key_indicators'].get('fear_greed_score', 'N/A')}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Market analysis error: {str(e)}")
            return None

def setup_scheduler():
    """Setup the job scheduler."""
    logger.info("⏰ Setting up job scheduler...")
    
    # Create MacroIntel instance
    macrointel = EnhancedMacroIntel()
    
    # Schedule jobs
    schedule.every().day.at("06:00").do(macrointel.run_daily_report)  # Morning report
    schedule.every().day.at("18:00").do(macrointel.run_daily_report)  # Evening report
    schedule.every().hour.do(macrointel.run_market_analysis)          # Hourly market check
    
    logger.info("✅ Scheduler setup complete")
    logger.info("   📅 Daily reports: 06:00 and 18:00")
    logger.info("   📈 Market analysis: Every hour")
    
    return macrointel

def run_scheduler():
    """Run the job scheduler."""
    logger.info("🚀 Starting Enhanced MacroIntel Scheduler...")
    
    macrointel = setup_scheduler()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("⏹️  Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {str(e)}")

def test_system():
    """Test the enhanced system functionality."""
    logger.info("🧪 Testing Enhanced MacroIntel System...")
    
    macrointel = EnhancedMacroIntel()
    
    # Test individual components
    logger.info("Testing individual data sources...")
    
    # Test Benzinga
    benzinga_result = macrointel.fetch_benzinga_news()
    logger.info(f"Benzinga: {'✅ PASS' if benzinga_result['success'] else '❌ FAIL'}")
    
    # Test Polygon
    polygon_result = macrointel.fetch_polygon_indices()
    logger.info(f"Polygon: {'✅ PASS' if polygon_result['success'] else '❌ FAIL'}")
    
    # Test FMP Calendar
    fmp_result = macrointel.fetch_fmp_calendar()
    logger.info(f"FMP Calendar: {'✅ PASS' if fmp_result['success'] else '❌ FAIL'}")
    
    # Test Messari
    messari_result = macrointel.fetch_messari_intel()
    logger.info(f"Messari: {'✅ PASS' if messari_result['success'] else '❌ FAIL'}")
    
    # Test Twelve Data
    twelve_result = macrointel.fetch_twelve_data()
    logger.info(f"Twelve Data: {'✅ PASS' if twelve_result['success'] else '❌ FAIL'}")
    
    # Test Fear & Greed
    fg_result = macrointel.fetch_fear_greed_index()
    logger.info(f"Fear & Greed: {'✅ PASS' if fg_result['success'] else '❌ FAIL'}")
    
    # Test VIX
    vix_result = macrointel.fetch_vix_data()
    logger.info(f"VIX: {'✅ PASS' if vix_result['success'] else '❌ FAIL'}")
    
    # Test market analysis
    logger.info("Testing market analysis...")
    analysis_result = macrointel.run_market_analysis()
    if analysis_result:
        logger.info("✅ Market analysis test PASSED")
    else:
        logger.info("❌ Market analysis test FAILED")
    
    logger.info("🧪 System testing completed")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced MacroIntel System")
    parser.add_argument("--test", action="store_true", help="Run system tests")
    parser.add_argument("--report", action="store_true", help="Generate single comprehensive report")
    parser.add_argument("--scheduler", action="store_true", help="Run the job scheduler")
    parser.add_argument("--analysis", action="store_true", help="Run market analysis")
    
    args = parser.parse_args()
    
    if args.test:
        test_system()
    elif args.report:
        macrointel = EnhancedMacroIntel()
        macrointel.generate_comprehensive_report()
    elif args.analysis:
        macrointel = EnhancedMacroIntel()
        macrointel.run_market_analysis()
    elif args.scheduler:
        run_scheduler()
    else:
        # Default: run scheduler
        run_scheduler()

if __name__ == "__main__":
    main() 