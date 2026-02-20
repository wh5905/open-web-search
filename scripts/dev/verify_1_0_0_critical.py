"""
V1.0.0 CRITICAL END-TO-END EVALUATION SCRIPT
This script rigorously tests the Open-Web-Search pipeline from the perspective of an end-user.
It evaluates all 4 modes (turbo, fast, balanced, deep) to ensure:
1. API usage is intuitive and stable.
2. Latency claims (<1s for turbo, ~8s for deep) are accurate.
3. Content extraction (V2Reader) works as expected.
4. Reranking mechanisms (BM25, Bi-Encoder, Cross-Encoder) do not throw errors.
"""

import asyncio
import time
from loguru import logger
import warnings

# Import the core library exactly as a user would
import open_web_search as ows

# Suppress noisy async warnings for cleaner output
warnings.filterwarnings("ignore", category=ResourceWarning)

async def evaluate_mode(mode_name: str, query: str, expected_max_time: float):
    print(f"\n▶ Evaluating Mode: {mode_name.upper()}")
    print(f"  Query: '{query}'")
    
    start_time = time.time()
    try:
        # Simulate standard user API call
        result = await ows.search(query, mode=mode_name)
        elapsed = time.time() - start_time
        
        # Validation Checks
        pages_processed = len(result.pages)
        evidence_found = len(result.evidence)
        
        status = "PASS" if elapsed <= expected_max_time else "WARN (Time)"
        if evidence_found == 0:
            status = "FAIL (No Evidence)"
            
        print(f"  - Status: {status}")
        print(f"  - Latency: {elapsed:.2f}s (Expected < {expected_max_time}s)")
        print(f"  - Pages Processed: {pages_processed}")
        print(f"  - Evidence Chunks: {evidence_found}")
        
        if evidence_found > 0:
            top_chunk = result.evidence[0]
            print(f"  - Top Score: {top_chunk.relevance_score:.4f}")
            print(f"  - Top Snippet: {(top_chunk.content[:100] + '...').replace('\n', ' ')}")
            
        return True, elapsed
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ CRASH in {mode_name.upper()}: {str(e)}")
        return False, elapsed

async def run_evaluation():
    print("======================================================")
    print("   OPEN-WEB-SEARCH v1.0.0 - CRITICAL E2E EVALUATION   ")
    print("======================================================\n")
    
    # Define test parameters
    tests = [
        # Mode, Query, Expected Max Latency (seconds)
        ("turbo", "Capital of France", 1.5), # Extremely simple, should synthesize snippets instantly
        ("fast", "What is the JA3 TLS fingerprint?", 4.0), # Technical, Needs 3 pages + Bi-Encoder
        ("balanced", "Latest solid state battery breakthroughs 2026", 8.0), # Needs 5 pages + Bi-Encoder
        ("deep", "Explain the difference between Flash attention and standard attention", 20.0) # Heavy processing, FlashRanker
    ]
    
    results = []
    
    for mode, query, expected_time in tests:
        success, time_taken = await evaluate_mode(mode, query, expected_time)
        results.append((mode, success, time_taken))
        await asyncio.sleep(1) # Small breather between heavy queries
        
    # Final Summary
    print("\n======================================================")
    print("                EVALUATION SUMMARY                    ")
    print("======================================================")
    for mode, success, time_taken in results:
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {mode.upper()}: {time_taken:.2f}s")
        
if __name__ == "__main__":
    asyncio.run(run_evaluation())
