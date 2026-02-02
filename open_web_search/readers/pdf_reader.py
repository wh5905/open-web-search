import io
import asyncio
from typing import List, Optional
import httpx
from loguru import logger
from open_web_search.readers.base import BaseReader
from open_web_search.schemas.results import FetchedPage

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

class PdfReader(BaseReader):
    """
    Specialized reader for PDF documents.
    Downloads the PDF binary and extracts text using pypdf.
    """
    def __init__(self, concurrency: int = 3):
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    async def _fetch_one(self, url: str) -> FetchedPage:
        if not HAS_PYPDF:
            return FetchedPage(url=url, error="pypdf not installed")

        async with self.semaphore:
            try:
                logger.debug(f"Downloading PDF: {url}")
                resp = await self.client.get(url)
                
                if resp.status_code >= 400:
                    return FetchedPage(url=url, status_code=resp.status_code, error=f"HTTP {resp.status_code}")
                
                # Check Content-Type just in case
                content_type = resp.headers.get("content-type", "").lower()
                if "pdf" not in content_type and not url.lower().endswith(".pdf"):
                     logger.warning(f"URL {url} might not be a PDF (Content-Type: {content_type})")

                # Parse PDF
                pdf_file = io.BytesIO(resp.content)
                reader = pypdf.PdfReader(pdf_file)
                
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                
                full_text = "\n".join(text)
                
                # Metadata
                info = reader.metadata
                title = info.title if info and info.title else url.split("/")[-1]
                
                return FetchedPage(
                    url=url,
                    final_url=str(resp.url),
                    status_code=resp.status_code,
                    title=title,
                    text_plain=full_text,
                    text_markdown=full_text, # PDF text is plain usually
                    metadata=dict(info) if info else {}
                )
                
            except Exception as e:
                logger.error(f"PDF fetch failed for {url}: {e}")
                return FetchedPage(url=url, error=str(e))

    async def read_many(self, urls: List[str]) -> List[FetchedPage]:
        tasks = [self._fetch_one(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def close(self):
        await self.client.aclose()
