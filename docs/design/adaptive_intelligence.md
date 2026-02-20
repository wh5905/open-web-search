# Adaptive Intelligence (v0.9.5+)

## 1. Vision
Transform `open-web-search` from a **Passive Tool** (follows config) into an **Active Agent** (optimizes config).

**Core Philosophy**: "Maximum Result, Minimum Commpute."

---

## 2. Key Components

### 2.1. The Cognitive Router (Pre-Search)
Before executing any search, a lightweight "Router" analyzes the user query to select the optimal pipeline strategy.

*   **Input**: Query string + User Constraints
*   **Model**: Zero-Shot Classifier (e.g., `facebook/bart-large-mnli`) or SLM (Quantized Llama-3-8B).
*   **Output**: `LinkerConfig`

| Query Type | Example | Router Decision | Reason |
| :--- | :--- | :--- | :--- |
| **Navigational** | "Twitter login", "Youtube" | `mode=fast`, `reranker=fast` | Only need top 1 link. |
| **Factual** | "Population of Seoul 2026" | `mode=fast`, `reranker=fast` | Simple fact lookup. |
| **Analytical** | "Compare architectures of DeepSeek vs GPT-4" | `mode=balanced`, `reranker=flash` | Needs precision to distinguish models. |
| **Research** | "Impact of quantum computing on crypto regulation" | `mode=deep`, `reader=browser` | Complex, obscure sources likely needed. |

### 2.2. Dynamic Escalation (Runtime)
The system monitors its own performance during the `DeepResearchLoop`. If heuristics fail, it "escalates" capabilities.

*   **Trigger**:
    *   `len(evidence) == 0` after Round 1.
    *   `blocked_domains` count > 3.
*   **Escalation Actions**:
    1.  **Browser Escalation**: Switch `reader` from `trafilatura` (HTTP) to `playwright` (Headless).
    2.  **Keyword Expansion**: "Unblock" strict keywords or try cross-lingual search.
    3.  **Source Expansion**: If Google blocked us, switch to DuckDuckGo or SearXNG instances.

### 2.3. The "Good Enough" Stopper
Instead of running for fixed iterations (e.g., `max_depth=3`), the agent calculates an "Information Gain" score.
*   If `Information Gain` plateaus (Round 3 adds nothing new), stop early to save time/cost.

---

## 3. Technology Stack (2026 Era)

*   **SLM (Small Language Models)**:
    *   Use on-device models (e.g., `Microsoft Phi-4` or `Google Gemma 3-2B`) for routing decisions.
    *   Low latency (<50ms), Privacy-preserving.
*   **JSON Mode**:
    *   Strict JSON output for all internal decisions (Router, Planner).
*   **MCTS (Monte Carlo Tree Search)**:
    *   (Future) For complex multi-step research, simulate potential search paths and choose the most promising one (AlphaGo style research).

---

## 4. User Experience (UX)

*   **Transparent Reasoning**: The agent should explain *why* it chose a mode.
    > "I detected this is a complex financial topic. I'm switching to **Deep Mode** with **FlashRanker** for precision."
*   **Interactive Steering**:
    > "I found conflicting data on X. Should I dig deeper into that specific conflict?"

## 5. Implementation Roadmap

1.  **Phase 1 (Heuristic Router)**: Regex/Keyword based routing (Cheap, Fast).
2.  **Phase 2 (Escalation Loop)**: Implement the "Retry with Browser" logic in `DeepResearchLoop`.
3.  **Phase 3 (SLM Integration)**: Optional dependency to load a local LLM for smart routing.
