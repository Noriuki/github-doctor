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


class GitHubProfilePort(ABC):
    """Port for user/profile-level GitHub API (REST + optional GraphQL)."""

    @abstractmethod
    async def get_user(self, username: str) -> dict[str, Any]:
        """GET /users/{username}."""
        ...

    @abstractmethod
    async def list_user_public_repos(self, username: str, *, per_page: int = 100) -> list[dict[str, Any]]:
        """List public repositories for a user (REST)."""
        ...

    @abstractmethod
    async def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """
        POST /graphql. Requires token for reliable use.
        Raises if unauthenticated and GitHub rejects.
        """
        ...
