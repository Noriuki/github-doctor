"""Health score computation from report components."""

from app.domain.models import (
    RepositoryHealthReport,
    DocumentationScore,
    TestStatus,
    CICDStatus,
    DependencyHealth,
    TestPresence,
    CICDType,
)


def compute_documentation_score(doc: DocumentationScore) -> float:
    """Convert documentation score (0-10) to 0-100 scale."""
    return (doc.score / 10.0) * 100.0


def compute_tests_score(tests: TestStatus) -> float:
    """Score tests: present=100, missing=0, unknown=50."""
    if tests.present == TestPresence.PRESENT:
        return 100.0
    if tests.present == TestPresence.MISSING:
        return 0.0
    return 50.0


def compute_cicd_score(cicd: CICDStatus) -> float:
    """Score CI/CD: detected=100, none=0."""
    if cicd.detected and cicd.type == CICDType.GITHUB_ACTIONS:
        return 100.0
    return 0.0


def compute_dependencies_score(deps: DependencyHealth) -> float:
    """Score dependencies: fewer outdated = higher. 0 outdated=100, all outdated=0."""
    if deps.total_dependencies == 0:
        return 100.0  # No deps to worry about
    outdated = deps.outdated_count
    total = deps.total_dependencies
    if total <= 0:
        return 100.0
    ratio = 1.0 - (outdated / total)
    return max(0.0, ratio * 100.0)


# Weights for overall health (must sum to 1.0)
WEIGHT_DOCUMENTATION = 0.25
WEIGHT_TESTS = 0.25
WEIGHT_CICD = 0.25
WEIGHT_DEPENDENCIES = 0.25


def compute_health_score(report: RepositoryHealthReport) -> float:
    """
    Compute overall health score (0-100) from report components.
    Uses weighted average: documentation, tests, CI/CD, dependencies (25% each).
    """
    doc_score = compute_documentation_score(report.documentation)
    tests_score = compute_tests_score(report.tests)
    cicd_score = compute_cicd_score(report.cicd)
    deps_score = compute_dependencies_score(report.dependencies)

    total = (
        WEIGHT_DOCUMENTATION * doc_score
        + WEIGHT_TESTS * tests_score
        + WEIGHT_CICD * cicd_score
        + WEIGHT_DEPENDENCIES * deps_score
    )
    return round(total, 1)
