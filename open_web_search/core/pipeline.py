import asyncio
import time
from typing import List, Optional
from loguru import logger

from open_web_search.config import LinkerConfig
from open_web_search.schemas.results import PipelineOutput, SearchResult, FetchedPage, EvidenceChunk

from open_web_search.engines.ddg import DuckDuckGoEngine
from open_web_search.engines.searxng import SearxngEngine
from open_web_search.readers.v2_reader import V2Reader
from open_web_search.readers.pdf_reader import PdfReader
from open_web_search.readers.browser import PlaywrightReader
from open_web_search.refiners.keyword import KeywordRefiner
from open_web_search.refiners.hybrid import HybridRefiner
from open_web_search.security.guards import SecurityGuard
from open_web_search.core.planner import Planner
from open_web_search.crawling.crawler import NeuralCrawler
from open_web_search.crawling.analyzer import LinkAnalyzer

class AsyncPipeline:
    def __init__(self, config: Optional[LinkerConfig] = None):
        self.config = config or LinkerConfig()
        self.request_id = f"req_{int(time.time()*1000)}"
        
        # Initialize components
        # Initialize components
        engines = []
        
        # 1. Primary: SearXNG
        if self.config.engine_provider == "searxng" and self.config.engine_base_url:
            try:
                engines.append(SearxngEngine(
                    base_url=self.config.engine_base_url, 
                    language=self.config.search_language,
                    max_retries=self.config.max_retries
                ))
            except Exception as e:
                logger.error(f"Failed to init SearXNG: {e}")

        # 2. Secondary: DuckDuckGo (Always added as fallback if not primary, or primary fails)
        try:
            # Map standard language codes to DDG regions if needed
            # For simplicity, passing config.search_language directly.
            # Users should use 'us-en', 'kr-kr', 'wt-wt' formats.
            # Default 'auto' maps to 'us-en' (Safe default to avoid IP-based bias)
            ddg_region = "us-en"
            if self.config.search_language and self.config.search_language != "auto":
                ddg_region = self.config.search_language
                
            engines.append(DuckDuckGoEngine(
                region=ddg_region,
                max_retries=self.config.max_retries
            ))
        except Exception as e:
            logger.error(f"Failed to init DDG: {e}")
            
        # 3. Tertiary: Brave (Future Implementation via Config/Key)
        # if self.config.brave_api_key: ...
        
        if not engines:
            # Fallback if everything fails?? DDG usually robust.
            # But we must have at least one.
            logger.critical("No search engines available! Pipeline effectively broken.")
        
        from open_web_search.engines.composite import CompositeSearchEngine
        self.engine = CompositeSearchEngine(engines)
            
        if self.config.reader_type == "browser":
            self.reader = PlaywrightReader(
                concurrency=self.config.concurrency,
                custom_headers=self.config.custom_headers
            )
        else:
            self.reader = V2Reader(
                concurrency=self.config.concurrency,
                custom_headers=self.config.custom_headers
            )
            
        # PDF Reader
        self.pdf_reader = PdfReader(concurrency=2)
        
        # Crawler (Web Walker) Integration
        self.crawler = None
        if self.config.use_neural_crawler and self.config.reader_type == "browser":
            try:
                analyzer = LinkAnalyzer(model_name="all-MiniLM-L6-v2")
                # We cast self.reader to PlaywrightReader since we checked the type
                self.crawler = NeuralCrawler(reader=self.reader, analyzer=analyzer)
                logger.info("Neural Web Walker enabled.")
            except Exception as e:
                logger.error(f"Failed to init NeuralCrawler: {e}")
        
        # 4. Refiner (FlashRanker Integration - ADR 004)
        if self.config.reranker_type == "flash":
            from open_web_search.refiners.flash import FlashRefiner
            logger.info("⚡ [Pipeline] Using FlashRanker (SLM Cross-Encoder)")
            self.refiner = FlashRefiner(self.config)
        else:
            # Default Hybrid Refiner (Bi-Encoder)
            self.refiner = HybridRefiner(
                chunk_size=self.config.chunk_size, 
                min_relevance=self.config.min_relevance
            )
            
        self.security = SecurityGuard(self.config.security)
        self.planner = Planner(self.config)
        self._resilient_browser = None # Lazy loaded singleton for resilience

    async def run(self, query: str, context: Optional[dict] = None) -> PipelineOutput:
        start_time = time.time()
        logger.info(f"[{self.request_id}] Pipeline started for query: {query}")
        
        output = PipelineOutput(query=query)
        if context and "blocked_domains" in context:
            logger.info(f"[{self.request_id}] Context awareness: Blocked {context['blocked_domains']}")
        
        try:
            # 1. Plan
            rewritten_queries = await self.planner.plan(query, context)
            output.rewritten_queries = rewritten_queries
            
            # 2. Search
            logger.info(f"[{self.request_id}] Rewritten Queries: {rewritten_queries}")
            results = await self.engine.search(rewritten_queries)
            output.results = results
            logger.info(f"[{self.request_id}] Found {len(results)} results")
            
            if not results:
                return output

            # 3. Filter & Read (or Crawl)
            urls = []
            pdf_urls = []
            
            for r in results:
                if self.security.is_allowed_url(r.url):
                    # Robust PDF Detection
                    lower_url = r.url.lower()
                    if lower_url.endswith(".pdf") or "/pdf/" in lower_url:
                        pdf_urls.append(r.url)
                    else:
                        urls.append(r.url)
                        
                    if len(urls) + len(pdf_urls) >= self.config.reader_max_pages:
                        break
            
            logger.debug(f"[{self.request_id}] Target URLs: {len(urls)} HTML, {len(pdf_urls)} PDF")
            
            pages = []
            
            # --- EXTREME OPTIMIZATION: ZERO-FETCH TURBO MODE ---
            if getattr(self.config, "mode", "balanced") == "turbo":
                logger.info(f"[{self.request_id}] ⚡ TURBO MODE: Bypassing Reader, using Search Snippets only.")
                # Directly construct virtual pages from snippets
                for r in results:
                    if r.url in urls or r.url in pdf_urls:
                        vp = FetchedPage(
                            url=r.url,
                            title=r.title,
                            text_plain=f"Source: {r.url}\nTitle: {r.title}\n\nSummary (from Search Engine):\n{r.snippet}",
                            status_code=200
                        )
                        pages.append(vp)
            else:
                # Browser/Standard Reading
                if self.crawler:
                    logger.info(f"[{self.request_id}] Engaging Neural Web Walker...")
                    # Crawl recursively starting from HTML URLs
                    if urls:
                        pages.extend(await self.crawler.crawl(
                            start_urls=urls, 
                            query=query, 
                            max_pages=self.config.crawler_max_pages,
                            depth=self.config.crawler_max_depth
                        ))
                elif urls:
                    logger.debug(f"[{self.request_id}] Reading {len(urls)} pages (Standard)")
                    pages.extend(await self.reader.read_many(urls))
                    
                    # --- STEALTH ESCALATION (Phase 16 - Resilient Upgrade) ---
                    if self.config.enable_stealth_escalation and not isinstance(self.reader, PlaywrightReader):
                        pages, stats = await self._recover_with_browser(pages, self.request_id)
                        output.telemetry.update(stats)
                    # -------------------------------------
                
                # PDF Reading
                if pdf_urls and self.pdf_reader:
                    logger.debug(f"[{self.request_id}] Reading {len(pdf_urls)} PDF documents")
                    pages.extend(await self.pdf_reader.read_many(pdf_urls))
            
            
            # Sanitize pages
            # Sanitize pages & Snippet Fallback (v0.5 Universality)
            final_pages = []
            
            # Map URLs to original search results for snippet access
            url_to_snippet = {r.url: (r.snippet, r.title) for r in results}
            
            for p in pages:
                if p.text_plain:
                    p.text_plain = self.security.sanitize_text(p.text_plain)
                if p.text_markdown:
                    p.text_markdown = self.security.sanitize_text(p.text_markdown)
                
                # Check for blocking/failure
                is_failed = False
                if not p.text_plain or len(p.text_plain) < 50:
                    is_failed = True
                if p.error or (p.status_code and p.status_code >= 400):
                    is_failed = True
                
                # Cognitive Unblocking: Always track blocked/failed domains
                if is_failed:
                     try:
                         from urllib.parse import urlparse
                         domain = urlparse(p.url).netloc.replace("www.", "")
                         # Basic dedupe
                         if domain not in output.blocked_domains:
                             output.blocked_domains.append(domain)
                     except:
                         pass

                if is_failed and self.config.enable_snippet_fallback:
                     snippet, original_title = url_to_snippet.get(p.url, ("", ""))
                     if snippet and len(snippet) > 20:
                         logger.warning(f"[{self.request_id}] Fallback to Snippet for {p.url} (Reason: {p.error or 'Blocked'})")
                         # Construct fallback page
                         p.text_plain = f"Source: {p.url}\nTitle: {original_title}\n\nSummary (from Search Engine):\n{snippet}"
                         p.text_markdown = p.text_plain
                         p.error = None # Clear error so it is processed
                         p.status_code = 200 # Soft success
                     else:
                         # Truly dead
                         logger.warning(f"[{self.request_id}] Page dead and no snippet: {p.url}")
                         continue
                
                final_pages.append(p)
            
            output.pages = final_pages
            
            # 4. Refine
            logger.debug(f"[{self.request_id}] Refining evidence")
            evidence = await self.refiner.refine(pages, query)
            output.evidence = evidence
            logger.info(f"[{self.request_id}] Extracted {len(evidence)} evidence chunks")

        except Exception as e:
            logger.exception(f"[{self.request_id}] Pipeline failed")
            output.trace["error"] = str(e)
        
        finally:
            output.elapsed_ms = int((time.time() - start_time) * 1000)
            output.trace["total_ms"] = output.elapsed_ms
            # Clean up if needed
            if hasattr(self.engine, 'close'):
                if asyncio.iscoroutinefunction(self.engine.close):
                    await self.engine.close()
            # If we didn't use crawler, close reader? Reader usually shared or persistent?
            # PlaywrightReader usually needs explicit close if it started the browser.
            # But here we might want to keep it open? 
            # For now, let's close it to be safe and avoid zombies in CLI usage.
            if hasattr(self.reader, 'close'):
                 await self.reader.close()
            # Cleanup Resilient Browser if initialized
            if self._resilient_browser and hasattr(self._resilient_browser, 'close'):
                await self._resilient_browser.close()
            
        return output

        return output

    async def _recover_with_browser(self, pages: List[FetchedPage], req_id: str) -> tuple[List[FetchedPage], dict]:
        """
        Resilience: Detects failed/blocked pages and re-fetches them using a Headless Browser.
        Lazy-loads the browser reader to save resources.
        Returns: (updated_pages, telemetry_data)
        """
        telemetry = {"resilience_triggered": False, "recovered_count": 0, "attempted_urls": []}
        
        failed_urls = []
        for p in pages:
            # Heuristic: Blocked if empty, error, or very short content
            is_blocked = (
                p.error is not None or 
                not p.text_plain or 
                len(p.text_plain) < 300 or # Too short strictly
                "enable javascript" in (p.text_plain or "").lower() or
                "cloudflare" in (p.text_plain or "").lower()
            )
            if is_blocked:
                failed_urls.append(p.url)
        
        if not failed_urls:
            return pages, telemetry

        telemetry["resilience_triggered"] = True
        telemetry["attempted_urls"] = failed_urls
        logger.warning(f"[{req_id}] 🛡️ Resilience Triggered: Recovering {len(failed_urls)} blocked URLs via Browser...")
        
        # Lazy Init Singleton Browser
        if not self._resilient_browser:
            try:
                self._resilient_browser = PlaywrightReader(
                    concurrency=2,
                    headless=True,
                    custom_headers=self.config.custom_headers
                )
                logger.info(f"[{req_id}] Initialized Resilient Browser (Singleton)")
            except Exception as e:
                logger.error(f"[{req_id}] Failed to init Resilient Browser: {e}")
                telemetry["error"] = str(e)
                return pages, telemetry

        try:
            stealth_pages = await self._resilient_browser.read_many(failed_urls)
            
            # Merge results back: Replace failed pages with stealth pages
            stealth_map = {op.url: op for op in stealth_pages}
            new_pages = []
            recovery_count = 0
            
            for p in pages:
                if p.url in stealth_map:
                    sp = stealth_map[p.url]
                    if sp.text_plain and len(sp.text_plain) > 100:
                        logger.info(f"[{req_id}] ✅ Recovered: {p.url}")
                        new_pages.append(sp)
                        recovery_count += 1
                        continue
                new_pages.append(p)
            
            telemetry["recovered_count"] = recovery_count
            logger.info(f"[{req_id}] Resilience Summary: Recovered {recovery_count}/{len(failed_urls)} pages.")
            return new_pages, telemetry
            
        except Exception as e:
            logger.error(f"[{req_id}] Resilience failed during read: {e}")
            telemetry["error"] = str(e)
            return pages, telemetry
