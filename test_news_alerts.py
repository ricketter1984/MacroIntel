#!/usr/bin/env python3
"""
Test script for MacroIntel News Alerts System
Verifies functionality and simulates alerts
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported."""
    
    print("🧪 Testing News Alerts Module Imports")
    print("=" * 50)
    
    # Test core dependencies
    try:
        import tkinter as tk
        print("✅ tkinter (GUI)")
    except ImportError:
        print("⚠️ tkinter (GUI) - GUI features disabled")
    
    try:
        from plyer import notification
        print("✅ plyer (notifications)")
    except ImportError:
        print("❌ plyer (notifications) - install with: pip install plyer")
        return False
    
    # Test news alerts module
    try:
        from news_alerts import NewsAlertsEngine, NewsAlertsGUI
        print("✅ news_alerts module")
    except ImportError as e:
        print(f"❌ news_alerts module: {e}")
        return False
    
    # Test MacroIntel integration
    try:
        from utils.api_clients import fetch_all_news
        print("✅ MacroIntel news integration")
    except ImportError:
        print("⚠️ MacroIntel integration - limited functionality")
    
    return True

def test_engine_initialization():
    """Test the NewsAlertsEngine initialization."""
    
    print("\n🔧 Testing Engine Initialization")
    print("=" * 40)
    
    try:
        from news_alerts import NewsAlertsEngine
        
        # Initialize with test config
        test_config = "test_config/news_alerts.json"
        os.makedirs("test_config", exist_ok=True)
        
        engine = NewsAlertsEngine(config_file=test_config)
        print("✅ Engine initialized successfully")
        
        # Test configuration
        print(f"📝 Config file: {engine.config_file}")
        print(f"📊 Alerts log: {engine.alerts_log}")
        print(f"🔔 Enabled: {engine.is_enabled()}")
        print(f"⏰ Check interval: {engine.config['check_interval']} seconds")
        print(f"🎯 Keywords categories: {len(engine.config['strategy_keywords'])}")
        
        # Test methods
        print("\n🧪 Testing Engine Methods:")
        
        # Test headline analysis
        test_headlines = [
            "Fed Raises Interest Rates by 0.25%",
            "Bitcoin Surges Above $50,000 on ETF News", 
            "Oil Prices Spike Amid OPEC Production Cuts",
            "Inflation Data Shows Cooling Trend",
            "Tech Stocks Rally on AI Optimism"
        ]
        
        for headline in test_headlines:
            analysis = engine.analyze_headline(headline)
            if analysis["is_relevant"]:
                categories = ", ".join(analysis["categories"])
                priority = analysis["max_priority"]
                print(f"  🎯 {priority.upper()} - {categories}: {headline}")
            else:
                print(f"  ⚪ Not relevant: {headline}")
        
        return engine
        
    except Exception as e:
        print(f"❌ Engine initialization failed: {e}")
        return None

def test_notification_system(engine):
    """Test the notification system."""
    
    print("\n🔔 Testing Notification System")
    print("=" * 35)
    
    try:
        from plyer import notification
        
        # Test basic notification
        print("📱 Sending test notification...")
        notification.notify(
            title="📰 MacroIntel Test Alert",
            message="This is a test notification from the news alerts system",
            app_name="MacroIntel",
            timeout=3
        )
        print("✅ Test notification sent")
        
        # Test alert processing with sample article
        sample_article = {
            "title": "Federal Reserve Announces Emergency Rate Cut",
            "summary": "The Federal Reserve announced an emergency 0.75% rate cut to combat economic uncertainty",
            "source": "test",
            "url": "https://example.com/test",
            "tone": "bearish"
        }
        
        analysis = engine.analyze_headline(
            sample_article["title"], 
            sample_article["summary"]
        )
        
        if analysis["is_relevant"]:
            print(f"📊 Sample analysis: {analysis['max_priority']} priority")
            print(f"🏷️ Categories: {', '.join(analysis['categories'])}")
            
            # Test should_notify logic
            should_notify = engine.should_notify(analysis["categories"])
            print(f"🔔 Should notify: {should_notify}")
            
            if should_notify:
                # Send actual alert
                notified = engine.send_notification(
                    sample_article["title"], 
                    analysis, 
                    sample_article
                )
                print(f"📤 Alert sent: {notified}")
                
                # Log the alert
                engine.log_alert(
                    sample_article["title"],
                    analysis,
                    sample_article,
                    notified
                )
                print("📝 Alert logged successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification test failed: {e}")
        return False

def test_configuration_management(engine):
    """Test configuration loading and saving."""
    
    print("\n⚙️ Testing Configuration Management")
    print("=" * 40)
    
    try:
        # Test configuration access
        original_enabled = engine.is_enabled()
        print(f"📊 Original state: {'Enabled' if original_enabled else 'Disabled'}")
        
        # Test toggle
        engine.toggle_alerts(not original_enabled)
        new_state = engine.is_enabled()
        print(f"🔄 After toggle: {'Enabled' if new_state else 'Disabled'}")
        
        # Restore original state
        engine.toggle_alerts(original_enabled)
        restored_state = engine.is_enabled()
        print(f"↩️ Restored state: {'Enabled' if restored_state else 'Disabled'}")
        
        # Test keyword management
        keywords = engine.config["strategy_keywords"]
        print(f"\n📋 Strategy Keywords ({len(keywords)} categories):")
        
        for category, config in keywords.items():
            enabled = "✅" if config.get("enabled", True) else "❌"
            priority = config.get("priority", "low")
            term_count = len(config.get("terms", []))
            print(f"  {enabled} {category.title()}: {priority} priority, {term_count} terms")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_alerts_logging(engine):
    """Test the alerts logging functionality."""
    
    print("\n📝 Testing Alerts Logging")
    print("=" * 30)
    
    try:
        # Create sample alerts
        sample_alerts = [
            {
                "title": "Fed Meeting Results in Rate Hike",
                "summary": "Federal Reserve increases rates by 0.25%",
                "source": "test_fed",
                "categories": ["fed"],
                "priority": "high"
            },
            {
                "title": "Bitcoin Breaks New All-Time High",
                "summary": "Bitcoin surges past $70,000 on institutional demand",
                "source": "test_crypto", 
                "categories": ["bitcoin"],
                "priority": "medium"
            },
            {
                "title": "Oil Prices Surge on Supply Concerns",
                "summary": "Crude oil rises 5% on geopolitical tensions",
                "source": "test_oil",
                "categories": ["oil", "geopolitical"],
                "priority": "medium"
            }
        ]
        
        # Process sample alerts
        for alert_data in sample_alerts:
            analysis = {
                "categories": alert_data["categories"],
                "max_priority": alert_data["priority"],
                "matches": [{"category": cat, "term": "test", "priority": alert_data["priority"]} for cat in alert_data["categories"]]
            }
            
            engine.log_alert(
                alert_data["title"],
                analysis,
                alert_data,
                notified=True
            )
        
        print(f"✅ Logged {len(sample_alerts)} sample alerts")
        
        # Test alerts summary
        summary = engine.get_alerts_summary(hours=24)
        print(f"📊 Alerts summary:")
        print(f"  📈 Total: {summary['total']}")
        print(f"  🔔 Notifications: {summary['notifications_sent']}")
        
        if summary.get("by_priority"):
            print(f"  📊 By priority: {summary['by_priority']}")
        
        if summary.get("by_category"):
            print(f"  🏷️ By category: {summary['by_category']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def test_cli_interface():
    """Test the CLI interface."""
    
    print("\n💻 Testing CLI Interface")
    print("=" * 25)
    
    try:
        # Test CLI commands (simulate)
        cli_commands = [
            "--status",
            "--summary 24",
            "--test"
        ]
        
        print("📋 Available CLI commands:")
        for cmd in cli_commands:
            print(f"  python news_alerts.py {cmd}")
        
        # Test actual status command
        from news_alerts import NewsAlertsEngine
        engine = NewsAlertsEngine(config_file="test_config/news_alerts.json")
        
        print(f"\n📊 Current Status:")
        print(f"  Enabled: {engine.is_enabled()}")
        print(f"  Running: {engine.running}")
        print(f"  Check interval: {engine.config['check_interval']}s")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files."""
    
    test_files = [
        "test_config/news_alerts.json",
        "test_config",
        "logs/news_alerts.log"
    ]
    
    for file_path in test_files:
        try:
            path = Path(file_path)
            if path.is_file():
                path.unlink()
                print(f"🗑️ Cleaned up file: {file_path}")
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
                print(f"🗑️ Cleaned up directory: {file_path}")
        except Exception as e:
            print(f"⚠️ Could not clean up {file_path}: {e}")

def show_demo_instructions():
    """Show instructions for running the news alerts system."""
    
    print("\n🚀 News Alerts Demo Instructions")
    print("=" * 40)
    
    print("1. Start GUI Interface:")
    print("   python news_alerts.py")
    print()
    print("2. Start CLI Monitoring:")
    print("   python news_alerts.py --monitor")
    print()
    print("3. Check Status:")
    print("   python news_alerts.py --status")
    print()
    print("4. Enable/Disable Alerts:")
    print("   python news_alerts.py --enable")
    print("   python news_alerts.py --disable")
    print()
    print("5. Test Notification:")
    print("   python news_alerts.py --test")
    print()
    print("6. View Recent Alerts:")
    print("   python news_alerts.py --summary 24")
    print()
    print("🔧 Configuration:")
    print("• Edit config/news_alerts.json to customize keywords")
    print("• Check logs/alerts_log.json for alert history")
    print("• Ensure plyer is installed for notifications")
    print()
    print("📊 Integration:")
    print("• Works with existing MacroIntel news sources")
    print("• Can be integrated into dashboard_app.py")
    print("• Supports background monitoring")

def main():
    """Main test execution."""
    
    print("🔔 MacroIntel News Alerts - System Test")
    print("=" * 60)
    
    test_results = []
    
    try:
        # Test imports
        imports_ok = test_imports()
        test_results.append(("Imports", imports_ok))
        
        if not imports_ok:
            print("\n❌ Critical dependencies missing - cannot continue")
            return
        
        # Test engine
        engine = test_engine_initialization()
        test_results.append(("Engine Init", engine is not None))
        
        if engine:
            # Test notifications
            notifications_ok = test_notification_system(engine)
            test_results.append(("Notifications", notifications_ok))
            
            # Test configuration
            config_ok = test_configuration_management(engine)
            test_results.append(("Configuration", config_ok))
            
            # Test logging
            logging_ok = test_alerts_logging(engine)
            test_results.append(("Logging", logging_ok))
        
        # Test CLI
        cli_ok = test_cli_interface()
        test_results.append(("CLI Interface", cli_ok))
        
        # Show results
        print("\n" + "=" * 60)
        print("🎯 Test Results Summary:")
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name}: {status}")
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        if passed == total:
            print(f"\n✅ All {total} tests passed! News alerts system is ready.")
            show_demo_instructions()
        else:
            print(f"\n⚠️ {passed}/{total} tests passed. Check output for issues.")
    
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
    finally:
        cleanup_test_files()
        print("\n🏁 Test complete")

if __name__ == "__main__":
    main() 