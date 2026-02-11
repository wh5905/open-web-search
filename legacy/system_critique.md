# Open-Web-Search System Critique & Gap Analysis

Based on the `detailed_evaluation_report.md` for the query *"Mamba architecture vs Transformer architecture 2024"*, we have identified critical structural weaknesses in the current v0.3 architecture.

While the system *mechanically* works (Plan -> Search -> Answer), it fails to deliver *comprehensive* research due to specific bottlenecks in diversity and context management.

## 1. Planning Layer: "The Synonym Trap"
**Observation**: The Planner generated 3 queries that were essentially synonyms:
1. `...performance comparison 2024`
2. `...recent benchmarks...`
3. `...key differences in speed...`

**Critique**: This provides **Redundancy**, not **Coverage**. It did not explicitly ask for:
- "Mamba hardware requirements vs Transformer (GPU memory)"
- "Mamba training stability vs Transformer"
- "Mamba accuracy on standard benchmarks (MMLU, GSM8k)"

**Impact**: The search results were homogeneous. If the first query misses a specific angle (e.g., hardware), the others will likely miss it too.

## 2. Retrieval Layer: "The PDF Blindspot"
**Observation**:
- Result #2 ([2403.18276] RankMamba...) yielded only **3,352 characters**.
- Result #5 ([2503.24067] TransMamba...) yielded **39,817 characters**.

**Critique**:
- The system successfully scraped the **Abstract Page** of Result #2 (Arxiv) but failed to navigate to or parse the **Full PDF**.
- Result #5 likely had an HTML formatted version available (Arxiv HTML), which is why it was captured fully.
- Serious research requires reading PDFs, which constitute 80% of high-quality technical knowledge.

**Impact**: The system ignores high-quality dense papers if they are in PDF format, favoring blog posts or HTML-native papers.

## 3. Reading Layer: "The Anti-Bot Wall"
**Observation**:
- Result #3 (Reddit) -> **Failed (403)**
- Result #4 (ScienceDirect) -> **Failed (403)**

**Critique**:
- `PlaywrightReader` is currently detectable or lacking proper headers for strict sites.
- Losing Reddit (community consensus) and ScienceDirect (academic source) significantly reduces the "Real World vs Academic" balance of the answer.

## 4. Refinement Layer: "The Rabbit Hole Effect" (CRITICAL)
**Observation**:
- **All Top 10 Evidence Chunks** came from a **SINGLE Source** (Result #5: `arxiv.org/html/2503.24067v1`).
- The Re-ranker scored chunks from this file as 0.94~0.76.

**Critique**:
- Because Result #5 was the only "Long, Clean, Relevant" text found (due to #2 being just an abstract and others being blogs), it **dominated the context window**.
- `HybridRefiner` does not enforce **Source Diversity**. It simply picks the "best chunks globally". If one document is excellent, it fills the entire answer context.

**Impact**: The Final Answer is heavily biased. It talks extensively about "TransMamba" (the topic of Source #5) rather than a balanced view of the entire field. The answer is essentially a summary of *one paper* disguised as a literature review.

## 5. Cognitive Layer: "Tunnel Vision"
**Observation**:
- The answer cites `[1]`, `[2]`, `[5]` etc., but if you look closely, they all point back to the context provided by that single TransMamba paper.

**Critique**:
- The LLM did its job correctly (synthesizing provided evidence), but because the evidence was biased (The Rabbit Hole), the answer became a "TransMamba Advertisement".

---

## Strategic Recommendations for v0.4

### 1. Fix Planning (Aspect-Based Decomposition)
- **Action**: Force the Planner to generate **orthogonal** queries (e.g., "Hardware", "Accuracy", "Training Speed") rather than just rephrasing.

### 2. Implement "MMR" (Maximal Marginal Relevance) in Refinement
- **Action**: When selecting top K chunks, penalize chunks from the *same document* if that document is already well-represented. Ensure at least 3-4 *different* sources constitute the final context.

### 3. PDF Parsing Capability
- **Action**: Detect `.pdf` URLs or Arxiv Abstract pages, and specifically target the PDF binary using a library like `pdfplumber` or `marker-pdf`.

### 4. Browser Steering / Evasion
- **Action**: Upgrade `PlaywrightReader` to use `stealth-plugin` or better User-Agent rotation to bypass 403s on Reddit/ScienceDirect.
