from typing import Optional, Type, List, Dict, Any, Union
import asyncio
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document

from open_web_search.core.loop import DeepResearchLoop
from open_web_search.config import LinkerConfig

class LinkerSearchWrapper:
    """Wrapper to hold the research loop and run it synchronously if needed."""
    def __init__(self, config: Optional[LinkerConfig] = None):
        # UPGRADE: Use DeepResearchLoop for full Plan/Search/Refine/Synthesize cycle
        self.loop_agent = DeepResearchLoop(config)
    
    def run(self, query: str) -> Dict[str, Any]:
        """Synchronous run helper."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            raise RuntimeError("Event loop is running. Use 'run_async' instead.")
        
        return loop.run_until_complete(self.run_async(query))

    async def run_async(self, query: str) -> Dict[str, Any]:
        output = await self.loop_agent.run(query)
        # Convert Pydantic to Dict for standard tool output
        return output.model_dump()

class LinkerSearchInput(BaseModel):
    query: str = Field(description="The search query to look up.")

class LinkerSearchTool(BaseTool):
    name: str = "open_web_search"
    description: str = "A search engine optimized for LLMs. Returns comprehensive, accurate, and trusted results. Useful for when you need to answer questions about current events."
    args_schema: Type[BaseModel] = LinkerSearchInput
    
    # Config Fields allow users to pass them in init
    engine_provider: str = "ddg"
    engine_base_url: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: str = "gpt-3.5-turbo"
    llm_api_key: str = "EMPTY"
    search_depth: str = "fast"
    
    wrapper: Optional[LinkerSearchWrapper] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Verify wrapper exists or create it from config options
        if not self.wrapper:
            config = LinkerConfig(
                engine_provider=self.engine_provider,
                engine_base_url=self.engine_base_url,
                llm_base_url=self.llm_base_url,
                llm_model=self.llm_model,
                llm_api_key=self.llm_api_key,
                mode="deep" if self.search_depth == "advanced" else "fast"
            )
            self.wrapper = LinkerSearchWrapper(config)

    def _run(self, query: str) -> str:
        """Use the tool synchronously."""
        try:
            result = self.wrapper.run(query)
            
            # UPGRADE: Prefer the Synthesized Answer if available (Tavily style)
            if result.get("answer"):
                return result["answer"]
            
            # Fallback to evidence
            evidence = result.get("evidence", [])
            output_text = ""
            for e in evidence:
                output_text += f"Source: {e['url']}\nContent: {e['content']}\n\n"
            
            if not output_text:
                return "No results found."
                
            return output_text
        except Exception as e:
            return f"Search failed: {e}"

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        try:
            result = await self.wrapper.run_async(query)
            
            # UPGRADE: Prefer the Synthesized Answer if available
            if result.get("answer"):
                return result["answer"]

            evidence = result.get("evidence", [])
            output_text = ""
            for e in evidence:
                output_text += f"---\nSource: {e['url']}\nContent: {e['content']}\n"
            
            if not output_text:
                return "No results found."
                
            return output_text
        except Exception as e:
            return f"Search failed: {e}"

class LinkerSearchRetriever(BaseRetriever):
    wrapper: LinkerSearchWrapper = Field(default_factory=LinkerSearchWrapper)
    k: int = 5
    
    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        # Sync version
        try:
            result = self.wrapper.run(query)
            return self._parse_to_docs(result)
        except Exception as e:
            # Log error
            return []

    async def _aget_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        # Async version
        try:
            result = await self.wrapper.run_async(query)
            return self._parse_to_docs(result)
        except Exception as e:
            return []
            
    def _parse_to_docs(self, result: Dict[str, Any]) -> List[Document]:
        docs = []
        evidence = result.get("evidence", [])
        for e in evidence[:self.k]:
            docs.append(Document(
                page_content=e['content'],
                metadata={
                    "source": e['url'],
                    "title": e.get('title'),
                    "score": e.get('relevance_score')
                }
            ))
        return docs
