#!/usr/bin/env python3
"""
API Explorer Engine
Core functionality for schema loading, fuzzy matching, and result parsing.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from fuzzywuzzy import fuzz
import re
import html

logger = logging.getLogger(__name__)

class APIExplorerEngine:
    """Core engine for API schema exploration and search"""
    
    def __init__(self, schemas_dir: str = "data/api_schemas"):
        self.schemas_dir = Path(schemas_dir)
        self.api_schemas = {}
        self.endpoint_index = []
        
        logger.info(f"Initialized API Explorer Engine")
        logger.info(f"Schemas directory: {self.schemas_dir.absolute()}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might be artifacts
        text = re.sub(r'[^\w\s\-\.\/\?=&]', '', text)
        
        # Clean up common artifacts
        text = re.sub(r'https?://[^\s]+', '', text)  # Remove URLs
        text = re.sub(r'apiKey=[^\s]+', '', text)    # Remove API keys
        
        return text.strip()
    
    def load_schemas(self) -> Dict[str, Any]:
        """Load all JSON schema files from the schemas directory"""
        logger.info("Loading API schemas...")
        
        if not self.schemas_dir.exists():
            logger.error(f"Schemas directory does not exist: {self.schemas_dir}")
            return {}
        
        # Find all JSON files (exclude extraction_summary.json)
        json_files = [f for f in self.schemas_dir.glob("*.json") 
                     if f.name != "extraction_summary.json"]
        
        if not json_files:
            logger.warning(f"No JSON schema files found in {self.schemas_dir}")
            return {}
        
        logger.info(f"Found {len(json_files)} schema files")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                api_name = schema.get('api_info', {}).get('name', json_file.stem)
                self.api_schemas[api_name] = schema
                
                # Index endpoints
                self._index_endpoints(api_name, schema)
                
                logger.info(f"Loaded schema for: {api_name}")
                
            except Exception as e:
                logger.error(f"Error loading schema from {json_file.name}: {str(e)}")
        
        logger.info(f"Successfully loaded {len(self.api_schemas)} API schemas")
        logger.info(f"Indexed {len(self.endpoint_index)} endpoints")
        
        return self.api_schemas
    
    def _index_endpoints(self, api_name: str, schema: Dict[str, Any]):
        """Index endpoints for search"""
        endpoints = schema.get('endpoints', [])
        
        for endpoint in endpoints:
            # Clean the endpoint data
            clean_description = self._clean_text(endpoint.get('description', ''))
            clean_method = self._clean_text(endpoint.get('method', ''))
            clean_path = self._clean_text(endpoint.get('path', ''))
            
            # Skip endpoints with obviously malformed data
            if len(clean_method) > 10 or len(clean_path) > 200:
                continue
            
            # Create searchable endpoint record
            indexed_endpoint = {
                'api_name': api_name,
                'endpoint': clean_path,
                'method': clean_method,
                'url': clean_path,
                'description': clean_description,
                'parameters': endpoint.get('parameters', []),
                'responses': endpoint.get('responses', []),
                'required_params': self._extract_required_params(endpoint.get('parameters', [])),
                'full_endpoint_data': endpoint
            }
            
            # Only add if we have meaningful data
            if clean_path and clean_method and len(clean_description) > 10:
                self.endpoint_index.append(indexed_endpoint)
    
    def _extract_required_params(self, parameters: List[Dict[str, Any]]) -> List[str]:
        """Extract required parameters from parameter list"""
        required = []
        for param in parameters:
            if param.get('required', False):
                param_name = self._clean_text(param.get('name', ''))
                if param_name:
                    required.append(param_name)
        return required
    
    def search_endpoints(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search endpoints using natural language query"""
        logger.info(f"Searching for: {query}")
        
        if not self.endpoint_index:
            logger.warning("No endpoints indexed. Please load schemas first.")
            return []
        
        # Perform fuzzy search
        results = self._fuzzy_search(query, max_results)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                'endpoint': result['endpoint'],
                'method': result['method'],
                'url': result['url'],
                'required_params': result['required_params'],
                'description': result['description'][:200] + "..." if len(result['description']) > 200 else result['description'],
                'api_name': result['api_name'],
                'score': result.get('score', 0)
            }
            formatted_results.append(formatted_result)
        
        logger.info(f"Found {len(formatted_results)} matching endpoints")
        return formatted_results
    
    def _fuzzy_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform fuzzy search on indexed endpoints"""
        query_lower = query.lower()
        results = []
        
        for endpoint in self.endpoint_index:
            score = 0
            
            # Search in different fields with different weights
            fields_to_search = [
                (endpoint['description'], 3),  # Description gets highest weight
                (endpoint['endpoint'], 2),     # Endpoint path gets medium weight
                (endpoint['method'], 1),       # Method gets lower weight
                (endpoint['api_name'], 1),     # API name gets lower weight
            ]
            
            for field_value, weight in fields_to_search:
                if field_value:
                    field_lower = field_value.lower()
                    
                    # Exact match gets highest score
                    if query_lower in field_lower:
                        score += weight * 100
                    
                    # Partial word matches
                    query_words = query_lower.split()
                    for word in query_words:
                        if len(word) > 2:  # Only consider words longer than 2 chars
                            if word in field_lower:
                                score += weight * 50
                            
                            # Fuzzy match for similar words
                            fuzzy_score = fuzz.partial_ratio(word, field_lower)
                            if fuzzy_score > 80:
                                score += weight * (float(fuzzy_score) / 100) * 30
            
            # Check if any query words match parameter names
            for param in endpoint['parameters']:
                param_name = self._clean_text(param.get('name', '')).lower()
                param_desc = self._clean_text(param.get('description', '')).lower()
                
                for word in query_lower.split():
                    if len(word) > 2:
                        if word in param_name or word in param_desc:
                            score += 20
            
            if score > 0:
                result = endpoint.copy()
                result['score'] = float(score)
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    def get_endpoint_details(self, api_name: str, endpoint_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific endpoint"""
        for endpoint in self.endpoint_index:
            if (endpoint['api_name'] == api_name and 
                endpoint['endpoint'] == endpoint_path):
                return endpoint
        return None
    
    def list_apis(self) -> List[str]:
        """List all loaded APIs"""
        return list(self.api_schemas.keys())
    
    def get_api_summary(self, api_name: str) -> Dict[str, Any]:
        """Get summary information about a specific API"""
        if api_name not in self.api_schemas:
            return {}
        
        schema = self.api_schemas[api_name]
        endpoints = [e for e in self.endpoint_index if e['api_name'] == api_name]
        
        return {
            'name': api_name,
            'version': schema.get('api_info', {}).get('version', 'unknown'),
            'base_url': schema.get('api_info', {}).get('base_url', ''),
            'total_endpoints': len(endpoints),
            'methods': list(set(e['method'] for e in endpoints)),
            'description': self._clean_text(schema.get('metadata', {}).get('description', ''))
        }
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Main method to ask a question and get structured response"""
        logger.info(f"Processing question: {question}")
        
        # Load schemas if not already loaded
        if not self.api_schemas:
            self.load_schemas()
        
        # Search for relevant endpoints
        results = self.search_endpoints(question, max_results=5)
        
        # Format response
        response = {
            'question': question,
            'total_results': len(results),
            'results': results,
            'timestamp': str(Path().stat().st_mtime) if Path().exists() else ''
        }
        
        return response 