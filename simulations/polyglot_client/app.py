import asyncio
import time
import httpx
import os
from dotenv import load_dotenv

load_dotenv("../../.env")

API_URL = "http://127.0.0.1:8000/search"

# Mock Queries simulating a dashboard
QUERIES = [
    "Next.js 14 server actions example",
    "React Server Components best practices",
    "Express.js vs Fastify benchmark 2024",
    "Tailwind CSS v4 features",
    "Vercel AI SDK tutorial"
]

async def fetch_search(client, query):
    start = time.time()
    try:
        # Simulate Tavily API Request Format
        payload = {
            "query": query,
            "max_results": 3,
            "include_answer": True,
            "search_depth": "basic" # Fast mode for dashboard
        }
        
        response = await client.post(API_URL, json=payload, timeout=30.0)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            title = data['results'][0]['title'] if data['results'] else "No results"
            print(f"[✅ 200] {query[:20]}... | {elapsed:.2f}s | Top: {title}")
            return True
        else:
            print(f"[❌ {response.status_code}] {query[:20]}... | Error: {response.text}")
            return False
            
    except Exception as e:
        import traceback
        print(f"[❌ FAIL] {query[:20]}... | Exception: {type(e).__name__}: {e}")
        return False

async def main():
    print("=== PROJECT BETA: Polyglot Dashboard ===")
    print(f"Scenario: High-concurrency dashboard hitting {API_URL}")
    print(f"Simulating {len(QUERIES)} concurrent users...")
    
    async with httpx.AsyncClient() as client:
        tasks = [fetch_search(client, q) for q in QUERIES]
        results = await asyncio.gather(*tasks)
        
    print("-" * 30)
    print(f"Success Rate: {sum(results)}/{len(results)}")

if __name__ == "__main__":
    asyncio.run(main())
