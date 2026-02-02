from abc import ABC, abstractmethod
from typing import List
from open_web_search.schemas.results import SearchResult

class BaseSearchEngine(ABC):
    @abstractmethod
    async def search(self, queries: List[str]) -> List[SearchResult]:
        pass
