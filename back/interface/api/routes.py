"""API routes for repository analysis."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from back.application.analyze_repository_use_case import AnalyzeRepositoryUseCase
from back.application.repository_analysis.report_formatter import report_to_markdown, get_badge_url
from back.domain.models import RepositoryHealthReport
from back.infrastructure.cache import get_report_cache
from back.infrastructure.metrics import get_metrics

router = APIRouter(prefix="/analyze", tags=["analyze"])


def get_use_case() -> AnalyzeRepositoryUseCase:
    """Dependency: create use case with configured GitHub client."""
    from back.config import get_github_client
    return AnalyzeRepositoryUseCase(github=get_github_client())


async def _get_report_uncached(owner: str, repo: str, raw: bool = False) -> RepositoryHealthReport:
    use_case = get_use_case()
    return await use_case.execute(owner, repo, include_raw_metadata=raw)


async def _get_report(owner: str, repo: str, raw: bool = False) -> RepositoryHealthReport:
    """Get report from cache or compute and cache it. Updates metrics."""
    cache = get_report_cache()
    metrics = get_metrics()
    cached = cache.get(owner, repo, raw)
    if cached is not None:
        metrics.record_cache_hit()
        return cached
    metrics.record_cache_miss()
    metrics.record_report_generated()
    report = await _get_report_uncached(owner, repo, raw)
    cache.set(owner, repo, report, raw=raw)
    return report


# More specific paths first so they are not captured by {owner}/{repo}
@router.get("/{owner}/{repo}/report.md", response_class=PlainTextResponse)
async def analyze_repo_markdown(owner: str, repo: str) -> str:
    """Return the repository health report as Markdown."""
    try:
        report = await _get_report(owner, repo)
        return report_to_markdown(report)
    except Exception as e:
        get_metrics().record_error()
        raise HTTPException(status_code=502, detail=f"Failed to analyze repository: {e!s}") from e


@router.get("/{owner}/{repo}/badge")
async def get_repo_badge(owner: str, repo: str) -> dict:
    """
    Return badge URL for the repository health score (for use in README).
    Uses shields.io style; you can embed the returned URL in an image tag.
    """
    try:
        report = await _get_report(owner, repo)
        url = get_badge_url(report)
        return {"url": url, "score": report.health_score, "markdown": f"![Health]({url})"}
    except Exception as e:
        get_metrics().record_error()
        raise HTTPException(status_code=502, detail=f"Failed to analyze repository: {e!s}") from e


@router.get("/{owner}/{repo}", response_model=RepositoryHealthReport)
async def analyze_repo(
    owner: str,
    repo: str,
    raw: bool = Query(False, description="Include raw GitHub API metadata in response"),
) -> RepositoryHealthReport:
    """
    Analyze a GitHub repository and return a health report (JSON).

    - **owner**: GitHub username or organization
    - **repo**: Repository name
    - **raw**: If true, include raw repository metadata from GitHub API
    """
    try:
        return await _get_report(owner, repo, raw=raw)
    except Exception as e:
        get_metrics().record_error()
        raise HTTPException(status_code=502, detail=f"Failed to analyze repository: {e!s}") from e
