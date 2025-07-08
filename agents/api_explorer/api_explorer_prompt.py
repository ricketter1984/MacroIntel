#!/usr/bin/env python3
"""
API Explorer Prompt
Handles prompt preparation for AI-enhanced reasoning.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class APIExplorerPrompt:
    """Handles prompt preparation and AI-enhanced reasoning"""
    
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client
        
        if not self.client:
            logger.warning("No OpenAI client provided. AI enhancement will be disabled.")
    
    def interpret_query_with_openai(self, query: str, sample_endpoints: List[Dict[str, Any]]) -> str:
        """Use OpenAI to interpret and enhance the natural language query"""
        if not self.client:
            return query
        
        prompt = self._build_interpretation_prompt(query, sample_endpoints)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful API search assistant. Provide concise, relevant keywords."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            keywords = response.choices[0].message.content.strip()
            logger.info(f"OpenAI generated keywords: {keywords}")
            
            # Combine original query with keywords
            enhanced_query = f"{query} {keywords}"
            return enhanced_query
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            return query
    
    def _build_interpretation_prompt(self, query: str, sample_endpoints: List[Dict[str, Any]]) -> str:
        """Build the prompt for query interpretation"""
        return f"""
You are an API search assistant. The user is asking about API endpoints. 
Based on the query and the sample endpoints below, provide keywords that would help find relevant endpoints.

User Query: "{query}"

Sample Endpoints:
{json.dumps(sample_endpoints, indent=2)}

Provide 3-5 relevant keywords separated by spaces that would help find matching endpoints.
Focus on: HTTP methods, path patterns, functionality, and data types.

Keywords:"""
    
    def enhance_search_query(self, query: str, context: Dict[str, Any]) -> str:
        """Enhance a search query with additional context"""
        if not self.client:
            return query
        
        prompt = self._build_enhancement_prompt(query, context)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an API search assistant. Enhance queries with relevant technical terms."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.2
            )
            
            enhanced_query = response.choices[0].message.content.strip()
            logger.info(f"Enhanced query: {enhanced_query}")
            
            return enhanced_query
            
        except Exception as e:
            logger.error(f"Query enhancement failed: {str(e)}")
            return query
    
    def _build_enhancement_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build the prompt for query enhancement"""
        return f"""
Enhance the following API search query with relevant technical terms and synonyms.

Original Query: "{query}"

Context:
- Available APIs: {', '.join(context.get('available_apis', []))}
- Common patterns: {', '.join(context.get('common_patterns', []))}
- Data types: {', '.join(context.get('data_types', []))}

Provide an enhanced version of the query that includes relevant technical terms, HTTP methods, and data types that would help find the most relevant API endpoints.

Enhanced Query:"""
    
    def generate_search_suggestions(self, query: str, available_endpoints: List[Dict[str, Any]]) -> List[str]:
        """Generate search suggestions based on the query"""
        if not self.client:
            return []
        
        prompt = self._build_suggestions_prompt(query, available_endpoints)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an API search assistant. Provide alternative search queries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.4
            )
            
            suggestions_text = response.choices[0].message.content.strip()
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
            
            logger.info(f"Generated suggestions: {suggestions}")
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {str(e)}")
            return []
    
    def _build_suggestions_prompt(self, query: str, available_endpoints: List[Dict[str, Any]]) -> str:
        """Build the prompt for generating search suggestions"""
        return f"""
Based on the user's query and available endpoints, suggest alternative search queries that might be helpful.

User Query: "{query}"

Available Endpoint Types:
{json.dumps([{'method': ep.get('method', ''), 'path': ep.get('endpoint', ''), 'description': ep.get('description', '')[:50]} for ep in available_endpoints[:10]], indent=2)}

Provide 3-5 alternative search queries that the user might want to try.
Each suggestion should be on a new line and be a complete, natural language query.

Suggestions:"""
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the intent behind a query"""
        if not self.client:
            return {"intent": "search", "confidence": 0.5}
        
        prompt = self._build_intent_analysis_prompt(query)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an API search assistant. Analyze query intent."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            intent_text = response.choices[0].message.content.strip()
            
            # Parse the intent analysis
            intent_analysis = {
                "intent": "search",
                "confidence": 0.5,
                "data_types": [],
                "http_methods": [],
                "api_focus": None
            }
            
            # Simple parsing of the response
            if "data" in intent_text.lower():
                intent_analysis["data_types"].append("data")
            if "price" in intent_text.lower():
                intent_analysis["data_types"].append("price")
            if "get" in intent_text.lower():
                intent_analysis["http_methods"].append("GET")
            if "post" in intent_text.lower():
                intent_analysis["http_methods"].append("POST")
            
            logger.info(f"Query intent analysis: {intent_analysis}")
            return intent_analysis
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            return {"intent": "search", "confidence": 0.5}
    
    def _build_intent_analysis_prompt(self, query: str) -> str:
        """Build the prompt for intent analysis"""
        return f"""
Analyze the intent behind this API search query.

Query: "{query}"

Provide a brief analysis of:
1. What type of data the user is looking for
2. What HTTP methods might be relevant
3. Which APIs might be most relevant

Analysis:""" 