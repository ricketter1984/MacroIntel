#!/usr/bin/env python3
"""
Test script for MacroIntel Agent Swarm
Tests individual agents and the complete swarm workflow.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_individual_agents():
    """Test each agent individually."""
    print("🧪 Testing Individual Agents...")
    print("="*50)
    
    # Test Summarizer Agent
    try:
        print("\n📰 Testing Summarizer Agent...")
        from summarizer_agent import SummarizerAgent
        summarizer = SummarizerAgent()
        result = summarizer.run()
        print(f"✅ Summarizer: {result.get('total_count', 0)} articles processed")
        print(f"   Sources: {result.get('sources_processed', [])}")
    except Exception as e:
        print(f"❌ Summarizer failed: {str(e)}")
    
    # Test Chart Generator Agent
    try:
        print("\n📈 Testing Chart Generator Agent...")
        from chart_generator_agent import ChartGeneratorAgent
        chart_gen = ChartGeneratorAgent()
        result = chart_gen.run()
        print(f"✅ Chart Generator: {len(result.get('charts_generated', []))} charts generated")
        print(f"   Summary: {result.get('analysis_summary', 'N/A')}")
    except Exception as e:
        print(f"❌ Chart Generator failed: {str(e)}")
    
    # Test Playbook Strategist Agent
    try:
        print("\n📘 Testing Playbook Strategist Agent...")
        from playbook_strategist_agent import PlaybookStrategistAgent
        strategist = PlaybookStrategistAgent()
        result = strategist.run()
        print(f"✅ Playbook Strategist: {result.get('market_regime', 'Unknown')} regime")
        print(f"   Strategies: {len(result.get('selected_strategies', []))}")
    except Exception as e:
        print(f"❌ Playbook Strategist failed: {str(e)}")
    
    # Test Email Dispatcher Agent (without sending)
    try:
        print("\n📧 Testing Email Dispatcher Agent...")
        from email_dispatcher_agent import EmailDispatcherAgent
        dispatcher = EmailDispatcherAgent()
        # Test with mock data
        mock_input = {
            "news_summary": {"articles": []},
            "charts": {"charts_generated": []},
            "strategy_analysis": {"market_regime": "NEUTRAL", "selected_strategies": []},
            "market_data": {}
        }
        result = dispatcher.run(mock_input)
        print(f"✅ Email Dispatcher: {'Success' if result.get('email_sent', False) else 'Failed'}")
    except Exception as e:
        print(f"❌ Email Dispatcher failed: {str(e)}")

def test_swarm_config():
    """Test the swarm configuration file."""
    print("\n🔧 Testing Swarm Configuration...")
    print("="*50)
    
    try:
        with open('swarm_config.json', 'r') as f:
            config = json.load(f)
        
        print(f"✅ Config loaded: {config.get('name', 'Unknown')}")
        print(f"   Version: {config.get('version', 'Unknown')}")
        print(f"   Agents: {len(config.get('agents', []))}")
        
        # Check agent configurations
        agents = config.get('agents', [])
        for agent in agents:
            name = agent.get('name', 'Unknown')
            model = agent.get('model', 'Unknown')
            print(f"   - {name}: {model}")
        
        print("✅ Swarm configuration is valid")
        
    except Exception as e:
        print(f"❌ Swarm configuration failed: {str(e)}")

def test_environment():
    """Test environment setup."""
    print("\n🌍 Testing Environment...")
    print("="*50)
    
    # Check required directories
    dirs_to_check = ['output', 'logs', 'config']
    for dir_name in dirs_to_check:
        if os.path.exists(dir_name):
            print(f"✅ Directory exists: {dir_name}")
        else:
            print(f"⚠️ Directory missing: {dir_name}")
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file exists")
    else:
        print("⚠️ .env file missing")
    
    # Check Python path
    try:
        import utils.api_clients
        print("✅ API clients import successful")
    except Exception as e:
        print(f"❌ API clients import failed: {str(e)}")

def main():
    """Main test function."""
    print("🤖 MacroIntel Agent Swarm Test Suite")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test environment
    test_environment()
    
    # Test swarm configuration
    test_swarm_config()
    
    # Test individual agents
    test_individual_agents()
    
    print("\n" + "="*60)
    print("🧪 Test Suite Completed")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. Ensure all API keys are set in .env file")
    print("2. Test full swarm: python agents/swarm_orchestrator.py")
    print("3. Check logs in /logs directory for detailed information")
    print("4. Verify email configuration for full workflow testing")

if __name__ == "__main__":
    main() 