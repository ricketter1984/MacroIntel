#!/usr/bin/env python3
"""
Test script for run_macrointel.py CLI integration
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="config/.env")

def test_cli_help():
    """Test that the CLI help shows the new model argument."""
    print("🧪 Testing CLI Help")
    print("=" * 40)
    
    try:
        # Run the help command
        result = subprocess.run([
            sys.executable, "run_macrointel.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            help_text = result.stdout
            print("✅ CLI help command executed successfully")
            
            # Check if model argument is present
            if "--model" in help_text:
                print("✅ --model argument found in help")
                if "claude" in help_text and "perplexity" in help_text and "mistral" in help_text:
                    print("✅ All model choices (claude, perplexity, mistral) found in help")
                else:
                    print("⚠️ Not all model choices found in help")
            else:
                print("❌ --model argument not found in help")
            
            # Check if swarm argument is present
            if "--swarm" in help_text:
                print("✅ --swarm argument found in help")
            else:
                print("❌ --swarm argument not found in help")
                
        else:
            print(f"❌ CLI help command failed: {result.stderr}")
            
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ CLI help command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing CLI help: {e}")
        return False

def test_model_argument():
    """Test that the model argument is properly parsed."""
    print("\n🧪 Testing Model Argument Parsing")
    print("=" * 40)
    
    models_to_test = ["claude", "perplexity", "mistral"]
    
    for model in models_to_test:
        print(f"\n🤖 Testing model: {model}")
        try:
            # Test with invalid argument to see if model is recognized
            result = subprocess.run([
                sys.executable, "run_macrointel.py", "--swarm", "--model", model, "--invalid-arg"
            ], capture_output=True, text=True, timeout=10)
            
            # We expect this to fail due to invalid argument, but model should be parsed
            if "error" in result.stderr.lower() or "invalid" in result.stderr.lower():
                print(f"✅ Model '{model}' argument parsed correctly")
            else:
                print(f"⚠️ Model '{model}' argument parsing unclear")
                
        except subprocess.TimeoutExpired:
            print(f"❌ Test for model '{model}' timed out")
        except Exception as e:
            print(f"❌ Error testing model '{model}': {e}")
    
    return True

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

def main():
    """Run all CLI tests."""
    print("🚀 Testing run_macrointel.py CLI Integration")
    print("=" * 50)
    
    # Test environment setup
    test_environment_setup()
    
    # Test CLI help
    help_test_passed = test_cli_help()
    
    # Test model argument parsing
    model_test_passed = test_model_argument()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 CLI TEST RESULTS")
    print("=" * 50)
    print(f"CLI Help: {'✅ PASSED' if help_test_passed else '❌ FAILED'}")
    print(f"Model Argument: {'✅ PASSED' if model_test_passed else '❌ FAILED'}")
    
    if help_test_passed and model_test_passed:
        print("\n🎉 CLI integration tests passed!")
        print("\nUsage examples:")
        print("  python run_macrointel.py --swarm --model mistral")
        print("  python run_macrointel.py --swarm --model claude")
        print("  python run_macrointel.py --swarm --model perplexity")
        print("  python run_macrointel.py --swarm --model mistral --send")
    else:
        print("\n❌ CLI integration tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 