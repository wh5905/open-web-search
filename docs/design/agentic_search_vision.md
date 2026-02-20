# Agentic Search Vision (2025-2026)

## 1. Market Analysis: What Users & Developers Want

Based on recent trends (LangChain, AutoGPT, BabyAGI, and 2026 architectural patterns), the demand has shifted from **"Information Retrieval"** to **"Actionable Intelligence"**.

### User Personas
1.  **The Agent Developer (Builder)**
    *   **Pain Point**: "My agent gets stuck when a website blocks it" or "My agent hallucinates when search results are garbage."
    *   **Need**: A **Robust "Legs"** for their brain. They don't want to write retry logic; they want the tool to *just work*.
    *   **Keyword**: Reliability, Observability ("Why did it fail?").

2.  **The End User (Consumer)**
    *   **Pain Point**: "I have to ask 5 times to get the right depth."
    *   **Need**: **Context-Awareness**. The system should know that "Apple price" needs a stock chart (Fast), but "Apple vs Samsung strategy" needs a report (Deep).
    *   **Keyword**: Latency-Quality Tradeoff.

## 2. Core Philosophy for Linker-Search

We are building the **Operational Layer** (The "Body"), not the Strategic Layer (The "Brain").

*   **Brain's Job (Agent/LLM)**: "I need to find X to solve Y." (Strategy)
*   **Body's Job (Linker-Search)**: "I will try HTTP, if that fails, I'll use a Headless Browser, and if that fails, I'll try a cache." (Tactics)

## 3. Revised Adaptive Design: "The Unbreakable Tool"

Instead of a "Cognitive Router" (which tries to be the Brain), we focus on **"Self-Correction & Resilience"**.

### Feature 1: The "Hedgehog" Protocol (Resilience)
*If one path is blocked, try another immediately without bothering the user.*

*   **Scenario**: User asks for "Bloomberg article".
*   **Action**:
    1.  Try `trafilatura` (HTTP) -> Failed (403 Forbidden).
    2.  **Auto-Switch**: Spawn `playwright` (Headless) -> Success.
    3.  **Result**: Return content with a note: "Accessed via Browser".

### Feature 2: "Smart Snippets" (Context)
*Don't just dump text. Pre-process it.*

*   **Scenario**: User asks "Python 3.12 release date".
*   **Action**:
    *   FlashRanker identifies the *exact sentence*.
    *   Return: `{ "answer": "Oct 2, 2023", "source": "...", "confidence": 0.99 }`
    *   This saves the Agent from reading 5000 tokens.

### Feature 3: "Transparent Telemetry" (Observability)
*Let the Agent know what happened.*

*   Return a structured trace:
    ```json
    {
      "status": "success",
      "method": "browser_fallback",
      "attempts": 2,
      "cost": "high_compute"
    }
    ```
    This allows the Agent to learn ("Ah, this site is heavy, I'll avoid it next time").

## 4. Trade-off Analysis: Is it worth it?

The "Unbreakable" promise comes with costs. We must be transparent about these.

### The Cost of Resilience
| Metric | ⚡ HTTP Mode (Trafilatura) | 🐢 Browser Mode (Playwright) | Impact |
| :--- | :--- | :--- | :--- |
| **Latency** | ~0.5s - 1.5s | ~3.0s - 8.0s | **5x Slower**. Critical for real-time chat. |
| **Compute** | Minimal CPU | High CPU (Chromium instance) | Expensive on small VPS/Lamda. |
| **Stability** | Fails on JS/Anti-bot | Works on 95% of sites | Essential for "Deep Research". |

### Strategic Mitigation
To balance this, we will implement **Lazy Escalation**:
1.  **Default to Fast**: Always try HTTP first. 80% of sites work fine.
2.  **Explicit Opt-out**: Users can set `safe_mode=True` to disable browser fallback if speed is critical.
3.  **Singleton Browser**: Reuse the browser instance to cut startup time (from 3s to 0.5s).

## 5. Conclusion
We should **NOT** build a complex LLM Router inside Linker-Search.
We **SHOULD** build robust **Self-Correction** and **Observability** features. This makes us the best "Tool" for any "Brain".

