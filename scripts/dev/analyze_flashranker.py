import asyncio
import time
from open_web_search.config import LinkerConfig
from open_web_search.core.pipeline import AsyncPipeline
from open_web_search.schemas.results import EvidenceChunk

# Mock Token Counter (Simple approximation: 1 word = 1.3 tokens)
def count_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)

async def analyze_strategy(strategy_name: str, config: LinkerConfig, query: str):
    print(f"\n--- Strategy: {strategy_name} ---")
    
    pipeline = AsyncPipeline(config)
    start_time = time.time()
    try:
        output = await pipeline.run(query)
    except Exception as e:
        print(f"Error: {e}")
        return
        
    duration = time.time() - start_time
    
    # Calculate Token Load
    total_tokens = 0
    relevant_chunks = 0
    
    print(f"Time: {duration:.2f}s")
    print(f"Evidence Count: {len(output.evidence)}")
    
    for i, chunk in enumerate(output.evidence):
        tokens = count_tokens(chunk.content)
        total_tokens += tokens
        
        # Check for key information (manual ground truth check for this query)
        # Query: "Python 3.13 release notes"
        # Key Info: "JIT", "October 2024", "GIL"
        has_info = any(k in chunk.content.lower() for k in ["jit", "october", "gil", "3.13", "release"])
        if has_info:
            relevant_chunks += 1
            
        print(f"  [Chunk {i}] Tokens: {tokens} | Relevance Score: {chunk.relevance_score:.2f} | Has Key Info: {has_info}")
        if i < 1:
            print(f"   Sample: {chunk.content[:100]}...")

    print(f"Total Input Tokens to LLM: ~{total_tokens}")
    print(f"Relevant Chunks Found: {relevant_chunks}/{len(output.evidence)}")
    return total_tokens, relevant_chunks, duration

async def main():
    query = "What are the new features in Python 3.13?"
    
    # 1. Fast Mode (Snippets / Raw Search)
    # Uses Bi-Encoder but relies heavily on search engine snippets if reader fails or is fast
    print(">>> 1. FAST Mode (Bi-Encoder / Snippets)")
    cfg_fast = LinkerConfig(mode="fast")
    # Force snippet fallback to simulate "Search API only" behavior for comparison?
    # Actually Fast mode uses Trafilatura but with timeout 3s.
    await analyze_strategy("Fast (Bi-Encoder)", cfg_fast, query)

    # 2. Deep Mode (FlashRanker)
    print("\n>>> 2. DEEP Mode (FlashRanker / Cross-Encoder)")
    cfg_deep = LinkerConfig(mode="deep")
    # Ensure CPU for consistent testing if GPU not available
    cfg_deep.device = "auto"
    await analyze_strategy("Deep (FlashRanker)", cfg_deep, query)

if __name__ == "__main__":
    asyncio.run(main())
