import asyncio
import os
import uvicorn
import requests
import time
from multiprocessing import Process

def run_server():
    """Run the FastAPI server for testing."""
    uvicorn.run("open_web_search.server.app:app", host="127.0.0.1", port=9999, log_level="warning")

def test_server_api():
    print("🚀 Starting Server API Test...")
    
    # 1. Start Server in Background
    proc = Process(target=run_server, daemon=True)
    proc.start()
    time.sleep(10) # Wait for startup (increased for slow machines)
    
    try:
        url = "http://127.0.0.1:9999/search"
        payload = {
            "query": "What is FlashRanker?",
            "mode": "fast",
            "reranker": "fast", # Use fast for quick test
            "max_results": 2
        }
        
        print(f"📡 Sending Request: {payload}")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Answer: {data.get('answer')}")
            print(f"Results: {len(data.get('results', []))}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        proc.terminate()
        proc.join()
        print("🛑 Server Stopped")

if __name__ == "__main__":
    test_server_api()
