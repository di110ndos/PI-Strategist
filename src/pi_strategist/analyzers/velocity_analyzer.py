"""Velocity analyzer for sprint velocity metrics and trend detection."""

import math
from dataclasses import dataclass, field
from enum import Enum

from pi_strategist.models import Sprint


class VelocityTrend(Enum):
    """Direction of velocity trend across sprints."""

    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


@dataclass
class ConfidenceIntervals:
    """Confidence intervals for capacity estimates."""

    p50: float  # Median estimate
    p85: float  # 85th percentile (optimistic)
    p95: float  # 95th percentile (stretch)


@dataclass
class SprintVelocity:
    """Velocity metrics for a single sprint."""

    sprint_name: str
    capacity: float  # Net capacity hours
    load: float  # Actual load hours
    velocity_ratio: float  # load / capacity (1.0 = perfect match)
    unused_capacity: float  # capacity - load (negative if overloaded)


@dataclass
class VelocityAnalysis:
    """Complete velocity analysis result."""

    sprint_velocities: list[SprintVelocity] = field(default_factory=list)
    mean_velocity: float = 0.0
    velocity_std_dev: float = 0.0
    velocity_variance: float = 0.0
    trend: VelocityTrend = VelocityTrend.STABLE
    trend_slope: float = 0.0
    confidence_intervals: ConfidenceIntervals = field(
        default_factory=lambda: ConfidenceIntervals(p50=0.0, p85=0.0, p95=0.0)
    )
    sprint_count: int = 0


class VelocityAnalyzer:
    """Analyzer for sprint velocity and trend detection."""

    def __init__(self, trend_threshold: float = 0.02):
        """Initialize the velocity analyzer.

        Args:
            trend_threshold: Minimum slope magnitude to classify as
                improving or declining (default 0.02 per sprint).
        """
        self.trend_threshold = trend_threshold

    def analyze(self, sprints: list[Sprint]) -> VelocityAnalysis:
        """Analyze velocity across a list of sprints.

        Args:
            sprints: List of sprints with capacity and task data.

        Returns:
            VelocityAnalysis with metrics, trend, and confidence intervals.
        """
        if not sprints:
            return VelocityAnalysis()

        sprint_velocities = self._compute_sprint_velocities(sprints)
        ratios = [sv.velocity_ratio for sv in sprint_velocities]

        mean_vel = self._mean(ratios)
        variance = self._variance(ratios, mean_vel)
        std_dev = math.sqrt(variance)

        trend_slope = self._linear_regression_slope(ratios)
        trend = self._classify_trend(trend_slope)

        loads = [s.sprint_load for s in sprints]
        confidence = self._compute_confidence_intervals(loads)

        return VelocityAnalysis(
            sprint_velocities=sprint_velocities,
            mean_velocity=round(mean_vel, 4),
            velocity_std_dev=round(std_dev, 4),
            velocity_variance=round(variance, 4),
            trend=trend,
            trend_slope=round(trend_slope, 4),
            confidence_intervals=confidence,
            sprint_count=len(sprints),
        )

    def _compute_sprint_velocities(
        self, sprints: list[Sprint]
    ) -> list[SprintVelocity]:
        """Compute velocity metrics for each sprint."""
        results = []
        for sprint in sprints:
            capacity = sprint.net_capacity
            load = sprint.sprint_load
            ratio = (load / capacity) if capacity > 0 else 0.0
            results.append(
                SprintVelocity(
                    sprint_name=sprint.name,
                    capacity=round(capacity, 2),
                    load=round(load, 2),
                    velocity_ratio=round(ratio, 4),
                    unused_capacity=round(capacity - load, 2),
                )
            )
        return results

    @staticmethod
    def _mean(values: list[float]) -> float:
        """Calculate the arithmetic mean."""
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _variance(values: list[float], mean: float) -> float:
        """Calculate population variance."""
        if len(values) < 2:
            return 0.0
        return sum((v - mean) ** 2 for v in values) / len(values)

    @staticmethod
    def _linear_regression_slope(values: list[float]) -> float:
        """Compute slope of simple linear regression (y = values, x = index).

        Uses least-squares: slope = sum((xi - x_mean)(yi - y_mean)) / sum((xi - x_mean)^2)
        """
        n = len(values)
        if n < 2:
            return 0.0

        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0
        return numerator / denominator

    def _classify_trend(self, slope: float) -> VelocityTrend:
        """Classify the velocity trend based on regression slope."""
        if slope > self.trend_threshold:
            return VelocityTrend.IMPROVING
        elif slope < -self.trend_threshold:
            return VelocityTrend.DECLINING
        return VelocityTrend.STABLE

    def _compute_confidence_intervals(
        self, loads: list[float]
    ) -> ConfidenceIntervals:
        """Compute confidence intervals from historical load data.

        Uses sorted percentiles of actual load values to estimate
        future capacity needs at p50, p85, and p95 levels.
        """
        if not loads:
            return ConfidenceIntervals(p50=0.0, p85=0.0, p95=0.0)

        sorted_loads = sorted(loads)
        n = len(sorted_loads)

        p50 = self._percentile(sorted_loads, n, 0.50)
        p85 = self._percentile(sorted_loads, n, 0.85)
        p95 = self._percentile(sorted_loads, n, 0.95)

        return ConfidenceIntervals(
            p50=round(p50, 2),
            p85=round(p85, 2),
            p95=round(p95, 2),
        )

    @staticmethod
    def _percentile(sorted_values: list[float], n: int, p: float) -> float:
        """Calculate the p-th percentile using linear interpolation."""
        if n == 1:
            return sorted_values[0]

        rank = p * (n - 1)
        lower = int(rank)
        upper = min(lower + 1, n - 1)
        fraction = rank - lower

        return sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])
