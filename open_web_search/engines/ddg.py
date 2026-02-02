import asyncio
from typing import List
from duckduckgo_search import DDGS
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from open_web_search.engines.base import BaseSearchEngine
from open_web_search.schemas.results import SearchResult

class DuckDuckGoEngine(BaseSearchEngine):
    def __init__(self, region: str = "wt-wt", max_retries: int = 3):
        self.region = region
        self.max_retries = max_retries
        self.ddgs = DDGS()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _search_one(self, query: str) -> List[SearchResult]:
        results = []
        try:
            # backend='api' is usually fastest, 'html' for fallback, 'lite' for lightest
            # DDGS is sync, so we run it in a thread
            ddg_results = await asyncio.to_thread(
                self.ddgs.text, keywords=query, region=self.region, max_results=10
            )

            if not ddg_results:
                 return []
            
            for r in ddg_results:
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                    source_engine="ddg",
                    raw=r
                ))
        except Exception as e:
            logger.warning(f"DDG search failed for '{query}': {e}")
            raise e # Trigger retry
            
        return results

    async def search(self, queries: List[str]) -> List[SearchResult]:
        tasks = [self._search_one(q) for q in queries]
        # Use return_exceptions=True to allow partial success
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
                # Log error from gather
                logger.error(f"Search error in batch: {res}")

        return final_results
