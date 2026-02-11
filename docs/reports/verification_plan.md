# Open-Web-Search Real-World Verification Plan

## Goal
Validate `Open-Web-Search` not just as a library, but as a robust infrastructure component by seamlessly integrating it into three distinct "Client Projects" that mimic modern AI development patterns.

## Infrastructure
All simulations will use the user's existing Local LLM and Open-Web-Search services.
- **LLM**: `Qwen/Qwen3-4B-Instruct-2507` (at `http://192.168.0.10:8101/v1`)
- **Search**: Open-Web-Search API Server (at `http://127.0.0.1:8000`)
- **Library**: `linker-search` (Local install)

---

## 🏗️ Simulation Projects

### 1. Project Alpha: "The Trend Spotter" (LangChain Native)
**Persona**: A Python developer building a daily news digest bot using LangChain.
**Pattern**: Import `LinkerSearchTool` -> Bind to LC Agent -> Run.
**Hypothesis**: The tool should work as a drop-in replacement for standard search tools without detailed configuration.
**Test**:
- Create `simulations/trend_spotter/main.py`.
- Use `LangGraph` or `LangChain` AgentExecutor.
- Ask: "What are the latest AI agent frameworks released this month?"
- **Validation**: Check if it correctly cites sources and uses the local LLM via LangChain's standard interface.

### 2. Project Beta: "The Polyglot Dashboard" (Infrastructure Consumer)
**Persona**: A Node.js/Next.js developer (Simulated) who treats Open-Web-Search as an external API.
**Pattern**: Pure HTTP Requests using `httpx` (simulating `fetch`) to the local API Server (`python -m open_web_search.cli serve`).
**Hypothesis**: The API Server must handle concurrent requests and strictly adhere to the Tavily JSON schema.
**Test**:
- Create `simulations/polyglot_client/app.py` (Mocking a dashboard backend).
- Execute 5 concurrent search requests (simulating multi-user traffic).
- **Validation**: Confirm 200 OK responses, correct JSON structure, and server stability under load.

### 3. Project Gamma: "The Deep Thesis Writer" (Autonomous Walker)
**Persona**: A Research Scientist consuming the core library for deep work.
**Pattern**: Direct usage of `DeepResearchLoop` with `NeuralCrawler` enabled.
**Hypothesis**: The agent should navigate through technical documentation links to finding specific implementation details that a shallow search would miss.
**Test**:
- Create `simulations/thesis_writer/research.py`.
- Task: "Compare the implementation differences of 'Attention Mechanisms' in PyTorch vs TensorFlow with code examples." (Requires clicking into docs).
- **Validation**: presence of code snippets or deep links in the final report.

---

## Execution Roadmap

1.  **Environment Prep**: Create `simulations/` folder and separate virtual envs if needed (we'll share the main one for simplicity but treating them as separate apps).
2.  **Implementation**: Code each project.
3.  **Live Fire**: Run each simulation against the running `cli serve` and local LLM.
4.  **Verdict**: Report on Integration Friction, Latency, and Quality.
