import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from loguru import logger
import hashlib

from open_web_search.readers.base import BaseReader
from open_web_search.schemas.results import FetchedPage
from open_web_search.utils.cache import CacheManager

try:
    from curl_cffi import requests as curl_requests
    from selectolax.parser import HTMLParser
    DEPENDENCIES_LOADED = True
except ImportError:
    DEPENDENCIES_LOADED = False
    logger.warning("V2Reader dependencies missing. Run: pip install curl_cffi selectolax")

class V2Reader(BaseReader):
    """
    Next-Generation Stealth Reader (2026 Architecture).
    Uses curl_cffi to spoof TLS/JA3 fingerprints (bypassing Cloudflare/Datadome).
    Uses selectolax for C-level, ultra-fast DOM parsing (replacing slow heuristic extraction).
    """
    def __init__(self, concurrency: int = 5, cache_dir: str = ".linker_cache", custom_headers: Optional[dict] = None):
        if not DEPENDENCIES_LOADED:
            raise ImportError("V2Reader requires 'curl_cffi' and 'selectolax'.")
            
        self.executor = ThreadPoolExecutor(max_workers=concurrency)
        self.cache = CacheManager.get_instance(cache_dir=cache_dir)
        self.custom_headers = custom_headers or {}
        
        # curl_cffi supports impersonate targets. We will use a modern Chrome signature.
        self.impersonate_target = "chrome120" 

    def _extract_text_selectolax(self, html_content: str) -> str:
        """
        Ultra-fast heuristic extraction using selectolax.
        Attempts to locate the primary content node before extracting text.
        """
        tree = HTMLParser(html_content)
        
        # 1. Strip noise (Scripts, Styles, Nav, Footers, Ads)
        tags_to_remove = [
            'script', 'style', 'noscript', 'meta', 'head', 'link', 
            'nav', 'footer', 'header', 'aside', 'iframe', 'svg',
            '[aria-hidden="true"]', '.ad', '.advertisement', '.social-share',
            '#sidebar', '.sidebar', '.menu', '.widget', '.cookie-banner'
        ]
        
        for tag in tags_to_remove:
            for node in tree.css(tag):
                node.decompose()
                
        # 2. Try to find the main article container (Heuristic)
        main_content_selectors = [
            'article', 'main', '[role="main"]', 
            '.post-content', '.article-content', '.entry-content', '#content'
        ]
        
        target_node = tree.body
        for selector in main_content_selectors:
            found = tree.css_first(selector)
            if found:
                target_node = found
                break
                
        if not target_node:
            target_node = tree.body
            
        # 3. Extract visible text with basic formatting
        # We replace block elements with newlines for readable markdown-ish output
        if not target_node:
            return ""
            
        clean_text = target_node.text(separator='\n\n', strip=True)
        
        # Cleanup excess newlines
        import re
        clean_text = re.sub(r'\\n{3,}', '\\n\\n', clean_text)
        
        return clean_text

    def _fetch_one_sync(self, url: str) -> FetchedPage:
        cache_key = f"v2page:{hashlib.md5(url.encode()).hexdigest()}"
        cached_page = self.cache.get(cache_key)
        if cached_page and not cached_page.error:
            return cached_page

        page = FetchedPage(url=url)
        try:
            # 1. FETCH (The Stealth Move)
            # curl_cffi handles the TLS/JA3 spoofing perfectly.
            response = curl_requests.get(
                url, 
                impersonate=self.impersonate_target,
                timeout=10,
                headers=self.custom_headers
            )
            
            page.status_code = response.status_code
            
            if response.status_code == 200:
                # 2. PARSE (The Speed Move)
                clean_text = self._extract_text_selectolax(response.text)
                
                if clean_text and len(clean_text) > 50:
                    page.text_plain = clean_text
                    page.text_markdown = clean_text # V2 primarily focuses on raw text extraction speed
                    self.cache.set(cache_key, page)
                else:
                    page.error = "Selectolax extraction empty or too short."
            else:
                page.error = f"Blocked or failed. Status: {response.status_code}"
                
        except Exception as e:
            page.error = str(e)
            logger.warning(f"[V2Reader] Failed to read {url}: {e}")
            
        return page

    async def read_many(self, urls: List[str]) -> List[FetchedPage]:
        """
        Runs the highly optimized synchronous curl_cffi fetches concurrently.
        """
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, self._fetch_one_sync, url)
            for url in urls
        ]
        return await asyncio.gather(*tasks)

    async def close(self):
        self.executor.shutdown(wait=False)
