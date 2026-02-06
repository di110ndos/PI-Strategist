"""Plotly chart components for PI Strategist dashboards."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from pi_strategist.models import (
    DeploymentCluster,
    RedFlag,
    RedFlagSeverity,
)
from pi_strategist.web.theme import (
    AMBER,
    BLUE,
    BORDER,
    CHART_PALETTE,
    CYAN,
    GREEN,
    RED,
    SEVERITY_CONFIG,
    STRATEGY_COLORS,
    TEXT_DIM,
    TEXT_MUTED,
    TEXT_PRIMARY,
    VIOLET,
    plotly_layout,
)

# ─── Capacity Charts ─────────────────────────────────────────────


def render_capacity_burndown_chart(analyses) -> None:
    """Grouped bar chart: net capacity vs sprint load per sprint.

    Args:
        analyses: list[SprintAnalysis] from capacity_analyzer.
    """
    if not analyses:
        return

    sprint_names = [a.sprint.name for a in analyses]
    capacities = [a.sprint.net_capacity for a in analyses]
    loads = [a.sprint.sprint_load for a in analyses]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Net Capacity",
        x=sprint_names,
        y=capacities,
        marker_color=CYAN,
        marker_line=dict(width=0),
        opacity=0.85,
    ))

    fig.add_trace(go.Bar(
        name="Sprint Load",
        x=sprint_names,
        y=loads,
        marker_color=[RED if ld > cap else BLUE for ld, cap in zip(loads, capacities)],
        marker_line=dict(width=0),
        opacity=0.85,
    ))

    fig.update_layout(
        **plotly_layout(
            barmode="group",
            yaxis=dict(title="Hours", gridcolor=BORDER),
            xaxis=dict(title=""),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=350,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_utilization_trend_chart(analyses) -> None:
    """Line chart showing utilization % across sprints with threshold bands.

    Args:
        analyses: list[SprintAnalysis] from capacity_analyzer.
    """
    if not analyses:
        return

    sprint_names = [a.sprint.name for a in analyses]
    utilizations = [a.utilization_percent for a in analyses]

    fig = go.Figure()

    # Threshold bands
    fig.add_hrect(y0=0, y1=80, fillcolor=GREEN, opacity=0.05, line_width=0)
    fig.add_hrect(y0=80, y1=100, fillcolor=AMBER, opacity=0.05, line_width=0)
    fig.add_hrect(y0=100, y1=max(max(utilizations, default=100) + 10, 120),
                  fillcolor=RED, opacity=0.05, line_width=0)

    # 100% threshold line
    fig.add_hline(y=100, line_dash="dash", line_color=RED, opacity=0.5,
                  annotation_text="100% capacity", annotation_position="top right",
                  annotation_font_color=TEXT_DIM)

    # Utilization line
    fig.add_trace(go.Scatter(
        x=sprint_names,
        y=utilizations,
        mode="lines+markers+text",
        text=[f"{u:.0f}%" for u in utilizations],
        textposition="top center",
        textfont=dict(color=TEXT_MUTED, size=11),
        line=dict(color=CYAN, width=3),
        marker=dict(
            size=10,
            color=[GREEN if u <= 80 else AMBER if u <= 100 else RED for u in utilizations],
            line=dict(color=CYAN, width=2),
        ),
        name="Utilization",
    ))

    fig.update_layout(
        **plotly_layout(
            yaxis=dict(title="Utilization %", gridcolor=BORDER, range=[0, max(max(utilizations, default=100) + 15, 120)]),
            xaxis=dict(title=""),
            showlegend=False,
            height=300,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


# ─── Red Flag Charts ─────────────────────────────────────────────


def render_risk_distribution_chart(red_flags: list[RedFlag]) -> None:
    """Donut chart showing red flag severity distribution.

    Args:
        red_flags: List of detected red flags.
    """
    if not red_flags:
        return

    counts = {
        "Critical": len([rf for rf in red_flags if rf.severity == RedFlagSeverity.CRITICAL]),
        "Moderate": len([rf for rf in red_flags if rf.severity == RedFlagSeverity.MODERATE]),
        "Low": len([rf for rf in red_flags if rf.severity == RedFlagSeverity.LOW]),
    }

    # Filter out zero counts
    labels = [k for k, v in counts.items() if v > 0]
    values = [v for v in counts.values() if v > 0]
    colors = []
    for label in labels:
        severity = {"Critical": RedFlagSeverity.CRITICAL, "Moderate": RedFlagSeverity.MODERATE, "Low": RedFlagSeverity.LOW}[label]
        colors.append(SEVERITY_CONFIG[severity]["color"])

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color=BORDER, width=2)),
        textinfo="label+value",
        textfont=dict(color=TEXT_PRIMARY, size=13),
        hovertemplate="%{label}: %{value} issues<extra></extra>",
    )])

    fig.update_layout(
        **plotly_layout(
            showlegend=False,
            height=280,
            margin=dict(l=20, r=20, t=20, b=20),
            annotations=[dict(
                text=f"<b>{len(red_flags)}</b><br><span style='font-size:11px;color:{TEXT_MUTED}'>total</span>",
                x=0.5, y=0.5, font_size=22, showarrow=False, font_color=TEXT_PRIMARY,
            )],
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_risk_by_category_chart(red_flags: list[RedFlag]) -> None:
    """Horizontal bar chart of red flags grouped by category.

    Args:
        red_flags: List of detected red flags.
    """
    if not red_flags:
        return

    categories: dict[str, dict[str, int]] = {}
    for rf in red_flags:
        cat = rf.category
        sev = rf.severity.value
        if cat not in categories:
            categories[cat] = {"critical": 0, "moderate": 0, "low": 0}
        categories[cat][sev] += 1

    sorted_cats = sorted(categories.keys(), key=lambda c: sum(categories[c].values()), reverse=True)

    fig = go.Figure()

    for sev_name, sev_color in [("critical", RED), ("moderate", AMBER), ("low", BLUE)]:
        fig.add_trace(go.Bar(
            name=sev_name.title(),
            y=sorted_cats,
            x=[categories[c][sev_name] for c in sorted_cats],
            orientation="h",
            marker_color=sev_color,
            opacity=0.85,
        ))

    fig.update_layout(
        **plotly_layout(
            barmode="stack",
            height=max(200, len(sorted_cats) * 35 + 80),
            xaxis=dict(title="Count", gridcolor=BORDER),
            yaxis=dict(title="", autorange="reversed"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=160, r=40, t=40, b=40),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


# ─── Resource Charts ──────────────────────────────────────────────


def render_resource_heatmap(analysis) -> None:
    """Heatmap of resource allocation across sprints.

    Args:
        analysis: PIAnalysis object with resources and sprints.
    """
    if not analysis.resources or not analysis.sprints:
        return

    sprint_names = sorted(analysis.sprints)
    resource_names = sorted(analysis.resources.keys(),
                            key=lambda n: -analysis.resources[n].total_hours)[:25]

    z_data = []
    hover_text = []
    for rname in resource_names:
        resource = analysis.resources[rname]
        row = []
        hover_row = []
        for sprint in sprint_names:
            hours = resource.sprint_hours.get(sprint, 0)
            row.append(hours)
            hover_row.append(f"{rname}<br>{sprint}: {hours:.0f}h")
        z_data.append(row)
        hover_text.append(hover_row)

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=sprint_names,
        y=resource_names,
        hovertext=hover_text,
        hovertemplate="%{hovertext}<extra></extra>",
        colorscale=[
            [0.0, "#1a1a2e"],
            [0.2, "#16213e"],
            [0.4, BLUE],
            [0.6, CYAN],
            [0.8, "#4ade80"],
            [1.0, GREEN],
        ],
        colorbar=dict(
            title="Hours",
            titlefont=dict(color=TEXT_MUTED),
            tickfont=dict(color=TEXT_DIM),
        ),
    ))

    fig.update_layout(
        **plotly_layout(
            height=max(300, len(resource_names) * 22 + 80),
            xaxis=dict(title="", side="top"),
            yaxis=dict(title="", autorange="reversed"),
            margin=dict(l=160, r=40, t=60, b=20),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_allocation_distribution_chart(analysis) -> None:
    """Histogram showing distribution of resource allocation percentages.

    Args:
        analysis: PIAnalysis object with resources.
    """
    if not analysis.resources:
        return

    PI_MAX = 488.0
    percentages = [
        (r.total_hours / PI_MAX) * 100
        for r in analysis.resources.values()
        if r.total_hours > 0
    ]

    if not percentages:
        return

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=percentages,
        nbinsx=15,
        marker_color=CYAN,
        marker_line=dict(color=BORDER, width=1),
        opacity=0.85,
        hovertemplate="Range: %{x}%<br>Count: %{y}<extra></extra>",
    ))

    # Threshold lines
    fig.add_vline(x=80, line_dash="dash", line_color=AMBER, opacity=0.6,
                  annotation_text="80%", annotation_position="top",
                  annotation_font_color=AMBER)
    fig.add_vline(x=105, line_dash="dash", line_color=RED, opacity=0.6,
                  annotation_text="105%", annotation_position="top",
                  annotation_font_color=RED)

    fig.update_layout(
        **plotly_layout(
            xaxis=dict(title="Allocation %", gridcolor=BORDER),
            yaxis=dict(title="Resources", gridcolor=BORDER),
            showlegend=False,
            height=280,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


# ─── Deployment Charts ───────────────────────────────────────────


def render_deployment_strategy_chart(clusters: list[DeploymentCluster]) -> None:
    """Pie chart of deployment strategies.

    Args:
        clusters: List of deployment clusters.
    """
    if not clusters:
        return

    strategy_counts: dict[str, int] = {}
    strategy_tasks: dict[str, int] = {}
    for cluster in clusters:
        name = cluster.strategy.value.replace("_", " ").title()
        strategy_counts[name] = strategy_counts.get(name, 0) + 1
        strategy_tasks[name] = strategy_tasks.get(name, 0) + len(cluster.tasks)

    labels = list(strategy_tasks.keys())
    values = list(strategy_tasks.values())
    colors = []
    for cluster in clusters:
        name = cluster.strategy.value.replace("_", " ").title()
        if name in labels and name not in [c for c, _ in zip(colors, range(len(colors)))]:
            colors.append(STRATEGY_COLORS.get(cluster.strategy, VIOLET))
    # Deduplicate to match labels
    color_map = {}
    for cluster in clusters:
        name = cluster.strategy.value.replace("_", " ").title()
        color_map[name] = STRATEGY_COLORS.get(cluster.strategy, VIOLET)
    colors = [color_map[l] for l in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker=dict(colors=colors, line=dict(color=BORDER, width=2)),
        textinfo="label+value",
        textfont=dict(color=TEXT_PRIMARY),
        hovertemplate="%{label}: %{value} tasks<extra></extra>",
    )])

    total_tasks = sum(values)
    fig.update_layout(
        **plotly_layout(
            showlegend=False,
            height=280,
            margin=dict(l=20, r=20, t=20, b=20),
            annotations=[dict(
                text=f"<b>{total_tasks}</b><br><span style='font-size:11px;color:{TEXT_MUTED}'>tasks</span>",
                x=0.5, y=0.5, font_size=22, showarrow=False, font_color=TEXT_PRIMARY,
            )],
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


# ─── Financial Charts ────────────────────────────────────────────


def render_cost_by_discipline_chart(analysis) -> None:
    """Horizontal bar chart of costs broken down by discipline.

    Args:
        analysis: PIAnalysis object with resources.
    """
    if not analysis.resources:
        return

    discipline_cost: dict[str, float] = {}
    for resource in analysis.resources.values():
        disc = resource.discipline or "Other"
        cost = resource.total_hours * resource.rate if resource.rate > 0 else 0
        discipline_cost[disc] = discipline_cost.get(disc, 0) + cost

    # Filter out zero cost
    discipline_cost = {k: v for k, v in discipline_cost.items() if v > 0}
    if not discipline_cost:
        return

    sorted_items = sorted(discipline_cost.items(), key=lambda x: x[1], reverse=True)
    labels = [k for k, _ in sorted_items]
    values = [v for _, v in sorted_items]

    # Cycle through palette
    colors = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(labels))]

    fig = go.Figure(data=[go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker_color=colors,
        marker_line=dict(width=0),
        opacity=0.85,
        text=[f"${v:,.0f}" for v in values],
        textposition="auto",
        textfont=dict(color=TEXT_PRIMARY, size=11),
        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
    )])

    fig.update_layout(
        **plotly_layout(
            height=max(200, len(labels) * 35 + 80),
            xaxis=dict(title="Cost ($)", gridcolor=BORDER),
            yaxis=dict(title="", autorange="reversed"),
            showlegend=False,
            margin=dict(l=160, r=40, t=20, b=40),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_sprint_cost_chart(analysis) -> None:
    """Bar chart of cost per sprint.

    Args:
        analysis: PIAnalysis object with resources and sprints.
    """
    if not analysis.resources or not analysis.sprints:
        return

    sprint_costs: dict[str, float] = {}
    for sprint_name in sorted(analysis.sprints):
        sprint_costs[sprint_name] = 0
        for resource in analysis.resources.values():
            hours = resource.sprint_hours.get(sprint_name, 0)
            if resource.rate > 0 and hours > 0:
                sprint_costs[sprint_name] += hours * resource.rate

    if not any(sprint_costs.values()):
        return

    labels = list(sprint_costs.keys())
    values = list(sprint_costs.values())

    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker_color=CYAN,
        marker_line=dict(width=0),
        opacity=0.85,
        text=[f"${v:,.0f}" for v in values],
        textposition="outside",
        textfont=dict(color=TEXT_MUTED, size=11),
        hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
    )])

    fig.update_layout(
        **plotly_layout(
            yaxis=dict(title="Cost ($)", gridcolor=BORDER),
            xaxis=dict(title=""),
            showlegend=False,
            height=300,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)
