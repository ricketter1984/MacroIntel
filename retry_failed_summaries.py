#!/usr/bin/env python3
"""
Retry Failed Summaries Script
Processes articles that failed to summarize and retries with different models
"""

import json
import os
from news_scanner.macro_insight_builder import get_failed_summaries, save_failed_summary, summarize_article

def retry_failed_summaries(max_retries=3):
    """
    Retry failed summaries with different models
    
    Args:
        max_retries: Maximum number of retry attempts per article
    """
    print("🔄 Loading failed summaries from retry queue...")
    
    failed_items = get_failed_summaries()
    if not failed_items:
        print("✅ No failed summaries found in retry queue.")
        return
    
    print(f"📋 Found {len(failed_items)} failed summaries to retry")
    
    # Models to try in order of preference
    models_to_try = ["gpt", "claude", "gemini"]
    
    successful_retries = 0
    still_failed = []
    
    for i, failed_item in enumerate(failed_items, 1):
        article = failed_item["article"]
        original_error = failed_item["error_reason"]
        retry_count = failed_item.get("retry_count", 0)
        
        if retry_count >= max_retries:
            print(f"⏭️  Skipping {i}. {article.get('title', 'No title')[:60]}... (max retries reached)")
            still_failed.append(failed_item)
            continue
        
        print(f"\n🔄 Retrying {i}. {article.get('title', 'No title')[:60]}...")
        print(f"   Original error: {original_error}")
        print(f"   Retry attempt: {retry_count + 1}/{max_retries}")
        
        # Try different models
        success = False
        for model in models_to_try:
            try:
                print(f"   Trying {model.upper()}...")
                result = summarize_article(article, model=model)
                
                if result and not result.get("summary", "").startswith("[Error"):
                    print(f"   ✅ Success with {model.upper()}!")
                    successful_retries += 1
                    success = True
                    break
                else:
                    print(f"   ❌ {model.upper()} failed")
                    
            except Exception as e:
                print(f"   ❌ {model.upper()} error: {str(e)}")
        
        if not success:
            # Update retry count and save back to queue
            failed_item["retry_count"] = retry_count + 1
            failed_item["error_reason"] = f"All models failed after {retry_count + 1} retries"
            still_failed.append(failed_item)
            print(f"   ❌ All models failed for this article")
    
    # Save updated failed summaries back to file
    try:
        with open("data/failed_summaries.json", "w") as f:
            json.dump(still_failed, f, indent=2)
        print(f"\n💾 Updated retry queue: {len(still_failed)} items remaining")
    except Exception as e:
        print(f"⚠️ Could not save updated retry queue: {e}")
    
    print(f"\n📊 Retry Summary:")
    print(f"   ✅ Successful retries: {successful_retries}")
    print(f"   ❌ Still failed: {len(still_failed)}")
    print(f"   📈 Success rate: {successful_retries}/{len(failed_items)} ({successful_retries/len(failed_items)*100:.1f}%)")

def clear_failed_summaries():
    """Clear all failed summaries from the retry queue"""
    try:
        with open("data/failed_summaries.json", "w") as f:
            json.dump([], f)
        print("🗑️ Cleared all failed summaries from retry queue")
    except Exception as e:
        print(f"⚠️ Could not clear retry queue: {e}")

def show_failed_summaries():
    """Display all failed summaries in the retry queue"""
    failed_items = get_failed_summaries()
    
    if not failed_items:
        print("✅ No failed summaries in retry queue")
        return
    
    print(f"📋 Failed Summaries ({len(failed_items)} items):")
    print("=" * 80)
    
    for i, failed_item in enumerate(failed_items, 1):
        article = failed_item["article"]
        error = failed_item["error_reason"]
        model = failed_item["model_used"]
        retry_count = failed_item.get("retry_count", 0)
        timestamp = failed_item.get("timestamp", "Unknown")
        
        print(f"\n{i}. {article.get('title', 'No title')}")
        print(f"   Error: {error}")
        print(f"   Model: {model}")
        print(f"   Retries: {retry_count}")
        print(f"   Timestamp: {timestamp}")
        print("-" * 40)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Retry Failed Summaries')
    parser.add_argument('--retry', action='store_true', help='Retry failed summaries')
    parser.add_argument('--show', action='store_true', help='Show failed summaries')
    parser.add_argument('--clear', action='store_true', help='Clear all failed summaries')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts (default: 3)')
    
    args = parser.parse_args()
    
    if args.show:
        show_failed_summaries()
    elif args.clear:
        clear_failed_summaries()
    elif args.retry:
        retry_failed_summaries(args.max_retries)
    else:
        print("Please specify an action: --retry, --show, or --clear")
        print("Example: python retry_failed_summaries.py --retry") 