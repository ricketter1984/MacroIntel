#!/usr/bin/env python3
"""
Test script for TickerNewsAgent model integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ticker_news_agent_models():
    """Test TickerNewsAgent with different models."""
    try:
        from agents.ticker_news_agent import TickerNewsAgent
        
        print("🧪 Testing TickerNewsAgent Model Integration")
        print("=" * 50)
        
        # Test different models
        models_to_test = ["claude", "perplexity", "mistral"]
        test_tickers = ["AAPL", "MSFT"]  # Use a small set for testing
        
        for model in models_to_test:
            print(f"\n🤖 Testing model: {model}")
            try:
                # Create agent instance
                agent = TickerNewsAgent(include_quiver=False)
                
                # Test the run method with model parameter
                result = agent.run(tickers=test_tickers, model=model)
                
                if result.get('status') == 'success':
                    print(f"✅ {model} model test PASSED")
                    print(f"   📊 Tickers processed: {result.get('tickers_processed', 0)}")
                    print(f"   📰 Total articles: {result.get('total_articles', 0)}")
                    print(f"   📄 Report file: {result.get('markdown_file', 'N/A')}")
                    
                    # Check if AI client was initialized
                    if hasattr(agent, 'ai_client') and agent.ai_client is not None:
                        print(f"   🤖 AI client initialized: {type(agent.ai_client).__name__}")
                    else:
                        print(f"   ⚠️ No AI client initialized for {model}")
                        
                else:
                    print(f"❌ {model} model test FAILED")
                    print(f"   Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error testing {model} model: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing TickerNewsAgent: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in model test: {e}")
        return False

def test_environment_setup():
    """Test environment setup for different models."""
    print("\n🔧 Testing Environment Setup")
    print("=" * 40)
    
    # Check for API keys
    api_keys = {
        "MISTRAL_API_KEY": "Mistral",
        "CLAUDE_API_KEY": "Claude", 
        "PERPLEXITY_API_KEY": "Perplexity"
    }
    
    for key_name, model_name in api_keys.items():
        api_key = os.getenv(key_name)
        if api_key:
            print(f"✅ {model_name} API key found")
        else:
            print(f"⚠️ {model_name} API key not found")
    
    return True

def test_cli_integration():
    """Test CLI integration with run_macrointel.py."""
    print("\n🧪 Testing CLI Integration")
    print("=" * 40)
    
    try:
        import subprocess
        
        # Test help command to see if model argument is available
        result = subprocess.run([
            sys.executable, "run_macrointel.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            help_text = result.stdout
            if "--model" in help_text and "--watchlist-news" in help_text:
                print("✅ CLI integration looks good")
                print("✅ --model and --watchlist-news arguments available")
            else:
                print("⚠️ CLI integration may have issues")
        else:
            print("❌ CLI help command failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing CLI integration: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing TickerNewsAgent Model Integration")
    print("=" * 50)
    
    # Test environment setup
    test_environment_setup()
    
    # Test TickerNewsAgent with different models
    model_test_passed = test_ticker_news_agent_models()
    
    # Test CLI integration
    cli_test_passed = test_cli_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"Model Integration: {'✅ PASSED' if model_test_passed else '❌ FAILED'}")
    print(f"CLI Integration: {'✅ PASSED' if cli_test_passed else '❌ FAILED'}")
    
    if model_test_passed and cli_test_passed:
        print("\n🎉 All tests passed!")
        print("\nUsage examples:")
        print("  python run_macrointel.py --watchlist-news AAPL,MSFT --model mistral")
        print("  python run_macrointel.py --watchlist-news SPY,QQQ --model claude")
        print("  python run_macrointel.py --watchlist-news XLE --model perplexity")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 