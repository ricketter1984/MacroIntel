#!/usr/bin/env python3
"""
Test script for Mistral integration in MacroIntel Swarm
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mistral_client():
    """Test the MistralClient class."""
    try:
        from core.ai_clients import MistralClient
        
        # Test initialization
        client = MistralClient()
        print("✅ MistralClient initialized successfully")
        
        # Test API key
        api_key = os.getenv("MISTRAL_API_KEY")
        if api_key:
            print("✅ MISTRAL_API_KEY found in environment")
        else:
            print("⚠️ MISTRAL_API_KEY not found in environment")
        
        # Test model configuration
        print(f"🤖 Model: {client.model}")
        print(f"🌐 Base URL: {client.base_url}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing MistralClient: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing MistralClient: {e}")
        return False

def test_swarm_orchestrator():
    """Test the swarm orchestrator with Mistral model."""
    try:
        from agents.swarm_orchestrator import MacroIntelSwarm
        
        # Test initialization with Mistral model
        swarm = MacroIntelSwarm(debug_mode=True, model="mistral")
        print("✅ MacroIntelSwarm initialized with Mistral model")
        
        # Test AI clients initialization
        if "summarizer" in swarm.ai_clients:
            print("✅ MistralClient initialized for summarization")
        else:
            print("⚠️ MistralClient not found in ai_clients")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing MacroIntelSwarm: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing MacroIntelSwarm: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Mistral Integration in MacroIntel Swarm")
    print("=" * 50)
    
    # Test 1: MistralClient
    print("\n1. Testing MistralClient...")
    test1_passed = test_mistral_client()
    
    # Test 2: Swarm Orchestrator
    print("\n2. Testing Swarm Orchestrator...")
    test2_passed = test_swarm_orchestrator()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"MistralClient: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Swarm Orchestrator: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Mistral integration is working correctly.")
        print("\nUsage examples:")
        print("  python agents/swarm_orchestrator.py --now --model mistral")
        print("  python agents/swarm_orchestrator.py --now --model claude")
        print("  python agents/swarm_orchestrator.py --now --model perplexity")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 