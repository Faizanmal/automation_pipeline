"""
Content fetching using multiple scraping APIs.
"""
import asyncio
import logging
from typing import Optional, Tuple
import httpx
logger = logging.getLogger(__name__)
# API endpoints
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v0/scrape"
SCRAPINGBEE_API_URL = "https://app.scrapingbee.com/api/v1/"
class FetchError(Exception):
    """Fetch error."""
    pass
class FetchClient:
    """Base class for fetch clients."""
    def __init__(
        self,
        api_key: str,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.session: Optional[httpx.AsyncClient] = None
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=self.timeout_seconds)
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    async def fetch_page(self, url: str) -> Tuple[Optional[bytes], Optional[bytes], Optional[str]]:
        raise NotImplementedError("Subclasses must implement fetch_page method")
    async def fetch_pdf(self, url: str) -> Optional[bytes]:
        raise NotImplementedError("Subclasses must implement fetch_pdf method")
class FirecrawlFetchClient(FetchClient):
    """Client for fetching content via Firecrawl."""
    async def _make_request(self, url: str) -> dict:
        if not self.session:
            raise RuntimeError("Client not initialized")
        payload = {
            "url": url,
            "formats": ["markdown", "html"],
            "onlyMainContent": True,
            "waitFor": 1000,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Firecrawl attempt {attempt + 1}/{self.max_retries}: {url}")
                response = await self.session.post(
                    FIRECRAWL_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                logger.debug(f"Firecrawl response status: {response.status_code}")
                if response.status_code == 429:
                    logger.warning(f"Firecrawl rate limited (429), attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                    raise FetchError("Rate limited after retries")
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                last_error = f"Timeout: {e}"
                logger.warning(f"Firecrawl timeout on attempt {attempt + 1}: {url}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(3 * (attempt + 1))
                    continue
                raise FetchError(last_error)
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                last_error = f"HTTP {status_code}"
                logger.error(f"Firecrawl API error {status_code} for {url}")
                if status_code >= 500 and attempt < self.max_retries - 1:
                    await asyncio.sleep(3 * (attempt + 1))
                    continue
                raise FetchError(last_error)
            except Exception as e:
                last_error = str(e)
                logger.error(f"Firecrawl request error on attempt {attempt + 1}: {type(e).__name__}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                raise FetchError(last_error)
        raise FetchError(f"Failed after {self.max_retries} attempts")
    async def fetch_page(self, url: str) -> Tuple[Optional[bytes], Optional[bytes], Optional[str]]:
        try:
            response_data = await self._make_request(url)
            if not response_data.get("success", False):
                error_msg = response_data.get("error", "Unknown error")
                logger.warning(f"Firecrawl failed for {url}: {error_msg}")
                return None, None, None
            content_data = response_data.get("data", {})
            markdown = content_data.get("markdown")
            html = content_data.get("html")
            if not markdown:
                markdown = content_data.get("content")
            html_bytes = html.encode("utf-8") if html else None
            markdown_text = markdown if isinstance(markdown, str) else None
            if not html_bytes and not markdown_text:
                logger.warning(f"Firecrawl returned empty page for {url}")
                return None, None, None
            logger.info(f"✅ Firecrawl fetched {url} (html={bool(html_bytes)}, markdown={bool(markdown_text)})")
            return html_bytes, None, markdown_text
        except FetchError as e:
            logger.error(f"Fetch error for {url}: {e}")
            return None, None, None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {type(e).__name__}: {e}")
            return None, None, None
    async def fetch_pdf(self, url: str) -> Optional[bytes]:
        if not self.session:
            raise RuntimeError("Client not initialized")
        try:
            response = await self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to fetch PDF {url}: {e}")
            return None
class ScrapingBeeFetchClient(FetchClient):
    """Client for fetching content via ScrapingBee."""
    async def _make_request(self, url: str) -> bytes:
        if not self.session:
            raise RuntimeError("Client not initialized")
        params = {
            "api_key": self.api_key,
            "url": url,
            "render_js": "true",
            "keep_headers": "true",
            "premium_proxy": "false",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"ScrapingBee attempt {attempt + 1}/{self.max_retries}: {url}")
                response = await self.session.get(
                    SCRAPINGBEE_API_URL,
                    params=params,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                logger.debug(f"ScrapingBee response status: {response.status_code}")
                if response.status_code == 429:
                    logger.warning(f"ScrapingBee rate limited (429), attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                    raise FetchError("Rate limited after retries")
                response.raise_for_status()
                return response.content
            except httpx.TimeoutException as e:
                last_error = f"Timeout: {e}"
                logger.warning(f"ScrapingBee timeout on attempt {attempt + 1}: {url}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(3 * (attempt + 1))
                    continue
                raise FetchError(last_error)
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                last_error = f"HTTP {status_code}"
                logger.error(f"ScrapingBee API error {status_code} for {url}")
                if status_code >= 500 and attempt < self.max_retries - 1:
                    await asyncio.sleep(3 * (attempt + 1))
                    continue
                raise FetchError(last_error)
            except Exception as e:
                last_error = str(e)
                logger.error(f"ScrapingBee request error on attempt {attempt + 1}: {type(e).__name__}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                raise FetchError(last_error)
        raise FetchError(f"Failed after {self.max_retries} attempts")
    async def fetch_page(self, url: str) -> Tuple[Optional[bytes], Optional[bytes], Optional[str]]:
        try:
            html_bytes = await self._make_request(url)
            if not html_bytes:
                logger.warning(f"ScrapingBee returned empty content for {url}")
                return None, None, None
            logger.info(f"✅ ScrapingBee fetched {url} (html bytes={len(html_bytes)})")
            return html_bytes, None, None
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None, None, None
    async def fetch_pdf(self, url: str) -> Optional[bytes]:
        if not self.session:
            raise RuntimeError("Client not initialized")
        try:
            response = await self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to fetch PDF {url}: {e}")
            return None
async def fetch_content(
    url: str,
    api_key: str,
    timeout_seconds: int = 30,
    is_pdf: bool = False,
) -> Tuple[Optional[bytes], Optional[bytes], Optional[str]]:
    async with FirecrawlFetchClient(api_key, timeout_seconds) as client:
        if is_pdf:
            pdf = await client.fetch_pdf(url)
            return None, pdf, None
        return await client.fetch_page(url)
async def fetch_bulk(
    urls: list,
    api_key: str,
    max_concurrent: int = 5,
    timeout_seconds: int = 30,
) -> dict:
    results = {}
    semaphore = asyncio.Semaphore(max_concurrent)
    async def fetch_with_semaphore(url: str):
        async with semaphore:
            html, pdf, md = await fetch_content(url, api_key, timeout_seconds)
            results[url] = (html, pdf, md)
    tasks = [fetch_with_semaphore(url) for url in urls]
    await asyncio.gather(*tasks, return_exceptions=True)
    return results
