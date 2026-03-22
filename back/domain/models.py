"""Domain models for repository health reporting."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TestPresence(str, Enum):
    """Whether tests are present and where."""

    PRESENT = "present"
    MISSING = "missing"
    UNKNOWN = "unknown"


class CICDType(str, Enum):
    """Type of CI/CD detected."""

    GITHUB_ACTIONS = "github_actions"
    NONE = "none"
    UNKNOWN = "unknown"


class DocumentationScore(BaseModel):
    """Documentation quality metrics."""

    score: int = Field(ge=0, le=10, description="Documentation score 0-10")
    has_readme: bool = False
    readme_size_bytes: int = 0
    has_badges: bool = False
    has_installation: bool = False
    has_usage: bool = False
    message: str = ""


class TestStatus(BaseModel):
    """Test directory and file detection."""

    present: TestPresence = TestPresence.UNKNOWN
    test_dirs: list[str] = Field(default_factory=list)
    test_files_count: int = 0
    message: str = ""


class CICDStatus(BaseModel):
    """CI/CD configuration status."""

    detected: bool = False
    type: CICDType = CICDType.NONE
    workflow_files: list[str] = Field(default_factory=list)
    message: str = ""


class DependencyHealth(BaseModel):
    """Dependency health summary."""

    total_dependencies: int = 0
    outdated_count: int = 0
    dependency_files: list[str] = Field(default_factory=list)
    message: str = ""


class RepositoryHealthReport(BaseModel):
    """Full repository health report."""

    repository: str = Field(description="owner/repo format")
    documentation: DocumentationScore = Field(default_factory=DocumentationScore)
    tests: TestStatus = Field(default_factory=TestStatus)
    cicd: CICDStatus = Field(default_factory=CICDStatus)
    dependencies: DependencyHealth = Field(default_factory=DependencyHealth)
    health_score: float = Field(ge=0.0, le=100.0, description="Overall health score 0-100%")
    raw_metadata: Optional[dict] = Field(default=None, description="Raw repo metadata from API")


class PinnedRepoHighlight(BaseModel):
    """One pinned or highlighted repository with health summary."""

    repository: str = Field(description="owner/repo")
    description: str = ""
    stars: int = 0
    health_score: float = Field(ge=0.0, le=100.0, default=0.0)
    one_liner: str = Field(default="", description="Short takeaway for recruiters")


class ProfileCompleteness(BaseModel):
    """How complete the public profile looks (recruiter signal)."""

    has_profile_readme: bool = False
    profile_readme_bytes: int = 0
    has_bio: bool = False
    has_company: bool = False
    has_location: bool = False
    has_blog: bool = False
    has_twitter: bool = False
    score: int = Field(ge=0, le=10, description="Completeness 0-10")
    message: str = ""


class ProfileHealthReport(BaseModel):
    """GitHub profile analysis — presentation + pinned/top repos health."""

    username: str
    display_name: Optional[str] = None
    followers: int = 0
    public_repos: int = 0
    created_at: str = ""
    completeness: ProfileCompleteness = Field(default_factory=ProfileCompleteness)
    pinned_source: str = Field(
        default="unknown",
        description="graphql_pinned | rest_top_stars | mixed",
    )
    highlights: list[PinnedRepoHighlight] = Field(default_factory=list)
    full_repo_reports: Optional[list[RepositoryHealthReport]] = Field(
        default=None,
        description="Included when include_details=true",
    )
    profile_score: float = Field(ge=0.0, le=100.0, description="Overall profile sellability 0-100%")
    recruiter_pitch: str = Field(
        default="",
        description="One paragraph summary for portfolio / recruiters",
    )
