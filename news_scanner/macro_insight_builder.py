import os
import requests
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# Initialize API clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
claude_api_key = os.getenv("CLAUDE_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Retry queue for failed summaries
failed_summaries = []

def save_failed_summary(article, error_reason, model_used):
    """Save failed summary to retry queue"""
    failed_item = {
        "article": article,
        "error_reason": error_reason,
        "model_used": model_used,
        "timestamp": datetime.now().isoformat(),
        "retry_count": 0
    }
    failed_summaries.append(failed_item)
    
    # Save to file for persistence
    try:
        with open("data/failed_summaries.json", "w") as f:
            json.dump(failed_summaries, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save failed summary: {e}")

def get_failed_summaries():
    """Load failed summaries from file"""
    try:
        with open("data/failed_summaries.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def summarize_article(article, model="claude"):
    """
    Summarize the article using specified AI model and return structured insight.
    
    Args:
        article: Dictionary containing 'title', 'body', 'url'
        model: AI model to use ('claude', 'gpt', 'gemini')
    
    Returns:
        Dictionary with structured insight: title, url, summary, affected_tickers, tone
    """
    system_prompt = (
        "You are a financial analyst assistant. Given a news article, return a structured response with:\n"
        "- A short 2-sentence summary\n"
        "- Why it matters (1 line)\n"
        "- Affected tickers or sectors (comma-separated)\n"
        "- Overall tone: Bullish / Bearish / Neutral / Volatile\n\n"
        "Format your response exactly as:\n"
        "SUMMARY: [2-sentence summary]\n"
        "WHY IT MATTERS: [1 line explanation]\n"
        "AFFECTED TICKERS: [comma-separated list]\n"
        "TONE: [Bullish/Bearish/Neutral/Volatile]"
    )

    content = f"TITLE: {article['title']}\n\nBODY: {article['body']}"
    
    try:
        if model.lower() == "claude":
            return _summarize_with_claude(content, system_prompt)
        elif model.lower() == "gpt":
            return _summarize_with_gpt(content, system_prompt)
        elif model.lower() == "gemini":
            return _summarize_with_gemini(content, system_prompt)
        else:
            raise ValueError(f"Unsupported model: {model}")
            
    except ValueError as e:
        print(f"⚠️  {str(e)}")
        save_failed_summary(article, str(e), model)
        return {
            "summary": f"[Model Error] {str(e)}",
            "affected_tickers": "",
            "tone": "Neutral"
        }
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "model" in error_msg.lower():
            print(f"⚠️  Claude model not available — falling back to GPT-3.5: {error_msg}")
            # Fallback to GPT-3.5
            try:
                print(f"🔄 Retrying with GPT-3.5...")
                return _summarize_with_gpt(content, system_prompt)
            except Exception as gpt_error:
                print(f"❌ GPT fallback also failed: {gpt_error}")
                save_failed_summary(article, f"Claude failed: {error_msg}, GPT fallback failed: {gpt_error}", f"{model}->gpt")
                return {
                    "summary": f"[Fallback Error] Claude failed, GPT fallback failed: {gpt_error}",
                    "affected_tickers": "",
                    "tone": "Neutral"
                }
        elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            print(f"⚠️  API key error — check your {model.upper()} API key configuration")
            save_failed_summary(article, error_msg, model)
        else:
            print(f"⚠️  {model.upper()} API error: {error_msg}")
            save_failed_summary(article, error_msg, model)
        
        return {
            "summary": f"[{model.upper()} API Error] {error_msg}",
            "affected_tickers": "",
            "tone": "Neutral"
        }


def _summarize_with_claude(content, system_prompt):
    """Summarize using Anthropic Claude API"""
    if not claude_api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": claude_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": f"{system_prompt}\n\n{content}"}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            raw = response.json()["content"][0]["text"]
            print(f"✅ Claude-3-Haiku summarization successful")
            return _parse_structured_response(raw)
        elif response.status_code == 404:
            # Try with the standard model name if the specific version fails
            print("⚠️  Claude model version not found, trying standard model...")
            data["model"] = "claude-3-haiku"
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                raw = response.json()["content"][0]["text"]
                print(f"✅ Claude-3-Haiku (standard) summarization successful")
                return _parse_structured_response(raw)
            else:
                raise Exception(f"Claude API error: {response.status_code} - {response.text}")
        else:
            raise Exception(f"Claude API error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Claude API request failed: {str(e)}")
    except KeyError as e:
        raise Exception(f"Claude API response format error: {str(e)}")
    except Exception as e:
        raise Exception(f"Claude API error: {str(e)}")


def _summarize_with_gpt(content, system_prompt):
    """Summarize using OpenAI GPT API"""
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use 3.5-turbo for cost savings
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        temperature=0.5
    )
    
    raw = response.choices[0].message.content
    print(f"✅ GPT-3.5-Turbo summarization successful")
    return _parse_structured_response(raw)


def _summarize_with_gemini(content, system_prompt):
    """Summarize using Google Gemini API"""
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_api_key}"
    
    data = {
        "contents": [{
            "parts": [{
                "text": f"{system_prompt}\n\n{content}"
            }]
        }]
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        print(f"✅ Gemini-Pro summarization successful")
        return _parse_structured_response(raw)
    else:
        raise Exception(f"Gemini API error: {response.status_code} - {response.text}")


def _parse_structured_response(raw_response):
    """Parse the structured response from AI models"""
    lines = raw_response.strip().split('\n')
    parsed = {
        "summary": "",
        "affected_tickers": "",
        "tone": "Neutral"
    }
    
    for line in lines:
        line = line.strip()
        if line.startswith("SUMMARY:"):
            parsed["summary"] = line.replace("SUMMARY:", "").strip()
        elif line.startswith("WHY IT MATTERS:"):
            # Combine with summary
            why_matters = line.replace("WHY IT MATTERS:", "").strip()
            if parsed["summary"]:
                parsed["summary"] += " " + why_matters
            else:
                parsed["summary"] = why_matters
        elif line.startswith("AFFECTED TICKERS:"):
            parsed["affected_tickers"] = line.replace("AFFECTED TICKERS:", "").strip()
        elif line.startswith("TONE:"):
            parsed["tone"] = line.replace("TONE:", "").strip()
    
    return parsed


def summarize_all(articles, model="claude", limit=15):
    """
    Summarize articles using specified AI model, limited to first N articles.
    
    Args:
        articles: List of article dictionaries
        model: AI model to use ('claude', 'gpt', 'gemini')
        limit: Maximum number of articles to summarize (default: 15)
    
    Returns:
        List of summarized articles with structured insights
    """
    # Limit the number of articles to process (default 15, max 20)
    max_limit = min(limit, 20)
    articles_to_process = articles[:max_limit]
    total_articles = len(articles)
    
    print(f"\n🧠 Summarizing first {len(articles_to_process)} of {total_articles} articles using {model.upper()}...\n")
    
    if total_articles > max_limit:
        print(f"⚠️  Limiting to first {max_limit} articles to manage API costs and processing time\n")
    
    summaries = []
    
    for i, article in enumerate(articles_to_process, 1):
        print(f"  {i}. {article.get('title', 'No title')[:80]}...")
        
        try:
            # Use specified model for summarization
            summary_result = summarize_article(article, model)
            
            # Combine original article data with structured summary
            summary_result = {
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "summary": summary_result.get("summary", ""),
                "affected_tickers": summary_result.get("affected_tickers", ""),
                "tone": summary_result.get("tone", "Neutral")
            }
            
            summaries.append(summary_result)
            
        except Exception as e:
            print(f"    ❌ Error summarizing: {str(e)}")
            save_failed_summary(article, str(e), model)
            # Add article without summary
            summary_result = {
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "summary": f"[Error summarizing: {str(e)}]",
                "affected_tickers": "",
                "tone": "Neutral"
            }
            summaries.append(summary_result)
    
    print(f"\n✅ Completed summarization of {len(summaries)} articles")
    
    # Report failed summaries
    if failed_summaries:
        print(f"⚠️  {len(failed_summaries)} failed summaries saved to retry queue")
    
    return summaries
