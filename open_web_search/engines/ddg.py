import asyncio
from typing import List
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from curl_cffi import requests as curl_requests
from selectolax.parser import HTMLParser

from open_web_search.engines.base import BaseSearchEngine
from open_web_search.schemas.results import SearchResult

class DuckDuckGoEngine(BaseSearchEngine):
    def __init__(self, region: str = "wt-wt", max_retries: int = 3):
        self.region = region
        self.max_retries = max_retries
        
        # Chrome impersonation session
        self.client = curl_requests.AsyncSession(
            impersonate="chrome120",
            timeout=10.0,
            headers={"Referer": "https://lite.duckduckgo.com/"}
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _search_one(self, query: str) -> List[SearchResult]:
        results = []
        try:
            # We scrape the DuckDuckGo Lite HTML version directly.
            # This is vastly more stable than unofficial JSON endpoints because we use curl_cffi.
            params = {
                "q": query,
                "kl": self.region,
                "df": "" 
            }
            
            resp = await self.client.post(
                "https://lite.duckduckgo.com/lite/", 
                data=params
            )
            resp.raise_for_status()
            
            tree = HTMLParser(resp.text)
            
            # DDG Lite uses tables for results
            for tr in tree.css("tr"):
                td_result = tr.css_first("td.result-snippet")
                if not td_result:
                    continue
                    
                # The title and URL are usually in the previous TR row with class 'result-sponsored' or just an anchor
                # A more robust selector for DDG lite:
                # Actually, DDG lite structure:
                # <tr> <td> <a class="result-title">...
                # <tr> <td class="result-snippet">...
                pass
            
            # Since parsing the table can be slightly brittle if DDG changes, 
            # let's write a robust extraction for the standard DDG HTML
            # Actually, `html.duckduckgo.com/html` is better structured
            resp = await self.client.post(
                "https://html.duckduckgo.com/html/", 
                data={"q": query, "kl": self.region}
            )
            resp.raise_for_status()
            
            tree = HTMLParser(resp.text)
            
            for elem in tree.css(".result"):
                a_tag = elem.css_first("a.result__a")
                if not a_tag:
                    continue
                
                title = a_tag.text(strip=True)
                url = a_tag.attributes.get('href', '')
                
                # Clean up DDG redirect URL if present
                if url.startswith("//duckduckgo.com/l/?uddg="):
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                    if 'uddg' in parsed:
                        url = urllib.parse.unquote(parsed['uddg'][0])
                
                snippet_tag = elem.css_first(".result__snippet")
                snippet = snippet_tag.text(strip=True) if snippet_tag else ""
                
                if url and title and not url.startswith("javascript:"):
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source_engine="ddg",
                        raw={"title": title, "url": url, "content": snippet}
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
        
    async def close(self):
        if hasattr(self.client, 'close'):
            if asyncio.iscoroutinefunction(self.client.close):
                await self.client.close()
            else:
                self.client.close()
