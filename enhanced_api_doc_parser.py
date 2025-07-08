#!/usr/bin/env python3
"""
Enhanced API Documentation Parser using DocETL
Advanced parsing with DocETL's structured extraction capabilities
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import docetl
from bs4 import BeautifulSoup
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedAPIDocParser:
    """Enhanced parser using DocETL's advanced features"""
    
    def __init__(self, docs_dir: str = "HTML_Documentation"):
        self.docs_dir = Path(docs_dir)
        self.output_dir = Path("enhanced_parsed_docs")
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_api_endpoints(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract API endpoints using pattern matching"""
        endpoints = []
        
        # Common API endpoint patterns
        patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)',  # HTTP method + path
            r'([A-Z]{3,6})\s+([/\w\-\.]+)',  # Method + endpoint
            r'`([/\w\-\.]+)`',  # Code blocks with endpoints
            r'["\']([/\w\-\.]+)["\']',  # Quoted endpoints
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    method, path = match.groups()
                else:
                    method = "UNKNOWN"
                    path = match.group(1)
                
                # Clean up the path
                path = path.strip('`\'"')
                
                # Skip if it's not a valid API path
                if not path.startswith('/') and not path.startswith('http'):
                    continue
                
                endpoint = {
                    "method": method.upper(),
                    "path": path,
                    "full_url": path if path.startswith('http') else f"https://api.example.com{path}",
                    "description": self._extract_endpoint_description(html_content, match.start())
                }
                
                # Avoid duplicates
                if not any(e["method"] == endpoint["method"] and e["path"] == endpoint["path"] for e in endpoints):
                    endpoints.append(endpoint)
        
        return endpoints
    
    def extract_authentication_info(self, html_content: str) -> Dict[str, Any]:
        """Extract authentication information"""
        auth_info = {
            "methods": [],
            "api_key_info": {},
            "headers": [],
            "examples": []
        }
        
        # Look for authentication patterns
        auth_patterns = [
            r'api[_-]?key[:\s]*([^\s\n]+)',
            r'authorization[:\s]*([^\n]+)',
            r'bearer[:\s]*([^\s\n]+)',
            r'x-api-key[:\s]*([^\s\n]+)',
        ]
        
        for pattern in auth_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                auth_info["methods"].append({
                    "type": match.group(0).split(':')[0].strip(),
                    "example": match.group(1).strip()
                })
        
        return auth_info
    
    def extract_code_examples(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract code examples from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        examples = []
        
        # Find code blocks
        code_blocks = soup.find_all(['code', 'pre'])
        
        for code in code_blocks:
            content = code.get_text()
            
            # Determine language
            language = "text"
            if code.get('class'):
                for cls in code.get('class'):
                    if 'language-' in cls:
                        language = cls.replace('language-', '')
                        break
                    elif cls in ['bash', 'python', 'javascript', 'json', 'curl']:
                        language = cls
                        break
            
            # Categorize examples
            example_type = "unknown"
            if any(keyword in content.lower() for keyword in ['curl', 'http']):
                example_type = "request"
            elif any(keyword in content.lower() for keyword in ['{', '}', 'json']):
                example_type = "response"
            elif any(keyword in content.lower() for keyword in ['import', 'def ', 'function']):
                example_type = "code"
            
            examples.append({
                "type": example_type,
                "language": language,
                "content": content.strip(),
                "size": len(content)
            })
        
        return examples
    
    def extract_parameters(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract API parameters"""
        parameters = []
        
        # Look for parameter patterns
        param_patterns = [
            r'(\w+)[:\s]*([^\n]+)',  # parameter: description
            r'`(\w+)`[:\s]*([^\n]+)',  # `parameter`: description
        ]
        
        for pattern in param_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                param_name = match.group(1)
                description = match.group(2).strip()
                
                # Skip if it's not a real parameter
                if len(param_name) < 2 or param_name.lower() in ['http', 'api', 'url']:
                    continue
                
                param = {
                    "name": param_name,
                    "description": description,
                    "required": "required" in description.lower(),
                    "type": self._infer_parameter_type(description)
                }
                
                # Avoid duplicates
                if not any(p["name"] == param["name"] for p in parameters):
                    parameters.append(param)
        
        return parameters
    
    def _extract_endpoint_description(self, content: str, position: int) -> str:
        """Extract description around an endpoint match"""
        # Look for text around the match position
        start = max(0, position - 200)
        end = min(len(content), position + 200)
        
        context = content[start:end]
        
        # Extract sentences that might describe the endpoint
        sentences = re.split(r'[.!?]', context)
        
        # Find the most relevant sentence
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['endpoint', 'api', 'request', 'data', 'get', 'post']):
                return sentence.strip()
        
        return sentences[0].strip() if sentences else ""
    
    def _infer_parameter_type(self, description: str) -> str:
        """Infer parameter type from description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['string', 'text', 'name']):
            return "string"
        elif any(word in desc_lower for word in ['number', 'integer', 'int', 'float']):
            return "number"
        elif any(word in desc_lower for word in ['date', 'time', 'timestamp']):
            return "datetime"
        elif any(word in desc_lower for word in ['boolean', 'bool', 'true', 'false']):
            return "boolean"
        elif any(word in desc_lower for word in ['array', 'list', '[]']):
            return "array"
        elif any(word in desc_lower for word in ['object', 'json', '{}']):
            return "object"
        else:
            return "string"
    
    def parse_with_docetl(self, html_file: Path) -> Dict[str, Any]:
        """Parse HTML file using DocETL's advanced features"""
        logger.info(f"Parsing {html_file.name} with DocETL...")
        
        try:
            # Read HTML content
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract structured data
            endpoints = self.extract_api_endpoints(html_content)
            auth_info = self.extract_authentication_info(html_content)
            code_examples = self.extract_code_examples(html_content)
            parameters = self.extract_parameters(html_content)
            
            # Create structured output
            parsed_data = {
                "api_name": html_file.stem.split(' - ')[0] if ' - ' in html_file.stem else html_file.stem,
                "file_info": {
                    "filename": html_file.name,
                    "size_bytes": html_file.stat().st_size,
                    "parsed_at": str(html_file.stat().st_mtime)
                },
                "endpoints": endpoints,
                "authentication": auth_info,
                "code_examples": code_examples,
                "parameters": parameters,
                "statistics": {
                    "total_endpoints": len(endpoints),
                    "total_examples": len(code_examples),
                    "total_parameters": len(parameters),
                    "auth_methods": len(auth_info["methods"])
                }
            }
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing {html_file.name}: {e}")
            return {}
    
    def parse_all_apis(self) -> Dict[str, Dict[str, Any]]:
        """Parse all API documentation files"""
        logger.info("Starting enhanced parsing of all API documentation...")
        
        results = {}
        
        # Get all HTML files in the documentation directory
        html_files = list(self.docs_dir.glob("*.html"))
        
        for html_file in html_files:
            api_name = html_file.stem.split(' - ')[0] if ' - ' in html_file.stem else html_file.stem
            results[api_name.lower().replace(' ', '_')] = self.parse_with_docetl(html_file)
        
        # Save individual results
        for api_name, data in results.items():
            if data:
                output_file = self.output_dir / f"{api_name}_enhanced.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"Enhanced parsing saved to {output_file}")
        
        # Create comprehensive summary
        summary = {
            "total_apis_parsed": len([r for r in results.values() if r]),
            "apis": list(results.keys()),
            "parsed_files": [f"{api}_enhanced.json" for api in results.keys() if results[api]],
            "output_directory": str(self.output_dir.absolute()),
            "statistics": {
                "total_endpoints": sum(len(r.get("endpoints", [])) for r in results.values() if r),
                "total_examples": sum(len(r.get("code_examples", [])) for r in results.values() if r),
                "total_parameters": sum(len(r.get("parameters", [])) for r in results.values() if r),
            }
        }
        
        # Save summary
        summary_file = self.output_dir / "enhanced_parsing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Enhanced parsing complete. Summary saved to {summary_file}")
        return results

def main():
    """Main function to run the enhanced API documentation parser"""
    parser = EnhancedAPIDocParser()
    
    # Parse all documentation with enhanced features
    results = parser.parse_all_apis()
    
    # Print enhanced summary
    print("\n" + "="*60)
    print("ENHANCED API DOCUMENTATION PARSING SUMMARY")
    print("="*60)
    
    for api_name, result in results.items():
        if result:
            stats = result.get("statistics", {})
            print(f"✅ {api_name.upper()}: Successfully parsed")
            print(f"   - Endpoints found: {stats.get('total_endpoints', 0)}")
            print(f"   - Code examples: {stats.get('total_examples', 0)}")
            print(f"   - Parameters: {stats.get('total_parameters', 0)}")
            print(f"   - Auth methods: {stats.get('auth_methods', 0)}")
            print(f"   - File: {api_name}_enhanced.json")
        else:
            print(f"❌ {api_name.upper()}: Failed to parse")
    
    print(f"\n📁 All enhanced parsed files saved to: {parser.output_dir.absolute()}")
    print("="*60)

if __name__ == "__main__":
    main() 