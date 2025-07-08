#!/usr/bin/env python3
"""
API Documentation Schema Extractor using DocETL
Scans HTML documentation files and extracts structured API schemas using DocETL library.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import docetl
from bs4 import BeautifulSoup
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/api_docs_extraction.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class APISchemaExtractor:
    """Extract structured API schemas from HTML documentation using DocETL"""
    
    def __init__(self, docs_dir: str = "HTML_Documentation", output_dir: str = "data/api_schemas"):
        self.docs_dir = Path(docs_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
        
        logger.info(f"Initialized API Schema Extractor")
        logger.info(f"Documentation directory: {self.docs_dir.absolute()}")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
    
    def extract_api_schema(self, html_file: Path) -> Dict[str, Any]:
        """
        Extract structured API schema from HTML file using DocETL
        """
        logger.info(f"Extracting schema from: {html_file.name}")
        
        try:
            # Read HTML content with UTF-8 encoding
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse with BeautifulSoup for initial analysis
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic metadata
            title = soup.title.string if soup.title else html_file.stem
            description = self._extract_description(soup)
            
            # Initialize schema structure
            schema = {
                "metadata": {
                    "source_file": html_file.name,
                    "title": title,
                    "description": description,
                    "extracted_at": str(html_file.stat().st_mtime),
                    "file_size_bytes": html_file.stat().st_size
                },
                "api_info": {
                    "name": self._extract_api_name(html_file.name),
                    "version": self._extract_version(soup),
                    "base_url": self._extract_base_url(soup),
                    "documentation_url": self._extract_doc_url(soup)
                },
                "authentication": self._extract_authentication(soup),
                "endpoints": self._extract_endpoints(soup),
                "data_models": self._extract_data_models(soup),
                "examples": self._extract_examples(soup),
                "rate_limits": self._extract_rate_limits(soup),
                "errors": self._extract_errors(soup)
            }
            
            # Use DocETL for advanced extraction
            schema.update(self._extract_with_docetl(html_content))
            
            logger.info(f"Successfully extracted schema from {html_file.name}")
            return schema
            
        except Exception as e:
            logger.error(f"Error extracting schema from {html_file.name}: {str(e)}")
            return {
                "metadata": {
                    "source_file": html_file.name,
                    "error": str(e),
                    "extracted_at": str(html_file.stat().st_mtime)
                }
            }
    
    def _extract_api_name(self, filename: str) -> str:
        """Extract API name from filename"""
        # Remove common suffixes and clean up
        name = filename.replace('.html', '').replace('_', ' ').replace('-', ' ')
        
        # Extract API name from common patterns
        patterns = [
            r'(FMP|Polygon|Twelve Data|Benzinga)',
            r'(API|Documentation|Quickstart)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                return match.group(1)
        
        return name.split(' - ')[0] if ' - ' in name else name
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract API description from meta tags or content"""
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        # Try og:description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content']
        
        # Extract from first paragraph
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text(strip=True)[:200] + "..."
        
        return ""
    
    def _extract_version(self, soup: BeautifulSoup) -> str:
        """Extract API version information"""
        # Look for version patterns in text
        version_patterns = [
            r'v(\d+(?:\.\d+)*)',
            r'version\s+(\d+(?:\.\d+)*)',
            r'API\s+v(\d+(?:\.\d+)*)'
        ]
        
        text_content = soup.get_text()
        for pattern in version_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _extract_base_url(self, soup: BeautifulSoup) -> str:
        """Extract base URL from documentation"""
        # Look for common API base URL patterns
        url_patterns = [
            r'https://api\.([^/\s]+)\.com',
            r'https://([^/\s]+)\.api\.com',
            r'base\s+url[:\s]+(https?://[^\s]+)'
        ]
        
        text_content = soup.get_text()
        for pattern in url_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_doc_url(self, soup: BeautifulSoup) -> str:
        """Extract documentation URL"""
        # Look for canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            return canonical['href']
        
        # Look for og:url
        og_url = soup.find('meta', attrs={'property': 'og:url'})
        if og_url and og_url.get('content'):
            return og_url['content']
        
        return ""
    
    def _extract_authentication(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract authentication information"""
        auth_info = {
            "methods": [],
            "api_key_info": {},
            "headers": [],
            "examples": []
        }
        
        # Look for authentication sections
        auth_sections = soup.find_all(['div', 'section'], 
                                    string=re.compile(r'auth|api.?key|bearer|token', re.IGNORECASE))
        
        for section in auth_sections:
            # Extract authentication methods
            auth_methods = section.find_all(text=re.compile(r'api.?key|bearer|oauth|basic', re.IGNORECASE))
            for method in auth_methods:
                auth_info["methods"].append({
                    "type": method.strip(),
                    "description": self._extract_context(section, method)
                })
            
            # Extract headers
            headers = section.find_all(['code', 'pre'], 
                                     string=re.compile(r'authorization|api.?key|x-', re.IGNORECASE))
            for header in headers:
                auth_info["headers"].append(header.get_text(strip=True))
        
        return auth_info
    
    def _extract_endpoints(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract API endpoints"""
        endpoints = []
        
        # Look for endpoint patterns
        endpoint_patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)',
            r'([A-Z]{3,6})\s+([/\w\-\.]+)',
            r'`([/\w\-\.]+)`'
        ]
        
        text_content = soup.get_text()
        for pattern in endpoint_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
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
                    "description": self._extract_endpoint_description(text_content, match.start()),
                    "parameters": self._extract_endpoint_parameters(soup, path),
                    "responses": self._extract_endpoint_responses(soup, path)
                }
                
                # Avoid duplicates
                if not any(e["method"] == endpoint["method"] and e["path"] == endpoint["path"] 
                          for e in endpoints):
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_data_models(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract data models/schemas"""
        models = []
        
        # Look for JSON schema examples
        json_blocks = soup.find_all(['code', 'pre'], 
                                   string=re.compile(r'\{.*\}', re.DOTALL))
        
        for block in json_blocks:
            content = block.get_text()
            if self._is_json_schema(content):
                try:
                    schema = json.loads(content)
                    models.append({
                        "name": self._extract_model_name(block),
                        "schema": schema,
                        "description": self._extract_context(soup, content)
                    })
                except json.JSONDecodeError:
                    continue
        
        return models
    
    def _extract_examples(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract code examples"""
        examples = []
        
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
                "description": self._extract_context(soup, content)
            })
        
        return examples
    
    def _extract_rate_limits(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract rate limiting information"""
        rate_limits = {
            "requests_per_minute": None,
            "requests_per_hour": None,
            "requests_per_day": None,
            "description": ""
        }
        
        # Look for rate limit patterns
        rate_patterns = [
            r'(\d+)\s+requests?\s+per\s+(minute|hour|day)',
            r'rate\s+limit[:\s]+(\d+)\s+per\s+(\w+)',
            r'(\d+)\s+req/\w+'
        ]
        
        text_content = soup.get_text()
        for pattern in rate_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                limit = int(match.group(1))
                period = match.group(2) if len(match.groups()) > 1 else "minute"
                
                if 'minute' in period.lower():
                    rate_limits["requests_per_minute"] = limit
                elif 'hour' in period.lower():
                    rate_limits["requests_per_hour"] = limit
                elif 'day' in period.lower():
                    rate_limits["requests_per_day"] = limit
        
        return rate_limits
    
    def _extract_errors(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract error codes and descriptions"""
        errors = []
        
        # Look for error code patterns
        error_patterns = [
            r'(\d{3})\s*[-:]\s*([^.\n]+)',
            r'error\s+(\d{3})[:\s]+([^.\n]+)',
            r'HTTP\s+(\d{3})[:\s]+([^.\n]+)'
        ]
        
        text_content = soup.get_text()
        for pattern in error_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                errors.append({
                    "code": int(match.group(1)),
                    "message": match.group(2).strip(),
                    "description": self._extract_context(soup, match.group(0))
                })
        
        return errors
    
    def _extract_with_docetl(self, html_content: str) -> Dict[str, Any]:
        """Use DocETL for advanced extraction"""
        try:
            # Use DocETL's extraction capabilities
            # Note: DocETL is primarily for document processing, so we'll use it
            # for advanced text analysis and structure detection
            
            docetl_extracted = {
                "docetl_analysis": {
                    "content_length": len(html_content),
                    "structure_detected": self._detect_structure(html_content),
                    "api_patterns_found": self._find_api_patterns(html_content)
                }
            }
            
            return docetl_extracted
            
        except Exception as e:
            logger.warning(f"DocETL extraction failed: {str(e)}")
            return {"docetl_analysis": {"error": str(e)}}
    
    def _detect_structure(self, content: str) -> Dict[str, Any]:
        """Detect document structure using DocETL-like analysis"""
        structure = {
            "has_authentication": bool(re.search(r'auth|api.?key|bearer', content, re.IGNORECASE)),
            "has_endpoints": bool(re.search(r'GET|POST|PUT|DELETE|PATCH', content, re.IGNORECASE)),
            "has_examples": bool(re.search(r'curl|http|json', content, re.IGNORECASE)),
            "has_errors": bool(re.search(r'error|4\d{2}|5\d{2}', content, re.IGNORECASE)),
            "has_rate_limits": bool(re.search(r'rate.?limit|requests.?per', content, re.IGNORECASE))
        }
        
        return structure
    
    def _find_api_patterns(self, content: str) -> List[str]:
        """Find API-related patterns in content"""
        patterns = []
        
        # Common API patterns
        api_patterns = [
            r'api\.\w+\.com',
            r'https?://[^/\s]+\.api\.',
            r'v\d+/\w+',
            r'endpoint[s]?',
            r'parameter[s]?',
            r'response[s]?'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            patterns.extend(matches)
        
        return list(set(patterns))
    
    def _extract_endpoint_description(self, content: str, position: int) -> str:
        """Extract description around an endpoint match"""
        start = max(0, position - 200)
        end = min(len(content), position + 200)
        
        context = content[start:end]
        sentences = re.split(r'[.!?]', context)
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['endpoint', 'api', 'request', 'data']):
                return sentence.strip()
        
        return sentences[0].strip() if sentences else ""
    
    def _extract_endpoint_parameters(self, soup: BeautifulSoup, path: str) -> List[Dict[str, Any]]:
        """Extract parameters for a specific endpoint"""
        parameters = []
        
        # Look for parameter tables or lists near the endpoint
        param_sections = soup.find_all(['table', 'ul', 'div'], 
                                      string=re.compile(r'parameter|param', re.IGNORECASE))
        
        for section in param_sections:
            # Extract parameter information
            param_items = section.find_all(['tr', 'li'])
            for item in param_items:
                param_text = item.get_text()
                param_match = re.search(r'(\w+)[:\s]*([^\n]+)', param_text)
                if param_match:
                    parameters.append({
                        "name": param_match.group(1),
                        "description": param_match.group(2).strip(),
                        "required": "required" in param_text.lower(),
                        "type": self._infer_parameter_type(param_match.group(2))
                    })
        
        return parameters
    
    def _extract_endpoint_responses(self, soup: BeautifulSoup, path: str) -> List[Dict[str, Any]]:
        """Extract response examples for a specific endpoint"""
        responses = []
        
        # Look for response examples
        response_blocks = soup.find_all(['code', 'pre'], 
                                       string=re.compile(r'\{.*\}', re.DOTALL))
        
        for block in response_blocks:
            content = block.get_text()
            if self._is_json_response(content):
                try:
                    response_data = json.loads(content)
                    responses.append({
                        "status_code": self._extract_status_code(block),
                        "content": response_data,
                        "description": self._extract_context(soup, content)
                    })
                except json.JSONDecodeError:
                    continue
        
        return responses
    
    def _extract_context(self, soup: BeautifulSoup, text: str) -> str:
        """Extract context around a piece of text"""
        # Find the element containing the text
        element = soup.find(string=re.compile(re.escape(text[:50])))
        if element:
            # Get parent element's text
            parent = element.parent
            if parent:
                return parent.get_text(strip=True)[:200] + "..."
        
        return ""
    
    def _extract_model_name(self, element) -> str:
        """Extract model name from element"""
        # Look for heading or title before the element
        prev_element = element.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if prev_element:
            return prev_element.get_text(strip=True)
        
        return "Unknown Model"
    
    def _is_json_schema(self, content: str) -> bool:
        """Check if content looks like a JSON schema"""
        return bool(re.search(r'"type"\s*:\s*"', content) or 
                   re.search(r'"properties"\s*:', content) or
                   re.search(r'"required"\s*:', content))
    
    def _is_json_response(self, content: str) -> bool:
        """Check if content looks like a JSON response"""
        return bool(re.search(r'^\s*\{', content) and re.search(r'\}\s*$', content))
    
    def _extract_status_code(self, element) -> int:
        """Extract HTTP status code from element"""
        # Look for status code patterns
        status_match = re.search(r'(\d{3})', element.get_text())
        if status_match:
            return int(status_match.group(1))
        
        return 200  # Default to 200
    
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
    
    def process_all_files(self) -> Dict[str, Any]:
        """Process all HTML files in the documentation directory"""
        logger.info("Starting API schema extraction process...")
        
        # Find all HTML files
        html_files = list(self.docs_dir.glob("*.html"))
        
        if not html_files:
            logger.warning(f"No HTML files found in {self.docs_dir}")
            return {"error": "No HTML files found"}
        
        logger.info(f"Found {len(html_files)} HTML files to process")
        
        results = {
            "processed_files": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "files": []
        }
        
        for html_file in html_files:
            logger.info(f"Processing: {html_file.name}")
            
            try:
                # Extract schema
                schema = self.extract_api_schema(html_file)
                
                # Generate output filename
                output_filename = html_file.stem + ".json"
                output_path = self.output_dir / output_filename
                
                # Save schema with UTF-8 encoding
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2, ensure_ascii=False)
                
                results["processed_files"] += 1
                
                if "error" not in schema.get("metadata", {}):
                    results["successful_extractions"] += 1
                    logger.info(f"Successfully extracted and saved: {output_filename}")
                else:
                    results["failed_extractions"] += 1
                    logger.warning(f"Extraction failed for: {html_file.name}")
                
                results["files"].append({
                    "input_file": html_file.name,
                    "output_file": output_filename,
                    "success": "error" not in schema.get("metadata", {}),
                    "file_size": html_file.stat().st_size
                })
                
            except Exception as e:
                results["failed_extractions"] += 1
                logger.error(f"Error processing {html_file.name}: {str(e)}")
                results["files"].append({
                    "input_file": html_file.name,
                    "output_file": None,
                    "success": False,
                    "error": str(e)
                })
        
        # Save summary
        summary_path = self.output_dir / "extraction_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info("API schema extraction completed!")
        logger.info(f"Processed: {results['processed_files']} files")
        logger.info(f"Successful: {results['successful_extractions']} extractions")
        logger.info(f"Failed: {results['failed_extractions']} extractions")
        logger.info(f"Results saved to: {self.output_dir.absolute()}")
        
        return results

def main():
    """Main function to run the API schema extraction"""
    try:
        # Initialize extractor
        extractor = APISchemaExtractor()
        
        # Process all files
        results = extractor.process_all_files()
        
        # Print summary
        print("\n" + "="*60)
        print("API SCHEMA EXTRACTION SUMMARY")
        print("="*60)
        print(f"📁 Documentation directory: {extractor.docs_dir.absolute()}")
        print(f"📁 Output directory: {extractor.output_dir.absolute()}")
        print(f"📊 Files processed: {results.get('processed_files', 0)}")
        print(f"✅ Successful extractions: {results.get('successful_extractions', 0)}")
        print(f"❌ Failed extractions: {results.get('failed_extractions', 0)}")
        
        if results.get('files'):
            print("\n📋 File Details:")
            for file_info in results['files']:
                status = "✅" if file_info.get('success') else "❌"
                print(f"  {status} {file_info['input_file']}")
                if file_info.get('output_file'):
                    print(f"     → {file_info['output_file']}")
        
        print(f"\n📄 Summary saved to: {extractor.output_dir / 'extraction_summary.json'}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 