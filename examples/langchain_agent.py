import os
import sys
import asyncio
from typing import Dict, Any

from open_web_search.config import LinkerConfig
from open_web_search.integrations.langchain import LinkerSearchTool, LinkerSearchWrapper

# This script demonstrates that LinkerSearchTool is a valid LangChain tool
# and can be invoked just like any other tool (e.g. TavilySearchResults).

async def main():
    print("Initializing Linker-Search Tool...")
    
    # 1. Configuration
    config = LinkerConfig(
        mode="balanced", 
        observability_level="full"
    )
    
    # 2. Tool Instantiation
    # We create the wrapper explicitly to pass config
    wrapper = LinkerSearchWrapper(config=config)
    tool = LinkerSearchTool(wrapper=wrapper)

    print(f"Tool Name: {tool.name}")           # Should be 'open_web_search'
    print(f"Tool Args Schema: {tool.args_schema.schema_json()}")
    
    # 3. Simulation: Agent calls the tool
    query = "current CEO of OpenAI"
    print(f"\n[Agent Simulation] Invoking tool with query: '{query}'")
    
    # Tools are usually invoked via .invoke() or .ainvoke() in LangChain
    try:
        # Sync invoke
        # result = tool.invoke({"query": query})
        
        # Async invoke
        result = await tool.ainvoke({"query": query})
        
        print("\n[Tool Output]")
        print("--------------------------------------------------")
        print(result[:500] + ("..." if len(result) > 500 else ""))
        print("--------------------------------------------------")
        
    except Exception as e:
        print(f"Tool invocation failed: {e}")

    # 4. LangGraph/LangChain compatibility note
    print("\n[Integration Note]")
    print("To use with LangGraph:")
    print("  from langgraph.prebuilt import create_react_agent")
    print("  from langchain_openai import ChatOpenAI")
    print("  tools = [tool]")
    print("  model = ChatOpenAI(model='gpt-4o')")
    print("  agent = create_react_agent(model, tools)")

if __name__ == "__main__":
    asyncio.run(main())
