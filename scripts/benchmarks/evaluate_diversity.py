import asyncio
import os
import sys
import json
from collections import Counter
from urllib.parse import urlparse
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from open_web_search.core.loop import DeepResearchLoop
from open_web_search.config import LinkerConfig

load_dotenv(".env")

QUERIES = [
    # {
    #     "type": "Concept",
    #     "query": "Explain 'Agentic Patterns' in AI software engineering and how they differ from standard RAG"
    # },
    # {
    #     "type": "News/Technical",
    #     "query": "New features and breaking changes in TypeScript 5.8 beta release notes"
    # },
    # {
    #     "type": "Community/BestPractice",
    #     "query": "Best practices for error handling in Rust reddit discussions 2024"
    # },
    {
        "type": "Opinion/Debate",
        "query": "Is Vercel pricing model too expensive for startups?HN vs Reddit opinions"
    }
]

async def run_evaluation():
    config = LinkerConfig(
        engine_provider="searxng",
        engine_base_url="http://127.0.0.1:8080",
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_model=os.getenv("LLM_MODEL"),
        mode="deep"
    )
    
    agent = DeepResearchLoop(config)
    report_lines = ["# Linker-Search Diversity & Source Analysis Report\n"]
    
    global_domains = Counter()
    global_types = Counter() # pdf, html, blocked
    
    for item in QUERIES:
        q_type = item["type"]
        q_text = item["query"]
        
        print(f"\n[Evaluator] Running: {q_type} - {q_text[:30]}...")
        
        # Capture Output
        output = await agent.run(q_text)
        
        report_lines.append(f"## Type: {q_type}")
        report_lines.append(f"**Query**: {q_text}")
        
        # 1. Planner Analysis
        report_lines.append("### 1. Planner Logic")
        if output.rewritten_queries:
            for i, sq in enumerate(output.rewritten_queries):
                report_lines.append(f"- `{sq}`")
        else:
            report_lines.append("- (No decomposition)")
            
        # 2. Source Analysis
        domains = []
        status_codes = []
        
        for p in output.pages:
            domain = urlparse(p.url).netloc.replace("www.", "")
            domains.append(domain)
            global_domains[domain] += 1
            
            if p.error:
                status = "BLOCKED/ERR"
                global_types["blocked"] += 1
            elif p.url.endswith(".pdf"):
                status = "PDF"
                global_types["pdf"] += 1
            else:
                status = "HTML"
                global_types["html"] += 1
            status_codes.append(f"{domain}({status})")

        report_lines.append("\n### 2. Sources Found")
        report_lines.append(f"- **Unique Domains**: {', '.join(set(domains))}")
        report_lines.append(f"- **Status**: {', '.join(status_codes[:5])}...")
        
        # 3. Answer Quality Snippet
        report_lines.append("\n### 3. Answer Snippet")
        report_lines.append(f"> {output.answer[:300]}...\n")
        report_lines.append("---\n")
        
    # Summary Statistics
    report_lines.append("## Global Statistics")
    report_lines.append(f"- **Top Domains**: {global_domains.most_common(5)}")
    report_lines.append(f"- **Content Types**: {dict(global_types)}")
    
    with open("diversity_analysis_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print("\n[Evaluator] Report generated: diversity_analysis_report.md")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
