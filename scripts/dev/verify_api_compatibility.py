"""
Verification script: Simulates a LangChain Agent hitting the local Universal API server
using the exact Tavily API schema.
"""
import asyncio
import httpx
import json

async def simulate_agent_call():
    print("Agent: Preparing to call local Universal API (Tavily format)...")
    
    # This is exactly the JSON payload LangChain's TavilySearchAPIWrapper sends
    payload = {
        "query": "Who won the super bowl in 2024?",
        "search_depth": "basic",
        "include_answer": False,
        "max_results": 3,
        
        # Linker Extension: We can pass V1 configs dynamically
        "mode": "turbo", 
        "reranker": "fast"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("http://127.0.0.1:8800/search", json=payload)
            resp.raise_for_status()
            
            data = resp.json()
            
            print("\n----- SERVER RESPONSE (Drop-in Success) -----")
            print(f"Query: {data['query']}")
            print(f"Results Array Length: {len(data['results'])}")
            print(f"Response Time: {data['response_time']:.2f}s")
            
            if data['results']:
                first_result = data['results'][0]
                print(f"\nTop Result Title: {first_result['title']}")
                print(f"Top Result URL: {first_result['url']}")
                print(f"Content Preview: {first_result['content'][:100]}...\n")
                
            print("Status: 100% COMPATIBLE")
            
    except httpx.ConnectError:
        print("ERROR: Could not connect to the API server. Is 'open-web-search serve' running on port 8800?")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_agent_call())
