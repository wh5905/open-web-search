import os
import requests
import json
from dotenv import load_dotenv

load_dotenv("../../.env")

# In CrewAI, users typically import 'TavilySearchTool'
# We simulate how CrewAI enables tools via env vars.
# TAVILY_API_URL -> http://127.0.0.1:8000/search

def mock_crewai_usage():
    print("=== PROJECT EPSILON: The Marketing Crew (CrewAI Mock) ===")
    print("Scenario: Verifying Universal API with CrewAI-style pattern.")
    
    # 1. Configuration (Simulating .env)
    api_key = "linker-local"
    api_url = "http://127.0.0.1:8000/search"
    
    # 2. Agent Action (Researcher)
    query = "Benefits of local LLMs for enterprise security"
    print(f"\n[Agent: Researcher] Executing task: Find info about '{query}'")
    
    # CrewAI calls the tool logic internally. We mock that call (HTTP POST).
    payload = {
        "query": query,
        "max_results": 3,
        "search_depth": "advanced",
        "include_answer": True
    }
    
    try:
        print(f"[Tool] POST {api_url}")
        resp = requests.post(api_url, json=payload, timeout=60)
        
        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("answer", "No answer")
            sources = [r["url"] for r in data.get("results", [])]
            
            print(f"\n[Agent: Researcher] Found insights:\n{answer[:300]}...")
            print(f"\n[Sources]\n" + "\n".join(sources))
            
            # 3. Agent Action (Writer) - mock
            print(f"\n[Agent: Writer] Drafting blog post based on findings...")
            print("[Success] Workflow completed.")
        else:
            print(f"[Error] API returned {resp.status_code}: {resp.text}")

    except Exception as e:
        print(f"[Fatal] Connection failed: {e}")

if __name__ == "__main__":
    mock_crewai_usage()
