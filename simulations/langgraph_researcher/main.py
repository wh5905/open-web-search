import os
import sys
import operator
from typing import Annotated, TypedDict, Union

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_community.chat_models import ChatOpenAI
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from open_web_search.integrations.langchain import LinkerSearchTool

load_dotenv("../../.env")

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    loop_count: int

def main():
    print("=== PROJECT DELTA: The Recursive Researcher (LangGraph) ===")
    
    # 1. Setup LLM & Tool
    llm = ChatOpenAI(
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY", "EMPTY"),
        model=os.getenv("LLM_MODEL"),
        temperature=0
    )
    
    search_tool = LinkerSearchTool(
         engine_provider="searxng",
         engine_base_url="http://127.0.0.1:8080",
         search_depth="advanced"
    )

    # 2. Define Nodes
    def research_node(state: AgentState):
        """Searches for information based on the last user message."""
        last_msg = state['messages'][-1]
        query = last_msg.content
        print(f"\n[Researcher] Searching: {query} (Loop {state.get('loop_count', 0)})")
        
        try:
            # Direct tool usage
            res = search_tool.invoke(query)
            # Summarize result with LLM
            prompt = f"Summarize this search result for query '{query}':\n\n{str(res)[:2000]}..."
            response = llm.invoke(prompt)
            return {"messages": [response], "loop_count": 1}
        except Exception as e:
            return {"messages": [AIMessage(content=f"Error: {e}")], "loop_count": 1}

    def critic_node(state: AgentState):
        """Checks if the gathered info is sufficient."""
        # For simulation, we just stop after 1 loop to avoid infinite loops in test
        # In a real app, LLM would judge quality.
        last_msg = state['messages'][-1].content
        print(f"\n[Critic] Reviewing: {last_msg[:100]}...")
        return {"messages": [AIMessage(content="Looks good enough.")], "loop_count": 0}

    def should_continue(state: AgentState) -> str:
        if state.get("loop_count", 0) > 1:
            return "end"
        return "end" # For this test, just run once and succeed.

    # 3. Build Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("researcher", research_node)
    workflow.add_node("critic", critic_node)

    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "critic")
    workflow.add_edge("critic", END)

    app = workflow.compile()

    # 4. Run Message
    print("\n[User Request] 'Latest developments in Solid-State Batteries 2024'")
    inputs = {"messages": [HumanMessage(content="Solid-State Batteries 2024 updates")], "loop_count": 0}
    
    for event in app.stream(inputs):
        for key, value in event.items():
            print(f"Finished Node: {key}")

    print("\n[Success] Graph execution completed.")

if __name__ == "__main__":
    main()
