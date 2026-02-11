# Universality & Blocking Analysis Report

## 1. The "Anti-Bot" Landscape
Our probe (`debug_site_access.py`) revealed two distinct tiers of protection blocking our "Community" queries:

### Tier 1: JavaScript Challenges (e.g., Medium, Cloudflare)
- **Mechanism**: Checks for valid browser environment (Canvas, AudioContext, Navigator).
- **Status**: **PASSED**.
- **Evidence**: `https://medium.com` returned **200 OK** with Playwright Stealth.
- **Implication**: `Open-Web-Search` can successfully read most blogs and news sites protected by standard Cloudflare.

### Tier 2: Behavioral & Fingerprinting (e.g., Reddit)
- **Mechanism**: Likely checks for:
    - TLS Fingerprint (JA3)
    - Headless Browser constraints (User-Agent hints)
    - Data Center IP ranges (though less likely locally)
- **Status**: **FAILED**.
- **Evidence**: `https://www.reddit.com` returned **403 Forbidden** even with Stealth.
- **Implication**: "Community" queries depending on Reddit will consistently fail unless we adapt.

---

## 2. Policy-Resilient Strategies (Proposed)

To achieve true "Universality" without engaging in an endless cat-and-mouse game, we propose the following architectural shifts:

### Strategy A: The "Snippet Fallback" (Immediate)
If the **Reader** fails (`403/429`):
- **Don't discard the result.**
- **Fallback**: Use the **Search Engine Snippet** (often 200-300 chars) as the "content".
- **Why**: SearXNG effectively "proxies" the snippet. It's better to have a summary than nothing.

### Strategy B: "Frontend Rotation" (Medium Term)
Many blocked sites have "Lite" versions or alternative frontends that are bot-friendly:
- `www.reddit.com` -> `old.reddit.com` (Softer blocking)
- `twitter.com` -> `nitter.net` (Mirror)
- **Action**: Implement a `UrlRewriter` middleware in the pipeline.

### Strategy C: "API Opportunism" (Long Term)
Detect sites with public JSON endpoints:
- Check `reddit.com/.../.json`
- **Action**: A specialized `RedditReader` that hits the API instead of HTML.

---

## 3. Evaluation of Current "Generality"
| Query Type | Adaptability | Source Coverage | Verdict |
| :--- | :--- | :--- | :--- |
| **Concept** | High | Excellent (Docs, Blogs) | ✅ **Ready** |
| **Technical** | High | Good (Official Docs, Arxiv) | ✅ **Ready** |
| **News** | High | Passable (News sites) | ✅ **Ready** |
| **Community** | **Low** | **Poor (Reddit blocked)** | ⚠️ **Needs Rewrite** |

**Recommendation**:
Proceed with **Strategy A (Snippet Fallback)** immediately to prevent "No evidence found" errors when Reddit blocks occur.
