#!/usr/bin/env python3
"""
MacroIntel News Alerts System
Monitors news feeds for high-impact headlines and triggers desktop notifications
"""

import os
import sys
import json
import time
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import argparse
import signal

# Configure stdout encoding for Unicode support
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Desktop notifications
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

# MacroIntel modules with improved error handling
MACROINTEL_AVAILABLE = False
fetch_all_news = None
SummarizerAgent = None

try:
    # Try different import paths for MacroIntel modules
    try:
        from utils.api_clients import fetch_all_news
        logging.info("Successfully imported fetch_all_news from utils.api_clients")
    except ImportError:
        try:
            from scripts.fetch_all_news import fetch_all_news
            logging.info("Successfully imported fetch_all_news from scripts")
        except ImportError:
            logging.warning("Could not import fetch_all_news from any location")
            
    try:
        from agents.summarizer_agent import SummarizerAgent
        logging.info("Successfully imported SummarizerAgent from agents")
    except ImportError:
        import logging
        logging.warning("⚠️ Could not import SummarizerAgent — using fallback.")

        class SummarizerAgent:
            def summarize(self, article):
                return {
                    "summary": "No AI summary available.",
                    "sentiment": "neutral",
                    "tags": []
                }
            
            def run(self):
                return {
                    "articles": [],
                    "summary": "No AI summary available.",
                    "sentiment": "neutral",
                    "tags": []
                }
    
    # Check if we have at least one working module
    if fetch_all_news is not None:
        MACROINTEL_AVAILABLE = True
        logging.info("MacroIntel modules partially available")
    else:
        logging.warning("No MacroIntel modules available")
        
except Exception as e:
    logging.error(f"Error importing MacroIntel modules: {e}")
    MACROINTEL_AVAILABLE = False

class NewsAlertsEngine:
    """Core engine for monitoring news and triggering alerts."""
    
    def __init__(self, config_file="config/news_alerts.json"):
        """Initialize the news alerts engine."""
        
        self.config_file = Path(config_file)
        self.alerts_log = Path("logs/alerts_log.json")
        self.running = False
        self.monitor_thread = None
        
        # Default configuration
        self.config = {
            "enabled": True,
            "check_interval": 300,  # 5 minutes
            "notification_cooldown": 900,  # 15 minutes per keyword
            "max_notifications_per_hour": 10,
            "strategy_keywords": {
                "fed": {
                    "terms": ["federal reserve", "fed", "jerome powell", "fomc", "federal open market", "fed meeting", "fed decision", "fed rate"],
                    "priority": "high",
                    "enabled": True
                },
                "inflation": {
                    "terms": ["inflation", "cpi", "consumer price index", "pce", "deflation", "price stability", "inflationary"],
                    "priority": "high", 
                    "enabled": True
                },
                "oil": {
                    "terms": ["oil price", "crude oil", "opec", "brent", "wti", "petroleum", "oil production", "energy crisis"],
                    "priority": "medium",
                    "enabled": True
                },
                "bitcoin": {
                    "terms": ["bitcoin", "btc", "cryptocurrency", "crypto", "blockchain", "bitcoin price", "bitcoin etf"],
                    "priority": "medium",
                    "enabled": True
                },
                "geopolitical": {
                    "terms": ["war", "conflict", "sanctions", "trade war", "china trade", "tariffs", "russia", "ukraine"],
                    "priority": "high",
                    "enabled": True
                },
                "market_stress": {
                    "terms": ["market crash", "recession", "bear market", "volatility spike", "vix", "market selloff", "panic"],
                    "priority": "critical",
                    "enabled": True
                }
            }
        }
        
        # Setup logging first
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/news_alerts.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        self.alerts_log.parent.mkdir(exist_ok=True)
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Load existing configuration
        self.load_config()
        
        # Tracking variables
        self.last_notifications = {}  # keyword -> timestamp
        self.notification_count = 0
        self.last_hour_reset = time.time()
        self.processed_articles = set()  # To avoid duplicate notifications

    def load_config(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    stored_config = json.load(f)
                    self.config.update(stored_config)
                self.logger.info(f"SUCCESS: Loaded configuration from {self.config_file}")
            else:
                self.save_config()
                self.logger.info(f"CONFIG: Created default configuration at {self.config_file}")
        except Exception as e:
            self.logger.error(f"ERROR: Error loading config: {e}")

    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"SAVE: Saved configuration to {self.config_file}")
        except Exception as e:
            self.logger.error(f"ERROR: Error saving config: {e}")

    def is_enabled(self) -> bool:
        """Check if alerts are enabled."""
        return self.config.get("enabled", False)

    def toggle_alerts(self, enabled: bool):
        """Enable or disable alerts."""
        self.config["enabled"] = enabled
        self.save_config()
        status = "enabled" if enabled else "disabled"
        self.logger.info(f"ALERT: News alerts {status}")

    def analyze_headline(self, headline: str, summary: str = "") -> Dict[str, Any]:
        """Analyze a headline for strategy-relevant keywords."""
        
        combined_text = f"{headline} {summary}".lower()
        matches = []
        max_priority = "low"
        
        for category, config in self.config["strategy_keywords"].items():
            if not config.get("enabled", True):
                continue
                
            terms = config.get("terms", [])
            priority = config.get("priority", "low")
            
            for term in terms:
                if term.lower() in combined_text:
                    matches.append({
                        "category": category,
                        "term": term,
                        "priority": priority
                    })
                    
                    # Update max priority
                    if priority == "critical":
                        max_priority = "critical"
                    elif priority == "high" and max_priority != "critical":
                        max_priority = "high"
                    elif priority == "medium" and max_priority not in ["critical", "high"]:
                        max_priority = "medium"
                    
                    break  # Only one match per category
        
        return {
            "matches": matches,
            "max_priority": max_priority,
            "is_relevant": len(matches) > 0,
            "categories": [m["category"] for m in matches]
        }

    def should_notify(self, categories: List[str]) -> bool:
        """Check if we should send a notification based on cooldown and limits."""
        
        current_time = time.time()
        
        # Reset hourly notification count
        if current_time - self.last_hour_reset > 3600:
            self.notification_count = 0
            self.last_hour_reset = current_time
        
        # Check hourly limit
        if self.notification_count >= self.config.get("max_notifications_per_hour", 10):
            return False
        
        # Check cooldown for any of the categories
        cooldown = self.config.get("notification_cooldown", 900)
        for category in categories:
            last_notification = self.last_notifications.get(category, 0)
            if current_time - last_notification < cooldown:
                return False
        
        return True

    def send_notification(self, headline: str, analysis: Dict[str, Any], article: Dict[str, Any]):
        """Send desktop notification for relevant news."""
        
        if not NOTIFICATIONS_AVAILABLE:
            self.logger.warning("⚠️ Notifications not available - plyer not installed")
            return False
        
        try:
            # Format notification content
            categories = ", ".join(analysis["categories"]).title()
            priority = analysis["max_priority"].upper()
            
            title = f"📰 MacroIntel Alert ({priority})"
            message = f"{categories}: {headline[:100]}{'...' if len(headline) > 100 else ''}"
            
            # Priority-based timeout
            timeout_map = {"critical": 15, "high": 10, "medium": 7, "low": 5}
            timeout = timeout_map.get(analysis["max_priority"], 5)
            
            # Send notification
            notification.notify(
                title=title,
                message=message,
                app_name="MacroIntel",
                timeout=timeout
            )
            
            # Update tracking
            current_time = time.time()
            for category in analysis["categories"]:
                self.last_notifications[category] = current_time
            
            self.notification_count += 1
            
            self.logger.info(f"NOTIFY: Sent notification: {priority} - {categories}")
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error sending notification: {e}")
            return False

    def log_alert(self, headline: str, analysis: Dict[str, Any], article: Dict[str, Any], notified: bool):
        """Log alert to JSON file."""
        
        try:
            # Load existing alerts
            alerts = []
            if self.alerts_log.exists():
                try:
                    with open(self.alerts_log, 'r') as f:
                        alerts = json.load(f)
                except json.JSONDecodeError:
                    alerts = []
            
            # Create alert entry
            alert_entry = {
                "timestamp": datetime.now().isoformat(),
                "headline": headline,
                "summary": article.get("summary", ""),
                "source": article.get("source", "unknown"),
                "url": article.get("url", ""),
                "categories": analysis["categories"],
                "priority": analysis["max_priority"],
                "matches": analysis["matches"],
                "notified": notified,
                "sentiment": article.get("tone", "neutral")
            }
            
            # Add to alerts list
            alerts.append(alert_entry)
            
            # Keep only last 1000 alerts
            if len(alerts) > 1000:
                alerts = alerts[-1000:]
            
            # Save to file
            with open(self.alerts_log, 'w') as f:
                json.dump(alerts, f, indent=2)
            
            self.logger.info(f"LOG: Logged alert: {analysis['max_priority']} - {headline[:50]}...")
            
        except Exception as e:
            self.logger.error(f"ERROR: Error logging alert: {e}")

    def fetch_news_feeds(self) -> List[Dict[str, Any]]:
        """Fetch news from available sources."""
        
        articles = []
        
        try:
            if MACROINTEL_AVAILABLE and fetch_all_news is not None:
                # Use MacroIntel's news fetching
                self.logger.info("NEWS: Fetching news from MacroIntel sources...")
                articles = fetch_all_news()
                self.logger.info(f"SUCCESS: Fetched {len(articles)} articles from MacroIntel")
            else:
                self.logger.warning("WARNING: MacroIntel modules not available")
        
        except Exception as e:
            self.logger.error(f"ERROR: Error fetching news: {e}")
        
        return articles

    def process_articles(self, articles: List[Dict[str, Any]]):
        """Process articles for relevant content and send alerts."""
        
        relevant_count = 0
        notification_count = 0
        
        for article in articles:
            try:
                headline = article.get("title", "")
                summary = article.get("summary", "")
                
                # Skip if we've already processed this article
                article_id = f"{headline[:50]}_{article.get('source', 'unknown')}"
                if article_id in self.processed_articles:
                    continue
                
                self.processed_articles.add(article_id)
                
                # Clean up old processed articles (keep last 1000)
                if len(self.processed_articles) > 1000:
                    old_articles = list(self.processed_articles)[:500]
                    for old_id in old_articles:
                        self.processed_articles.discard(old_id)
                
                # Analyze headline
                analysis = self.analyze_headline(headline, summary)
                
                if analysis["is_relevant"]:
                    relevant_count += 1
                    
                    # Check if we should notify
                    should_notify = self.should_notify(analysis["categories"])
                    notified = False
                    
                    if should_notify:
                        notified = self.send_notification(headline, analysis, article)
                        if notified:
                            notification_count += 1
                    
                    # Log the alert
                    self.log_alert(headline, analysis, article, notified)
                    
                    self.logger.info(
                        f"RELEVANT: {analysis['max_priority']} - {', '.join(analysis['categories'])} - "
                        f"{'NOTIFIED' if notified else 'SILENT'} - {headline[:50]}..."
                    )
            
            except Exception as e:
                self.logger.error(f"ERROR: Error processing article: {e}")
                continue
        
        if relevant_count > 0:
            self.logger.info(f"SUMMARY: Processed {len(articles)} articles: {relevant_count} relevant, {notification_count} notifications sent")

    def monitor_loop(self):
        """Main monitoring loop."""
        
        self.logger.info("START: Starting news monitoring loop...")
        
        while self.running:
            try:
                if self.is_enabled():
                    # Fetch and process news
                    articles = self.fetch_news_feeds()
                    if articles:
                        self.process_articles(articles)
                    else:
                        self.logger.warning("WARNING: No articles fetched")
                else:
                    self.logger.debug("SKIP: News alerts disabled, skipping check")
                
                # Sleep for configured interval
                interval = self.config.get("check_interval", 300)
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"ERROR: Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def start_monitoring(self):
        """Start the news monitoring in a background thread."""
        
        if self.running:
            self.logger.warning("WARNING: Monitoring already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("SUCCESS: News monitoring started")

    def stop_monitoring(self):
        """Stop the news monitoring."""
        
        if not self.running:
            self.logger.warning("WARNING: Monitoring not running")
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("STOP: News monitoring stopped")

    def get_alerts_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of recent alerts."""
        
        try:
            if not self.alerts_log.exists():
                return {"total": 0, "by_priority": {}, "by_category": {}}
            
            with open(self.alerts_log, 'r') as f:
                alerts = json.load(f)
            
            # Filter recent alerts
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_alerts = [
                alert for alert in alerts
                if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
            ]
            
            # Analyze alerts
            by_priority = {}
            by_category = {}
            notifications_sent = 0
            
            for alert in recent_alerts:
                # Count by priority
                priority = alert["priority"]
                by_priority[priority] = by_priority.get(priority, 0) + 1
                
                # Count by category
                for category in alert["categories"]:
                    by_category[category] = by_category.get(category, 0) + 1
                
                # Count notifications
                if alert["notified"]:
                    notifications_sent += 1
            
            return {
                "total": len(recent_alerts),
                "notifications_sent": notifications_sent,
                "by_priority": by_priority,
                "by_category": by_category,
                "recent_alerts": recent_alerts[-10:]  # Last 10 alerts
            }
            
        except Exception as e:
            self.logger.error(f"ERROR: Error getting alerts summary: {e}")
            return {"total": 0, "notifications_sent": 0, "by_priority": {}, "by_category": {}, "error": str(e)}

class NewsAlertsGUI:
    """GUI interface for managing news alerts."""
    
    def __init__(self, engine: NewsAlertsEngine):
        """Initialize the GUI."""
        
        self.engine = engine
        self.root = tk.Tk()
        self.root.title("MacroIntel News Alerts")
        self.root.geometry("600x500")
        
        # Create GUI elements
        self.create_widgets()
        self.update_status()
        
        # Start periodic updates
        self.update_gui()

    def create_widgets(self):
        """Create GUI widgets."""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Checking status...")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Controls section
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="5")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.toggle_button = ttk.Button(controls_frame, text="Toggle Alerts", command=self.toggle_alerts)
        self.toggle_button.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(controls_frame, text="Test Notification", command=self.test_notification).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(controls_frame, text="Refresh", command=self.update_status).grid(row=0, column=2)
        
        # Keywords section
        keywords_frame = ttk.LabelFrame(main_frame, text="Strategy Keywords", padding="5")
        keywords_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Keywords tree
        self.keywords_tree = ttk.Treeview(keywords_frame, columns=("priority", "enabled"), show="tree headings")
        self.keywords_tree.heading("#0", text="Category")
        self.keywords_tree.heading("priority", text="Priority")
        self.keywords_tree.heading("enabled", text="Enabled")
        
        self.keywords_tree.column("#0", width=150)
        self.keywords_tree.column("priority", width=80)
        self.keywords_tree.column("enabled", width=80)
        
        scrollbar = ttk.Scrollbar(keywords_frame, orient="vertical", command=self.keywords_tree.yview)
        self.keywords_tree.configure(yscrollcommand=scrollbar.set)
        
        self.keywords_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Recent alerts section
        alerts_frame = ttk.LabelFrame(main_frame, text="Recent Alerts", padding="5")
        alerts_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.alerts_text = tk.Text(alerts_frame, height=8, wrap=tk.WORD)
        alerts_scrollbar = ttk.Scrollbar(alerts_frame, orient="vertical", command=self.alerts_text.yview)
        self.alerts_text.configure(yscrollcommand=alerts_scrollbar.set)
        
        self.alerts_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        alerts_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=1)
        main_frame.columnconfigure(0, weight=1)
        keywords_frame.rowconfigure(0, weight=1)
        keywords_frame.columnconfigure(0, weight=1)
        alerts_frame.rowconfigure(0, weight=1)
        alerts_frame.columnconfigure(0, weight=1)

    def update_status(self):
        """Update status display."""
        
        try:
            # Update status
            enabled = self.engine.is_enabled()
            running = self.engine.running
            
            if enabled and running:
                status = "🟢 Alerts enabled and monitoring"
                button_text = "Disable Alerts"
            elif enabled and not running:
                status = "🟡 Alerts enabled but not monitoring"
                button_text = "Start Monitoring"
            else:
                status = "🔴 Alerts disabled"
                button_text = "Enable Alerts"
            
            self.status_label.config(text=status)
            self.toggle_button.config(text=button_text)
            
            # Update keywords tree
            self.keywords_tree.delete(*self.keywords_tree.get_children())
            
            for category, config in self.engine.config["strategy_keywords"].items():
                priority = config.get("priority", "low")
                enabled = "✅" if config.get("enabled", True) else "❌"
                
                self.keywords_tree.insert("", tk.END, text=category.title(), 
                                        values=(priority.title(), enabled))
            
            # Update recent alerts
            self.update_alerts_display()
            
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {e}")

    def update_alerts_display(self):
        """Update recent alerts display."""
        
        try:
            summary = self.engine.get_alerts_summary(hours=24)
            
            self.alerts_text.delete(1.0, tk.END)
            
            # Summary
            total = summary.get("total", 0)
            notifications = summary.get("notifications_sent", 0)
            
            self.alerts_text.insert(tk.END, f"📊 Last 24 hours: {total} alerts, {notifications} notifications\n\n")
            
            # By priority
            by_priority = summary.get("by_priority", {})
            if by_priority:
                self.alerts_text.insert(tk.END, "Priority breakdown:\n")
                for priority, count in by_priority.items():
                    self.alerts_text.insert(tk.END, f"  {priority.title()}: {count}\n")
                self.alerts_text.insert(tk.END, "\n")
            
            # Recent alerts
            recent = summary.get("recent_alerts", [])
            if recent:
                self.alerts_text.insert(tk.END, "Recent alerts:\n")
                for alert in recent[-5:]:  # Last 5
                    timestamp = alert["timestamp"][:16]  # Just date and time
                    priority = alert["priority"]
                    categories = ", ".join(alert["categories"])
                    headline = alert["headline"][:60]
                    notified = "🔔" if alert["notified"] else "🔇"
                    
                    self.alerts_text.insert(tk.END, 
                        f"{timestamp} [{priority.upper()}] {notified} {categories}: {headline}...\n")
        
        except Exception as e:
            self.alerts_text.insert(tk.END, f"❌ Error loading alerts: {e}\n")

    def toggle_alerts(self):
        """Toggle alerts enabled/disabled."""
        
        try:
            current_enabled = self.engine.is_enabled()
            self.engine.toggle_alerts(not current_enabled)
            
            if not current_enabled:
                # Starting alerts
                if not self.engine.running:
                    self.engine.start_monitoring()
            else:
                # Stopping alerts
                if self.engine.running:
                    self.engine.stop_monitoring()
            
            self.update_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle alerts: {e}")

    def test_notification(self):
        """Send a test notification."""
        
        try:
            if NOTIFICATIONS_AVAILABLE:
                notification.notify(
                    title="📰 MacroIntel Test Alert",
                    message="This is a test notification from MacroIntel News Alerts",
                    app_name="MacroIntel",
                    timeout=5
                )
                messagebox.showinfo("Success", "Test notification sent!")
            else:
                messagebox.showerror("Error", "Notifications not available - install plyer")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send test notification: {e}")

    def update_gui(self):
        """Periodic GUI updates."""
        
        try:
            self.update_status()
        except:
            pass
        
        # Schedule next update
        self.root.after(30000, self.update_gui)  # Update every 30 seconds

    def run(self):
        """Run the GUI."""
        self.root.mainloop()

def run_cli(engine: NewsAlertsEngine):
    """Run CLI interface for news alerts."""
    
    parser = argparse.ArgumentParser(description="MacroIntel News Alerts CLI")
    parser.add_argument("--enable", action="store_true", help="Enable alerts")
    parser.add_argument("--disable", action="store_true", help="Disable alerts")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--summary", type=int, nargs='?', const=24, help="Show alerts summary for N hours (default: 24)")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring (blocks)")
    parser.add_argument("--test", action="store_true", help="Send test notification")
    
    args = parser.parse_args()
    
    if args.enable:
        engine.toggle_alerts(True)
        print("SUCCESS: News alerts enabled")
    
    elif args.disable:
        engine.toggle_alerts(False)
        print("DISABLE: News alerts disabled")
    
    elif args.status:
        enabled = engine.is_enabled()
        running = engine.running
        print(f"STATUS: {'Enabled' if enabled else 'Disabled'}, {'Running' if running else 'Stopped'}")
        
        # Show configuration
        print(f"CONFIG: Check interval: {engine.config['check_interval']} seconds")
        print(f"CONFIG: Max notifications/hour: {engine.config['max_notifications_per_hour']}")
        
        # Show keywords
        print("\nKEYWORDS: Strategy keywords:")
        for category, config in engine.config["strategy_keywords"].items():
            status = "ENABLED" if config.get("enabled", True) else "DISABLED"
            priority = config.get("priority", "low")
            print(f"  {status} {category}: {priority} priority")
    
    elif args.test:
        if NOTIFICATIONS_AVAILABLE:
            notification.notify(
                title="MacroIntel Test Alert",
                message="This is a test notification from MacroIntel News Alerts CLI",
                app_name="MacroIntel",
                timeout=5
            )
            print("SUCCESS: Test notification sent")
        else:
            print("ERROR: Notifications not available - install plyer")
    
    elif args.monitor:
        print("START: Starting news monitoring... (Ctrl+C to stop)")
        
        def signal_handler(sig, frame):
            print("\nSTOP: Stopping news monitoring...")
            engine.stop_monitoring()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        engine.start_monitoring()
        
        try:
            while engine.running:
                time.sleep(1)
        except KeyboardInterrupt:
            engine.stop_monitoring()
    
    elif args.summary is not None:
        summary = engine.get_alerts_summary(hours=args.summary)
        print(f"SUMMARY: Alerts summary (last {args.summary} hours):")
        print(f"  Total alerts: {summary.get('total', 0)}")
        print(f"  Notifications sent: {summary.get('notifications_sent', 0)}")
        
        if summary.get("by_priority"):
            print("  By priority:")
            for priority, count in summary["by_priority"].items():
                print(f"    {priority}: {count}")
        
        if summary.get("by_category"):
            print("  By category:")
            for category, count in summary["by_category"].items():
                print(f"    {category}: {count}")
        
        if summary.get("error"):
            print(f"  Error: {summary['error']}")
    
    else:
        parser.print_help()

def main():
    """Main entry point."""
    
    # Initialize engine first (to avoid showing header for help)
    engine = NewsAlertsEngine()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # CLI mode
        run_cli(engine)
    else:
        # GUI mode - only show header when starting GUI
        print("MacroIntel News Alerts System")
        print("=" * 50)
        
        # Check dependencies
        if not NOTIFICATIONS_AVAILABLE:
            print("WARNING: plyer not available - notifications disabled")
        
        if not MACROINTEL_AVAILABLE:
            print("WARNING: MacroIntel modules not available - limited functionality")
        
        print("GUI: Starting GUI interface...")
        
        try:
            gui = NewsAlertsGUI(engine)
            gui.run()
        except ImportError:
            print("ERROR: GUI not available - tkinter not installed")
            print("HELP: Use CLI mode: python news_alerts.py --help")
        except Exception as e:
            print(f"ERROR: GUI error: {e}")
            print("HELP: Use CLI mode: python news_alerts.py --help")

if __name__ == "__main__":
    main() 