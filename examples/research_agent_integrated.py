import asyncio
import os
from dotenv import load_dotenv

# Ensure we use the .venv if running directly
# import sys
# sys.path.append(".")

from open_web_search.core.loop import DeepResearchLoop
from open_web_search.config import LinkerConfig

# Load env including LLM_BASE_URL
load_dotenv(".env")

async def main():
    print("Initializing Linker-Search Agent with NEURAL WEB WALKER...")
    
    llm_url = os.getenv("LLM_BASE_URL")
    llm_model = os.getenv("LLM_MODEL")
    
    # Enable the WALKER!
    config = LinkerConfig(
        mode="deep",
        llm_base_url=llm_url,
        llm_model=llm_model,
        engine_provider="searxng",
        engine_base_url="http://127.0.0.1:8080",
        search_language="ko-KR",
        reader_type="browser",
        
        # --- THE MAGIC SWITCH ---
        use_neural_crawler=True,
        crawler_max_pages=5, # Allow it to find 5 pages via walking
        crawler_max_depth=2  # Go 2 clicks deep
    )
    
    agent = DeepResearchLoop(config=config)
    
    # A query that needs deep reading
    # "Official Guide" implies we need to find the specific guide, not just the landing page
    query = "Python 3.12 패턴 매칭 공식 문서 튜토리얼 내용 요약"
    
    print(f"\n[Mission] {query}")
    print("-" * 50)
    
    output = await agent.run(query)
    
    print("\n" + "="*50)
    print("FINAL ANSWER")
    print("="*50)
    print(output.answer)
    
    print("\n[Sources Found via Walking]")
    for i, p in enumerate(output.pages):
        text_len = len(p.text_plain) if p.text_plain else 0
        print(f"[{i+1}] {p.title} ({text_len} chars)")
        print(f"    URL: {p.url}")

if __name__ == "__main__":
    asyncio.run(main())
