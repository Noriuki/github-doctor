"""Analyze GitHub user profile — completeness + pinned/top repos health."""

from typing import Any, Optional

from back.application.ports import GitHubProfilePort, GitHubRepositoryPort
from back.application.repository_analysis.analyze_repository import analyze_repository
from back.application.profile_analysis.scoring import build_recruiter_pitch, compute_profile_score
from back.domain.models import (
    ProfileHealthReport,
    ProfileCompleteness,
    PinnedRepoHighlight,
    RepositoryHealthReport,
)

PINNED_GQL = """
query($login: String!) {
  user(login: $login) {
    login
    name
    bio
    company
    location
    websiteUrl
    twitterUsername
    createdAt
    followers { totalCount }
    repositories { totalCount }
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes {
        ... on Repository {
          name
          owner { login }
          description
          stargazerCount
        }
      }
    }
  }
}
"""


def _completeness_from_user_and_readme(
    user: dict[str, Any],
    profile_readme: Optional[str],
) -> ProfileCompleteness:
    bio = (user.get("bio") or "").strip()
    blog = (user.get("blog") or "").strip()
    company = (user.get("company") or "").strip()
    location = (user.get("location") or "").strip()
    twitter = (user.get("twitter_username") or "").strip()

    readme_bytes = len(profile_readme.encode("utf-8")) if profile_readme else 0
    has_pr = readme_bytes > 0

    points = 0
    if has_pr:
        points += 3
    if bio:
        points += 2
    if company:
        points += 1
    if location:
        points += 1
    if blog:
        points += 1
    if twitter:
        points += 1
    # small bonus for longer readme
    if readme_bytes > 400:
        points += 1
    score = min(10, points)

    msg_parts = []
    if has_pr:
        msg_parts.append(f"README de perfil ({readme_bytes} bytes)")
    else:
        msg_parts.append("Sem README no repositório username/username")
    if bio:
        msg_parts.append("bio")
    if company or location:
        msg_parts.append("empresa/local")
    if blog:
        msg_parts.append("site")
    if twitter:
        msg_parts.append("Twitter/X")

    return ProfileCompleteness(
        has_profile_readme=has_pr,
        profile_readme_bytes=readme_bytes,
        has_bio=bool(bio),
        has_company=bool(company),
        has_location=bool(location),
        has_blog=bool(blog),
        has_twitter=bool(twitter),
        score=score,
        message=", ".join(msg_parts) if msg_parts else "Perfil mínimo",
    )


def _one_liner_from_report(r: RepositoryHealthReport) -> str:
    return (
        f"Docs {r.documentation.score}/10 · "
        f"Testes: {r.tests.present.value} · "
        f"CI: {'sim' if r.cicd.detected else 'não'} · "
        f"Score {r.health_score:.0f}%"
    )


async def analyze_profile(
    repo_port: GitHubRepositoryPort,
    profile_port: GitHubProfilePort,
    username: str,
    *,
    include_full_reports: bool = False,
    max_repos_to_analyze: int = 6,
) -> ProfileHealthReport:
    """
    Load user, profile README, pinned (GraphQL if token) or top starred repos, run repo health on each.
    """
    user = await profile_port.get_user(username)
    login = user.get("login") or username

    # Profile README: special repo login/login
    readme_content: Optional[str] = None
    for path in ("README.md", "readme.md", "Readme.md"):
        readme_content = await repo_port.get_file_content(login, login, path)
        if readme_content:
            break
    if not readme_content:
        root = await repo_port.list_directory(login, login, "")
        for item in root or []:
            if item.get("type") == "file" and item.get("name", "").lower().startswith("readme"):
                readme_content = await repo_port.get_file_content(login, login, item.get("path", ""))
                break

    completeness = _completeness_from_user_and_readme(user, readme_content)

    pinned_normalized: list[dict[str, Any]] = []
    pinned_source = "rest_top_stars"

    try:
        gql = await profile_port.graphql(PINNED_GQL, {"login": login})
        u = (gql.get("data") or {}).get("user")
        if u and u.get("pinnedItems"):
            nodes = u["pinnedItems"].get("nodes") or []
            for node in nodes:
                if not node:
                    continue
                owner = (node.get("owner") or {}).get("login") or login
                name = node.get("name")
                if not name:
                    continue
                pinned_normalized.append(
                    {
                        "owner": owner,
                        "name": name,
                        "description": node.get("description") or "",
                        "stars": node.get("stargazerCount") or 0,
                    }
                )
            if pinned_normalized:
                pinned_source = "graphql_pinned"
    except Exception:
        pinned_normalized = []

    if not pinned_normalized:
        all_repos = await profile_port.list_user_public_repos(login, per_page=100)
        sorted_repos = sorted(
            all_repos,
            key=lambda r: r.get("stargazers_count") or 0,
            reverse=True,
        )[:max_repos_to_analyze]
        for r in sorted_repos:
            owner = (r.get("owner") or {}).get("login") or login
            pinned_normalized.append(
                {
                    "owner": owner,
                    "name": r.get("name") or "",
                    "description": r.get("description") or "",
                    "stars": r.get("stargazers_count") or 0,
                }
            )
        pinned_source = "rest_top_stars"

    highlights: list[PinnedRepoHighlight] = []
    full_reports: list[RepositoryHealthReport] = []

    for item in pinned_normalized[:max_repos_to_analyze]:
        owner, name = item["owner"], item["name"]
        if not name:
            continue
        try:
            rep = await analyze_repository(repo_port, owner, name, include_raw_metadata=False)
        except Exception:
            rep = RepositoryHealthReport(
                repository=f"{owner}/{name}",
                health_score=0.0,
            )
        hl = PinnedRepoHighlight(
            repository=f"{owner}/{name}",
            description=item.get("description", ""),
            stars=int(item.get("stars") or 0),
            health_score=rep.health_score,
            one_liner=_one_liner_from_report(rep),
        )
        highlights.append(hl)
        if include_full_reports:
            full_reports.append(rep)

    followers = int(user.get("followers") or 0)
    public_repos = int(user.get("public_repos") or 0)
    display_name = user.get("name")
    created_at = user.get("created_at") or ""

    profile_score = compute_profile_score(completeness, highlights, followers, public_repos)

    report = ProfileHealthReport(
        username=login,
        display_name=display_name,
        followers=followers,
        public_repos=public_repos,
        created_at=created_at,
        completeness=completeness,
        pinned_source=pinned_source,
        highlights=highlights,
        full_repo_reports=full_reports if include_full_reports else None,
        profile_score=profile_score,
        recruiter_pitch="",
    )
    report.recruiter_pitch = build_recruiter_pitch(report)
    return report
