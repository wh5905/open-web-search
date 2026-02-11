import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Robust Project Root Detection
# Current location: scripts/benchmarks/evaluate_search_quality.py
# Root is 2 levels up.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Fallback: If run from root (before move), use SCRIPT_DIR
if (SCRIPT_DIR / "open_web_search").exists():
    PROJECT_ROOT = SCRIPT_DIR

# 1. Setup Python Path (so 'import open_web_search' works)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from open_web_search.core.loop import DeepResearchLoop
from open_web_search.config import LinkerConfig
from open_web_search.schemas.results import PipelineOutput

# 2. Load Env from Root
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"Warning: .env not found at {env_path}")

def generate_report(output: PipelineOutput, filename: str = None):
    if not filename:
        # Default: docs/reports/detailed_evaluation_report.md
        report_dir = PROJECT_ROOT / "docs" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        filename = report_dir / "detailed_evaluation_report.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Open-Web-Search Transparent Evaluation Report\n\n")
        f.write(f"**Query**: {output.query}\n")
        f.write(f"**Generated At**: {output.pages[0].retrieved_at if output.pages else 'N/A'}\n\n")
        
        # 1. Planning Layer
        f.write("## 1. Planning Layer (Query Decomposition)\n")
        f.write("The LLM decomposed the user query into the following search queries:\n")
        if output.rewritten_queries:
            for q in output.rewritten_queries:
                f.write(f"- `{q}`\n")
        else:
            f.write("- *(No rewriting triggered, used original query)*\n")
        f.write("\n")
        
        # 2. Retrieval Layer
        f.write("## 2. Retrieval Layer (Raw Search Results)\n")
        f.write("The Search Engine (SearXNG) returned the following URLs:\n")
        for i, res in enumerate(output.results):
            f.write(f"### {i+1}. [{res.title}]({res.url})\n")
            f.write(f"- **Snippet**: {res.snippet}\n")
            f.write(f"- **Engine**: {res.source_engine}\n")
        f.write("\n")
        
        # 3. Reading Layer (Scraping)
        f.write("## 3. Reading Layer (Content Extraction)\n")
        f.write("The Reader visited the URLs and extracted full text:\n")
        for i, page in enumerate(output.pages):
            content_len = len(page.text_plain) if page.text_plain else 0
            status = "Success" if page.text_plain else f"Failed ({page.error})"
            f.write(f"- **[{i+1}] {page.url}**\n")
            f.write(f"  - Status: {status}\n")
            f.write(f"  - Extracted Characters: {content_len}\n")
        f.write("\n")
        
        # 4. Refinement Layer (Evidence Selection)
        f.write("## 4. Refinement Layer (RAG Evidence)\n")
        f.write("The Re-ranker selected the following chunks as 'High Quality Evidence' for the LLM:\n")
        for i, chunk in enumerate(output.evidence):
            f.write(f"### Chunk {i+1} (Score: {chunk.relevance_score:.2f})\n")
            f.write(f"> {chunk.content[:300]}...\n\n")
            f.write(f"*Source: {chunk.url}*\n")
        f.write("\n")
        
        # 5. Cognitive Layer (Synthesis)
        f.write("## 5. Cognitive Layer (Final Answer)\n")
        f.write("The LLM synthesized this answer based **ONLY** on the evidence above:\n\n")
        f.write("```\n")
        f.write(output.answer)
        f.write("\n```\n")

async def main():
    # Setup
    config = LinkerConfig(
        engine_provider="searxng",
        engine_base_url="http://127.0.0.1:8080",
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_model=os.getenv("LLM_MODEL"),
        mode="deep"
    )
    
    agent = DeepResearchLoop(config)
    
    # Query designed to test v0.4 upgrades (Aspect Planning, PDF reading, MMR Diversity)
    query = "DeepSeek-V3 architecture innovations (MLA, MoE) and training cost efficiency compared to Llama 3.1"
    print(f"Running evaluation for: {query}")
    
    output = await agent.run(query)
    
    # Generate Report
    generate_report(output)
    print("Report generated: detailed_evaluation_report.md")

if __name__ == "__main__":
    asyncio.run(main())
