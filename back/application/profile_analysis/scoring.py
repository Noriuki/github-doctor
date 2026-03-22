"""Profile sellability score (recruiter-oriented)."""

import math

from back.domain.models import ProfileCompleteness, PinnedRepoHighlight, ProfileHealthReport


def completeness_to_points(c: ProfileCompleteness) -> float:
    """Map 0-10 completeness to 0-35 points."""
    return (c.score / 10.0) * 35.0


def activity_score(followers: int, public_repos: int) -> float:
    """0-20 points: social proof + body of work."""
    follower_pts = min(10.0, math.log10(max(followers, 0) + 10) * 3.3)
    repo_pts = min(10.0, public_repos / 4.0)
    return min(20.0, follower_pts + repo_pts)


def highlights_avg_health(highlights: list[PinnedRepoHighlight]) -> float:
    if not highlights:
        return 50.0  # neutral if no pins
    return sum(h.health_score for h in highlights) / len(highlights)


def compute_profile_score(
    completeness: ProfileCompleteness,
    highlights: list[PinnedRepoHighlight],
    followers: int,
    public_repos: int,
) -> float:
    """
    Overall 0-100: completeness (35%) + avg repo health (45%) + activity (20%).
    """
    comp_pts = completeness_to_points(completeness)
    health_pts = (highlights_avg_health(highlights) / 100.0) * 45.0
    act_pts = activity_score(followers, public_repos)
    total = comp_pts + health_pts + act_pts
    return round(min(100.0, total), 1)


def build_recruiter_pitch(report: ProfileHealthReport) -> str:
    """Short PT-BR pitch for portfolio context."""
    c = report.completeness
    parts = []
    if c.has_profile_readme:
        parts.append("README de perfil (repo username/username) configurado")
    else:
        parts.append("sem README de perfil — considere criar o repositório público com o mesmo nome do usuário")

    if c.has_bio:
        parts.append("bio visível")
    if c.has_location or c.has_company:
        parts.append("dados de contato/localização preenchidos")

    avg_h = highlights_avg_health(report.highlights)
    n = len(report.highlights)
    src = "fixados" if "graphql" in report.pinned_source else "destaque (repos públicos)"

    pitch = (
        f"@{report.username}: {', '.join(parts)}. "
        f"{n} repositório(s) em {src} com saúde média ~{avg_h:.0f}%. "
        f"Score geral {report.profile_score:.0f}% — "
    )
    if report.profile_score >= 75:
        pitch += "perfil forte para portfólio e primeira impressão."
    elif report.profile_score >= 50:
        pitch += "bom ponto de partida; reforçar README de perfil e pins ajuda em processos."
    else:
        pitch += "há espaço para melhorar README de perfil, bio e qualidade dos repositórios em destaque."
    return pitch
