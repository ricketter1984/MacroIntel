#!/usr/bin/env python3
"""
Enhanced MacroIntel System

This is the main entry point for the MacroIntel system, now with enhanced capabilities:
- Multi-source data integration (Polygon, FMP, Messari, Twelve Data, Fear & Greed, CME, Quiver)
- Enhanced visualizations (VIX analysis, multi-asset comparison, economic calendar impact)
- Strategy recommendations based on playbook logic
- Comprehensive risk assessment
- Automated report generation
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    import pytz
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

# Fix Unicode encoding issues on Windows
if sys.platform == "win32":
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

# Import local modules
from api_dispatcher import dispatch_api_task
from core.enhanced_report_builder import EnhancedReportBuilder
from core.enhanced_visualizations import EnhancedVisualizations
from agents.quiver_agent import run_quiver_pipeline, QuiverAgent
from utils.cme_scraper import fetch_cme_data

# Import agents when needed to avoid circular import issues
# from agents.ticker_news_agent import TickerNewsAgent (imported at runtime)
# from agents.chart_generator_agent import ChartGeneratorAgent (imported at runtime)

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
            'polygon': 'scripts/fetch_polygon_indices.py',
            'fmp_calendar': 'scripts/fetch_fmp_calendar.py',
            'messari': 'scripts/fetch_messari_intel.py',
            'twelve_data': 'scripts/fetch_twelve_data.py'
        }
        
        logger.info("🚀 Enhanced MacroIntel System initialized")
    
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
        """Fetch VIX data using the dedicated FMP API function."""
        logger.info("📊 Fetching VIX data from FMP API...")
        
        try:
            from utils.api_clients import fetch_vix_data
            
            # Use the dedicated VIX fetching function
            vix_df = fetch_vix_data(days=365)
            
            if vix_df is not None and not vix_df.empty:
                result = {
                    'success': True,
                    'data': vix_df,
                    'current_vix': float(vix_df['VIX'].iloc[-1]),
                    'avg_vix': float(vix_df['VIX'].mean()),
                    'vix_range': {
                        'min': float(vix_df['VIX'].min()),
                        'max': float(vix_df['VIX'].max())
                    }
                }
                
                logger.info(f"✅ VIX: {len(vix_df)} data points (current: {result['current_vix']:.2f})")
                return result
            else:
                logger.warning("⚠️ No VIX data returned from FMP API")
                return {
                    'success': False,
                    'error': 'No VIX data available from FMP API'
                }
                
        except Exception as e:
            logger.error(f"❌ Error fetching VIX data: {e}")
            return {
                'success': False,
                'error': f'VIX fetch failed: {str(e)}'
            }
    
    def aggregate_data_sources(self):
        """Aggregate data from all sources."""
        logger.info("🔄 Aggregating data from all sources...")
        
        aggregated_data = {
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        # Fetch from all sources
        sources_to_fetch = [
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
                if asset_data and len(asset_data) > 0:
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
            if market_data and len(market_data) > 0:
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
            logger.error(f"Report generation error: {str(e)}")
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
                if hasattr(vix_data, 'empty') and not vix_data.empty:
                    current_vix = vix_data['VIX'].iloc[-1] if 'VIX' in vix_data else 20
                else:
                    current_vix = 20
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
    
    def run_swarm_pipeline(self, model="claude"):
        """Run the complete MacroIntel swarm pipeline."""
        logger.info(f"🤖 Starting MacroIntel Swarm Pipeline with {model} model...")
        
        try:
            # Import the swarm orchestrator
            from agents.swarm_orchestrator import MacroIntelSwarm
            
            # Create swarm instance with specified model and execute
            swarm = MacroIntelSwarm(model=model)
            results = swarm.execute_swarm()
            
            if results.get("status") == "success":
                summary = results.get("summary", {})
                logger.info("✅ Swarm Pipeline Completed Successfully")
                logger.info(f"   📰 Articles Processed: {summary.get('articles_processed', 0)}")
                logger.info(f"   📈 Charts Generated: {summary.get('charts_generated', 0)}")
                logger.info(f"   📘 Market Regime: {summary.get('market_regime', 'Unknown')}")
                logger.info(f"   🎯 Strategies Selected: {summary.get('strategies_selected', 0)}")
                logger.info(f"   📧 Email Sent: {'✅ Yes' if summary.get('email_sent', False) else '❌ No'}")
                logger.info(f"   👥 Recipients: {summary.get('recipients_count', 0)}")
                logger.info(f"   ⏱️ Execution Time: {results.get('execution_time', 'Unknown')}")
                
                return True
            else:
                logger.error(f"❌ Swarm Pipeline Failed: {results.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Swarm Pipeline Error: {str(e)}")
            return False

def setup_scheduler():
    """Setup the APScheduler with swarm pipeline jobs."""
    if not SCHEDULER_AVAILABLE:
        logger.error("❌ APScheduler not available")
        return None, None
    
    logger.info("⏰ Setting up APScheduler...")
    
    # Create MacroIntel instance
    macrointel = EnhancedMacroIntel()
    
    # Create background scheduler
    scheduler = BackgroundScheduler()
    
    # Set timezone to Eastern Time
    eastern_tz = pytz.timezone('US/Eastern')
    
    # Schedule swarm pipeline at 07:30 ET (morning)
    scheduler.add_job(
        func=macrointel.run_swarm_pipeline,
        trigger=CronTrigger(hour=7, minute=30, timezone=eastern_tz),
        id='morning_swarm',
        name='Morning Swarm Pipeline (07:30 ET)',
        replace_existing=True
    )
    
    # Schedule swarm pipeline at 15:45 ET (10 min before close)
    scheduler.add_job(
        func=macrointel.run_swarm_pipeline,
        trigger=CronTrigger(hour=15, minute=45, timezone=eastern_tz),
        id='afternoon_swarm',
        name='Afternoon Swarm Pipeline (15:45 ET)',
        replace_existing=True
    )
    
    # Schedule daily report at 06:00 ET
    scheduler.add_job(
        func=macrointel.run_daily_report,
        trigger=CronTrigger(hour=6, minute=0, timezone=eastern_tz),
        id='daily_report',
        name='Daily Report (06:00 ET)',
        replace_existing=True
    )
    
    # Schedule market analysis every hour
    scheduler.add_job(
        func=macrointel.run_market_analysis,
        trigger=CronTrigger(minute=0, timezone=eastern_tz),
        id='hourly_analysis',
        name='Hourly Market Analysis',
        replace_existing=True
    )
    
    logger.info("✅ APScheduler setup complete")
    logger.info("   🤖 Swarm Pipeline: 07:30 ET and 15:45 ET")
    logger.info("   📅 Daily Report: 06:00 ET")
    logger.info("   📈 Market Analysis: Every hour")
    
    return scheduler, macrointel

def run_scheduler():
    """Run the APScheduler in background."""
    if not SCHEDULER_AVAILABLE:
        logger.error("❌ APScheduler not available. Install with: pip install apscheduler")
        print("❌ Scheduler functionality requires APScheduler. Install with: pip install apscheduler")
        return
    
    logger.info("🚀 Starting Enhanced MacroIntel APScheduler...")
    
    scheduler, macrointel = setup_scheduler()
    
    try:
        # Start the scheduler
        scheduler.start()
        logger.info("✅ APScheduler started successfully")
        logger.info("🔄 Scheduler running in background...")
        logger.info("⏹️  Press Ctrl+C to stop")
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Stopping scheduler...")
        scheduler.shutdown()
        logger.info("✅ Scheduler stopped gracefully")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {str(e)}")
        scheduler.shutdown()

def test_system():
    """Test the enhanced system functionality."""
    logger.info("🧪 Testing Enhanced MacroIntel System...")
    
    macrointel = EnhancedMacroIntel()
    
    # Test individual components
    logger.info("Testing individual data sources...")
    
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

    parser = argparse.ArgumentParser(description="Run MacroIntel CLI Pipeline")

    parser.add_argument('--watchlist-news', type=str, help="Comma-separated list of tickers to fetch news for")
    parser.add_argument('--send', action='store_true', help="Send email after report generation")
    parser.add_argument('--include-quiver', action='store_true', help="Include Quiver API data in the report")
    parser.add_argument('--schedule', action='store_true', help="Run scheduled jobs using APScheduler")
    parser.add_argument('--cme', action='store_true', help="Run CME forex futures module only (for standalone testing)")
    parser.add_argument('--test', action='store_true', help="Run a minimal email test with mock content")
    parser.add_argument('--vanna', action='store_true', help="Run VannaAgent to generate insights")
    parser.add_argument('--swarm', action='store_true', help="Run the MacroIntel swarm pipeline")
    parser.add_argument('--model', type=str, default="claude", choices=["claude", "perplexity", "mistral"], 
                       help="AI model to use for summarization (default: claude)")

    args = parser.parse_args()

    # Add the control logic to route commands
    if args.watchlist_news:
        from agents.ticker_news_agent import TickerNewsAgent
        tickers = [ticker.strip() for ticker in args.watchlist_news.split(",")]
        agent = TickerNewsAgent(include_quiver=args.include_quiver)
        result = agent.run(tickers=tickers, model=args.model)
        if result.get('status') == 'success':
            print(f"📄 Report saved to: {result.get('markdown_file')}")
            print(f"✅ Processed {result.get('tickers_processed')} tickers, found {result.get('total_articles')} articles")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        if args.send:
            from core.email_report import send_daily_report
            # Extract markdown file path from result
            markdown_path = result.get('markdown_file')
            if markdown_path:
                # Read markdown file and convert to HTML for email
                with open(markdown_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                # Simple HTML conversion (basic)
                html_content = f"<html><body><pre>{markdown_content}</pre></body></html>"
                send_daily_report(html_content)
            else:
                logger.error("❌ No markdown file found in result")
    elif args.schedule:
        from macrointel_automation.scheduler_jobs import run_scheduler
        run_scheduler()
    elif args.cme:
        from fetch_forex_cme import run_cme_forex_pipeline
        run_cme_forex_pipeline()
    elif args.swarm:
        print(f"🤖 Running MacroIntel Swarm Pipeline with {args.model} model...")
        macrointel = EnhancedMacroIntel()
        success = macrointel.run_swarm_pipeline(model=args.model)
        if success:
            print("✅ Swarm pipeline completed successfully")
        else:
            print("❌ Swarm pipeline failed")
    elif args.test:
        from core.email_report import send_test_email
        send_test_email()
    else:
        print("❗ No valid arguments provided. Use --help to see available options.")

if __name__ == "__main__":
    main() 