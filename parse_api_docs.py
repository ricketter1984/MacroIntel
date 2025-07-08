#!/usr/bin/env python3
"""
API Documentation Parser using DocETL
Parses HTML documentation from FMP, Polygon, Twelve Data, and Benzinga APIs
into structured formats for easier consumption and analysis.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
import docetl
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIDocParser:
    """Parser for API documentation using DocETL and BeautifulSoup"""
    
    def __init__(self, docs_dir: str = "HTML_Documentation"):
        self.docs_dir = Path(docs_dir)
        self.output_dir = Path("parsed_docs")
        self.output_dir.mkdir(exist_ok=True)
        
    def parse_polygon_docs(self) -> Dict[str, Any]:
        """Parse Polygon REST API documentation"""
        logger.info("Parsing Polygon API documentation...")
        
        doc_path = self.docs_dir / "REST API Quickstart ｜ Polygon (7_4_2025 8：18：32 AM).html"
        
        if not doc_path.exists():
            logger.error(f"Polygon documentation not found: {doc_path}")
            return {}
            
        try:
            # Read the HTML file
            with open(doc_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse with BeautifulSoup for initial structure analysis
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract key sections
            parsed_data = {
                "api_name": "Polygon",
                "title": soup.title.string if soup.title else "Polygon REST API",
                "endpoints": [],
                "authentication": {},
                "examples": [],
                "rate_limits": {},
                "metadata": {
                    "file_size": doc_path.stat().st_size,
                    "parsed_at": str(doc_path.stat().st_mtime)
                }
            }
            
            # Extract headings and their content
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
            for heading in headings:
                section = {
                    "level": heading.name,
                    "text": heading.get_text(strip=True),
                    "content": self._extract_section_content(heading)
                }
                parsed_data["endpoints"].append(section)
            
            # Look for code blocks and examples
            code_blocks = soup.find_all(['code', 'pre'])
            for i, code in enumerate(code_blocks):
                example = {
                    "type": code.name,
                    "content": code.get_text(),
                    "language": code.get('class', ['text'])[0] if code.get('class') else 'text'
                }
                parsed_data["examples"].append(example)
            
            # Save structured data
            output_file = self.output_dir / "polygon_api_parsed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Polygon docs parsed and saved to {output_file}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing Polygon docs: {e}")
            return {}
    
    def parse_fmp_docs(self) -> Dict[str, Any]:
        """Parse FMP API documentation"""
        logger.info("Parsing FMP API documentation...")
        
        doc_path = self.docs_dir / "Documentation V2 - API Reference ｜ FMP (7_4_2025 8：19：24 AM).html"
        
        if not doc_path.exists():
            logger.error(f"FMP documentation not found: {doc_path}")
            return {}
            
        try:
            # Read the HTML file
            with open(doc_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            parsed_data = {
                "api_name": "FMP",
                "title": soup.title.string if soup.title else "FMP API Documentation",
                "endpoints": [],
                "authentication": {},
                "examples": [],
                "rate_limits": {},
                "metadata": {
                    "file_size": doc_path.stat().st_size,
                    "parsed_at": str(doc_path.stat().st_mtime)
                }
            }
            
            # Extract API endpoints and methods
            # Look for common patterns in API documentation
            endpoint_sections = soup.find_all(['div', 'section'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['endpoint', 'api', 'method']))
            
            for section in endpoint_sections:
                endpoint_data = self._extract_endpoint_data(section)
                if endpoint_data:
                    parsed_data["endpoints"].append(endpoint_data)
            
            # Save structured data
            output_file = self.output_dir / "fmp_api_parsed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"FMP docs parsed and saved to {output_file}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing FMP docs: {e}")
            return {}
    
    def parse_twelve_data_docs(self) -> Dict[str, Any]:
        """Parse Twelve Data API documentation"""
        logger.info("Parsing Twelve Data API documentation...")
        
        doc_path = self.docs_dir / "API Documentation - Twelve Data (7_4_2025 8：23：18 AM).html"
        
        if not doc_path.exists():
            logger.error(f"Twelve Data documentation not found: {doc_path}")
            return {}
            
        try:
            # Read the HTML file
            with open(doc_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            parsed_data = {
                "api_name": "Twelve Data",
                "title": soup.title.string if soup.title else "Twelve Data API Documentation",
                "endpoints": [],
                "authentication": {},
                "examples": [],
                "rate_limits": {},
                "metadata": {
                    "file_size": doc_path.stat().st_size,
                    "parsed_at": str(doc_path.stat().st_mtime)
                }
            }
            
            # Extract endpoints and documentation sections
            sections = soup.find_all(['div', 'section', 'article'])
            for section in sections:
                section_data = self._extract_section_data(section)
                if section_data:
                    parsed_data["endpoints"].append(section_data)
            
            # Save structured data
            output_file = self.output_dir / "twelve_data_api_parsed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Twelve Data docs parsed and saved to {output_file}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing Twelve Data docs: {e}")
            return {}
    
    def parse_benzinga_docs(self) -> Dict[str, Any]:
        """Parse Benzinga API documentation"""
        logger.info("Parsing Benzinga API documentation...")
        
        doc_path = self.docs_dir / "Home - Benzinga (7_4_2025 7：24：57 PM).html"
        
        if not doc_path.exists():
            logger.error(f"Benzinga documentation not found: {doc_path}")
            return {}
            
        try:
            # Read the HTML file
            with open(doc_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            parsed_data = {
                "api_name": "Benzinga",
                "title": soup.title.string if soup.title else "Benzinga API Documentation",
                "endpoints": [],
                "authentication": {},
                "examples": [],
                "rate_limits": {},
                "metadata": {
                    "file_size": doc_path.stat().st_size,
                    "parsed_at": str(doc_path.stat().st_mtime)
                }
            }
            
            # Extract navigation and content sections
            nav_sections = soup.find_all(['nav', 'div'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['nav', 'menu', 'sidebar']))
            
            for nav in nav_sections:
                nav_data = self._extract_navigation_data(nav)
                if nav_data:
                    parsed_data["endpoints"].append(nav_data)
            
            # Save structured data
            output_file = self.output_dir / "benzinga_api_parsed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Benzinga docs parsed and saved to {output_file}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing Benzinga docs: {e}")
            return {}
    
    def _extract_section_content(self, heading) -> str:
        """Extract content following a heading"""
        content = []
        current = heading.next_sibling
        
        while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
            if hasattr(current, 'get_text'):
                text = current.get_text(strip=True)
                if text:
                    content.append(text)
            current = current.next_sibling
            
        return ' '.join(content)
    
    def _extract_endpoint_data(self, section) -> Dict[str, Any]:
        """Extract endpoint information from a section"""
        endpoint_data = {
            "name": "",
            "method": "",
            "url": "",
            "description": "",
            "parameters": [],
            "responses": []
        }
        
        # Look for method indicators (GET, POST, etc.)
        method_elements = section.find_all(text=lambda text: text and any(method in text.upper() for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']))
        if method_elements:
            endpoint_data["method"] = method_elements[0].strip()
        
        # Look for URLs
        url_elements = section.find_all(['code', 'pre'], text=lambda text: text and ('/' in text or 'http' in text))
        if url_elements:
            endpoint_data["url"] = url_elements[0].get_text(strip=True)
        
        # Extract description
        desc_elements = section.find_all(['p', 'div'], text=True)
        if desc_elements:
            endpoint_data["description"] = desc_elements[0].get_text(strip=True)
        
        return endpoint_data if any([endpoint_data["method"], endpoint_data["url"], endpoint_data["description"]]) else None
    
    def _extract_section_data(self, section) -> Dict[str, Any]:
        """Extract general section data"""
        section_data = {
            "title": "",
            "content": "",
            "links": [],
            "code_blocks": []
        }
        
        # Extract title
        title_elem = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if title_elem:
            section_data["title"] = title_elem.get_text(strip=True)
        
        # Extract content
        content_elem = section.find(['p', 'div'])
        if content_elem:
            section_data["content"] = content_elem.get_text(strip=True)
        
        # Extract links
        links = section.find_all('a', href=True)
        for link in links:
            section_data["links"].append({
                "text": link.get_text(strip=True),
                "url": link['href']
            })
        
        # Extract code blocks
        code_blocks = section.find_all(['code', 'pre'])
        for code in code_blocks:
            section_data["code_blocks"].append(code.get_text())
        
        return section_data if any([section_data["title"], section_data["content"], section_data["links"]]) else None
    
    def _extract_navigation_data(self, nav) -> Dict[str, Any]:
        """Extract navigation menu data"""
        nav_data = {
            "title": "",
            "items": []
        }
        
        # Extract navigation title
        title_elem = nav.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if title_elem:
            nav_data["title"] = title_elem.get_text(strip=True)
        
        # Extract navigation items
        nav_items = nav.find_all('a', href=True)
        for item in nav_items:
            nav_data["items"].append({
                "text": item.get_text(strip=True),
                "url": item['href']
            })
        
        return nav_data if nav_data["items"] else None
    
    def parse_all_docs(self) -> Dict[str, Dict[str, Any]]:
        """Parse all API documentation files"""
        logger.info("Starting to parse all API documentation...")
        
        results = {}
        
        # Parse each API's documentation
        results["polygon"] = self.parse_polygon_docs()
        results["fmp"] = self.parse_fmp_docs()
        results["twelve_data"] = self.parse_twelve_data_docs()
        results["benzinga"] = self.parse_benzinga_docs()
        
        # Create a summary report
        summary = {
            "total_apis_parsed": len([r for r in results.values() if r]),
            "apis": list(results.keys()),
            "parsed_files": [f"{api}_api_parsed.json" for api in results.keys() if results[api]],
            "output_directory": str(self.output_dir.absolute())
        }
        
        # Save summary
        summary_file = self.output_dir / "parsing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"All documentation parsed. Summary saved to {summary_file}")
        return results

def main():
    """Main function to run the API documentation parser"""
    parser = APIDocParser()
    
    # Parse all documentation
    results = parser.parse_all_docs()
    
    # Print summary
    print("\n" + "="*50)
    print("API DOCUMENTATION PARSING SUMMARY")
    print("="*50)
    
    for api_name, result in results.items():
        if result:
            print(f"✅ {api_name.upper()}: Successfully parsed")
            print(f"   - Endpoints found: {len(result.get('endpoints', []))}")
            print(f"   - Examples found: {len(result.get('examples', []))}")
            print(f"   - File: {api_name}_api_parsed.json")
        else:
            print(f"❌ {api_name.upper()}: Failed to parse")
    
    print(f"\n📁 All parsed files saved to: {parser.output_dir.absolute()}")
    print("="*50)

if __name__ == "__main__":
    main() 