import asyncio
from typing import List, Set, Dict, Optional
from loguru import logger
from urllib.parse import urlparse

from open_web_search.schemas.results import FetchedPage
from open_web_search.readers.browser import PlaywrightReader
from open_web_search.crawling.analyzer import LinkAnalyzer, LinkCandidate

class NeuralCrawler:
    """
    A persistent web walker that uses semantic similarity to decide 
    which links to follow next (Best-First Search).
    """

    def __init__(self, reader: PlaywrightReader, analyzer: LinkAnalyzer):
        self.reader = reader
        self.analyzer = analyzer
        self.visited_urls: Set[str] = set()
        self.domain_limit: Dict[str, int] = {} # Per-domain hit counter

    async def crawl(self, start_urls: List[str], query: str, max_pages: int = 5, depth: int = 2) -> List[FetchedPage]:
        logger.info(f"Starting Neural Crawl for query='{query}' with max_pages={max_pages}")
        
        # Priority Frontier: List of LinkCandidate
        frontier: List[LinkCandidate] = []
        collected_pages: List[FetchedPage] = []
        
        # Initialize frontier
        for url in start_urls:
            frontier.append(LinkCandidate(url=url, text="Start URL", score=1.0))

        pages_crawled = 0

        while frontier and pages_crawled < max_pages:
            # Sort frontier by score (High to Low)
            frontier.sort(key=lambda x: x.score, reverse=True)
            
            # Pop best candidate
            current = frontier.pop(0)
            
            # Skip if visited
            if current.url in self.visited_urls:
                continue
            
            self.visited_urls.add(current.url)
            
            # Domain Politeness (Simple check)
            domain = urlparse(current.url).netloc
            if self.domain_limit.get(domain, 0) > 3:
                # Skip if we hit this domain too much in one session
                # (Prevents getting stuck on one site)
                continue
            self.domain_limit[domain] = self.domain_limit.get(domain, 0) + 1

            logger.info(f"Crawling [Score: {current.score:.2f}]: {current.url}")
            
            # Fetch & Extract Links
            fetched_page, raw_links = await self.reader.fetch_with_links(current.url)
            
            collected_pages.append(fetched_page)
            pages_crawled += 1
            
            if fetched_page.error or not raw_links:
                continue

            # Analyze Links
            candidates = [
                LinkCandidate(url=l['url'], text=l['text'], context=l['context']) 
                for l in raw_links
            ]
            
            # Score them against query
            scored_candidates = self.analyzer.score_links(candidates, query)
            
            # Add top candidates to frontier
            # Filter low relevance
            for cand in scored_candidates:
                if cand.score > 0.4: # Tweak threshold
                     frontier.append(cand)
        
        logger.info(f"Crawl finished. Visited {pages_crawled} pages.")
        return collected_pages
