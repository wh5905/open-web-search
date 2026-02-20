import asyncio
from typing import List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from curl_cffi import requests as curl_requests
from selectolax.parser import HTMLParser

from open_web_search.engines.base import BaseSearchEngine
from open_web_search.schemas.results import SearchResult

class SearxngEngine(BaseSearchEngine):
    def __init__(self, base_url: str, language: str = "auto", max_retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.max_retries = max_retries
        
        # We use a persistent async session with Chrome 120 impersonation
        self.client = curl_requests.AsyncSession(
            impersonate="chrome120",
            timeout=10.0,
            headers={
                "X-Real-IP": "127.0.0.1",
                "X-Forwarded-For": "127.0.0.1"
            }
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _search_one(self, query: str) -> List[SearchResult]:
        results = []
        try:
            # SearXNG HTML Scraping (JSON API is often blocked on default docker without config)
            params = {
                "q": query,
                "categories": "general",
                "language": self.language if self.language != "auto" else "all"
            }
            resp = await self.client.get(f"{self.base_url}/search", params=params)
            resp.raise_for_status()
            
            # Selectolax is significantly faster than BeautifulSoup
            tree = HTMLParser(resp.text)
            
            # Select results
            # Standard SearXNG simple theme structure
            for article in tree.css("article.result")[:10]:
                h3 = article.css_first("h3 a")
                if not h3:
                    continue
                    
                title = h3.text(strip=True)
                url = h3.attributes.get('href', '')
                
                snippet_div = article.css_first(".content")
                snippet = snippet_div.text(strip=True) if snippet_div else ""
                
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source_engine="searxng",
                    published_at=None,
                    raw={"title": title, "url": url, "content": snippet}
                ))

        except curl_requests.errors.RequestsError as e:
            logger.warning(f"SearXNG connection failed: {e}. Is the container running?")
        except Exception as e:
            logger.warning(f"SearXNG search failed for '{query}': {e}")
            
        return results

    async def check_connection(self) -> bool:
        """Verifies if the SearXNG instance is reachable."""
        try:
            # Just hit the root page
            resp = await self.client.get(f"{self.base_url}/")
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"SearXNG check_connection failed: {e.__class__.__name__}: {e}")
            return False

    async def search(self, queries: List[str]) -> List[SearchResult]:
        tasks = [self._search_one(q) for q in queries]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        seen_urls = set()
        
        for res in results_list:
            if isinstance(res, list):
                for item in res:
                    if item.url not in seen_urls:
                        final_results.append(item)
                        seen_urls.add(item.url)
            else:
                logger.error(f"SearXNG batch error: {res}")

        return final_results
        
    async def close(self):
        # Await if it's a coroutine, or just call if it's a synchronous method
        if hasattr(self.client, 'close'):
            if asyncio.iscoroutinefunction(self.client.close):
                await self.client.close()
            else:
                self.client.close()
