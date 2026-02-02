import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import trafilatura
from loguru import logger
from datetime import datetime

from open_web_search.readers.base import BaseReader
from open_web_search.schemas.results import FetchedPage
from open_web_search.utils.cache import CacheManager

import random
import hashlib

class TrafilaturaReader(BaseReader):
    def __init__(self, max_warnings: int = 5, concurrency: int = 5, cache_dir: str = ".linker_cache", custom_headers: Optional[dict] = None):
        self.executor = ThreadPoolExecutor(max_workers=concurrency)
        self.cache = CacheManager.get_instance(cache_dir=cache_dir)
        self.custom_headers = custom_headers or {}
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    def _get_headers(self) -> dict:
        base_headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        # Merge custom headers (overwriting base if collision)
        if self.custom_headers:
             base_headers.update(self.custom_headers)
        return base_headers

    def _fetch_one_sync(self, url: str) -> FetchedPage:
        # Check cache first
        cache_key = f"page:{hashlib.md5(url.encode()).hexdigest()}"
        cached_page = self.cache.get(cache_key)
        if cached_page:
            # Check if it was an error? Maybe we retry errors? For now, return cached.
            # But we stored a FetchedPage object? Yes, pickle works with diskcache.
            if not cached_page.error:
                return cached_page
        
        page = FetchedPage(url=url)
        try:
            # Trafilatura's fetch_url is simple, but we can pass a config or just hope it works.
            # However, for better control, we might want to use httpx or requests and then pass to trafilatura.
            # But trafilatura.fetch_url does handle some things well. Let's try to pass 'headers' if possible, 
            # unfortunately fetch_url doesn't take headers dict directly in all versions, it takes a config object.
            # So simpler: use trafilatura's built-in download with no_ssl=True if needed.
            # Better approach: Use requests/httpx to get HTML, then trafilatura to extract.
            downloaded = trafilatura.fetch_url(url)
            
            # If default fetch fails, try custom logic could handle it, 
            # but for now let's just make sure we are not being blocked easily. 
            # Actually, trafilatura.fetch_url has internal UA. 
            # Let's switch to our own download to control headers.
            import httpx
            with httpx.Client(verify=False, follow_redirects=True, timeout=10.0) as client:
                resp = client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    downloaded = resp.text
                    page.status_code = 200
                else:
                    page.status_code = resp.status_code
                    downloaded = None
            
            if downloaded:
                result = trafilatura.extract(
                    downloaded, 
                    include_links=False, 
                    include_images=False, 
                    include_tables=False,
                    no_fallback=False,
                    output_format='markdown' 
                )
                if result:
                    page.text_markdown = result
                    page.text_plain = result 
                    # Cache successful result
                    self.cache.set(cache_key, page)
                else:
                    page.error = "Extraction returned empty"
            else:
                page.error = f"Failed to download: Status {page.status_code}"
                
        except Exception as e:
            page.error = str(e)
            logger.warning(f"Failed to read {url}: {e}")
            
        return page

    async def read_many(self, urls: List[str]) -> List[FetchedPage]:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, self._fetch_one_sync, url)
            for url in urls
        ]
        return await asyncio.gather(*tasks)
