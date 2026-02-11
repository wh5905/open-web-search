import asyncio
from open_web_search.engines.searxng import SearxngEngine
from open_web_search.config import LinkerConfig

async def main():
    config = LinkerConfig(engine_base_url="http://127.0.0.1:8080")
    engine = SearxngEngine(config.engine_base_url)
    
    query = "Key breakthroughs and comparisons of Agentic AI frameworks (LangGraph, CrewAI, AutoGen) in late 2024 and 2025"
    print(f"Searching for: {query}")
    
    # Pass as list, remove invalid arg
    results = await engine.search([query])
    
    print(f"Found {len(results)} results:")
    for i, res in enumerate(results):
        print(f"[{i+1}] {res.title}")
        print(f"    URL: {res.url}")
        print(f"    Snippet: {res.snippet[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
