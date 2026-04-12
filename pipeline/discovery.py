"""
URL discovery using multiple search APIs.
"""

import asyncio
import logging
from typing import List, Optional, Set

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
GOOGLE_SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"


class DiscoveryClient:
    """Base class for discovery clients."""
    
    def __init__(
        self,
        api_key: str,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize discovery client.
        
        Args:
            api_key: API key
            timeout_seconds: Request timeout
            max_retries: Maximum retries
        """
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(timeout=self.timeout_seconds)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    async def discover(
        self,
        company_website: str,
        keywords: List[str],
        seed_urls: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Discover URLs for a company.
        
        Args:
            company_website: Company website URL
            keywords: List of keywords to search
            seed_urls: Optional seed URLs
            
        Returns:
            List of discovered URLs
        """
        raise NotImplementedError("Subclasses must implement discover method")


class BraveDiscoveryClient(DiscoveryClient):
    """Client for discovering URLs via Brave Search API."""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _search(self, query: str) -> List[str]:
        """
        Execute search query.
        
        Args:
            query: Search query
            
        Returns:
            List of URLs
        """
        if not self.session:
            raise RuntimeError("Client not initialized")
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Accept": "application/json",
        }
        
        params = {
            "q": query,
            "count": 20,
        }
        
        try:
            response = await self.session.get(
                BRAVE_API_URL,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("web", [])
            
            urls = [result["url"] for result in results if "url" in result]
            logger.debug(f"Found {len(urls)} URLs for query: {query}")
            
            return urls
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limited by Brave API, retrying...")
                raise
            logger.error(f"Brave API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Discovery search failed for {query}: {e}")
            raise
    
    async def discover(
        self,
        company_website: str,
        keywords: List[str],
        seed_urls: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Discover URLs for a company.
        
        Args:
            company_website: Company website URL
            keywords: List of keywords to search
            seed_urls: Optional seed URLs
            
        Returns:
            List of discovered URLs
        """
        discovered: Set[str] = set()
        
        # Add seed URLs
        if seed_urls:
            discovered.update(seed_urls)
            logger.info(f"Added {len(seed_urls)} seed URLs")
        
        # Build search queries
        queries = self._build_queries(company_website, keywords)
        logger.info(f"Searching with {len(queries)} queries")
        
        # Execute searches
        for query in queries:
            try:
                urls = await self._search(query)
                discovered.update(urls)
                
                # Add small delay between requests to be respectful
                await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.warning(f"Failed to search query '{query}': {e}")
        
        result = list(discovered)
        logger.info(f"Discovery complete: {len(result)} unique URLs")
        
        return result
    
    def _build_queries(self, company_website: str, keywords: List[str]) -> List[str]:
        """
        Build search queries for Brave Search API.
        
        Args:
            company_website: Company website
            keywords: Keywords
            
        Returns:
            List of queries
        """
        queries: List[str] = []
        
        # Extract domain
        domain = company_website.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Build keyword searches using Brave site:filter and filetype:pdf where useful
        for keyword in keywords:
            query_html = f'site:{domain} {keyword}'
            query_pdf = f'site:{domain} {keyword} filetype:pdf'
            queries.append(query_pdf)
            queries.append(query_html)
        
        generic_queries = [
            f'site:{domain} annual report',
            f'site:{domain} financial statements',
            f'site:{domain} earnings',
            f'site:{domain} investor relations',
        ]
        
        for query in generic_queries:
            if query not in queries:
                queries.append(query)
        
        return queries[:15]  # Limit to 15 queries


class GoogleDiscoveryClient(DiscoveryClient):
    """Client for discovering URLs via Google Custom Search API."""
    
    def __init__(
        self,
        api_key: str,
        cx: str,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Google discovery client.
        
        Args:
            api_key: Google API key
            cx: Custom search engine ID
            timeout_seconds: Request timeout
            max_retries: Maximum retries
        """
        super().__init__(api_key, timeout_seconds, max_retries)
        self.cx = cx
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _search(self, query: str) -> List[str]:
        """
        Execute search query.
        
        Args:
            query: Search query
            
        Returns:
            List of URLs
        """
        if not self.session:
            raise RuntimeError("Client not initialized")
        
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": 10,  # Google allows max 10 results per request
        }
        
        try:
            response = await self.session.get(
                GOOGLE_SEARCH_API_URL,
                params=params,
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            urls = [item["link"] for item in items if "link" in item]
            logger.debug(f"Found {len(urls)} URLs for query: {query}")
            
            return urls
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limited by Google API, retrying...")
                raise
            logger.error(f"Google API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Discovery search failed for {query}: {e}")
            raise
    
    async def discover(
        self,
        company_website: str,
        keywords: List[str],
        seed_urls: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Discover URLs for a company.
        
        Args:
            company_website: Company website URL
            keywords: List of keywords to search
            seed_urls: Optional seed URLs
            
        Returns:
            List of discovered URLs
        """
        discovered: Set[str] = set()
        
        # Add seed URLs
        if seed_urls:
            discovered.update(seed_urls)
            logger.info(f"Added {len(seed_urls)} seed URLs")
        
        # Build search queries
        queries = self._build_queries(company_website, keywords)
        logger.info(f"Searching with {len(queries)} queries")
        
        # Execute searches
        for query in queries:
            try:
                urls = await self._search(query)
                discovered.update(urls)
                
                # Add small delay between requests to be respectful
                await asyncio.sleep(1.0)  # Google has stricter rate limits
            
            except Exception as e:
                logger.warning(f"Failed to search query '{query}': {e}")
        
        result = list(discovered)
        logger.info(f"Discovery complete: {len(result)} unique URLs")
        
        return result
    
    def _build_queries(self, company_website: str, keywords: List[str]) -> List[str]:
        """
        Build search queries.
        
        Args:
            company_website: Company website
            keywords: Keywords
            
        Returns:
            List of queries
        """
        queries: List[str] = []
        
        # Extract domain
        domain = company_website.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Generate site:domain queries with keywords
        for keyword in keywords:
            # PDF queries
            query_pdf = f'site:{domain} "{keyword}" filetype:pdf'
            queries.append(query_pdf)
            
            # HTML queries
            query_html = f'site:{domain} "{keyword}"'
            queries.append(query_html)
        
        # Generic queries for common document types
        generic_queries = [
            f'site:{domain} "annual report"',
            f'site:{domain} "financial statements"',
            f'site:{domain} "earnings"',
            f'site:{domain} "investor relations"',
        ]
        
        for query in generic_queries:
            if query not in queries:
                queries.append(query)
        
        return queries[:10]  # Google has stricter limits


class BingDiscoveryClient(DiscoveryClient):
    """Client for discovering URLs via Bing Web Search API."""
    
    def __init__(
        self,
        api_key: str,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Bing discovery client.
        
        Args:
            api_key: Bing API key
            timeout_seconds: Request timeout
            max_retries: Maximum retries
        """
        super().__init__(api_key, timeout_seconds, max_retries)
        self.api_url = "https://api.bing.microsoft.com/v7.0/search"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _search(self, query: str) -> List[str]:
        """
        Execute search query.
        
        Args:
            query: Search query
            
        Returns:
            List of URLs
        """
        if not self.session:
            raise RuntimeError("Client not initialized")
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        
        params = {
            "q": query,
            "count": 20,
            "responseFilter": "Webpages",
        }
        
        try:
            response = await self.session.get(
                self.api_url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            
            data = response.json()
            webpages = data.get("webPages", {}).get("value", [])
            
            urls = [page["url"] for page in webpages if "url" in page]
            logger.debug(f"Found {len(urls)} URLs for query: {query}")
            
            return urls
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limited by Bing API, retrying...")
                raise
            logger.error(f"Bing API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Discovery search failed for {query}: {e}")
            raise
    
    async def discover(
        self,
        company_website: str,
        keywords: List[str],
        seed_urls: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Discover URLs for a company.
        
        Args:
            company_website: Company website URL
            keywords: List of keywords to search
            seed_urls: Optional seed URLs
            
        Returns:
            List of discovered URLs
        """
        discovered: Set[str] = set()
        
        # Add seed URLs
        if seed_urls:
            discovered.update(seed_urls)
            logger.info(f"Added {len(seed_urls)} seed URLs")
        
        # Build search queries
        queries = self._build_queries(company_website, keywords)
        logger.info(f"Searching with {len(queries)} queries")
        
        # Execute searches
        for query in queries:
            try:
                urls = await self._search(query)
                discovered.update(urls)
                
                # Add small delay between requests to be respectful
                await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.warning(f"Failed to search query '{query}': {e}")
        
        result = list(discovered)
        logger.info(f"Discovery complete: {len(result)} unique URLs")
        
        return result
    
    def _build_queries(self, company_website: str, keywords: List[str]) -> List[str]:
        """
        Build search queries.
        
        Args:
            company_website: Company website
            keywords: Keywords
            
        Returns:
            List of queries
        """
        queries: List[str] = []
        
        # Extract domain
        domain = company_website.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Generate site:domain queries with keywords
        for keyword in keywords:
            # PDF queries
            query_pdf = f'site:{domain} "{keyword}" filetype:pdf'
            queries.append(query_pdf)
            
            # HTML queries
            query_html = f'site:{domain} "{keyword}"'
            queries.append(query_html)
        
        # Generic queries for common document types
        generic_queries = [
            f'site:{domain} "annual report"',
            f'site:{domain} "financial statements"',
            f'site:{domain} "earnings"',
            f'site:{domain} "investor relations"',
        ]
        
        for query in generic_queries:
            if query not in queries:
                queries.append(query)
        
        return queries[:20]  # Limit to avoid too many requests
    """Client for discovering URLs via Brave Search API."""
    
    def __init__(
        self,
        api_key: str,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize discovery client.
        
        Args:
            api_key: Brave Search API key
            timeout_seconds: Request timeout
            max_retries: Maximum retries
        """
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(timeout=self.timeout_seconds)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _search(self, query: str) -> List[str]:
        """
        Execute search query.
        
        Args:
            query: Search query
            
        Returns:
            List of URLs
        """
        if not self.session:
            raise RuntimeError("Client not initialized")
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Accept": "application/json",
        }
        
        params = {
            "q": query,
            "count": 20,
        }
        
        try:
            response = await self.session.get(
                BRAVE_API_URL,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("web", [])
            
            urls = [result["url"] for result in results if "url" in result]
            logger.debug(f"Found {len(urls)} URLs for query: {query}")
            
            return urls
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limited by Brave API, retrying...")
                raise
            logger.error(f"Brave API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Discovery search failed for {query}: {e}")
            raise
    
    async def discover(
        self,
        company_website: str,
        keywords: List[str],
        seed_urls: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Discover URLs for a company.
        
        Args:
            company_website: Company website URL
            keywords: List of keywords to search
            seed_urls: Optional seed URLs
            
        Returns:
            List of discovered URLs
        """
        discovered: Set[str] = set()
        
        # Add seed URLs
        if seed_urls:
            discovered.update(seed_urls)
            logger.info(f"Added {len(seed_urls)} seed URLs")
        
        # Build search queries
        queries = self._build_queries(company_website, keywords)
        logger.info(f"Searching with {len(queries)} queries")
        
        # Execute searches
        for query in queries:
            try:
                urls = await self._search(query)
                discovered.update(urls)
                
                # Add small delay between requests to be respectful
                await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.warning(f"Failed to search query '{query}': {e}")
        
        result = list(discovered)
        logger.info(f"Discovery complete: {len(result)} unique URLs")
        
        return result
    
    def _build_queries(self, company_website: str, keywords: List[str]) -> List[str]:
        """
        Build search queries.
        
        Args:
            company_website: Company website
            keywords: Keywords
            
        Returns:
            List of queries
        """
        queries: List[str] = []
        
        # Extract domain
        domain = company_website.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Generate site:domain queries with keywords
        for keyword in keywords:
            # PDF queries
            query_pdf = f'site:{domain} "{keyword}" filetype:pdf'
            queries.append(query_pdf)
            
            # HTML queries
            query_html = f'site:{domain} "{keyword}"'
            queries.append(query_html)
        
        # Generic queries for common document types
        generic_queries = [
            f'site:{domain} "annual report"',
            f'site:{domain} "financial statements"',
            f'site:{domain} "earnings"',
            f'site:{domain} "investor relations"',
        ]
        
        for query in generic_queries:
            if query not in queries:
                queries.append(query)
        
        return queries[:20]  # Limit to avoid too many requests


async def discover_urls(
    company_website: str,
    keywords: List[str],
    seed_urls: Optional[List[str]],
    api_key: str,
    timeout_seconds: int = 30,
) -> List[str]:
    """
    Discover URLs for a company (standalone function).
    
    Args:
        company_website: Company website URL
        keywords: Search keywords
        seed_urls: Optional seed URLs
        api_key: Brave API key
        timeout_seconds: Request timeout
        
    Returns:
        List of discovered URLs
    """
    async with DiscoveryClient(api_key, timeout_seconds) as client:
        return await client.discover(company_website, keywords, seed_urls)
