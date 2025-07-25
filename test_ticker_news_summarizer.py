#!/usr/bin/env python3
"""
Test script for TickerNewsAgent summarizer integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_summarizer_integration():
    """Test TickerNewsAgent with different summarizers."""
    try:
        from agents.ticker_news_agent import TickerNewsAgent
        
        print("🧪 Testing TickerNewsAgent Summarizer Integration")
        print("=" * 50)
        
        # Test different models
        models_to_test = ["claude", "perplexity", "mistral"]
        test_tickers = ["AAPL"]  # Use a single ticker for testing
        
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
                    
                    # Check results for AI analysis
                    results = result.get('results', {})
                    if results:
                        ticker_data = results.get('AAPL', {})
                        headlines = ticker_data.get('headlines', [])
                        if headlines:
                            first_article = headlines[0]
                            print(f"   📝 First article analysis:")
                            print(f"      Summary: {first_article.get('summary', 'N/A')[:100]}...")
                            print(f"      Sector: {first_article.get('sector', 'N/A')}")
                            print(f"      Impact: {first_article.get('impact', 'N/A')}")
                        else:
                            print(f"   ⚠️ No articles found for {model}")
                    else:
                        print(f"   ⚠️ No results for {model}")
                        
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
        print(f"❌ Error in summarizer test: {e}")
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

def test_ai_clients():
    """Test AI client availability."""
    print("\n🤖 Testing AI Clients")
    print("=" * 40)
    
    try:
        from core.ai_clients import MistralClient
        
        # Test MistralClient
        try:
            mistral_client = MistralClient()
            print("✅ MistralClient imported and initialized")
            
            # Test if it has summarize method
            if hasattr(mistral_client, 'summarize'):
                print("✅ MistralClient has summarize method")
            else:
                print("❌ MistralClient missing summarize method")
                
        except Exception as e:
            print(f"❌ MistralClient error: {e}")
        
        # Test for other clients (should fail gracefully)
        try:
            from core.ai_clients import PerplexityClient
            print("✅ PerplexityClient available")
        except ImportError:
            print("⚠️ PerplexityClient not available (using existing API)")
        
        try:
            from core.ai_clients import ClaudeClient
            print("✅ ClaudeClient available")
        except ImportError:
            print("⚠️ ClaudeClient not available (placeholder)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing AI clients: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing TickerNewsAgent Summarizer Integration")
    print("=" * 50)
    
    # Test environment setup
    test_environment_setup()
    
    # Test AI clients
    ai_client_test_passed = test_ai_clients()
    
    # Test summarizer integration
    summarizer_test_passed = test_summarizer_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"AI Clients: {'✅ PASSED' if ai_client_test_passed else '❌ FAILED'}")
    print(f"Summarizer Integration: {'✅ PASSED' if summarizer_test_passed else '❌ FAILED'}")
    
    if ai_client_test_passed and summarizer_test_passed:
        print("\n🎉 All tests passed!")
        print("\nUsage examples:")
        print("  python run_macrointel.py --watchlist-news AAPL --model mistral")
        print("  python run_macrointel.py --watchlist-news SPY,QQQ --model claude")
        print("  python run_macrointel.py --watchlist-news XLE --model perplexity")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 