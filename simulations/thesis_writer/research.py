import asyncio
import os
import sys

# Simulate installation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from open_web_search.core.loop import DeepResearchLoop
from open_web_search.config import LinkerConfig
from dotenv import load_dotenv

load_dotenv("../../.env")

async def main():
    print("=== PROJECT GAMMA: The Thesis Writer ===")
    print("Scenario: Deep technical research using Neural Web Walker.")
    
    # 1. Setup Deep Config
    llm_base = os.getenv("LLM_BASE_URL", "http://192.168.0.10:8101/v1")
    llm_model = os.getenv("LLM_MODEL", "Qwen/Qwen3-4B-Instruct-2507")
    print(f"DEBUG: LLM_BASE={llm_base} MODEL={llm_model}")
    
    config = LinkerConfig(
        engine_provider="searxng",
        engine_base_url="http://127.0.0.1:8080",
        llm_base_url=llm_base,
        llm_model=llm_model,
        
        # Enable the Walker
        use_neural_crawler=True,
        crawler_max_depth=2,
        crawler_max_pages=5,
        observability_level="full"
    )
    
    agent = DeepResearchLoop(config=config)
    
    # query = "PyTorch vs TensorFlow attention mechanism implementation differences code example"
    # Let's use something simpler but "deep" for the test
    query = "Python 3.12 F-string improvements detailed examples" 
    
    print(f"\n[Researching] {query}...")
    
    output = await agent.run(query)
    
    print("\n[Thesis Abstract / Answer]")
    print(output.answer)
    
    print("\n[References]")
    for p in output.pages:
        if p.text_plain and len(p.text_plain) > 100:
            print(f"- {p.title} ({p.url})")

if __name__ == "__main__":
    asyncio.run(main())
