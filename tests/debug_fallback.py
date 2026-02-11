import asyncio
from open_web_search.core.pipeline import AsyncPipeline
from open_web_search.config import LinkerConfig

async def test_fallback():
    print(">>> Testing Fallback Strategy (Hydra)")
    
    # 1. Config with BROKEN SearXNG URL to force failover
    config = LinkerConfig(
        engine_provider="searxng",
        engine_base_url="http://bad-url-that-fails:9999", # FORCE FAILURE
        max_retries=1,
        search_language="en-US" # Verify this fixes the Chinese/Zhihu issue
    )
    
    pipeline = AsyncPipeline(config)
    
    query = "What is the capital of France?"
    print(f"Query: {query}")
    print("Expecting SearXNG failure -> Fallback to DDG...")
    
    output = await pipeline.run(query)
    
    print(f"Results Found: {len(output.results)}")
    if output.results:
        first = output.results[0]
        print(f"Top Result: {first.title} ({first.url})")
        print(f"Source Engine: {first.source_engine}")
        
        if first.source_engine == "ddg":
            print("SUCCESS: Fallback to DDG worked!")
        else:
            print(f"FAIL: Source engine is {first.source_engine} (Expected ddg)")
    else:
        print("FAIL: No results returned.")

if __name__ == "__main__":
    import asyncio
    import sys
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(test_fallback())
