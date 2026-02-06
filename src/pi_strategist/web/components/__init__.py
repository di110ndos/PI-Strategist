"""UI components for PI Strategist Web Application."""

from pi_strategist.web.components.red_flags_display import (
    render_red_flags,
    render_red_flags_table,
    render_quick_summary,
)
from pi_strategist.web.components.capacity_display import render_capacity_analysis
from pi_strategist.web.components.deployment_display import render_deployment_analysis
from pi_strategist.web.components.roadmap_display import render_roadmap, render_roadmap_summary
from pi_strategist.web.components.charts import (
    render_capacity_burndown_chart,
    render_utilization_trend_chart,
    render_risk_distribution_chart,
    render_risk_by_category_chart,
    render_resource_heatmap,
    render_allocation_distribution_chart,
    render_deployment_strategy_chart,
    render_cost_by_discipline_chart,
    render_sprint_cost_chart,
)

__all__ = [
    "render_red_flags",
    "render_red_flags_table",
    "render_quick_summary",
    "render_capacity_analysis",
    "render_deployment_analysis",
    "render_roadmap",
    "render_roadmap_summary",
    "render_capacity_burndown_chart",
    "render_utilization_trend_chart",
    "render_risk_distribution_chart",
    "render_risk_by_category_chart",
    "render_resource_heatmap",
    "render_allocation_distribution_chart",
    "render_deployment_strategy_chart",
    "render_cost_by_discipline_chart",
    "render_sprint_cost_chart",
]
