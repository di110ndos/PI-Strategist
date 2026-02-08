"""Tests for the capacity analyzer."""

import pytest

from pi_strategist.analyzers.capacity_analyzer import CapacityAnalyzer
from pi_strategist.models import (
    CapacityPlan,
    Sprint,
    Task,
    SprintStatus,
    RedFlag,
    RedFlagSeverity,
    AcceptanceCriteria,
)


def _make_task(id: str, hours: float, sprint: str = "Sprint 1") -> Task:
    return Task(id=id, name=f"Task {id}", hours=hours, sprint=sprint)


def _make_sprint(name: str, total_hours: float, tasks: list[Task] | None = None) -> Sprint:
    return Sprint(name=name, total_hours=total_hours, tasks=tasks or [])


def _make_plan(sprints: list[Sprint]) -> CapacityPlan:
    return CapacityPlan(filename="test.xlsx", sprints=sprints)


class TestCapacityAnalyzer:
    """Tests for CapacityAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        return CapacityAnalyzer(default_buffer=0.20)

    def test_passing_sprint(self, analyzer):
        """Sprint under net capacity should pass."""
        tasks = [_make_task("T1", 30), _make_task("T2", 30)]
        sprint = _make_sprint("Sprint 1", 100, tasks)
        plan = _make_plan([sprint])

        results = analyzer.analyze(plan)
        assert len(results) == 1
        assert results[0].status == SprintStatus.PASS

    def test_failing_sprint(self, analyzer):
        """Sprint over net capacity should fail."""
        tasks = [_make_task("T1", 50), _make_task("T2", 50)]
        sprint = _make_sprint("Sprint 1", 100, tasks)  # net = 80, load = 100
        plan = _make_plan([sprint])

        results = analyzer.analyze(plan)
        assert len(results) == 1
        assert results[0].status == SprintStatus.FAIL

    def test_utilization_percent(self, analyzer):
        """Utilization should be load / net_capacity * 100."""
        tasks = [_make_task("T1", 40)]
        sprint = _make_sprint("Sprint 1", 100, tasks)  # net = 80, load = 40
        plan = _make_plan([sprint])

        results = analyzer.analyze(plan)
        assert results[0].utilization_percent == pytest.approx(50.0)

    def test_overflow_hours(self, analyzer):
        """Overflow should be positive when over capacity."""
        tasks = [_make_task("T1", 90)]
        sprint = _make_sprint("Sprint 1", 100, tasks)  # net = 80, overflow = 10
        plan = _make_plan([sprint])

        results = analyzer.analyze(plan)
        assert results[0].overflow_hours == pytest.approx(10.0)

    def test_multiple_sprints(self, analyzer):
        """Analyzer handles multiple sprints."""
        s1 = _make_sprint("Sprint 1", 100, [_make_task("T1", 40)])
        s2 = _make_sprint("Sprint 2", 100, [_make_task("T2", 90)])
        plan = _make_plan([s1, s2])

        results = analyzer.analyze(plan)
        assert len(results) == 2
        assert results[0].status == SprintStatus.PASS
        assert results[1].status == SprintStatus.FAIL

    def test_empty_plan(self, analyzer):
        """Empty plan produces no results."""
        plan = _make_plan([])
        results = analyzer.analyze(plan)
        assert results == []

    def test_empty_sprint(self, analyzer):
        """Sprint with no tasks should pass."""
        sprint = _make_sprint("Sprint 1", 100, [])
        plan = _make_plan([sprint])

        results = analyzer.analyze(plan)
        assert results[0].status == SprintStatus.PASS
        assert results[0].utilization_percent == pytest.approx(0.0)

    def test_with_red_flags(self, analyzer):
        """Red flags mark tasks as high-risk."""
        task = _make_task("T1", 40)
        sprint = _make_sprint("Sprint 1", 100, [task])
        plan = _make_plan([sprint])

        ac = AcceptanceCriteria(id="AC-1", text="must be fast")
        red_flag = RedFlag(
            ac=ac,
            flagged_term="fast",
            category="subjective",
            severity=RedFlagSeverity.CRITICAL,
            suggested_metric="Response time < 200ms",
            negotiation_script="What does fast mean?",
        )

        results = analyzer.analyze(plan, [red_flag])
        assert len(results) == 1

    def test_summary(self, analyzer):
        """Summary returns expected keys."""
        s1 = _make_sprint("Sprint 1", 100, [_make_task("T1", 40)])
        s2 = _make_sprint("Sprint 2", 100, [_make_task("T2", 90)])
        plan = _make_plan([s1, s2])

        results = analyzer.analyze(plan)
        summary = analyzer.summary(results)

        assert "total_sprints" in summary
        assert "passing_sprints" in summary
        assert "failing_sprints" in summary
        assert summary["total_sprints"] == 2

    def test_custom_buffer(self):
        """Custom buffer percentage is applied via Sprint."""
        analyzer = CapacityAnalyzer(default_buffer=0.10)
        tasks = [_make_task("T1", 85)]
        # Sprint's own buffer_percentage controls capacity, not analyzer's default
        sprint = Sprint(name="Sprint 1", total_hours=100, buffer_percentage=0.10, tasks=tasks)
        plan = _make_plan([sprint])

        results = analyzer.analyze(plan)
        # net = 100 * (1 - 0.10) = 90, load = 85 → pass
        assert results[0].status == SprintStatus.PASS

    def test_validate_capacity(self, analyzer):
        """Static capacity validation works."""
        status, overflow = analyzer.validate_capacity(100, 70, 0.20)
        assert status == SprintStatus.PASS
        assert overflow < 0

        status, overflow = analyzer.validate_capacity(100, 90, 0.20)
        assert status == SprintStatus.FAIL
        assert overflow > 0
