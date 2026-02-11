
import asyncio
import os
from open_web_search import LinkerConfig, AsyncPipeline
from open_web_search.schemas.results import FetchedPage, EvidenceChunk

async def main():
    print("🚀 Verifying FlashRanker (ADR 004)...")
    
    # 1. Setup Mock Data
    print("\n--- Setup Data ---")
    query = "Apple pie recipe vs Apple stock analysis"
    pages = [
        FetchedPage(url="http://cooking.com", text_plain="Apple pie is made with apples, sugar, and flour. It is delicious."),
        FetchedPage(url="http://finance.com", text_plain="Apple stock (AAPL) rose 5% today due to strong iPhone sales."),
        FetchedPage(url="http://news.com", text_plain="Farmers are growing more apples this year."),
        FetchedPage(url="http://tech.com", text_plain="New Macbook Pro released by Apple Inc.")
    ]
    # Manually split chunks for testing
    for p in pages:
        p.chunks = [EvidenceChunk(content=p.text_plain, source_url=p.url)]

    # 2. Test Fast Mode (Baseline)
    print("\n--- Testing 'Fast' Mode (Bi-Encoder) ---")
    config_fast = LinkerConfig(reranker_type="fast", max_evidence=2)
    pipeline_fast = AsyncPipeline(config_fast)
    # Inject pages directly to refiner
    chunks_fast = await pipeline_fast.refiner.refine(pages, query)
    print("Top Chunks (Fast):")
    for c in chunks_fast:
        print(f"[{c.relevance_score:.4f}] {c.content[:50]}...")

    # 3. Test Flash Mode (Cross-Encoder)
    print("\n--- Testing 'Flash' Mode (Cross-Encoder) ---")
    config_flash = LinkerConfig(reranker_type="flash", max_evidence=2)
    pipeline_flash = AsyncPipeline(config_flash)
    
    # This should trigger lazy load
    chunks_flash = await pipeline_flash.refiner.refine(pages, query)
    print("Top Chunks (Flash):")
    for c in chunks_flash:
        print(f"[{c.relevance_score:.4f}] {c.content[:50]}...")
        
    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    asyncio.run(main())
