# Ecosystem Verification Plan: "The Universal Engine"

## Goal
Prove that `Open-Web-Search` works seamlessly with major AI Agent frameworks: **LangGraph**, **CrewAI**, and **PydanticAI**.

## Strategy
We will use two integration patterns:
1.  **Native Integration**: Importing `LinkerSearchTool` directly (LangGraph).
2.  **Universal API (Tavily Mock)**: Pointing the framework's native `TavilyTool` to our local server (CrewAI, PydanticAI). This proves "Zero Code Change" compatibility.

---

## 🏗️ Simulation Projects

### 1. Project Delta: "The Refiner Loop" (LangGraph)
**Framework**: `langgraph`
**Concept**: A stateful graph where the agent searches, evaluates the quality, and researches again if needed.
**Integration**: Native `LinkerSearchTool`.
**Test**:
- State: `messages: list`
- Node 1: `research_node` (Uses Linker)
- Node 2: `curator_node` (LLM checks relevance)
- Edge: `should_continue`

### 2. Project Epsilon: "The Marketing Crew" (CrewAI)
**Framework**: `crewai`
**Concept**: A multi-agent team.
- Agent A (Researcher): Uses `TavilySearchTool` (but hijacked to localhost).
- Agent B (Writer): Writes a blog post based on Agent A.
**Integration**: **Universal API**. We set `TAVILY_API_BASE=http://localhost:8000/search`.
**Test**: Verify that CrewAI's internal Tavily tool talks to our server without crashing.

### 3. Project Zeta: "Structured Scout" (PydanticAI)
**Framework**: `pydantic-ai`
**Concept**: A strictly typed agent extracting data into a Pydantic model.
**Integration**: **Universal API**.
**Test**:
- Define `class StartupInfo(BaseModel)`
- Search for "Latest YC Startups" via our local engine.
- LLM extracts structured data from the search result.

---

## execution
1.  **Install Dependencies**: `langgraph crewai pydantic-ai` (Try installing; if too heavy/conflicting, mock the user code to demonstrate the pattern).
2.  **Run Simulations**: Execute against the running `cli serve`.
