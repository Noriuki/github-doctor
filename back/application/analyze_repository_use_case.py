"""Use case: analyze a GitHub repository and return health report."""

from back.application.ports import GitHubRepositoryPort
from back.application.repository_analysis.analyze_repository import analyze_repository
from back.domain.models import RepositoryHealthReport


class AnalyzeRepositoryUseCase:
    """Orchestrates repository analysis using a GitHub adapter."""

    def __init__(self, github: GitHubRepositoryPort):
        self._github = github

    async def execute(
        self, owner: str, repo: str, include_raw_metadata: bool = False
    ) -> RepositoryHealthReport:
        """Analyze the given repository and return its health report."""
        return await analyze_repository(
            self._github, owner, repo, include_raw_metadata=include_raw_metadata
        )
