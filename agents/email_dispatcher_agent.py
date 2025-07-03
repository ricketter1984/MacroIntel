#!/usr/bin/env python3
"""
Email Dispatcher Agent for MacroIntel Swarm
Calls email_report.py to build and send comprehensive HTML email reports.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_report import generate_email_content, send_daily_report
from utils.api_clients import init_env

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailDispatcherAgent:
    """Agent responsible for building and sending comprehensive email reports."""
    
    def __init__(self):
        """Initialize the email dispatcher agent."""
        init_env()
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("📧 Email Dispatcher Agent initialized")
    
    def build_html_report(self, news_summary: Dict[str, Any], charts: Dict[str, Any], 
                         strategy_analysis: Dict[str, Any], market_data: Dict[str, Any]) -> str:
        """
        Build comprehensive HTML report from all agent outputs.
        
        Args:
            news_summary: News analysis from summarizer agent
            charts: Chart generation results from chart generator agent
            strategy_analysis: Strategy analysis from playbook strategist agent
            market_data: Market data from various sources
            
        Returns:
            HTML content string
        """
        try:
            logger.info("📝 Building comprehensive HTML report...")
            
            # Extract articles from news summary
            articles = news_summary.get("articles", [])
            
            # Generate base email content
            html_content = generate_email_content(articles, limit=25)
            
            # Add strategy analysis section
            strategy_section = self._build_strategy_section(strategy_analysis)
            
            # Add chart section
            chart_section = self._build_chart_section(charts)
            
            # Insert strategy section before the news section
            news_start = html_content.find("<h2>📰 Relevant Headlines</h2>")
            if news_start != -1:
                html_content = (
                    html_content[:news_start] + 
                    strategy_section + 
                    chart_section + 
                    html_content[news_start:]
                )
            else:
                # If news section not found, append to end
                html_content += strategy_section + chart_section
            
            logger.info("✅ HTML report built successfully")
            return html_content
            
        except Exception as e:
            logger.error(f"❌ Error building HTML report: {str(e)}")
            return f"<h1>Error Building Report</h1><p>Error: {str(e)}</p>"
    
    def _build_strategy_section(self, strategy_analysis: Dict[str, Any]) -> str:
        """Build HTML section for strategy analysis."""
        try:
            market_regime = strategy_analysis.get("market_regime", "NEUTRAL")
            strategies = strategy_analysis.get("selected_strategies", [])
            avoid_list = strategy_analysis.get("avoid_list", [])
            macro_notes = strategy_analysis.get("macro_notes", [])
            
            # Convert macro_notes to string if it's a list
            if isinstance(macro_notes, list):
                macro_notes = "<br>".join([f"• {note}" for note in macro_notes])
            
            strategy_html = f"""
            <div style="margin: 20px 0; padding: 15px; background: #2c3e50; border-radius: 5px; color: white;">
                <h2>📘 Playbook Outlook</h2>
                <p><strong>Market Regime:</strong> {market_regime}</p>
                
                <h3>🎯 Recommended Strategies ({len(strategies)}):</h3>
                <ul>
            """
            
            for strategy in strategies:
                name = strategy.get("name", "Unknown Strategy")
                description = strategy.get("description", "")
                confidence = strategy.get("confidence", 0.0)
                strategy_html += f'<li><strong>{name}</strong> ({confidence:.1%} confidence)<br><small>{description}</small></li>'
            
            strategy_html += "</ul>"
            
            if avoid_list:
                strategy_html += f"""
                <h3>🚫 Avoid:</h3>
                <ul>
                """
                for avoid in avoid_list:
                    strategy_html += f"<li>{avoid}</li>"
                strategy_html += "</ul>"
            
            if macro_notes:
                strategy_html += f"""
                <h3>📈 Macro Notes:</h3>
                <p>{macro_notes}</p>
                """
            
            strategy_html += "</div>"
            return strategy_html
            
        except Exception as e:
            logger.error(f"❌ Error building strategy section: {str(e)}")
            return f"<div><h3>Strategy Analysis Error</h3><p>Error: {str(e)}</p></div>"
    
    def _build_chart_section(self, charts: Dict[str, Any]) -> str:
        """Build HTML section for charts."""
        try:
            charts_generated = charts.get("charts_generated", [])
            analysis_summary = charts.get("analysis_summary", "")
            
            if not charts_generated:
                return ""
            
            chart_html = f"""
            <div style="margin: 20px 0; padding: 15px; background: #34495e; border-radius: 5px; color: white;">
                <h2>📊 Market Visualizations</h2>
                <p>{analysis_summary}</p>
            """
            
            for chart in charts_generated:
                if chart.get("success", False):
                    chart_type = chart.get("chart_type", "Unknown")
                    description = chart.get("description", "")
                    file_path = chart.get("file_path", "")
                    
                    chart_html += f"""
                    <div style="margin: 10px 0; padding: 10px; background: #2c3e50; border-radius: 3px;">
                        <h4>{chart_type}</h4>
                        <p>{description}</p>
                        <p><small>Generated: {file_path}</small></p>
                    </div>
                    """
            
            chart_html += "</div>"
            return chart_html
            
        except Exception as e:
            logger.error(f"❌ Error building chart section: {str(e)}")
            return f"<div><h3>Chart Section Error</h3><p>Error: {str(e)}</p></div>"
    
    def send_email(self, html_content: str) -> Dict[str, Any]:
        """
        Send the HTML email report.
        
        Args:
            html_content: Complete HTML email content
            
        Returns:
            Dictionary with email sending results
        """
        try:
            logger.info("📧 Sending email report...")
            
            # Send the email
            success = send_daily_report(html_content)
            
            # Get recipients from environment
            recipients = os.getenv("EMAIL_RECIPIENTS", "").split(",") if os.getenv("EMAIL_RECIPIENTS") else []
            
            result = {
                "email_sent": success,
                "recipients": [r.strip() for r in recipients if r.strip()],
                "report_summary": f"Daily MacroIntel report sent to {len(recipients)} recipients",
                "attachments": [],
                "timestamp": datetime.now().isoformat()
            }
            
            if success:
                logger.info("✅ Email sent successfully")
            else:
                logger.error("❌ Failed to send email")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {str(e)}")
            return {
                "email_sent": False,
                "recipients": [],
                "report_summary": f"Failed to send email: {str(e)}",
                "attachments": [],
                "error": str(e)
            }
    
    def run(self, input_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Main execution method for the email dispatcher agent.
        
        Args:
            input_data: Input data from previous agents
            
        Returns:
            Dictionary with email sending results
        """
        logger.info("🚀 Starting Email Dispatcher Agent execution...")
        
        # Extract data from input
        if input_data:
            news_summary = input_data.get("news_summary", {})
            charts = input_data.get("charts", {})
            strategy_analysis = input_data.get("strategy_analysis", {})
            market_data = input_data.get("market_data", {})
        else:
            # Default empty data for standalone testing
            news_summary = {"articles": []}
            charts = {"charts_generated": []}
            strategy_analysis = {"market_regime": "NEUTRAL", "selected_strategies": []}
            market_data = {}
        
        # Build HTML report
        html_content = self.build_html_report(news_summary, charts, strategy_analysis, market_data)
        
        # Send email
        email_result = self.send_email(html_content)
        
        logger.info("✅ Email Dispatcher Agent execution completed")
        return email_result

def main():
    """Main function for standalone execution."""
    agent = EmailDispatcherAgent()
    result = agent.run()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 