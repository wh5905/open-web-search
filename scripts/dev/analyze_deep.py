import asyncio
import time
from open_web_search.config import LinkerConfig
from open_web_search.core.pipeline import AsyncPipeline

def count_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)

async def analyze_deep():
    print("\n>>> 2. DEEP Mode (FlashRanker / Cross-Encoder)")
    cfg_deep = LinkerConfig(mode="deep")
    cfg_deep.device = "auto"
    
    query = "What are the new features in Python 3.13?"
    
    pipeline = AsyncPipeline(cfg_deep)
    start_time = time.time()
    try:
        output = await pipeline.run(query)
    except Exception as e:
        print(f"Error: {e}")
        return
        
    duration = time.time() - start_time
    
    total_tokens = 0
    relevant_chunks = 0
    
    print(f"Time: {duration:.2f}s")
    print(f"Evidence Count: {len(output.evidence)}")
    
    for i, chunk in enumerate(output.evidence):
        tokens = count_tokens(chunk.content)
        total_tokens += tokens
        has_info = any(k in chunk.content.lower() for k in ["jit", "october", "gil", "3.13", "release"])
        if has_info:
            relevant_chunks += 1
            
        print(f"  [Chunk {i}] Tokens: {tokens} | Relevance Score: {chunk.relevance_score:.2f} | Has Key Info: {has_info}")
        if i < 1:
            print(f"   Sample: {chunk.content[:100]}...")

    print(f"Total Input Tokens to LLM: ~{total_tokens}")
    print(f"Relevant Chunks Found: {relevant_chunks}/{len(output.evidence)}")

if __name__ == "__main__":
    asyncio.run(analyze_deep())
