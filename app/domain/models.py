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
