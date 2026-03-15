"""Application ports - interfaces for infrastructure."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class GitHubRepositoryPort(ABC):
    """Port for fetching repository data from GitHub."""

    @abstractmethod
    async def get_repo(self, owner: str, repo: str) -> dict[str, Any]:
        """Fetch repository metadata."""
        ...

    @abstractmethod
    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Fetch file content (decoded). Returns None if not found."""
        ...

    @abstractmethod
    async def list_directory(self, owner: str, repo: str, path: str) -> list[dict[str, Any]]:
        """List directory contents. Returns list of item dicts with name, type, path."""
        ...
