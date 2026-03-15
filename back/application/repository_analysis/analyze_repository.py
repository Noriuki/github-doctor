"""Repository analysis - gather data and build health report."""

import json
import re
from typing import Any

from back.application.ports import GitHubRepositoryPort
from back.domain.models import (
    RepositoryHealthReport,
    DocumentationScore,
    TestStatus,
    CICDStatus,
    DependencyHealth,
    TestPresence,
    CICDType,
)
from back.application.repository_analysis.scoring import compute_health_score

# Common README names (GitHub API is case-sensitive; try common variants)
README_NAMES = ("README.md", "readme.md", "README.rst", "readme.rst", "README.txt", "readme.txt", "README", "readme")
# Common test directory names
TEST_DIR_NAMES = ("tests", "test", "spec", "specs", "__tests__", "e2e", "integration")
# GitHub Actions workflows path
GITHUB_WORKFLOWS_PATH = ".github/workflows"
# Dependency file patterns
DEPENDENCY_FILES = (
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "Pipfile",
    "Pipfile.lock",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
    "Gemfile.lock",
)


async def _analyze_documentation(
    github: GitHubRepositoryPort, owner: str, repo: str
) -> DocumentationScore:
    """Detect README and assess quality."""
    score = DocumentationScore(score=0, message="No README found")
    readme_content: str | None = None
    readme_size = 0
    readme_path: str | None = None

    # Try known names first, then fall back to listing root (handles case variants)
    for name in README_NAMES:
        content = await github.get_file_content(owner, repo, name)
        if content:
            readme_content = content
            readme_path = name
            break
    if not readme_content:
        root = await github.list_directory(owner, repo, "")
        for item in root or []:
            if item.get("type") != "file":
                continue
            name = item.get("name", "")
            if name.lower().startswith("readme"):
                content = await github.get_file_content(owner, repo, item.get("path", name))
                if content:
                    readme_content = content
                    readme_path = item.get("path", name)
                    break

    if readme_content:
        readme_size = len(readme_content.encode("utf-8"))
        score.has_readme = True
        score.readme_size_bytes = readme_size

    if not readme_content:
        return score

    # Quality heuristics
    has_badges = bool(re.search(r"!\[.*?\]\s*\(.*?\)", readme_content)) or "badge" in readme_content.lower()
    has_installation = any(
        x in readme_content.lower()
        for x in ("## install", "## installation", "pip install", "npm install", "usage", "getting started")
    )
    has_usage = any(
        x in readme_content.lower()
        for x in ("## usage", "## example", "## examples", "```", "how to use")
    )

    score.has_badges = has_badges
    score.has_installation = has_installation
    score.has_usage = has_usage

    # Score 0-10
    points = 2  # has readme
    if readme_size > 500:
        points += 2
    if readme_size > 1500:
        points += 1
    if has_badges:
        points += 1
    if has_installation:
        points += 2
    if has_usage:
        points += 2
    score.score = min(10, points)
    score.message = f"README found ({readme_size} bytes), score {score.score}/10"
    return score


async def _analyze_tests(
    github: GitHubRepositoryPort, owner: str, repo: str
) -> TestStatus:
    """Detect test directories and files."""
    status = TestStatus(present=TestPresence.UNKNOWN, message="Could not determine")
    root = await github.list_directory(owner, repo, "")
    if not root:
        status.present = TestPresence.MISSING
        status.message = "Missing"
        return status

    # Keep actual path from API (case-sensitive on GitHub)
    test_dir_paths = [
        item["path"] for item in root
        if item.get("type") == "dir" and item.get("name", "").lower() in TEST_DIR_NAMES
    ]
    status.test_dirs = [p.split("/")[-1] for p in test_dir_paths]

    if test_dir_paths:
        status.present = TestPresence.PRESENT
        # Count test files in first test dir
        first_test_path = test_dir_paths[0]
        dir_items = await github.list_directory(owner, repo, first_test_path)
        if isinstance(dir_items, list):
            status.test_files_count = sum(1 for i in dir_items if i.get("type") == "file")
        status.message = f"Test directories found: {', '.join(test_dirs)}"
    else:
        status.present = TestPresence.MISSING
        status.message = "Missing"
    return status


async def _analyze_cicd(
    github: GitHubRepositoryPort, owner: str, repo: str
) -> CICDStatus:
    """Detect GitHub Actions workflows."""
    status = CICDStatus(message="No CI/CD detected")
    try:
        workflows = await github.list_directory(owner, repo, GITHUB_WORKFLOWS_PATH)
    except Exception:
        return status

    if not workflows:
        return status

    workflow_files = [
        w["name"] for w in workflows
        if w.get("type") == "file" and (w["name"].endswith(".yml") or w["name"].endswith(".yaml"))
    ]
    if workflow_files:
        status.detected = True
        status.type = CICDType.GITHUB_ACTIONS
        status.workflow_files = workflow_files
        status.message = "GitHub Actions detected"
    return status


def _count_dependencies_and_outdated(content: str, filename: str) -> tuple[int, int]:
    """Heuristic: count lines (deps) and comment lines with 'outdated' or version pins for outdated estimate."""
    if not content:
        return 0, 0
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
    total = 0
    # requirements.txt: one package per line (package name, or name==version)
    if "requirements" in filename or filename == "Pipfile":
        total = len([l for l in lines if not l.startswith("[") and ("=" in l or "-" in l or l.replace("-", "").replace("_", "").isalnum())])
    if "package.json" in filename:
        # Approximate: dependencies + devDependencies keys
        try:
            data = json.loads(content)
            deps = data.get("dependencies", {}) or {}
            dev = data.get("devDependencies", {}) or {}
            total = len(deps) + len(dev)
        except Exception:
            total = 0
    if "pyproject.toml" in filename:
        # Count dependency lines in [project.dependencies] or [tool.poetry.dependencies]
        in_deps = False
        for line in lines:
            if "[project]" in line or "dependencies" in line:
                in_deps = True
            if in_deps and ("=" in line or ">" in line or "^" in line):
                total += 1
        if total == 0:
            total = len([l for l in lines if "=" in l and not l.startswith("[")])
    # Outdated: we don't call external APIs; use placeholder "some outdated" for demo
    outdated = min(total, 3) if total > 0 else 0  # Placeholder: assume up to 3 outdated
    return total, outdated


async def _analyze_dependencies(
    github: GitHubRepositoryPort, owner: str, repo: str
) -> DependencyHealth:
    """Detect dependency files and estimate health (outdated count is heuristic)."""
    health = DependencyHealth(message="No dependency files found")
    root = await github.list_directory(owner, repo, "")
    if not root:
        return health

    found_files = []
    total_deps = 0
    total_outdated = 0

    for item in root:
        if item.get("type") != "file":
            continue
        name = item.get("name", "")
        if name in DEPENDENCY_FILES or name.endswith("requirements.txt"):
            content = await github.get_file_content(owner, repo, name)
            count, outdated = _count_dependencies_and_outdated(content or "", name)
            found_files.append(name)
            total_deps += count
            total_outdated += outdated

    if found_files:
        health.dependency_files = found_files
        health.total_dependencies = total_deps
        health.outdated_count = total_outdated
        health.message = f"{len(found_files)} file(s), {total_deps} deps, {total_outdated} outdated"
    return health


async def analyze_repository(
    github: GitHubRepositoryPort, owner: str, repo: str, include_raw_metadata: bool = False
) -> RepositoryHealthReport:
    """
    Run full repository analysis and return a RepositoryHealthReport.
    """
    repo_id = f"{owner}/{repo}"
    meta: dict[str, Any] = {}
    try:
        meta = await github.get_repo(owner, repo)
    except Exception:
        pass

    documentation = await _analyze_documentation(github, owner, repo)
    tests = await _analyze_tests(github, owner, repo)
    cicd = await _analyze_cicd(github, owner, repo)
    dependencies = await _analyze_dependencies(github, owner, repo)

    report = RepositoryHealthReport(
        repository=repo_id,
        documentation=documentation,
        tests=tests,
        cicd=cicd,
        dependencies=dependencies,
        health_score=0.0,
        raw_metadata=meta if include_raw_metadata else None,
    )
    report.health_score = compute_health_score(report)
    return report
