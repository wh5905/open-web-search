from abc import ABC, abstractmethod
from typing import List
from open_web_search.schemas.results import FetchedPage

class BaseReader(ABC):
    @abstractmethod
    async def read_many(self, urls: List[str]) -> List[FetchedPage]:
        pass
