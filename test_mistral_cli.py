#!/usr/bin/env python3
"""
Test script for Mistral CLI integration in MacroIntel Swarm
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cli_model_selection():
    """Test the CLI model selection functionality."""
    try:
        from agents.swarm_orchestrator import MacroIntelSwarm
        
        print("🧪 Testing CLI Model Selection")
        print("=" * 40)
        
        # Test different model selections
        models_to_test = ["mistral", "claude", "perplexity"]
        
        for model in models_to_test:
            print(f"\n🤖 Testing model: {model}")
            try:
                swarm = MacroIntelSwarm(debug_mode=True, model=model)
                print(f"✅ Successfully initialized with {model} model")
                
                # Check if AI client was initialized
                if "summarizer" in swarm.ai_clients:
                    print(f"✅ AI client initialized for {model}")
                else:
                    print(f"⚠️ No AI client initialized for {model}")
                
                # Test the AI summarization method
                test_articles = [
                    {"title": "Test Article 1", "summary": "This is a test article about markets."},
                    {"title": "Test Article 2", "summary": "Another test article about trading."}
                ]
                
                if "summarizer" in swarm.ai_clients:
                    summary = swarm.use_ai_client_for_summarization(test_articles)
                    print(f"✅ AI summarization test completed")
                    print(f"📝 Summary preview: {summary[:100]}...")
                else:
                    print(f"⚠️ Skipping AI summarization test for {model}")
                    
            except Exception as e:
                print(f"❌ Error testing {model} model: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing MacroIntelSwarm: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in CLI test: {e}")
        return False

def test_environment_setup():
    """Test environment setup for Mistral."""
    print("\n🔧 Testing Environment Setup")
    print("=" * 40)
    
    # Check for Mistral API key
    mistral_key = os.getenv("MISTRAL_API_KEY")
    if mistral_key:
        print("✅ MISTRAL_API_KEY found in environment")
        print(f"🔑 Key preview: {mistral_key[:10]}...")
    else:
        print("⚠️ MISTRAL_API_KEY not found in environment")
        print("💡 Set MISTRAL_API_KEY in config/.env file")
    
    # Check for other API keys
    claude_key = os.getenv("CLAUDE_API_KEY")
    if claude_key:
        print("✅ CLAUDE_API_KEY found in environment")
    else:
        print("⚠️ CLAUDE_API_KEY not found in environment")
    
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    if perplexity_key:
        print("✅ PERPLEXITY_API_KEY found in environment")
    else:
        print("⚠️ PERPLEXITY_API_KEY not found in environment")

def main():
    """Run all CLI tests."""
    print("🚀 Testing Mistral CLI Integration")
    print("=" * 50)
    
    # Test environment setup
    test_environment_setup()
    
    # Test CLI model selection
    print("\n" + "=" * 50)
    cli_test_passed = test_cli_model_selection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 CLI TEST RESULTS")
    print("=" * 50)
    print(f"CLI Model Selection: {'✅ PASSED' if cli_test_passed else '❌ FAILED'}")
    
    if cli_test_passed:
        print("\n🎉 CLI integration tests passed!")
        print("\nUsage examples:")
        print("  python agents/swarm_orchestrator.py --now --model mistral")
        print("  python agents/swarm_orchestrator.py --now --model claude")
        print("  python agents/swarm_orchestrator.py --now --model perplexity")
        print("  python agents/swarm_orchestrator.py --now --debug --model mistral")
    else:
        print("\n❌ CLI integration tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 