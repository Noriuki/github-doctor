#!/usr/bin/env python3
"""
Verification script: runs the analysis flow with a mock GitHub client.
Run from project root: python scripts/verify_flow.py
Requires: pip install -r requirements.txt
"""

import asyncio
import sys
from pathlib import Path

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from back.application.ports import GitHubRepositoryPort
from back.application.repository_analysis.analyze_repository import analyze_repository
from back.domain.models import RepositoryHealthReport


class MockGitHubClient(GitHubRepositoryPort):
    """Mock that returns minimal data to exercise the pipeline."""

    async def get_repo(self, owner: str, repo: str) -> dict:
        return {"full_name": f"{owner}/{repo}", "default_branch": "main"}

    async def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        if "readme" in path.lower():
            return "# Test\n\n## Installation\n`pip install x`\n\n## Usage\n```python\nimport x\n```\n" + "x" * 600
        if "requirements" in path.lower():
            return "fastapi>=0.100\nhttpx>=0.24\npydantic>=2.0\n"
        return None

    async def list_directory(self, owner: str, repo: str, path: str) -> list[dict]:
        if path == "":
            return [
                {"name": "README.md", "type": "file", "path": "README.md"},
                {"name": "tests", "type": "dir", "path": "tests"},
                {"name": "requirements.txt", "type": "file", "path": "requirements.txt"},
                {"name": "app", "type": "dir", "path": "app"},
            ]
        if path == "tests":
            return [
                {"name": "test_app.py", "type": "file", "path": "tests/test_app.py"},
                {"name": "conftest.py", "type": "file", "path": "tests/conftest.py"},
            ]
        if path == ".github/workflows":
            return [
                {"name": "ci.yml", "type": "file", "path": ".github/workflows/ci.yml"},
            ]
        return []


async def main() -> None:
    client = MockGitHubClient()
    report = await analyze_repository(client, "foo", "bar")
    assert isinstance(report, RepositoryHealthReport)
    assert report.repository == "foo/bar"
    assert report.documentation.has_readme
    assert report.documentation.score >= 6
    assert report.tests.present.value == "present"
    assert report.cicd.detected
    assert report.dependencies.total_dependencies >= 0
    assert 0 <= report.health_score <= 100
    print("Repository:", report.repository)
    print("Documentation:", report.documentation.score, "/10 -", report.documentation.message)
    print("Tests:", report.tests.message)
    print("CI/CD:", report.cicd.message)
    print("Dependencies:", report.dependencies.message)
    print("Health Score:", report.health_score, "%")
    print("\n[OK] Analysis pipeline is functional.")


if __name__ == "__main__":
    asyncio.run(main())
