"""Data models for PI Strategist."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RedFlagSeverity(Enum):
    """Severity levels for red flags."""

    CRITICAL = "critical"
    MODERATE = "moderate"
    LOW = "low"


class ObligationType(Enum):
    """Types of obligation statements."""

    SHALL = "shall"
    MUST = "must"
    WILL = "will"
    SHALL_NOT = "shall not"
    MUST_NOT = "must not"
    WILL_NOT = "will not"


class SLAMetricType(Enum):
    """Types of SLA/SLO metrics."""

    UPTIME = "uptime"
    AVAILABILITY = "availability"
    RESPONSE_TIME = "response_time"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RECOVERY_TIME = "recovery_time"


class SprintStatus(Enum):
    """Sprint capacity status."""

    PASS = "pass"
    FAIL = "fail"


class DeploymentStrategy(Enum):
    """Deployment strategy types."""

    FEATURE_FLAG = "feature_flag"
    FULL_DEPLOYMENT = "full_deployment"


@dataclass
class AcceptanceCriteria:
    """Represents an acceptance criterion."""

    id: str
    text: str
    story_id: Optional[str] = None
    epic_id: Optional[str] = None


@dataclass
class RedFlag:
    """Represents a detected red flag in acceptance criteria."""

    ac: AcceptanceCriteria
    flagged_term: str
    category: str
    severity: RedFlagSeverity
    suggested_metric: str
    negotiation_script: str


@dataclass
class Obligation:
    """Represents a detected obligation statement."""

    text: str
    obligation_type: ObligationType
    subject: str  # Who is obligated (e.g., "the vendor", "the system")
    action: str  # What they must do
    source_line: str  # Original text containing the obligation
    is_negative: bool = False  # True for "shall not", "must not", etc.


@dataclass
class SLAFinding:
    """Represents a detected SLA/SLO metric."""

    metric_type: SLAMetricType
    value: str  # The numeric value (e.g., "99.9", "200")
    unit: str  # The unit (e.g., "%", "ms", "seconds", "requests/second")
    source_line: str  # Original text containing the SLA
    is_valid: bool = True  # Whether the SLA is well-defined
    warning: str = ""  # Any warnings about the SLA definition


@dataclass
class Task:
    """Represents a task in the capacity planner."""

    id: str
    name: str
    hours: float
    sprint: str
    story_id: Optional[str] = None
    epic_id: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class Story:
    """Represents a user story."""

    id: str
    name: str
    description: str
    epic_id: Optional[str] = None
    acceptance_criteria: list[AcceptanceCriteria] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)


@dataclass
class Epic:
    """Represents an epic."""

    id: str
    name: str
    description: str
    stories: list[Story] = field(default_factory=list)


@dataclass
class Sprint:
    """Represents a sprint with capacity information."""

    name: str
    total_hours: float
    buffer_percentage: float = 0.20
    tasks: list[Task] = field(default_factory=list)

    @property
    def buffer_hours(self) -> float:
        """Calculate buffer hours."""
        return self.total_hours * self.buffer_percentage

    @property
    def net_capacity(self) -> float:
        """Calculate net capacity after buffer."""
        return self.total_hours - self.buffer_hours

    @property
    def sprint_load(self) -> float:
        """Calculate total load from tasks."""
        return sum(task.hours for task in self.tasks)

    @property
    def status(self) -> SprintStatus:
        """Determine if sprint is overloaded."""
        return SprintStatus.PASS if self.sprint_load <= self.net_capacity else SprintStatus.FAIL

    @property
    def overflow_hours(self) -> float:
        """Calculate hours over capacity (negative if under)."""
        return self.sprint_load - self.net_capacity


@dataclass
class DeploymentCluster:
    """Represents a group of tasks for deployment."""

    name: str
    tasks: list[Task]
    strategy: DeploymentStrategy
    deploy_timing: str
    dependencies: list[str] = field(default_factory=list)
    rollback_plan: str = ""


@dataclass
class DEDDocument:
    """Represents a parsed DED document."""

    filename: str
    epics: list[Epic] = field(default_factory=list)
    raw_text: str = ""

    @property
    def all_stories(self) -> list[Story]:
        """Get all stories across all epics."""
        return [story for epic in self.epics for story in epic.stories]

    @property
    def all_acceptance_criteria(self) -> list[AcceptanceCriteria]:
        """Get all acceptance criteria across all stories."""
        return [ac for story in self.all_stories for ac in story.acceptance_criteria]

    @property
    def all_tasks(self) -> list[Task]:
        """Get all tasks across all stories."""
        return [task for story in self.all_stories for task in story.tasks]


@dataclass
class CapacityPlan:
    """Represents a parsed capacity planner."""

    filename: str
    sprints: list[Sprint] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def all_tasks(self) -> list[Task]:
        """Get all tasks across all sprints."""
        return [task for sprint in self.sprints for task in sprint.tasks]

    @property
    def total_hours(self) -> float:
        """Get total hours across all sprints."""
        return sum(sprint.total_hours for sprint in self.sprints)

    @property
    def total_load(self) -> float:
        """Get total load across all sprints."""
        return sum(sprint.sprint_load for sprint in self.sprints)


@dataclass
class AnalysisResult:
    """Complete analysis result."""

    ded: Optional[DEDDocument] = None
    capacity: Optional[CapacityPlan] = None
    red_flags: list[RedFlag] = field(default_factory=list)
    deployment_clusters: list[DeploymentCluster] = field(default_factory=list)

    @property
    def critical_flags(self) -> list[RedFlag]:
        """Get critical severity red flags."""
        return [rf for rf in self.red_flags if rf.severity == RedFlagSeverity.CRITICAL]

    @property
    def moderate_flags(self) -> list[RedFlag]:
        """Get moderate severity red flags."""
        return [rf for rf in self.red_flags if rf.severity == RedFlagSeverity.MODERATE]

    @property
    def low_flags(self) -> list[RedFlag]:
        """Get low severity red flags."""
        return [rf for rf in self.red_flags if rf.severity == RedFlagSeverity.LOW]

    @property
    def cd_eligible_count(self) -> int:
        """Count tasks eligible for early deployment."""
        return sum(len(cluster.tasks) for cluster in self.deployment_clusters)

    @property
    def cd_percentage(self) -> float:
        """Calculate percentage of tasks eligible for early deployment."""
        total = len(self.capacity.all_tasks) if self.capacity else 0
        if total == 0:
            return 0.0
        return (self.cd_eligible_count / total) * 100
