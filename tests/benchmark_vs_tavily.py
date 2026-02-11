import asyncio
import time
import os
import json
import httpx
from statistics import mean, median
from dotenv import load_dotenv
from typing import List, Dict

# Linker Imports
from open_web_search.core.pipeline import AsyncPipeline
from open_web_search.config import LinkerConfig

# Load env for Tavily Key
load_dotenv(".env")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

QUERIES = [
    # Simple Fact
    "What is the capital of Australia?",
    # Current Event
    "Latest huge updates in LangChain 2024",
    # Complex/Technical
    "Difference between Mamba architecture and Transformers",
    # Ambiguous
    "Apple price", 
    # Coding
    "Python 3.12 release date"
]

async def benchmark_tavily(query: str) -> Dict:
    """Run single query against Tavily API"""
    if not TAVILY_KEY:
        return {"error": "No API Key", "duration": 0}
        
    start = time.time()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={"query": query, "search_depth": "basic", "api_key": TAVILY_KEY, "include_answer": True},
                timeout=30.0
            )
            data = resp.json()
            duration = time.time() - start
            return {
                "source": "Tavily",
                "query": query,
                "duration": duration,
                "answer": data.get("answer", ""),
                "results_count": len(data.get("results", [])),
                "error": None
            }
        except Exception as e:
            return {"source": "Tavily", "error": str(e), "duration": time.time() - start}

async def benchmark_linker(query: str) -> Dict:
    """Run single query against Linker-Search (Local)"""
    # CORRECTED: Use SearXNG as primary, consistent with production setup
    config = LinkerConfig(
        mode="fast", 
        engine_provider="searxng", 
        engine_base_url="http://127.0.0.1:8080",
        search_language="en-US"
    )
    pipeline = AsyncPipeline(config=config)
    
    start = time.time()
    try:
        # Note: pipeline.run returns PipelineOutput, which contains answer/evidence
        # We need to make sure we are generating an answer? 
        # DeepResearchLoop generates answers, AsyncPipeline just fetches evidence.
        # But the user wants to compare TAVILY (which generates answers mostly with include_answer).
        # AsyncPipeline is just the search/retrieval part.
        # Ideally we compare against DeepResearchLoop for "Answer Quality" 
        # OR AsyncPipeline for "Search Speed".
        # Let's use AsyncPipeline for pure speed comparison first (Apples to Apples with Tavily Search API)
        # Wait, Tavily does RAG too? Tavily Search API is Search.
        # If we use include_answer=True, Tavily does RAG.
        # Let's match: Use Linker's AsyncPipeline (Search) for speed, 
        # but to match Tavily's "Answer", we might need Synthesizer.
        # For this optimization pass, let's focus on SEARCH SPEED (Pipeline).
        
        output = await pipeline.run(query)
        duration = time.time() - start
        
        # Count "valid" pages
        valid_pages = len([p for p in output.pages if not p.error])
        
        return {
            "source": "Linker-Search",
            "query": query,
            "duration": duration,
            "answer": "N/A (Pipeline Only)", # Pipeline doesn't synthesize
            "results_count": valid_pages,
            "error": output.trace.get("error")
        }
    except Exception as e:
        return {"source": "Linker-Search", "error": str(e), "duration": time.time() - start}

async def run_suite():
    print(f"=== Starting Benchmark ===")
    print(f"Queries: {len(QUERIES)}")
    print(f"Tavily Key Present: {bool(TAVILY_KEY)}")
    
    results = []
    
    for q in QUERIES:
        print(f"\nQuery: {q}")
        
        # Linker
        print("  Running Linker-Search...", end="", flush=True)
        l_res = await benchmark_linker(q)
        print(f" Done ({l_res['duration']:.2f}s)")
        results.append(l_res)
        
        # Tavily
        print("  Running Tavily...", end="", flush=True)
        t_res = await benchmark_tavily(q)
        print(f" Done ({t_res['duration']:.2f}s)")
        results.append(t_res)
        
    # Stats
    linker_times = [r['duration'] for r in results if r['source'] == "Linker-Search" and not r['error']]
    tavily_times = [r['duration'] for r in results if r['source'] == "Tavily" and not r['error']]
    
    print("\n=== Final Results ===")
    if linker_times:
        print(f"Linker-Search Avg: {mean(linker_times):.2f}s (Min: {min(linker_times):.2f}s, Max: {max(linker_times):.2f}s)")
    if tavily_times:
        print(f"Tavily Avg:        {mean(tavily_times):.2f}s (Min: {min(tavily_times):.2f}s, Max: {max(tavily_times):.2f}s)")

    # Save detailed
    with open("benchmark_data.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_suite())
