"""GitHub REST API client adapter."""

import base64
from typing import Any, Optional

import httpx

from app.application.ports import GitHubRepositoryPort


class GitHubClient(GitHubRepositoryPort):
    """HTTP client for GitHub REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None, timeout: float = 30.0):
        self._token = token
        self._timeout = timeout
        self._headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHubDoctor/1.0",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    async def get_repo(self, owner: str, repo: str) -> dict[str, Any]:
        """Fetch repository metadata."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()

    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Fetch file content (decoded from base64). Returns None if not found."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=self._headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("content"):
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return None

    async def list_directory(self, owner: str, repo: str, path: str) -> list[dict[str, Any]]:
        """List directory contents. Returns list of items with name, type, path."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}" if path else f"{self.BASE_URL}/repos/{owner}/{repo}/contents"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=self._headers)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                return []
            return [{"name": item.get("name", ""), "type": item.get("type", "file"), "path": item.get("path", "")} for item in data]
