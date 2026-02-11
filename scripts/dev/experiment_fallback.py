import asyncio
import os
import shutil
import sys
from pathlib import Path
from dotenv import load_dotenv

# Robust Project Root Detection
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
# Fallback if run from root (before move)
if (SCRIPT_DIR / "open_web_search").exists():
    PROJECT_ROOT = SCRIPT_DIR

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Load Env
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path)

from open_web_search.core.loop import DeepResearchLoop
from open_web_search.config import LinkerConfig

# Query that targets a blocked site but has alternatives
# reddit is usually blocked. 
QUERY = "What are the most controversial opinions on Vercel pricing from Reddit and Hacker News in 2024?"

async def run_experiment(mode_name: str, fallback_enabled: bool):
    print(f"\n{'='*40}")
    print(f"Running Experiment: {mode_name} (Fallback={fallback_enabled})")
    print(f"{'='*40}")
    
    # 1. Clear Cache to force fresh search
    if os.path.exists(".linker_cache"):
        try:
            shutil.rmtree(".linker_cache")
            print("[Setup] Cache cleared.")
        except:
            pass
            
    # 2. Config
    config = LinkerConfig(
        engine_provider="searxng",
        engine_base_url="http://127.0.0.1:8080",
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_model=os.getenv("LLM_MODEL"),
        enable_snippet_fallback=fallback_enabled,
        max_evidence=5
    )
    
    agent = DeepResearchLoop(config)
    output = await agent.run(QUERY)
    
    print(f"\n[Result] {mode_name}")
    print(f"Trace Keys: {list(output.trace.keys())}")
    for k, v in output.trace.items():
        if k.startswith("round_"):
             # v is the dictionary of trace from that round
             queries = v.get('rewritten_queries', 'N/A') # Wait, pipeline trace doesn't store queries, output object does.
             # My loop logic: final_output.rewritten_queries = output.rewritten_queries (only last round)
             # I need to check how loop stores iteration data.
             # Loop: final_output.trace[f"round_{current_depth}"] = output.trace
             # Pipeline trace does NOT contain rewritten_queries by default schema?
             # Let's inspect v keys
             print(f"{k} Keys: {list(v.keys())}")
             print(f"{k} Trace: {v}")
             
    print(f"Evidence Count: {len(output.evidence)}")
    print(f"Answer Length: {len(output.answer)}")
    print("-" * 20)
    print(output.answer[:500] + "...")
    print("="*40)
    
    return output

async def main():
    # Run Mode A: Fallback ON (Current v0.5)
    # Expectation: Gets snippets from Reddit, answers quickly, but maybe shallow.
    await run_experiment("Mode A: Snippet Fallback ON", True)
    
    # Run Mode C: Synergistic (Fallback ON + Replanning)
    # Expectation: 
    # 1. Round 1: Reddit blocked -> Snippet Fallback (Score low).
    # 2. Loop continues (insufficient strong evidence).
    # 3. Replanning (Unblocking logic) -> Targets Medium/Blogs.
    # 4. Round 2: Scrapes Medium -> Better evidence.
    # 5. Result: Richer answer than Mode A.
    await run_experiment("Mode C: Smart Unblocking (Active)", True)

if __name__ == "__main__":
    asyncio.run(main())
