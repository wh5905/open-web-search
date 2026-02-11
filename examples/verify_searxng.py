import asyncio
import os
from dotenv import load_dotenv
from open_web_search.core.pipeline import AsyncPipeline
from open_web_search.config import LinkerConfig

load_dotenv()

async def verify():
    print("Verifying SearXNG integration...")
    
    # Configure for SearXNG + Korean
    config = LinkerConfig(
        engine_provider="searxng",
        engine_base_url=os.getenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080"),
        search_language="ko-KR"
    )
    
    pipeline = AsyncPipeline(config)
    
    # Check connection
    if hasattr(pipeline.engine, "check_connection"):
        alive = await pipeline.engine.check_connection()
        print(f"Engine Alive: {alive}")
        if not alive:
            print("Engine is down. Aborting.")
            return

    # Search
    query = "파이썬 3.12 새로운 기능"
    print(f"Searching for: {query}")
    results = await pipeline.engine.search([query])
    
    if results:
        print(f"Found {len(results)} results.")
        for r in results[:3]:
            print(f"- [{r.title}]({r.url})")
            if "파이썬" not in r.title and "Python" not in r.title and "3.12" not in r.title:
                 print(f"  WARNING: Relevance unclear: {r.snippet[:50]}...")
    else:
        print("No results found!")
        
    await pipeline.engine.close()

if __name__ == "__main__":
    asyncio.run(verify())
