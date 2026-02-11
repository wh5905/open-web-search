import os
import sys

# Simulate installation by adding root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# from langchain.agents import AgentExecutor, create_json_chat_agent
# from langchain_community.chat_models import ChatOpenAI
# from langchain_core.tools import Tool
from dotenv import load_dotenv

# Use our library!
from open_web_search.integrations.langchain import LinkerSearchTool

# Load Env
# Load Env
env_path = os.path.join(os.path.dirname(__file__), "../../.env")
load_dotenv(env_path)

def main():
    import sys
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    print("=== PROJECT ALPHA: The Trend Spotter ===")
    print("Scenario: Verifying LinkerSearchTool as a LangChain Tool.")
    
    # 2. Setup Tool
    try:
        search_tool = LinkerSearchTool(
             engine_provider="searxng",
             engine_base_url="http://127.0.0.1:8080",
             search_depth="advanced",
             # CRITICAL: Pass LLM config so Planner/Synthesizer works!
             llm_base_url=os.getenv("LLM_BASE_URL"),
             llm_model=os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        )
        print("LinkerSearchTool initialized successfully (with LLM).")
    except Exception as e:
        print(f"Tool init failed: {e}")
        return

    # 4. Run Mission
    import time
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    query = f"Key breakthroughs and comparisons of Agentic AI frameworks (LangGraph, CrewAI, AutoGen) in late 2024 and 2025 as of {timestamp}"
    print(f"\n[User Request] {query}")
    
    try:
        # Direct Tool Invocation (Clean Standard Usage)
        result = search_tool.invoke(query)
        print("\n[Tool Output]")
        print(result)
        
        print(f"\nSuccess! Tool works via LangChain interface.")
    except Exception as e:
        print(f"\n[Error] Tool Invocation Failed: {e}")

if __name__ == "__main__":
    main()
