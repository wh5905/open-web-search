import asyncio
import threading
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
load_dotenv("../../.env")

# --- 1. The Corporate Intranet (Hidden Service) ---
app = FastAPI()

@app.get("/wiki/competitor-x-strategy", response_class=HTMLResponse)
def internal_wiki(x_corp_token: str = Header(None)):
    if x_corp_token != "omega-level-access":
        raise HTTPException(status_code=403, detail="Access Denied")
    return """
    <html>
        <body>
            <h1>Competitor X: Project 'Nebula' Strategy</h1>
            <p><strong>CONFIDENTIAL / INTERNAL USE ONLY</strong></p>
            <p>Our intel suggests Competitor X is launching 'Nebula' in Q3.</p>
            <p>Key Features: Ultra-low latency search (10ms) using purely cached snippets.</p>
            <p>Weakness: Low accuracy on complex queries.</p>
        </body>
    </html>
    """

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=9998, log_level="error")

# --- 2. The Analyst Agent (Linker-Search) ---
from open_web_search.core.loop import DeepResearchLoop
from open_web_search.config import LinkerConfig, SecurityConfig

async def agent_task():
    print("=== PROJECT OMEGA: The Corporate Strategist ===")
    print("[Scenario] Integrated Analysis: Internal Intel + External Market Data")
    
    # 1. Initialize in Enterprise Mode
    config = LinkerConfig(
        # General Settings
        mode="balanced",
        engine_provider="searxng",
        engine_base_url="http://127.0.0.1:8080",
        search_language="en-US",
        
        # Security / Enterprise
        network_profile="enterprise", # Allow private IP
        custom_headers={"X-Corp-Token": "omega-level-access"},
        security=SecurityConfig(
            allowed_domains=["127.0.0.1", "google.com", "duckduckgo.com", "ycombinator.com"], # Strict Whitelist + Intranet
            network_profile="enterprise"
        ),
        
        # LLM
        llm_base_url=os.getenv("LLM_BASE_URL", "http://192.168.0.10:8101/v1"),
        llm_model=os.getenv("LLM_MODEL", "Qwen/Qwen3-4B-Instruct-2507"),
    )
    
    # We need to manually inject the internal URL into the planner or context
    # because DDG won't find localhost URLs.
    # In a real app, the RAG system might feed "related documents" into the prompt.
    # Here, we will explicitly ask the agent to "check the internal wiki at ..."
    
    wiki_url = "http://127.0.0.1:9998/wiki/competitor-x-strategy"
    query = f"""
    Compare 'Competitor X Nebula' (source: {wiki_url}) against current market standards for Search Latency.
    What are the typical latencies for Google/Algolia?
    Synthesize an executive summary.
    """
    
    print(f"\n[Analyst] Executing Integrated Research Plan...")
    agent = DeepResearchLoop(config=config)
    
    output = await agent.run(query)
    
    print("\n" + "="*50)
    print("EXECUTIVE SUMMARY (GENERATED)")
    print("="*50)
    print(output.answer)
    print("\n" + "="*50)
    
    print("\n[Audit Trace]")
    for p in output.pages:
        if "127.0.0.1" in p.url:
            print(f"✅ INTERNAL SOURCE ACCESSED: {p.url}")
        else:
            print(f"🌐 EXTERNAL SOURCE ACCESSED: {p.url}")

async def main():
    # Start Intranet
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    await asyncio.sleep(2)
    
    await agent_task()

if __name__ == "__main__":
    asyncio.run(main())
