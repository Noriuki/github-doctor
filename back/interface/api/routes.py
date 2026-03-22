"""API routes for repository analysis."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from back.application.analyze_profile_use_case import AnalyzeProfileUseCase
from back.application.analyze_repository_use_case import AnalyzeRepositoryUseCase
from back.application.repository_analysis.report_formatter import report_to_markdown, get_badge_url
from back.domain.models import ProfileHealthReport, RepositoryHealthReport
from back.infrastructure.cache import get_profile_cache, get_report_cache
from back.infrastructure.metrics import get_metrics

router = APIRouter(prefix="/analyze", tags=["analyze"])


def get_use_case() -> AnalyzeRepositoryUseCase:
    """Dependency: create use case with configured GitHub client."""
    from back.config import get_github_client
    return AnalyzeRepositoryUseCase(github=get_github_client())


def get_profile_use_case() -> AnalyzeProfileUseCase:
    from back.config import get_github_client
    client = get_github_client()
    return AnalyzeProfileUseCase(repo_port=client, profile_port=client)


async def _get_profile_uncached(username: str, include_details: bool) -> ProfileHealthReport:
    uc = get_profile_use_case()
    return await uc.execute(username, include_full_reports=include_details)


async def _get_profile(username: str, include_details: bool = False) -> ProfileHealthReport:
    cache = get_profile_cache()
    metrics = get_metrics()
    cached = cache.get(username, include_details)
    if cached is not None:
        metrics.record_cache_hit()
        return cached
    metrics.record_cache_miss()
    metrics.record_report_generated()
    report = await _get_profile_uncached(username, include_details)
    cache.set(username, report, include_details)
    return report


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


# /profile/{username} before /{owner}/{repo} (evita conflito owner=profile)
@router.get(
    "/profile/{username}",
    response_model=ProfileHealthReport,
    tags=["profile"],
    summary="Analisar perfil GitHub",
)
async def analyze_github_profile(
    username: str,
    include_details: bool = Query(
        False,
        description="Inclui relatórios completos de cada repo em destaque (resposta maior)",
    ),
) -> ProfileHealthReport:
    """
    Análise voltada a **portfólio / recrutadores**: README de perfil (repo user/user),
    completude (bio, links), repositórios fixados (GraphQL com token) ou top públicos por estrelas,
    e saúde média desses repositórios.
    """
    try:
        return await _get_profile(username, include_details=include_details)
    except Exception as e:
        get_metrics().record_error()
        raise HTTPException(status_code=502, detail=f"Failed to analyze profile: {e!s}") from e


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
