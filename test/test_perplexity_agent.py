#!/usr/bin/env python3
"""
Test script for Perplexity Macro Agent
"""

import os
import sys
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.perplexity_macro_agent import PerplexityMacroAgent

def test_perplexity_agent():
    """Test the Perplexity macro agent functionality."""
    print("🧪 Testing Perplexity Macro Agent...")
    
    # Initialize the agent
    agent = PerplexityMacroAgent()
    
    # Test with default keywords
    print("🔍 Testing with default macro keywords...")
    result = agent.run()
    
    print(f"✅ Test completed!")
    print(f"📊 Status: {result.get('status', 'unknown')}")
    print(f"📰 Articles found: {result.get('total_count', 0)}")
    print(f"💾 Output file: {result.get('output_file', 'none')}")
    
    if result.get('articles'):
        print("\n📋 Sample articles:")
        for i, article in enumerate(result['articles'][:3]):
            print(f"  {i+1}. {article.get('title', 'No title')[:60]}...")
            print(f"     Tags: {article.get('tags', [])}")
    
    return result

def test_perplexity_agent_with_topic():
    """Test the Perplexity macro agent with a specific topic."""
    print("\n🧪 Testing Perplexity Macro Agent with specific topic...")
    
    # Initialize the agent
    agent = PerplexityMacroAgent()
    
    # Test with specific topic
    topic = "Federal Reserve interest rates"
    print(f"🔍 Testing with topic: '{topic}'")
    result = agent.run(topic)
    
    print(f"✅ Test completed!")
    print(f"📊 Status: {result.get('status', 'unknown')}")
    print(f"📰 Articles found: {result.get('total_count', 0)}")
    print(f"💾 Output file: {result.get('output_file', 'none')}")
    
    return result

if __name__ == "__main__":
    print("🚀 Starting Perplexity Macro Agent Tests")
    print("=" * 50)
    
    # Test 1: Default keywords
    result1 = test_perplexity_agent()
    
    # Test 2: Specific topic
    result2 = test_perplexity_agent_with_topic()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    
    # Summary
    total_articles = result1.get('total_count', 0) + result2.get('total_count', 0)
    print(f"📊 Total articles found: {total_articles}")
    
    if total_articles > 0:
        print("✅ Perplexity Macro Agent is working correctly!")
    else:
        print("⚠️ No articles found - check API key and network connection") 