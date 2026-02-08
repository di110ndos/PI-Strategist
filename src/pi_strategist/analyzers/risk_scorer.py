"""Composite risk scorer for PI-level risk assessment."""

from dataclasses import dataclass, field
from enum import Enum

from pi_strategist.models import RedFlag, RedFlagSeverity
from pi_strategist.analyzers.capacity_analyzer import SprintAnalysis
from pi_strategist.analyzers.resource_analyzer import ResourceAnalysis


class RiskLevel(Enum):
    """Overall PI risk classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskFactor:
    """Individual risk factor contributing to the composite score."""

    name: str
    raw_value: float  # The measured value before weighting
    weighted_score: float  # Contribution to composite score (0-100 scale portion)
    weight: float  # Weight used for this factor
    description: str = ""


@dataclass
class RiskScoreResult:
    """Complete risk scoring result."""

    overall_score: float = 0.0  # Composite score 0-100
    risk_level: RiskLevel = RiskLevel.LOW
    factor_breakdown: list[RiskFactor] = field(default_factory=list)
    top_risk_factors: list[str] = field(default_factory=list)


# Default weights for each risk factor (must sum to 1.0)
DEFAULT_WEIGHTS = {
    "red_flags": 0.25,
    "capacity_overrun": 0.25,
    "velocity_variance": 0.15,
    "resource_over_allocation": 0.20,
    "dependency_complexity": 0.15,
}


class RiskScorer:
    """Composite risk scorer combining multiple analysis dimensions."""

    def __init__(self, weights: dict[str, float] | None = None):
        """Initialize the risk scorer.

        Args:
            weights: Optional custom weights for risk factors.
                Keys must match DEFAULT_WEIGHTS. Values must sum to 1.0.
        """
        self.weights = weights or DEFAULT_WEIGHTS

    def score(
        self,
        red_flags: list[RedFlag] | None = None,
        capacity_analyses: list[SprintAnalysis] | None = None,
        resource_analysis: ResourceAnalysis | None = None,
        velocity_variance: float = 0.0,
        dependency_count: int = 0,
        total_tasks: int = 0,
    ) -> RiskScoreResult:
        """Calculate composite PI risk score.

        Args:
            red_flags: List of detected red flags.
            capacity_analyses: Sprint capacity analysis results.
            resource_analysis: Resource utilization analysis result.
            velocity_variance: Velocity variance from VelocityAnalyzer.
            dependency_count: Total inter-task dependency count.
            total_tasks: Total number of tasks in the PI.

        Returns:
            RiskScoreResult with overall score, level, and breakdown.
        """
        factors: list[RiskFactor] = []

        # Factor 1: Red flag severity score
        rf_score = self._score_red_flags(red_flags or [])
        factors.append(RiskFactor(
            name="red_flags",
            raw_value=rf_score,
            weighted_score=rf_score * self.weights["red_flags"],
            weight=self.weights["red_flags"],
            description=self._red_flag_description(red_flags or []),
        ))

        # Factor 2: Capacity overrun
        cap_score = self._score_capacity_overrun(capacity_analyses or [])
        factors.append(RiskFactor(
            name="capacity_overrun",
            raw_value=cap_score,
            weighted_score=cap_score * self.weights["capacity_overrun"],
            weight=self.weights["capacity_overrun"],
            description=self._capacity_description(capacity_analyses or []),
        ))

        # Factor 3: Velocity variance
        vel_score = self._score_velocity_variance(velocity_variance)
        factors.append(RiskFactor(
            name="velocity_variance",
            raw_value=vel_score,
            weighted_score=vel_score * self.weights["velocity_variance"],
            weight=self.weights["velocity_variance"],
            description=f"Velocity variance: {velocity_variance:.4f}",
        ))

        # Factor 4: Resource over-allocation
        res_score = self._score_resource_over_allocation(resource_analysis)
        factors.append(RiskFactor(
            name="resource_over_allocation",
            raw_value=res_score,
            weighted_score=res_score * self.weights["resource_over_allocation"],
            weight=self.weights["resource_over_allocation"],
            description=self._resource_description(resource_analysis),
        ))

        # Factor 5: Dependency complexity
        dep_score = self._score_dependency_complexity(dependency_count, total_tasks)
        factors.append(RiskFactor(
            name="dependency_complexity",
            raw_value=dep_score,
            weighted_score=dep_score * self.weights["dependency_complexity"],
            weight=self.weights["dependency_complexity"],
            description=f"{dependency_count} dependencies across {total_tasks} tasks",
        ))

        overall = sum(f.weighted_score for f in factors)
        overall = max(0.0, min(100.0, overall))  # Clamp to 0-100

        risk_level = self._classify_risk(overall)

        # Top risk factors sorted by weighted contribution
        sorted_factors = sorted(factors, key=lambda f: -f.weighted_score)
        top_names = [f"{f.name} ({f.weighted_score:.1f})" for f in sorted_factors[:3]]

        return RiskScoreResult(
            overall_score=round(overall, 1),
            risk_level=risk_level,
            factor_breakdown=factors,
            top_risk_factors=top_names,
        )

    # --- Individual factor scoring (each returns 0-100) ---

    def _score_red_flags(self, red_flags: list[RedFlag]) -> float:
        """Score red flags on a 0-100 scale based on count and severity."""
        if not red_flags:
            return 0.0

        severity_weights = {
            RedFlagSeverity.CRITICAL: 15.0,
            RedFlagSeverity.MODERATE: 8.0,
            RedFlagSeverity.LOW: 3.0,
        }

        total = sum(severity_weights.get(rf.severity, 3.0) for rf in red_flags)
        # Cap at 100; ~7 critical flags saturate the score
        return min(100.0, total)

    def _score_capacity_overrun(
        self, analyses: list[SprintAnalysis]
    ) -> float:
        """Score capacity overrun on a 0-100 scale."""
        if not analyses:
            return 0.0

        total_capacity = sum(a.sprint.net_capacity for a in analyses)
        total_overflow = sum(max(0, a.overflow_hours) for a in analyses)

        if total_capacity <= 0:
            return 0.0

        overrun_pct = (total_overflow / total_capacity) * 100
        # Scale: 0% overrun = 0, 50%+ overrun = 100
        return min(100.0, overrun_pct * 2)

    def _score_velocity_variance(self, variance: float) -> float:
        """Score velocity variance on a 0-100 scale.

        Higher variance means less predictable delivery.
        Variance of 0.04 (~0.2 std dev in velocity ratio) is the saturation point.
        """
        # Scale: 0 variance = 0, 0.04+ variance = 100
        return min(100.0, (variance / 0.04) * 100)

    def _score_resource_over_allocation(
        self, analysis: ResourceAnalysis | None
    ) -> float:
        """Score resource over-allocation on a 0-100 scale."""
        if not analysis or analysis.total_resources == 0:
            return 0.0

        over_count = len(analysis.over_allocated)
        ratio = over_count / analysis.total_resources
        # Scale: 0% over-allocated = 0, 50%+ = 100
        base = min(100.0, ratio * 200)

        # Bonus for bottlenecks
        bottleneck_bonus = min(20.0, len(analysis.bottleneck_warnings) * 10.0)

        return min(100.0, base + bottleneck_bonus)

    def _score_dependency_complexity(
        self, dep_count: int, total_tasks: int
    ) -> float:
        """Score dependency complexity on a 0-100 scale."""
        if total_tasks == 0:
            return 0.0

        dep_ratio = dep_count / total_tasks
        # Scale: 0 deps/task = 0, 2+ deps/task = 100
        return min(100.0, dep_ratio * 50)

    # --- Classification and descriptions ---

    @staticmethod
    def _classify_risk(score: float) -> RiskLevel:
        """Classify overall risk score into a risk level."""
        if score <= 30:
            return RiskLevel.LOW
        elif score <= 60:
            return RiskLevel.MEDIUM
        elif score <= 80:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    @staticmethod
    def _red_flag_description(red_flags: list[RedFlag]) -> str:
        """Build a human-readable description of red flag counts."""
        if not red_flags:
            return "No red flags detected"
        by_severity: dict[str, int] = {}
        for rf in red_flags:
            key = rf.severity.value
            by_severity[key] = by_severity.get(key, 0) + 1
        parts = [f"{count} {sev}" for sev, count in by_severity.items()]
        return f"{len(red_flags)} red flags ({', '.join(parts)})"

    @staticmethod
    def _capacity_description(analyses: list[SprintAnalysis]) -> str:
        """Build a human-readable description of capacity status."""
        if not analyses:
            return "No capacity data"
        failing = sum(1 for a in analyses if a.overflow_hours > 0)
        return f"{failing}/{len(analyses)} sprints over capacity"

    @staticmethod
    def _resource_description(analysis: ResourceAnalysis | None) -> str:
        """Build a human-readable description of resource allocation."""
        if not analysis:
            return "No resource data"
        return (
            f"{len(analysis.over_allocated)} over-allocated, "
            f"{len(analysis.under_allocated)} under-allocated, "
            f"{len(analysis.bottleneck_warnings)} bottlenecks"
        )
