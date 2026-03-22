"""Use case: analyze a GitHub user profile."""

from back.application.profile_analysis.analyze_profile import analyze_profile
from back.application.ports import GitHubProfilePort, GitHubRepositoryPort
from back.domain.models import ProfileHealthReport


class AnalyzeProfileUseCase:
    """Orchestrates profile analysis."""

    def __init__(self, repo_port: GitHubRepositoryPort, profile_port: GitHubProfilePort):
        self._repo = repo_port
        self._profile = profile_port

    async def execute(
        self,
        username: str,
        *,
        include_full_reports: bool = False,
    ) -> ProfileHealthReport:
        return await analyze_profile(
            self._repo,
            self._profile,
            username.strip().lstrip("@"),
            include_full_reports=include_full_reports,
        )
