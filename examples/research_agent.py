import asyncio
import os
from dotenv import load_dotenv
from open_web_search.core.loop import DeepResearchLoop
from open_web_search.config import LinkerConfig

# Load env including LLM_BASE_URL
load_dotenv(".env")

async def main():
    print("Initializing Linker-Search Research Agent (Deep Loop)...")
    
    llm_url = os.getenv("LLM_BASE_URL")
    llm_model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    print(f"Using Local LLM at: {llm_url} (Model: {llm_model})")
    
    config = LinkerConfig(
        mode="deep",
        llm_base_url=llm_url,
        llm_model=llm_model, 
        observability_level="full",
        engine_provider="searxng",
        engine_base_url="http://127.0.0.1:8080",
        search_language="ko-KR",
        reader_type="browser"
    )
    
    # Initialize Deep Research Loop
    agent = DeepResearchLoop(config=config)
    
    # A complex query
    query = "Python 3.12 vs Python 3.11 주요 변경점"
    print(f"\n[User Query] {query}")
    print("-" * 50)
    
    # Run the loop
    output = await agent.run(query)
    
    # Save trace to file to avoid console encoding issues
    report_path = "evaluation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Research Report\n\n")
        f.write(f"**Query**: {output.query}\n\n")
        
        f.write("## 1. Planner Trace\n")
        if output.rewritten_queries:
            f.write("The planner decomposed the query into:\n")
            for q in output.rewritten_queries:
                f.write(f"- `{q}`\n")
        else:
            f.write("No decomposition performed.\n")
            
        f.write(f"\n## 2. Search & Refine Trace\n")
        f.write(f"- **Raw Results**: {len(output.results)}\n")
        f.write(f"- **Processed Pages**: {len(output.pages)}\n")
        
        for p in output.pages:
            f.write(f"  - {p.url} (Len: {len(p.text_plain or '')})\n")
            
        f.write(f"- **Evidence Chunks**: {len(output.evidence)}\n\n")
        
        f.write("### Top Evidence Used\n")
        for i, ev in enumerate(output.evidence[:3]):
            f.write(f"**Source [{i+1}]**: [{ev.title}]({ev.url})\n")
            f.write(f"- Score: {ev.relevance_score:.2f}\n")
            f.write(f"- Content: {ev.content[:300]}...\n\n")
            
        f.write("## 3. Final Synthesized Answer\n")
        f.write(output.answer or "No answer generated.")
        
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
