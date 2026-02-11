import asyncio
from open_web_search.core.pipeline import AsyncPipeline
from open_web_search.config import LinkerConfig
from open_web_search.engines.searxng import SearxngEngine
from open_web_search.readers.trafilatura_reader import TrafilaturaReader

# Mock or Override Engine to return a specific URL directly to test Scraper only?
# Or clearer: Just use the Pipeline but force a Search Result that points to Reddit.

from open_web_search.schemas.results import SearchResult

async def test_stealth_escalation():
    print(">>> Testing Stealth Escalation (Trafilatura -> Playwright)")
    
    config = LinkerConfig(
        reader_type="trafilatura",
        enable_stealth_escalation=True,
        engine_provider="ddg" # Doesn't matter, we inject results
    )
    
    pipeline = AsyncPipeline(config)
    
    # Manually inject a result for Reddit (which blocks simple scrapers)
    # We cheat by bypassing the search engine step and calling internal method?
    # No, AsyncPipeline.run does everything.
    # Let's verify via a query that returns Reddit.
    
    query = "latest reddit discussion on agi timeline 2025"
    print(f"Query: {query}")
    
    output = await pipeline.run(query)
    
    print(f"\nTotal Pages Read: {len(output.pages)}")
    
    reddit_pages = [p for p in output.pages if "reddit.com" in p.url]
    
    for p in reddit_pages:
        print(f"\n--- Page: {p.url} ---")
        content_len = len(p.text_plain or "")
        print(f"Content Length: {content_len}")
        print(f"Snippet (First 200chars): {(p.text_plain or '')[:200]}...")
        
        # Check if it was recovered
        # Reddit usually yields very short text on Trafilatura (< 1000 chars) or login screens.
        # Playwright should yield > 1000 chars of comments.
        if content_len > 1000:
            print("SUCCESS: Content seems substantial (likely passed via Stealth)")
        else:
            print("WARNING: Content short. Stealth might have failed or site is truly short.")

if __name__ == "__main__":
    asyncio.run(test_stealth_escalation())
