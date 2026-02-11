import sys
import os
import asyncio
from open_web_search.core.pipeline import AsyncPipeline
from open_web_search.config import LinkerConfig

# Ensure we can import open_web_search
# sys.path imports removed as we assume package is installed

async def main():
    print("Initializing Linker-Search...")
    config = LinkerConfig(
        mode="fast",
        observability_level="basic"
    )
    pipeline = AsyncPipeline(config)
    
    query = "latest advancements in quantum computing 2024"
    print(f"Searching for: {query}")
    
    output = await pipeline.run(query)
    
    print(f"\nSearch completed in {output.elapsed_ms}ms")
    print(f"Results: {len(output.results)}")
    print(f"Pages Fetched: {len(output.pages)}")
    for p in output.pages:
        print(f" - {p.url}: Status {p.status_code}, Text Len: {len(p.text_plain or '')}, Error: {p.error}")

    print(f"Evidence Chunks: {len(output.evidence)}")
    
    print("\n--- Evidence ---")
    for ev in output.evidence[:3]:
        print(f"[{ev.relevance_score:.2f}] {ev.title} ({ev.url})")
        print(f"{ev.content[:200]}...")
        print()

if __name__ == "__main__":
    asyncio.run(main())
