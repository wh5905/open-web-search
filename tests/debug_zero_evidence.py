import asyncio
import os
from open_web_search.engines.searxng import SearxngEngine
from open_web_search.config import LinkerConfig
from open_web_search.refiners.hybrid import HybridRefiner
from open_web_search.readers.trafilatura_reader import TrafilaturaReader
from open_web_search.schemas.results import FetchedPage

async def debug_search():
    print(">>> 1. SEARCH")
    config = LinkerConfig(engine_base_url="http://127.0.0.1:8080", enable_snippet_fallback=True)
    engine = SearxngEngine(config.engine_base_url)
    
    # query = "Is intermittent fasting effective for building muscle in women? Scientific consensus 2024."
    # query = "Effectiveness of intermittent fasting on muscle gain in women according to 2024 scientific studies"
    query = "Latest verified leaks for GTA VI release date and map features from Reddit and Twitter."
    results = await engine.search([query])
    print(f"Results: {len(results)}")
    
    if not results:
        print("No results.")
        return

    # Extract URLs from results
    urls = [r.url for r in results[:5]] # Take top 5
    print(f"Top 5 URLs: {urls}")
    
    print("\n>>> 2. READ (Trafilatura)")
    reader = TrafilaturaReader()
    pages = await reader.read_many(urls)
    print(f"Fetched {len(pages)} pages")
    
    # Simulate Pipeline Sanitize/Fallback
    print("\n>>> 3. SANITIZE & FALLBACK")
    final_pages = []
    url_to_snippet = {r.url: (r.snippet or "", r.title) for r in results}
    
    for p in pages:
        orig = url_to_snippet.get(p.url, ("", ""))
        snippet = orig[0]
        title = orig[1]
        
        failed = False
        if not p.text_plain or len(p.text_plain) < 50:
            failed = True
        
        print(f"Page {p.url[:30]}... len={len(p.text_plain or '')} failed={failed}")
        
        if failed and config.enable_snippet_fallback:
            if snippet and len(snippet) > 20:
                print(f" -> FALLBACK to Snippet: {snippet[:50]}...")
                p.text_plain = f"Source: {p.url}\nTitle: {title}\n\nSummary:\n{snippet}"
                p.text_markdown = p.text_plain
                failed = False
            else:
                print(" -> DEAD (No snippet)")
        
        if not failed:
            final_pages.append(p)
            
    print(f"Final Valid Pages: {len(final_pages)}")

    print("\n>>> 4. REFINE")
    refiner = HybridRefiner(chunk_size=config.chunk_size, min_relevance=config.min_relevance)
    evidence = await refiner.refine(final_pages, query)
    
    print(f"Total Evidence Chunks: {len(evidence)}")
    for e in evidence:
        print(f" - [{e.relevance_score:.2f}] {e.content[:100]}...")

if __name__ == "__main__":
    asyncio.run(debug_search())
