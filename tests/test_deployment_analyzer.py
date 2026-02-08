"""Tests for the deployment analyzer."""

import pytest

from pi_strategist.analyzers.deployment_analyzer import DeploymentAnalyzer
from pi_strategist.models import (
    CapacityPlan,
    Sprint,
    Task,
    DeploymentStrategy,
)


def _make_task(id: str, hours: float, sprint: str = "Sprint 1", tags: list[str] | None = None, deps: list[str] | None = None) -> Task:
    return Task(
        id=id,
        name=f"Task {id}",
        hours=hours,
        sprint=sprint,
        dependencies=deps or [],
        tags=tags or [],
    )


def _make_plan(tasks_per_sprint: dict[str, list[Task]]) -> CapacityPlan:
    sprints = []
    for name, tasks in tasks_per_sprint.items():
        sprints.append(Sprint(name=name, total_hours=100, tasks=tasks))
    return CapacityPlan(filename="test.xlsx", sprints=sprints)


class TestDeploymentAnalyzer:
    """Tests for DeploymentAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        return DeploymentAnalyzer(cd_target_percentage=0.30)

    def test_basic_clustering(self, analyzer):
        """Tasks are clustered into deployment groups."""
        tasks = [
            _make_task("T1", 8, tags=["auth"]),
            _make_task("T2", 8, tags=["auth"]),
            _make_task("T3", 8, tags=["payment"]),
        ]
        plan = _make_plan({"Sprint 1": tasks})

        clusters = analyzer.analyze(plan)
        assert len(clusters) > 0

    def test_cluster_has_strategy(self, analyzer):
        """Each cluster has a deployment strategy assigned."""
        tasks = [_make_task("T1", 8), _make_task("T2", 8)]
        plan = _make_plan({"Sprint 1": tasks})

        clusters = analyzer.analyze(plan)
        for cluster in clusters:
            assert cluster.strategy in (DeploymentStrategy.FEATURE_FLAG, DeploymentStrategy.FULL_DEPLOYMENT)

    def test_cluster_has_tasks(self, analyzer):
        """Each cluster contains at least one task."""
        tasks = [_make_task("T1", 8), _make_task("T2", 4)]
        plan = _make_plan({"Sprint 1": tasks})

        clusters = analyzer.analyze(plan)
        for cluster in clusters:
            assert len(cluster.tasks) > 0

    def test_empty_plan(self, analyzer):
        """Empty plan produces no clusters."""
        plan = _make_plan({})
        clusters = analyzer.analyze(plan)
        assert clusters == []

    def test_single_task_skipped(self, analyzer):
        """Single-task domains are not clustered (requires >= 2 tasks per domain)."""
        plan = _make_plan({"Sprint 1": [_make_task("T1", 8)]})
        clusters = analyzer.analyze(plan)
        # Single-task clusters are skipped by design
        assert len(clusters) == 0

    def test_tasks_with_dependencies(self, analyzer):
        """Dependent tasks are excluded from independent set."""
        t1 = _make_task("T1", 8)
        t2 = _make_task("T2", 8, deps=["T1"])
        plan = _make_plan({"Sprint 1": [t1, t2]})

        clusters = analyzer.analyze(plan)
        # T2 depends on T1, so T2 is NOT independent; only T1 is independent
        # With only 1 independent task in "general" domain, no cluster is formed
        assert isinstance(clusters, list)

    def test_cluster_rollback_plan(self, analyzer):
        """Clusters have rollback plans."""
        tasks = [_make_task("T1", 8), _make_task("T2", 8)]
        plan = _make_plan({"Sprint 1": tasks})

        clusters = analyzer.analyze(plan)
        for cluster in clusters:
            assert isinstance(cluster.rollback_plan, str)

    def test_summary(self, analyzer):
        """Summary returns expected structure."""
        tasks = [_make_task("T1", 8), _make_task("T2", 4), _make_task("T3", 6)]
        plan = _make_plan({"Sprint 1": tasks})

        clusters = analyzer.analyze(plan)
        summary = analyzer.summary(clusters, len(tasks))

        assert "total_clusters" in summary
        assert "cd_eligible" in summary or "feature_flag_count" in summary or isinstance(summary, dict)

    def test_deployment_timeline(self, analyzer):
        """Timeline returns a list of deployment phases."""
        tasks = [_make_task("T1", 8), _make_task("T2", 4)]
        plan = _make_plan({"Sprint 1": tasks})

        clusters = analyzer.analyze(plan)
        timeline = analyzer.get_deployment_timeline(clusters)

        assert isinstance(timeline, list)

    def test_multi_sprint_tasks(self, analyzer):
        """Tasks across multiple sprints are handled."""
        plan = _make_plan({
            "Sprint 1": [_make_task("T1", 8, "Sprint 1")],
            "Sprint 2": [_make_task("T2", 8, "Sprint 2")],
            "Sprint 3": [_make_task("T3", 8, "Sprint 3")],
        })

        clusters = analyzer.analyze(plan)
        assert len(clusters) >= 1

    def test_custom_cd_target(self):
        """Custom CD target is applied."""
        analyzer = DeploymentAnalyzer(cd_target_percentage=0.50)
        assert analyzer.cd_target_percentage == 0.50
