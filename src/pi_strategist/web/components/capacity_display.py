"""Capacity analysis visualization component."""

import streamlit as st
from typing import Optional

from pi_strategist.models import SprintStatus
from pi_strategist.analyzers.capacity_analyzer import SprintAnalysis, CapacityRecommendation
from pi_strategist.web.theme import COLORS, PRIORITY_COLORS, BORDER
from pi_strategist.web.components.charts import (
    render_capacity_burndown_chart,
    render_utilization_trend_chart,
)
from pi_strategist.reporters.csv_export import capacity_to_csv, render_csv_download


def render_capacity_analysis(
    analyses: list[SprintAnalysis],
    summary: Optional[dict] = None,
) -> None:
    """Render the capacity analysis display.

    Args:
        analyses: List of sprint analyses to display
        summary: Optional summary dictionary
    """
    if not analyses:
        st.warning("No capacity data to display.")
        return

    # Summary metrics
    _render_summary_metrics(analyses, summary)

    st.markdown("---")

    # Charts
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Capacity vs Load")
        render_capacity_burndown_chart(analyses)
    with chart_col2:
        st.markdown("#### Utilization Trend")
        render_utilization_trend_chart(analyses)

    st.markdown("---")

    # Sprint cards
    st.subheader("Sprint Details")
    _render_sprint_cards(analyses)

    # Recommendations
    all_recommendations = []
    for analysis in analyses:
        all_recommendations.extend(analysis.recommendations)

    if all_recommendations:
        st.markdown("---")
        st.subheader("Recommendations")
        _render_recommendations(all_recommendations)

    # CSV export
    st.markdown("---")
    render_csv_download(capacity_to_csv(analyses), "capacity_analysis.csv", "Download Capacity CSV")


def _render_summary_metrics(
    analyses: list[SprintAnalysis],
    summary: Optional[dict] = None,
) -> None:
    """Render summary metric cards."""
    if summary is None:
        # Calculate summary
        total = len(analyses)
        passing = sum(1 for a in analyses if a.status == SprintStatus.PASS)
        failing = total - passing
        total_capacity = sum(a.sprint.net_capacity for a in analyses)
        total_load = sum(a.sprint.sprint_load for a in analyses)
        utilization = (total_load / total_capacity * 100) if total_capacity > 0 else 0
    else:
        total = summary.get("total_sprints", len(analyses))
        passing = summary.get("passing_sprints", 0)
        failing = summary.get("failing_sprints", 0)
        utilization = summary.get("overall_utilization", 0)
        total_capacity = summary.get("total_capacity_hours", 0)
        total_load = summary.get("total_load_hours", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Sprints",
            value=total,
        )

    with col2:
        st.metric(
            label="Passing",
            value=passing,
            delta=None,
        )
        if passing == total:
            st.markdown(
                f'<span style="color: {COLORS["pass"]}">● All sprints within capacity</span>',
                unsafe_allow_html=True,
            )

    with col3:
        st.metric(
            label="Overloaded",
            value=failing,
            delta=None,
        )
        if failing > 0:
            st.markdown(
                f'<span style="color: {COLORS["fail"]}">● Requires attention</span>',
                unsafe_allow_html=True,
            )

    with col4:
        st.metric(
            label="Overall Utilization",
            value=f"{utilization:.1f}%",
        )
        if utilization > 100:
            st.markdown(
                f'<span style="color: {COLORS["fail"]}">● Over capacity</span>',
                unsafe_allow_html=True,
            )
        elif utilization > 80:
            st.markdown(
                f'<span style="color: {COLORS["warning"]}">● Near capacity</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<span style="color: {COLORS["pass"]}">● Healthy</span>',
                unsafe_allow_html=True,
            )


def _render_sprint_cards(analyses: list[SprintAnalysis]) -> None:
    """Render individual sprint cards."""
    # Create columns for sprints (2 per row)
    for i in range(0, len(analyses), 2):
        cols = st.columns(2)

        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(analyses):
                with col:
                    _render_sprint_card(analyses[idx])


def _render_sprint_card(analysis: SprintAnalysis) -> None:
    """Render a single sprint card."""
    sprint = analysis.sprint
    status_color = COLORS["pass"] if analysis.status == SprintStatus.PASS else COLORS["fail"]
    status_text = "PASS" if analysis.status == SprintStatus.PASS else "FAIL"

    with st.container():
        # Header with status badge
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(sprint.name)

        with col2:
            st.markdown(
                f'<span style="background-color: {status_color}; color: white; '
                f'padding: 4px 12px; border-radius: 4px; font-weight: bold;">'
                f"{status_text}</span>",
                unsafe_allow_html=True,
            )

        # Progress bar
        utilization = analysis.utilization_percent
        progress_color = (
            COLORS["pass"]
            if utilization <= 80
            else COLORS["warning"]
            if utilization <= 100
            else COLORS["fail"]
        )

        st.markdown(
            f"""
            <div style="background-color: {BORDER}; border-radius: 10px; height: 20px; margin: 10px 0;">
                <div style="background-color: {progress_color}; width: {min(utilization, 100)}%;
                     height: 100%; border-radius: 10px;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Capacity details
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Net Capacity",
                value=f"{sprint.net_capacity:.1f}h",
                help=f"Total: {sprint.total_hours:.1f}h - Buffer: {sprint.buffer_hours:.1f}h",
            )

        with col2:
            st.metric(
                label="Sprint Load",
                value=f"{sprint.sprint_load:.1f}h",
            )

        with col3:
            overflow = analysis.overflow_hours
            delta_str = f"+{overflow:.1f}h" if overflow > 0 else f"{overflow:.1f}h"
            st.metric(
                label="Overflow",
                value=f"{overflow:.1f}h",
                delta=delta_str if overflow != 0 else None,
                delta_color="inverse" if overflow > 0 else "normal",
            )

        # Task count
        st.caption(f"Tasks: {len(sprint.tasks)} | Utilization: {utilization:.1f}%")

        # High risk tasks
        if analysis.high_risk_tasks:
            with st.expander(f"High Risk Tasks ({len(analysis.high_risk_tasks)})"):
                for task in analysis.high_risk_tasks:
                    st.write(f"- **{task.id}**: {task.name} ({task.hours}h)")

        st.markdown("---")


def _render_recommendations(recommendations: list[CapacityRecommendation]) -> None:
    """Render capacity recommendations."""
    # Sort by priority
    sorted_recs = sorted(recommendations, key=lambda r: r.priority)

    priority_labels = {1: "High", 2: "Medium", 3: "Low"}

    for rec in sorted_recs:
        priority_label = priority_labels.get(rec.priority, "Unknown")
        priority_color = PRIORITY_COLORS.get(rec.priority, "#666")

        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(
                    f"**Move task `{rec.task.id}`** from {rec.from_sprint} → {rec.to_sprint}"
                )
                st.caption(rec.reason)
                st.caption(f"Task: {rec.task.name} ({rec.task.hours}h)")

            with col2:
                st.markdown(
                    f'<span style="color: {priority_color}; font-weight: bold;">'
                    f"Priority: {priority_label}</span>",
                    unsafe_allow_html=True,
                )

            st.markdown("---")


def render_capacity_table(analyses: list[SprintAnalysis]) -> None:
    """Render capacity data in a table format."""
    if not analyses:
        st.info("No capacity data to display.")
        return

    data = []
    for analysis in analyses:
        sprint = analysis.sprint
        data.append(
            {
                "Sprint": sprint.name,
                "Status": "PASS" if analysis.status == SprintStatus.PASS else "FAIL",
                "Net Capacity": f"{sprint.net_capacity:.1f}h",
                "Sprint Load": f"{sprint.sprint_load:.1f}h",
                "Utilization": f"{analysis.utilization_percent:.1f}%",
                "Overflow": f"{analysis.overflow_hours:.1f}h",
                "Tasks": len(sprint.tasks),
            }
        )

    st.dataframe(data, use_container_width=True)
