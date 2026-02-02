import asyncio
from typing import List, Optional
from loguru import logger
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

from open_web_search.readers.base import BaseReader
from open_web_search.schemas.results import FetchedPage

class PlaywrightReader(BaseReader):
    """
    A robust, resource-optimized browser reader using Playwright.
    """
    def __init__(self, headless: bool = True, concurrency: int = 3, custom_headers: Optional[dict] = None):
        self.headless = headless
        self.concurrency = concurrency
        self.custom_headers = custom_headers or {}
        self.semaphore = asyncio.Semaphore(concurrency)
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def start(self):
        if not HAS_PLAYWRIGHT:
            logger.error("Playwright not installed. Run `pip install playwright && playwright install chromium`")
            return
        
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-gpu", "--no-sandbox"]
            )

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _fetch_one(self, url: str) -> FetchedPage:
        if not HAS_PLAYWRIGHT:
            return FetchedPage(url=url, error="Playwright missing")

        if not self.browser:
            await self.start()

        async with self.semaphore:
            page = None
            context = None
            try:
                # Create a lightweight context
                import random
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
                ]
                ua = random.choice(user_agents)
                
                context = await self.browser.new_context(
                    user_agent=ua,
                    locale="en-US",
                    extra_http_headers={
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        **self.custom_headers 
                    }
                )
                
                # Block heavy resources
                await context.route("**/*", lambda route: route.abort() 
                    if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                    else route.continue_()
                )
                
                page = await context.new_page()
                
                # Navigate with timeout
                response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                status = response.status if response else 0
                
                if status >= 400:
                    return FetchedPage(url=url, status_code=status, error=f"HTTP {status}")

                # Wait slightly for hydration if needed or just grab text
                # Ideally we check for <main> or <body>
                content = await page.evaluate("document.body.innerText")
                title = await page.title()
                
                return FetchedPage(
                    url=url,
                    final_url=page.url,
                    status_code=status,
                    title=title,
                    text_plain=content,
                    text_markdown=content, # Simplification for now, usually we'd convert HTML to MD
                )
                
            except Exception as e:
                logger.warning(f"Browser fetch failed for {url}: {e}")
                return FetchedPage(url=url, error=str(e))
            finally:
                if page: await page.close()
                if context: await context.close()

    async def extract_links(self, url: str) -> List[dict]:
        """
        Explores the page at `url` and extracts candidate links with context.
        Note: This assumes the browser is already looking at `url` or will navigate to it.
        For efficiency, this is best called right after _fetch_one.
        """
        # For this design, we'll implement a standalone fetch-and-extract or 
        # assume the page is accessible. 
        # Ideally, we modify _fetch_one to return links, but to keep separation of concerns,
        # we'll make a specialized method that re-uses the open page if possible, 
        # but statelessness is safer. 
        
        # Let's rely on _fetch_one logic but expanded. 
        # Actually, best approach: Update _fetch_one to return a richer object 
        # or add a specific 'crawl' method.
        pass

    async def fetch_with_links(self, url: str) -> tuple[FetchedPage, List[dict]]:
        """
        Fetches the page and extracts all valid navigation links.
        Returns (FetchedPage, List[LinkCandidate_Dict])
        """
        if not self.browser:
            await self.start()

        async with self.semaphore:
            page = None
            context = None
            extracted_links = []
            fetched_page = None
            
            try:
                context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                await context.route("**/*", lambda route: route.abort() 
                    if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                    else route.continue_()
                )
                
                page = await context.new_page()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                status = response.status if response else 0
                
                # Extract Content (Robust)
                try:
                     # Wait for body to be present
                     await page.wait_for_selector("body", timeout=5000)
                     content = await page.evaluate("document.body.innerText")
                     title = await page.title()
                except Exception as e:
                     logger.warning(f"Failed to extract content: {e}")
                     content = ""
                     title = "No Title"

                fetched_page = FetchedPage(
                    url=url,
                    final_url=page.url,
                    status_code=status,
                    title=title,
                    text_plain=content,
                    text_markdown=content
                )

                # Extract Links (Robust)
                try:
                    links_data = await page.evaluate("""
                        () => {
                            try {
                                const links = Array.from(document.querySelectorAll('a[href]'));
                                return links.map(a => {
                                    const rect = a.getBoundingClientRect();
                                    if (rect.width < 1 || rect.height < 1) return null; 
                                    
                                    return {
                                        url: a.href,
                                        text: (a.innerText || "").slice(0, 100).trim(),
                                        context: (a.parentElement ? (a.parentElement.innerText || "") : "").slice(0, 200).trim()
                                    };
                                }).filter(l => l && l.text.length > 2 && l.url.startsWith('http'));
                            } catch (err) {
                                return [];
                            }
                        }
                    """)
                    extracted_links = links_data
                except Exception as e:
                    logger.warning(f"Failed to extract links JS: {e}")
                    extracted_links = []

            except Exception as e:
                logger.warning(f"Browser crawl failed for {url}: {e}")
                fetched_page = FetchedPage(url=url, error=str(e))
                
            finally:
                if page: await page.close()
                if context: await context.close()
                
            return fetched_page, extracted_links

    async def read_many(self, urls: List[str]) -> List[FetchedPage]:
        # Simple concurrent fetch for non-crawler use cases
        tasks = [self._fetch_one(url) for url in urls]
        return await asyncio.gather(*tasks)
