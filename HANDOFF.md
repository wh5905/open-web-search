# 🚀 Project Handoff: Open-Web-Search (v0.7.0)

> **To the Next Agent**: This project was formerly `linker-search`. We just completed a massive rebranding to `open-web-search`. Read this to sync your context immediately.

## 1. Project Identity 🌐
*   **Name**: `open-web-search` (PyPI compliant)
*   **Tagline**: "The Standard Open Source Alternative to Tavily"
*   **Core Value**: Local, Privacy-First, Deep Research (Recursive).
*   **Current Version**: `0.7.0` (Ready for PyPI)

## 2. Status Update (2026-02-02) ✅
*   **Refactor Complete**: Directory renamed `linker_search` -> `open_web_search`.
*   **Imports Updated**: All 60+ files updated. `import open_web_search` verified working.
*   **Docs Updated**: `README.md` and `pyproject.toml` reflect the new identity.
*   **Testing**: Ran `verify_rename.py` (Passed).

## 3. Immediate Next Steps (Priorities) 📋
1.  **Deploy v0.7.0**:
    *   Run `python -m build`
    *   Run `twine upload dist/*`
2.  **Start v0.8.0 (The Intelligence Kick)**:
    *   **FlashRanker**: Implement SLM-based Reranking (See `adr_004_flashranker_slm.md`).
    *   **Visuals**: Add Knowledge Graphs (`networkx`).

## 4. Key Files to Read 📂
*   `task.md`: The detailed checklist. We are at **Phase 20**.
*   `adr_004_flashranker_slm.md`: Design doc for the next feature.
*   `README.md`: The public face of the project.

## 5. Technical Context ⚙️
*   **Engine**: SearXNG (Docker) running on **port 8787** (Mapped from 8080).
*   **Server**: FastAPI running on **port 7800**.
*   **Deep Mode**: default behavior.

---
**Summary for User**: "We are ready to ship v0.7.0 as Open-Web-Search. Next step is PyPI upload and starting FlashRanker."
