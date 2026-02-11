import asyncio
import os
from open_web_search.core.planner import Planner
from open_web_search.config import LinkerConfig
from dotenv import load_dotenv

load_dotenv(".env")

async def test():
    config = LinkerConfig(
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_model=os.getenv("LLM_MODEL")
    )
    planner = Planner(config)
    
    query = "What are the most controversial opinions on Vercel pricing from Reddit and Hacker News in 2024?"
    context = {"blocked_domains": ["reddit.com", "news.ycombinator.com"]}
    
    print(f"Query: {query}")
    print(f"Context: {context}")
    print("-" * 20)
    
    queries = await planner.plan(query, context)
    
    print("-" * 20)
    print("Generated Queries:")
    for q in queries:
        print(f"- {q}")

if __name__ == "__main__":
    asyncio.run(test())
