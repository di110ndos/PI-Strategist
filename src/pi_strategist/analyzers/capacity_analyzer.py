"""Capacity analyzer for validating sprint loading."""

from dataclasses import dataclass
from typing import Optional

from pi_strategist.models import (
    CapacityPlan,
    RedFlag,
    Sprint,
    SprintStatus,
    Task,
)


@dataclass
class CapacityRecommendation:
    """Recommendation for capacity adjustment."""

    task: Task
    from_sprint: str
    to_sprint: str
    reason: str
    priority: int  # 1 = high, 2 = medium, 3 = low


@dataclass
class SprintAnalysis:
    """Analysis result for a single sprint."""

    sprint: Sprint
    status: SprintStatus
    overflow_hours: float
    utilization_percent: float
    recommendations: list[CapacityRecommendation]
    high_risk_tasks: list[Task]


class CapacityAnalyzer:
    """Analyzer for sprint capacity validation."""

    def __init__(self, default_buffer: float = 0.20):
        """Initialize the capacity analyzer.

        Args:
            default_buffer: Default buffer percentage (0.20 = 20%)
        """
        if not 0 <= default_buffer < 1:
            raise ValueError("Buffer percentage must be between 0 and 1")
        self.default_buffer = default_buffer

    def analyze(
        self,
        capacity_plan: CapacityPlan,
        red_flags: Optional[list[RedFlag]] = None,
    ) -> list[SprintAnalysis]:
        """Analyze a capacity plan for overloading.

        Args:
            capacity_plan: Parsed capacity plan
            red_flags: Optional list of red flags for prioritization

        Returns:
            List of sprint analysis results
        """
        results = []
        red_flag_tasks = self._get_red_flag_task_ids(red_flags) if red_flags else set()

        for i, sprint in enumerate(capacity_plan.sprints):
            analysis = self._analyze_sprint(
                sprint,
                index=i,
                all_sprints=capacity_plan.sprints,
                red_flag_tasks=red_flag_tasks,
            )
            results.append(analysis)

        return results

    def _analyze_sprint(
        self,
        sprint: Sprint,
        index: int,
        all_sprints: list[Sprint],
        red_flag_tasks: set[str],
    ) -> SprintAnalysis:
        """Analyze a single sprint."""
        status = sprint.status
        overflow = sprint.overflow_hours
        utilization = (sprint.sprint_load / sprint.net_capacity * 100) if sprint.net_capacity > 0 else 0

        recommendations = []
        high_risk_tasks = []

        # Identify high-risk tasks (those with red flags)
        for task in sprint.tasks:
            if task.id in red_flag_tasks or task.story_id in red_flag_tasks:
                high_risk_tasks.append(task)

        # Generate recommendations if overloaded
        if status == SprintStatus.FAIL:
            recommendations = self._generate_recommendations(
                sprint,
                index,
                all_sprints,
                overflow,
                high_risk_tasks,
            )

        # Check for high-risk tasks in later sprints that should be moved earlier
        if index > 0 and high_risk_tasks:
            for task in high_risk_tasks:
                # Check if earlier sprint has capacity
                for earlier_idx in range(index):
                    earlier_sprint = all_sprints[earlier_idx]
                    if earlier_sprint.net_capacity - earlier_sprint.sprint_load >= task.hours:
                        recommendations.append(
                            CapacityRecommendation(
                                task=task,
                                from_sprint=sprint.name,
                                to_sprint=earlier_sprint.name,
                                reason="High-risk task should be validated early",
                                priority=1,
                            )
                        )
                        break

        return SprintAnalysis(
            sprint=sprint,
            status=status,
            overflow_hours=overflow,
            utilization_percent=utilization,
            recommendations=recommendations,
            high_risk_tasks=high_risk_tasks,
        )

    def _generate_recommendations(
        self,
        sprint: Sprint,
        index: int,
        all_sprints: list[Sprint],
        overflow: float,
        high_risk_tasks: list[Task],
    ) -> list[CapacityRecommendation]:
        """Generate recommendations to fix overloaded sprint."""
        recommendations = []
        hours_to_move = overflow

        # Sort tasks by priority for moving (low risk first, highest hours first)
        high_risk_ids = {t.id for t in high_risk_tasks}
        movable_tasks = sorted(
            [t for t in sprint.tasks if t.id not in high_risk_ids],
            key=lambda t: (not getattr(t, 'is_high_risk', False), -t.hours),
        )

        # Find target sprints with capacity
        target_sprints = []
        for i, s in enumerate(all_sprints):
            if i > index:  # Only move to later sprints
                available = s.net_capacity - s.sprint_load
                if available > 0:
                    target_sprints.append((i, s, available))

        # Generate move recommendations
        for task in movable_tasks:
            if hours_to_move <= 0:
                break

            # Find best target sprint
            for target_idx, target_sprint, available in target_sprints:
                if available >= task.hours:
                    recommendations.append(
                        CapacityRecommendation(
                            task=task,
                            from_sprint=sprint.name,
                            to_sprint=target_sprint.name,
                            reason=f"Reduce overload by {task.hours}h",
                            priority=2,
                        )
                    )
                    hours_to_move -= task.hours
                    # Update available capacity tracking
                    target_sprints = [
                        (i, s, a - task.hours if i == target_idx else a)
                        for i, s, a in target_sprints
                    ]
                    break

        # If still overloaded, suggest splitting tasks
        if hours_to_move > 0:
            # Find largest tasks that could be split
            for task in sorted(sprint.tasks, key=lambda t: -t.hours):
                if task.hours > hours_to_move and task.hours > 4:  # Only split larger tasks
                    recommendations.append(
                        CapacityRecommendation(
                            task=task,
                            from_sprint=sprint.name,
                            to_sprint=f"{sprint.name} + later sprint",
                            reason=f"Consider splitting task ({task.hours}h) across sprints",
                            priority=3,
                        )
                    )
                    break

        return recommendations

    def _get_red_flag_task_ids(self, red_flags: list[RedFlag]) -> set[str]:
        """Extract task/story IDs associated with red flags."""
        ids = set()
        for rf in red_flags:
            if rf.ac.story_id:
                ids.add(rf.ac.story_id)
            if rf.ac.epic_id:
                ids.add(rf.ac.epic_id)
        return ids

    def summary(self, analyses: list[SprintAnalysis]) -> dict:
        """Generate summary of capacity analysis.

        Args:
            analyses: List of sprint analyses

        Returns:
            Summary dictionary
        """
        total_sprints = len(analyses)
        passing = sum(1 for a in analyses if a.status == SprintStatus.PASS)
        failing = total_sprints - passing

        total_capacity = sum(a.sprint.net_capacity for a in analyses)
        total_load = sum(a.sprint.sprint_load for a in analyses)
        overall_utilization = (total_load / total_capacity * 100) if total_capacity > 0 else 0

        return {
            "total_sprints": total_sprints,
            "passing_sprints": passing,
            "failing_sprints": failing,
            "overall_utilization": round(overall_utilization, 1),
            "total_capacity_hours": round(total_capacity, 1),
            "total_load_hours": round(total_load, 1),
            "total_recommendations": sum(len(a.recommendations) for a in analyses),
            "high_risk_task_count": sum(len(a.high_risk_tasks) for a in analyses),
        }

    def validate_capacity(
        self,
        total_hours: float,
        sprint_load: float,
        buffer_percentage: float = 0.20,
    ) -> tuple[SprintStatus, float]:
        """Quick capacity validation calculation.

        Args:
            total_hours: Total available hours
            sprint_load: Sum of task estimates
            buffer_percentage: Buffer percentage (default 20%)

        Returns:
            Tuple of (status, overflow_hours)
        """
        net_capacity = total_hours * (1 - buffer_percentage)
        overflow = sprint_load - net_capacity
        status = SprintStatus.PASS if overflow <= 0 else SprintStatus.FAIL
        return status, overflow

    def calculate_optimal_distribution(
        self,
        tasks: list[Task],
        sprints: list[Sprint],
    ) -> dict[str, list[Task]]:
        """Calculate optimal task distribution across sprints.

        Args:
            tasks: List of all tasks to distribute
            sprints: List of available sprints

        Returns:
            Dictionary mapping sprint names to assigned tasks
        """
        distribution: dict[str, list[Task]] = {s.name: [] for s in sprints}
        sprint_loads = {s.name: 0.0 for s in sprints}
        sprint_capacities = {s.name: s.net_capacity for s in sprints}

        # Sort tasks by hours (largest first for better bin packing)
        sorted_tasks = sorted(tasks, key=lambda t: -t.hours)

        for task in sorted_tasks:
            # Find sprint with most available capacity that can fit the task
            best_sprint = None
            best_available = -1

            for sprint in sprints:
                available = sprint_capacities[sprint.name] - sprint_loads[sprint.name]
                if available >= task.hours and available > best_available:
                    best_sprint = sprint.name
                    best_available = available

            if best_sprint:
                distribution[best_sprint].append(task)
                sprint_loads[best_sprint] += task.hours
            else:
                # No sprint has capacity, add to least loaded sprint
                least_loaded = min(sprint_loads, key=sprint_loads.get)
                distribution[least_loaded].append(task)
                sprint_loads[least_loaded] += task.hours

        return distribution
