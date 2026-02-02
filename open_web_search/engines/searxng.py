import asyncio
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from open_web_search.engines.base import BaseSearchEngine
from open_web_search.schemas.results import SearchResult

class SearxngEngine(BaseSearchEngine):
    def __init__(self, base_url: str, language: str = "auto", max_retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Select results
            # Standard SearXNG simple theme structure
            for article in soup.select("article.result")[:10]:
                h3 = article.select_one("h3 a")
                if not h3:
                    continue
                    
                title = h3.get_text(strip=True)
                url = h3['href']
                
                snippet_div = article.select_one(".content")
                snippet = snippet_div.get_text(strip=True) if snippet_div else ""
                
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source_engine="searxng",
                    published_at=None,
                    raw={"title": title, "url": url, "content": snippet}
                ))

        except httpx.RequestError as e:
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
        await self.client.aclose()
