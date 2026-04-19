from abc import ABC, abstractmethod


class SearchProvider(ABC):
    name: str

    @abstractmethod
    async def search(
        self,
        query: str,
        topic: str,
        max_results: int,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        **kwargs,
    ) -> dict:
        raise NotImplementedError