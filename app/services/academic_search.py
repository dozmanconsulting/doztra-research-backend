"""
Academic source search service for finding relevant research papers and sources.
Integrates with various academic databases and search engines.
"""

import logging
import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AcademicSearchService:
    """
    Service for searching academic sources across multiple databases and APIs.
    """
    
    def __init__(self):
        # API keys and configurations
        self.semantic_scholar_base_url = "https://api.semanticscholar.org/graph/v1"
        self.crossref_base_url = "https://api.crossref.org/works"
        self.arxiv_base_url = "http://export.arxiv.org/api/query"
        
        # Rate limiting
        self.request_delay = 0.1  # 100ms between requests
        
    async def search_academic_sources(
        self, 
        query: str, 
        max_results: int = 10,
        source_types: List[str] = None,
        year_range: tuple = None
    ) -> Dict[str, Any]:
        """
        Search for academic sources across multiple databases.
        
        Args:
            query: Search query/topic
            max_results: Maximum number of results to return
            source_types: Types of sources to include (journal, conference, book, etc.)
            year_range: Tuple of (start_year, end_year) for filtering
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info(f"Searching for academic sources: {query}")
            
            # Search across multiple sources concurrently
            search_tasks = [
                self._search_semantic_scholar(query, max_results // 2),
                self._search_crossref(query, max_results // 2),
                self._search_arxiv(query, min(5, max_results // 4))  # ArXiv for preprints
            ]
            
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine and process results
            all_sources = []
            search_metadata = {
                "query": query,
                "total_sources_found": 0,
                "databases_searched": [],
                "search_timestamp": datetime.utcnow().isoformat()
            }
            
            # Process Semantic Scholar results
            if not isinstance(results[0], Exception) and results[0]:
                semantic_sources = results[0].get("sources", [])
                all_sources.extend(semantic_sources)
                search_metadata["databases_searched"].append("Semantic Scholar")
                logger.info(f"Found {len(semantic_sources)} sources from Semantic Scholar")
            
            # Process CrossRef results
            if not isinstance(results[1], Exception) and results[1]:
                crossref_sources = results[1].get("sources", [])
                all_sources.extend(crossref_sources)
                search_metadata["databases_searched"].append("CrossRef")
                logger.info(f"Found {len(crossref_sources)} sources from CrossRef")
            
            # Process ArXiv results
            if not isinstance(results[2], Exception) and results[2]:
                arxiv_sources = results[2].get("sources", [])
                all_sources.extend(arxiv_sources)
                search_metadata["databases_searched"].append("ArXiv")
                logger.info(f"Found {len(arxiv_sources)} sources from ArXiv")
            
            # Remove duplicates and rank by relevance
            unique_sources = self._deduplicate_sources(all_sources)
            ranked_sources = self._rank_sources(unique_sources, query)
            
            # Apply filters
            if year_range:
                ranked_sources = self._filter_by_year(ranked_sources, year_range)
            
            if source_types:
                ranked_sources = self._filter_by_type(ranked_sources, source_types)
            
            # Limit results
            final_sources = ranked_sources[:max_results]
            
            search_metadata["total_sources_found"] = len(final_sources)
            
            return {
                "sources": final_sources,
                "metadata": search_metadata,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error searching academic sources: {str(e)}")
            return {
                "sources": [],
                "metadata": {
                    "query": query,
                    "error": str(e),
                    "search_timestamp": datetime.utcnow().isoformat()
                },
                "success": False
            }
    
    async def _search_semantic_scholar(self, query: str, limit: int) -> Dict[str, Any]:
        """Search Semantic Scholar API for academic papers."""
        try:
            url = f"{self.semantic_scholar_base_url}/paper/search"
            params = {
                "query": query,
                "limit": limit,
                "fields": "paperId,title,abstract,authors,year,citationCount,url,venue,publicationTypes"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = []
                        
                        for paper in data.get("data", []):
                            source = {
                                "id": paper.get("paperId"),
                                "title": paper.get("title", ""),
                                "abstract": paper.get("abstract", "")[:500] + "..." if paper.get("abstract") and len(paper.get("abstract", "")) > 500 else paper.get("abstract", ""),
                                "authors": [author.get("name", "") for author in paper.get("authors", [])],
                                "year": paper.get("year"),
                                "citation_count": paper.get("citationCount", 0),
                                "url": paper.get("url"),
                                "venue": paper.get("venue"),
                                "publication_types": paper.get("publicationTypes", []),
                                "source_database": "Semantic Scholar",
                                "relevance_score": 0.8  # Base score, will be adjusted
                            }
                            sources.append(source)
                        
                        return {"sources": sources}
                    else:
                        logger.warning(f"Semantic Scholar API returned status {response.status}")
                        return {"sources": []}
                        
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {str(e)}")
            return {"sources": []}
    
    async def _search_crossref(self, query: str, limit: int) -> Dict[str, Any]:
        """Search CrossRef API for academic publications."""
        try:
            url = self.crossref_base_url
            params = {
                "query": query,
                "rows": limit,
                "sort": "relevance",
                "select": "DOI,title,author,published-print,abstract,container-title,type,URL"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = []
                        
                        for item in data.get("message", {}).get("items", []):
                            # Extract publication year
                            year = None
                            if "published-print" in item and "date-parts" in item["published-print"]:
                                year = item["published-print"]["date-parts"][0][0]
                            
                            # Extract authors
                            authors = []
                            for author in item.get("author", []):
                                if "given" in author and "family" in author:
                                    authors.append(f"{author['given']} {author['family']}")
                                elif "family" in author:
                                    authors.append(author["family"])
                            
                            source = {
                                "id": item.get("DOI"),
                                "title": item.get("title", [""])[0] if item.get("title") else "",
                                "abstract": item.get("abstract", "")[:500] + "..." if item.get("abstract") and len(item.get("abstract", "")) > 500 else item.get("abstract", ""),
                                "authors": authors,
                                "year": year,
                                "citation_count": 0,  # CrossRef doesn't provide citation counts
                                "url": item.get("URL"),
                                "venue": item.get("container-title", [""])[0] if item.get("container-title") else "",
                                "publication_types": [item.get("type", "")],
                                "source_database": "CrossRef",
                                "relevance_score": 0.7  # Base score
                            }
                            sources.append(source)
                        
                        return {"sources": sources}
                    else:
                        logger.warning(f"CrossRef API returned status {response.status}")
                        return {"sources": []}
                        
        except Exception as e:
            logger.error(f"Error searching CrossRef: {str(e)}")
            return {"sources": []}
    
    async def _search_arxiv(self, query: str, limit: int) -> Dict[str, Any]:
        """Search ArXiv API for preprints and papers."""
        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": limit,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.arxiv_base_url, params=params) as response:
                    if response.status == 200:
                        content = await response.text()
                        sources = self._parse_arxiv_xml(content)
                        return {"sources": sources}
                    else:
                        logger.warning(f"ArXiv API returned status {response.status}")
                        return {"sources": []}
                        
        except Exception as e:
            logger.error(f"Error searching ArXiv: {str(e)}")
            return {"sources": []}
    
    def _parse_arxiv_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse ArXiv XML response."""
        try:
            import xml.etree.ElementTree as ET
            
            root = ET.fromstring(xml_content)
            sources = []
            
            # ArXiv uses Atom namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                published = entry.find('atom:published', ns)
                link = entry.find('atom:link[@type="text/html"]', ns)
                
                # Extract authors
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None:
                        authors.append(name.text)
                
                # Extract year from published date
                year = None
                if published is not None:
                    try:
                        year = int(published.text[:4])
                    except:
                        pass
                
                source = {
                    "id": entry.find('atom:id', ns).text if entry.find('atom:id', ns) is not None else "",
                    "title": title.text if title is not None else "",
                    "abstract": (summary.text[:500] + "...") if summary is not None and len(summary.text) > 500 else (summary.text if summary is not None else ""),
                    "authors": authors,
                    "year": year,
                    "citation_count": 0,  # ArXiv doesn't provide citation counts
                    "url": link.get('href') if link is not None else "",
                    "venue": "arXiv preprint",
                    "publication_types": ["preprint"],
                    "source_database": "ArXiv",
                    "relevance_score": 0.6  # Lower score for preprints
                }
                sources.append(source)
            
            return sources
            
        except Exception as e:
            logger.error(f"Error parsing ArXiv XML: {str(e)}")
            return []
    
    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sources based on title similarity."""
        unique_sources = []
        seen_titles = set()
        
        for source in sources:
            title = source.get("title", "").lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_sources.append(source)
        
        return unique_sources
    
    def _rank_sources(self, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank sources by relevance to the query."""
        query_words = set(query.lower().split())
        
        for source in sources:
            score = source.get("relevance_score", 0.5)
            
            # Boost score based on title relevance
            title_words = set(source.get("title", "").lower().split())
            title_overlap = len(query_words.intersection(title_words))
            score += title_overlap * 0.1
            
            # Boost score based on citation count
            citation_count = source.get("citation_count", 0)
            if citation_count > 100:
                score += 0.2
            elif citation_count > 50:
                score += 0.1
            elif citation_count > 10:
                score += 0.05
            
            # Boost score for recent publications
            year = source.get("year")
            if year and year >= 2020:
                score += 0.1
            elif year and year >= 2015:
                score += 0.05
            
            source["relevance_score"] = min(score, 1.0)  # Cap at 1.0
        
        # Sort by relevance score
        return sorted(sources, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    def _filter_by_year(self, sources: List[Dict[str, Any]], year_range: tuple) -> List[Dict[str, Any]]:
        """Filter sources by publication year range."""
        start_year, end_year = year_range
        filtered = []
        
        for source in sources:
            year = source.get("year")
            if year and start_year <= year <= end_year:
                filtered.append(source)
        
        return filtered
    
    def _filter_by_type(self, sources: List[Dict[str, Any]], source_types: List[str]) -> List[Dict[str, Any]]:
        """Filter sources by publication type."""
        filtered = []
        
        for source in sources:
            pub_types = source.get("publication_types", [])
            if any(ptype in source_types for ptype in pub_types):
                filtered.append(source)
        
        return filtered

# Create singleton instance
academic_search_service = AcademicSearchService()
