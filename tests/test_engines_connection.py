import asyncio
from open_web_search.engines.searxng import SearxngEngine
from open_web_search.engines.ddg import DuckDuckGoEngine

async def test():
    complex_query = "site:medium.com summary of Vercel pricing controversies 2024"
    print(f"Testing SearXNG with: {complex_query}")
    try:
        searx = SearxngEngine(base_url="http://127.0.0.1:8080")
        results = await searx.search(complex_query)
        print(f"SearXNG Results: {len(results)}")
        if results:
            print(f"Sample: {results[0].title} - {results[0].url}")
    except Exception as e:
        print(f"SearXNG Failed: {e}")

    complex_query = "Define agentic patterns in AI software engineering and their core components"
    
    print("\nTesting DDG with Complex Query...")
    try:
        ddg = DuckDuckGoEngine()
        results = await ddg.search(complex_query)
        print(f"DDG Results: {len(results)}")
        if results:
            print(f"Sample: {results[0].title} - {results[0].url}")
    except Exception as e:
        print(f"DDG Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
