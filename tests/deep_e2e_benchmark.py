import asyncio
import os
import json
from open_web_search.core.loop import DeepResearchLoop
from open_web_search.config import LinkerConfig
from dotenv import load_dotenv

load_dotenv(".env")

# Stress Test Scenarios defined in deep_test_plan.md
SCENARIOS = [
    {
        "id": "HALLUCINATION",
        "description": "False Premise Check",
        "query": "What are the new syntax features introduced in Python 4.0 release?",
        "intent": "Verify if agent corrects the user about Python 4.0 not existing."
    },
    {
        "id": "CONFLICT",
        "description": "Consensus Conflict",
        "query": "Is intermittent fasting effective for building muscle in women? Scientific consensus 2024.",
        "intent": "Check handling of contradictory medical evidence."
    },
    {
        "id": "TEMPORAL",
        "description": "Temporal Confusion",
        "query": "Who won the Super Bowl 2025 and what was the score?",
        "intent": "Test date filtering. Super Bowl 2025 hasn't happened as of early 2024 knowledge cutoff (or has it? It's Feb 2025 in reality context... wait, user time is 2026! So it HAS happened. Let's see if it finds 2025 results or 2024.)"
    },
    {
        "id": "CROSS_LINGUAL",
        "description": "Language Wall",
        "query": "일본의 '지진해일 대피 타워' 설계 기준과 최신 사례",
        "intent": "Test Korean query -> Japanese/English source retrieval."
    },
    {
        "id": "UNBLOCKING",
        "description": "Cognitive Maze",
        "query": "Latest verified leaks for GTA VI release date and map features from Reddit and Twitter.",
        "intent": "Stress test the Cognitive Unblocking logic against social media blocks."
    }
]

async def run_benchmark():
    config = LinkerConfig(
        engine_provider="searxng",
        engine_base_url="http://127.0.0.1:8080", 
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_model=os.getenv("LLM_MODEL"),
        enable_snippet_fallback=True, 
        max_evidence=5
    )
    
    agent = DeepResearchLoop(config)
    
    results = []
    
    print("Starting Deep E2E Stress Test Benchmark...")
    print("="*60)
    
    for i, scenario in enumerate(SCENARIOS):
        if i > 0:
            print("Cooling down (10s)...")
            await asyncio.sleep(10)

        print(f"\nRunning Scenario: {scenario['id']} ({scenario['description']})")
        print(f"Query: {scenario['query']}")
        
        try:
            output = await agent.run(scenario['query'])
            
            # Analyze Output
            result = {
                "id": scenario['id'],
                "query": scenario['query'],
                "answer": output.answer,
                "evidence_count": len(output.evidence),
                "steps": len(output.trace.keys()) if 'steps' not in output.trace else 1, # Heuristic
                "blocked_domains": output.blocked_domains,
                "rewritten_queries": output.rewritten_queries
            }
            results.append(result)
            
            print(f"-> Evidence: {len(output.evidence)} chunks")
            print(f"-> Blocked: {output.blocked_domains}")
            print(f"-> Answer Preview: {output.answer[:200]}...")
            
        except Exception as e:
            print(f"-> FAILED: {e}")
            results.append({"id": scenario['id'], "error": str(e)})

    # Generate Report
    with open("deep_stress_test_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n" + "="*60)
    print("Benchmark Complete. Results saved to deep_stress_test_report.json")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
