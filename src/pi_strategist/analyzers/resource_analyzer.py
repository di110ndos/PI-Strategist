"""Resource analyzer for per-person utilization, allocation flags, and bottleneck detection."""

import math
from dataclasses import dataclass, field

from pi_strategist.models import Sprint, Task


@dataclass
class ResourceSprintAllocation:
    """Allocation details for a single resource in a single sprint."""

    sprint_name: str
    allocated_hours: float
    sprint_capacity: float
    utilization_percent: float


@dataclass
class ResourceMetrics:
    """Aggregated metrics for a single resource."""

    name: str
    total_allocated_hours: float = 0.0
    total_available_hours: float = 0.0
    average_utilization: float = 0.0
    sprint_allocations: list[ResourceSprintAllocation] = field(default_factory=list)
    is_over_allocated: bool = False  # >100% in any sprint
    is_under_allocated: bool = False  # <50% average
    over_allocated_sprints: list[str] = field(default_factory=list)
    task_count: int = 0
    task_hours_cv: float = 0.0  # Coefficient of variation of task hours
    unique_stories: int = 0
    unique_epics: int = 0


@dataclass
class BottleneckWarning:
    """Warning for a resource identified as a potential bottleneck."""

    resource_name: str
    reason: str
    epic_count: int = 0
    story_count: int = 0
    sprint_count: int = 0


@dataclass
class ResourceAnalysis:
    """Complete resource analysis result."""

    resource_metrics: list[ResourceMetrics] = field(default_factory=list)
    over_allocated: list[str] = field(default_factory=list)
    under_allocated: list[str] = field(default_factory=list)
    bottleneck_warnings: list[BottleneckWarning] = field(default_factory=list)
    total_resources: int = 0


class ResourceAnalyzer:
    """Analyzer for per-resource utilization and bottleneck detection."""

    def __init__(
        self,
        over_threshold: float = 1.0,
        under_threshold: float = 0.5,
        bottleneck_epic_threshold: int = 3,
    ):
        """Initialize the resource analyzer.

        Args:
            over_threshold: Utilization ratio above which a sprint is flagged
                as over-allocated (1.0 = 100%).
            under_threshold: Average utilization ratio below which a resource
                is flagged as under-allocated (0.5 = 50%).
            bottleneck_epic_threshold: Minimum unique epic count to flag a
                resource as a potential bottleneck.
        """
        self.over_threshold = over_threshold
        self.under_threshold = under_threshold
        self.bottleneck_epic_threshold = bottleneck_epic_threshold

    def analyze(
        self,
        resources: dict[str, float],
        sprints: list[Sprint],
    ) -> ResourceAnalysis:
        """Analyze resource utilization across sprints.

        Args:
            resources: Dict mapping resource name to available hours per sprint.
            sprints: List of sprints containing task assignments.

        Returns:
            ResourceAnalysis with per-resource metrics and flags.
        """
        if not resources or not sprints:
            return ResourceAnalysis()

        # Build per-resource task map from task tags
        resource_tasks: dict[str, list[tuple[str, Task]]] = {
            name: [] for name in resources
        }
        for sprint in sprints:
            for task in sprint.tasks:
                for tag in task.tags:
                    if tag in resources:
                        resource_tasks[tag].append((sprint.name, task))

        metrics_list = []
        over_allocated = []
        under_allocated = []

        for name, hours_per_sprint in resources.items():
            tasks_with_sprints = resource_tasks.get(name, [])
            metrics = self._compute_resource_metrics(
                name, hours_per_sprint, tasks_with_sprints, sprints
            )
            metrics_list.append(metrics)

            if metrics.is_over_allocated:
                over_allocated.append(name)
            if metrics.is_under_allocated:
                under_allocated.append(name)

        bottlenecks = self._detect_bottlenecks(resource_tasks, resources)

        return ResourceAnalysis(
            resource_metrics=metrics_list,
            over_allocated=over_allocated,
            under_allocated=under_allocated,
            bottleneck_warnings=bottlenecks,
            total_resources=len(resources),
        )

    def _compute_resource_metrics(
        self,
        name: str,
        hours_per_sprint: float,
        tasks_with_sprints: list[tuple[str, Task]],
        sprints: list[Sprint],
    ) -> ResourceMetrics:
        """Compute utilization metrics for a single resource."""
        sprint_hours: dict[str, float] = {}
        all_task_hours: list[float] = []
        story_ids: set[str] = set()
        epic_ids: set[str] = set()

        for sprint_name, task in tasks_with_sprints:
            sprint_hours[sprint_name] = sprint_hours.get(sprint_name, 0.0) + task.hours
            all_task_hours.append(task.hours)
            if task.story_id:
                story_ids.add(task.story_id)
            if task.epic_id:
                epic_ids.add(task.epic_id)

        # Build per-sprint allocation records
        sprint_allocations = []
        over_allocated_sprints = []
        total_allocated = 0.0
        total_available = hours_per_sprint * len(sprints)

        for sprint in sprints:
            allocated = sprint_hours.get(sprint.name, 0.0)
            total_allocated += allocated
            utilization = (allocated / hours_per_sprint * 100) if hours_per_sprint > 0 else 0.0

            sprint_allocations.append(
                ResourceSprintAllocation(
                    sprint_name=sprint.name,
                    allocated_hours=round(allocated, 2),
                    sprint_capacity=round(hours_per_sprint, 2),
                    utilization_percent=round(utilization, 2),
                )
            )

            if hours_per_sprint > 0 and (allocated / hours_per_sprint) > self.over_threshold:
                over_allocated_sprints.append(sprint.name)

        avg_util = (total_allocated / total_available) if total_available > 0 else 0.0

        # Coefficient of variation of task hours
        task_cv = self._coefficient_of_variation(all_task_hours)

        return ResourceMetrics(
            name=name,
            total_allocated_hours=round(total_allocated, 2),
            total_available_hours=round(total_available, 2),
            average_utilization=round(avg_util * 100, 2),
            sprint_allocations=sprint_allocations,
            is_over_allocated=len(over_allocated_sprints) > 0,
            is_under_allocated=avg_util < self.under_threshold,
            over_allocated_sprints=over_allocated_sprints,
            task_count=len(all_task_hours),
            task_hours_cv=round(task_cv, 4),
            unique_stories=len(story_ids),
            unique_epics=len(epic_ids),
        )

    def _detect_bottlenecks(
        self,
        resource_tasks: dict[str, list[tuple[str, Task]]],
        resources: dict[str, float],
    ) -> list[BottleneckWarning]:
        """Detect resources that are potential skill bottlenecks."""
        warnings = []
        for name, tasks_with_sprints in resource_tasks.items():
            epic_ids: set[str] = set()
            story_ids: set[str] = set()
            sprint_names: set[str] = set()

            for sprint_name, task in tasks_with_sprints:
                sprint_names.add(sprint_name)
                if task.epic_id:
                    epic_ids.add(task.epic_id)
                if task.story_id:
                    story_ids.add(task.story_id)

            if len(epic_ids) >= self.bottleneck_epic_threshold:
                warnings.append(
                    BottleneckWarning(
                        resource_name=name,
                        reason=(
                            f"Allocated across {len(epic_ids)} epics in "
                            f"{len(sprint_names)} sprints — potential skill bottleneck"
                        ),
                        epic_count=len(epic_ids),
                        story_count=len(story_ids),
                        sprint_count=len(sprint_names),
                    )
                )

        return warnings

    @staticmethod
    def _coefficient_of_variation(values: list[float]) -> float:
        """Calculate the coefficient of variation (std_dev / mean)."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance) / mean
