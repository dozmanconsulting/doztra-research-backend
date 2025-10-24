"""
Firecrawl Web Scraping Service
Advanced web content extraction and processing
"""

import aiohttp
import os
from typing import Optional, Dict, Any, List
import logging
from urllib.parse import urlparse, urljoin
import asyncio

logger = logging.getLogger(__name__)

class FirecrawlService:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        self.base_url = "https://api.firecrawl.dev/v0"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def scrape_url(
        self, 
        url: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Scrape a single URL with advanced options"""
        
        scrape_request = {
            "url": url,
            "formats": ["markdown", "html", "rawHtml"],
            "onlyMainContent": True,
            "includeTags": ["title", "meta", "h1", "h2", "h3", "p", "article"],
            "excludeTags": ["nav", "footer", "aside", "script", "style"],
            "waitFor": 2000,  # Wait 2 seconds for dynamic content
            "screenshot": True,
            "fullPageScreenshot": False
        }
        
        # Override with custom options
        if options:
            scrape_request.update(options)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/scrape",
                headers=self.headers,
                json=scrape_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("data", {})
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to scrape URL: {response.status} - {error_text}")
    
    async def crawl_website(
        self, 
        url: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crawl entire website or specific paths"""
        
        crawl_request = {
            "url": url,
            "crawlerOptions": {
                "includes": [],  # Specific paths to include
                "excludes": ["/admin/*", "/login/*", "/api/*"],  # Paths to exclude
                "maxDepth": 3,  # Maximum crawl depth
                "limit": 50,    # Maximum pages to crawl
                "allowBackwardCrawling": False,
                "allowExternalContentLinks": False
            },
            "pageOptions": {
                "onlyMainContent": True,
                "includeHtml": False,
                "screenshot": False,
                "waitFor": 1000
            }
        }
        
        # Override with custom options
        if options:
            if "crawlerOptions" in options:
                crawl_request["crawlerOptions"].update(options["crawlerOptions"])
            if "pageOptions" in options:
                crawl_request["pageOptions"].update(options["pageOptions"])
        
        async with aiohttp.ClientSession() as session:
            # Start crawl job
            async with session.post(
                f"{self.base_url}/crawl",
                headers=self.headers,
                json=crawl_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    job_id = result.get("jobId")
                    
                    if job_id:
                        # Poll for completion
                        return await self._poll_crawl_job(job_id)
                    else:
                        raise Exception("No job ID returned from crawl request")
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to start crawl: {response.status} - {error_text}")
    
    async def _poll_crawl_job(self, job_id: str) -> Dict[str, Any]:
        """Poll crawl job status until complete"""
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(
                    f"{self.base_url}/crawl/status/{job_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        status = result.get("status")
                        
                        if status == "completed":
                            return result
                        elif status == "failed":
                            raise Exception(f"Crawl failed: {result.get('error', 'Unknown error')}")
                        else:
                            # Wait 10 seconds before polling again
                            await asyncio.sleep(10)
                    else:
                        raise Exception(f"Failed to check crawl status: {response.status}")
    
    async def extract_links(self, url: str) -> List[str]:
        """Extract all links from a webpage"""
        try:
            scraped_data = await self.scrape_url(url, {
                "formats": ["links"],
                "onlyMainContent": False
            })
            
            return scraped_data.get("links", [])
        except Exception as e:
            logger.error(f"Failed to extract links from {url}: {e}")
            return []
    
    async def get_page_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata from a webpage"""
        try:
            scraped_data = await self.scrape_url(url, {
                "formats": ["markdown"],
                "onlyMainContent": False,
                "includeTags": ["title", "meta", "h1"]
            })
            
            return {
                "title": scraped_data.get("metadata", {}).get("title", ""),
                "description": scraped_data.get("metadata", {}).get("description", ""),
                "keywords": scraped_data.get("metadata", {}).get("keywords", ""),
                "author": scraped_data.get("metadata", {}).get("author", ""),
                "language": scraped_data.get("metadata", {}).get("language", ""),
                "url": url,
                "domain": urlparse(url).netloc
            }
        except Exception as e:
            logger.error(f"Failed to get metadata from {url}: {e}")
            return {"url": url, "error": str(e)}
    
    def extract_content_data(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format scraped content"""
        return {
            "url": scraped_data.get("metadata", {}).get("sourceURL", ""),
            "title": scraped_data.get("metadata", {}).get("title", ""),
            "description": scraped_data.get("metadata", {}).get("description", ""),
            "content": scraped_data.get("markdown", ""),
            "html": scraped_data.get("html", ""),
            "text_length": len(scraped_data.get("markdown", "")),
            "metadata": scraped_data.get("metadata", {}),
            "links": scraped_data.get("links", []),
            "screenshot": scraped_data.get("screenshot", "")
        }
    
    async def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently"""
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "url": urls[i],
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append({
                    **self.extract_content_data(result),
                    "success": True
                })
        
        return processed_results

# Global service instance
web_scraping_service = FirecrawlService()
