"""Comprehensive PI Planning Dashboard Component."""

import streamlit as st
from typing import Optional
from dataclasses import dataclass

# Try to import plotly for advanced charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# Standard PI capacity per resource (4 sprints × 2 weeks × ~61 hours/week)
PI_HOURS_PER_RESOURCE = 488.0


@dataclass
class PIMetrics:
    """Aggregated PI metrics for dashboard display."""
    total_capacity_hours: float = 0.0  # Based on 488h per resource
    total_allocated_hours: float = 0.0
    total_remaining_hours: float = 0.0
    total_cost: float = 0.0
    num_sprints: int = 0
    num_resources: int = 0
    num_projects: int = 0
    utilization_percent: float = 0.0
    overallocated_count: int = 0


def render_pi_dashboard(analysis, plan) -> None:
    """Render comprehensive PI planning dashboard.

    Args:
        analysis: PIAnalysis object from parser
        plan: CapacityPlan object
    """
    # Calculate metrics
    metrics = _calculate_metrics(analysis)

    # Executive Summary
    _render_executive_summary(metrics, analysis)

    st.markdown("---")

    # Create tabs for different views
    tabs = st.tabs([
        "📊 Resource Summary",
        "📈 Sprint Capacity",
        "💼 Projects",
        "💰 Financial",
        "🗓️ Timeline",
        "⚠️ Risks & Warnings"
    ])

    with tabs[0]:
        _render_resource_summary(analysis)

    with tabs[1]:
        _render_sprint_capacity(analysis, plan)

    with tabs[2]:
        _render_project_summary(analysis)

    with tabs[3]:
        _render_financial_summary(analysis, metrics)

    with tabs[4]:
        _render_timeline_view(analysis, plan)

    with tabs[5]:
        _render_risks_warnings(analysis)


def _calculate_metrics(analysis) -> PIMetrics:
    """Calculate aggregate metrics from analysis."""
    metrics = PIMetrics()

    # Sprint metrics
    metrics.num_sprints = len(analysis.sprints)

    # Resource metrics
    metrics.num_resources = len(analysis.resources)
    calculated_hours = 0.0
    for resource_name, resource in analysis.resources.items():
        calculated_hours += resource.total_hours
        metrics.total_remaining_hours += sum(resource.sprint_remaining.values())
        # Calculate cost (hours × rate)
        if resource.rate > 0:
            metrics.total_cost += resource.total_hours * resource.rate

    # Use grand total from spreadsheet if available, otherwise use calculated sum
    if hasattr(analysis, 'grand_total_hours') and analysis.grand_total_hours > 0:
        metrics.total_allocated_hours = analysis.grand_total_hours
    else:
        metrics.total_allocated_hours = calculated_hours

    # Total capacity based on 488 hours per resource (standard PI capacity)
    metrics.total_capacity_hours = metrics.num_resources * PI_HOURS_PER_RESOURCE

    # Project metrics
    metrics.num_projects = len(analysis.projects)

    # Utilization
    if metrics.total_capacity_hours > 0:
        metrics.utilization_percent = (metrics.total_allocated_hours / metrics.total_capacity_hours) * 100

    # Overallocation count
    metrics.overallocated_count = len(analysis.overallocated_resources)

    return metrics


def _render_executive_summary(metrics: PIMetrics, analysis) -> None:
    """Render executive summary cards."""
    st.subheader("PI Executive Summary")

    # Top row - Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Team Capacity",
            f"{metrics.total_capacity_hours:,.0f}h",
            help=f"Based on {PI_HOURS_PER_RESOURCE:.0f}h per resource × {metrics.num_resources} team members"
        )

    with col2:
        st.metric(
            "Allocated Hours",
            f"{metrics.total_allocated_hours:,.0f}h",
            delta=f"{metrics.utilization_percent:.1f}% utilized",
            delta_color="normal" if metrics.utilization_percent <= 100 else "inverse"
        )

    with col3:
        st.metric(
            "Total Cost",
            f"${metrics.total_cost:,.0f}",
            help="Based on resource rates × hours"
        )

    with col4:
        st.metric(
            "Resources",
            metrics.num_resources,
            delta=f"{metrics.overallocated_count} over-allocated" if metrics.overallocated_count > 0 else None,
            delta_color="inverse" if metrics.overallocated_count > 0 else "normal"
        )

    with col5:
        st.metric(
            "Projects",
            metrics.num_projects,
        )

    # Health indicator
    if metrics.utilization_percent > 100:
        st.error(f"⚠️ PI is over-allocated by {metrics.utilization_percent - 100:.1f}%")
    elif metrics.utilization_percent > 85:
        st.warning(f"⚡ PI utilization is high at {metrics.utilization_percent:.1f}%")
    elif metrics.utilization_percent < 50:
        st.info(f"📊 PI utilization is low at {metrics.utilization_percent:.1f}% - capacity available")
    else:
        st.success(f"✅ PI utilization is healthy at {metrics.utilization_percent:.1f}%")


def _render_resource_summary(analysis) -> None:
    """Render detailed resource summary grouped by discipline with allocation % and color coding."""
    st.subheader("Resource Allocation Summary")

    if not analysis.resources:
        st.info("No resource data available")
        return

    PI_MAX_HOURS = PI_HOURS_PER_RESOURCE  # Use module constant

    # Calculate totals
    total_resources = len(analysis.resources)
    over_count = sum(1 for r in analysis.resources.values() if r.total_hours > PI_MAX_HOURS * 1.05)
    under_count = sum(1 for r in analysis.resources.values() if 0 < r.total_hours < PI_MAX_HOURS * 0.80)
    optimal_count = total_resources - over_count - under_count
    # Use grand total from spreadsheet if available, otherwise calculate
    if hasattr(analysis, 'grand_total_hours') and analysis.grand_total_hours > 0:
        total_hours = analysis.grand_total_hours
    else:
        total_hours = sum(r.total_hours for r in analysis.resources.values())
    total_cost = sum(r.total_hours * r.rate for r in analysis.resources.values() if r.rate > 0)

    # Summary cards row with tooltips
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Team Size",
            total_resources,
            help="Total number of team members allocated to this PI"
        )
    with col2:
        st.metric(
            "Total Hours",
            f"{total_hours:,.0f}h",
            help="Total hours from the Total Hours column in the spreadsheet"
        )
    with col3:
        st.metric(
            "Total Cost",
            f"${total_cost:,.0f}",
            help="Total cost calculated as hours × hourly rate for each resource"
        )
    with col4:
        avg_alloc = (total_hours / (total_resources * PI_MAX_HOURS) * 100) if total_resources > 0 else 0
        st.metric(
            "Avg Allocation",
            f"{avg_alloc:.0f}%",
            help="Average allocation percentage across all team members. Target is 80-100% of 488 hours per person"
        )
    with col5:
        health = optimal_count / total_resources * 100 if total_resources > 0 else 0
        st.metric(
            "Health Score",
            f"{health:.0f}%",
            help="Percentage of team members with optimal allocation (80-105%). Higher is better"
        )

    # Status summary bar with legend
    if total_resources > 0:
        over_pct = over_count / total_resources * 100
        under_pct = under_count / total_resources * 100
        ok_pct = optimal_count / total_resources * 100

        st.markdown(
            f'''<div style="display:flex;height:12px;border-radius:6px;overflow:hidden;margin:15px 0;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
                <div style="background:#28a745;width:{ok_pct}%;" title="Optimal (80-105%): {optimal_count} resources"></div>
                <div style="background:#f39c12;width:{under_pct}%;" title="Under-allocated (<80%): {under_count} resources"></div>
                <div style="background:#dc3545;width:{over_pct}%;" title="Over-allocated (>105%): {over_count} resources"></div>
            </div>
            <div style="display:flex;justify-content:center;gap:25px;font-size:0.85em;margin-bottom:15px;">
                <span title="Team members allocated between 80-105% of 488 hours">🟢 Optimal: {optimal_count}</span>
                <span title="Team members allocated less than 80% - may have capacity for more work">🟡 Under: {under_count}</span>
                <span title="Team members allocated more than 105% - at risk of burnout">🔴 Over: {over_count}</span>
            </div>''',
            unsafe_allow_html=True
        )

        # Add explanation
        with st.expander("ℹ️ Understanding Allocation Status", expanded=False):
            st.markdown("""
            **Allocation Targets (based on 488 hours per PI):**
            - **Optimal (80-105%)**: 390-512 hours - Healthy workload with buffer for unexpected work
            - **Under-allocated (<80%)**: Less than 390 hours - Has capacity for additional work
            - **Over-allocated (>105%)**: More than 512 hours - Risk of burnout, consider redistributing

            **Why 488 hours?**
            - Standard PI length: 4 sprints × 2 weeks = 8 weeks
            - Working hours: 8 weeks × 5 days × ~12.2 hours = 488 hours (accounting for meetings, etc.)
            """)

    st.markdown("---")

    # Group resources by discipline
    by_discipline = {}
    for name, resource in analysis.resources.items():
        disc = resource.discipline or "Other"
        if disc not in by_discipline:
            by_discipline[disc] = []
        by_discipline[disc].append((name, resource))

    # Render each discipline group as an expander
    for discipline in sorted(by_discipline.keys()):
        resources = by_discipline[discipline]

        # Calculate discipline totals
        disc_hours = sum(r.total_hours for _, r in resources)
        disc_cost = sum(r.total_hours * r.rate for _, r in resources if r.rate > 0)
        disc_over = sum(1 for _, r in resources if r.total_hours > PI_MAX_HOURS * 1.05)
        disc_under = sum(1 for _, r in resources if 0 < r.total_hours < PI_MAX_HOURS * 0.80)

        # Status indicator for expander header
        if disc_over > 0:
            status_badge = f"({disc_over} over-allocated)"
        elif disc_under > 0:
            status_badge = f"({disc_under} under-allocated)"
        else:
            status_badge = "(all optimal)"

        with st.expander(f"**{discipline}** — {len(resources)} members • {disc_hours:,.0f}h • ${disc_cost:,.0f} {status_badge}", expanded=True):
            # Table header
            header_cols = st.columns([3, 5, 2, 2])
            with header_cols[0]:
                st.caption("Name")
            with header_cols[1]:
                st.caption("Allocation (488h max)")
            with header_cols[2]:
                st.caption("Status")
            with header_cols[3]:
                st.caption("Cost")

            # Render each resource
            for name, resource in sorted(resources, key=lambda x: -x[1].total_hours):
                _render_resource_row(name, resource, PI_MAX_HOURS)

    # Detailed table view at bottom
    st.markdown("---")
    with st.expander("View Full Data Table", expanded=False):
        _render_resource_table(analysis.resources, PI_MAX_HOURS)


def _render_resource_row(name: str, resource, max_hours: float) -> None:
    """Render a single resource row with progress bar."""
    total_hours = resource.total_hours
    alloc_pct = (total_hours / max_hours * 100) if max_hours > 0 else 0

    # Determine color and status
    if alloc_pct > 105:
        color = "#dc3545"
        bg_color = "#f8d7da"
        status = "OVER"
    elif alloc_pct < 80 and total_hours > 0:
        color = "#856404"
        bg_color = "#fff3cd"
        status = "UNDER"
    elif total_hours > 0:
        color = "#155724"
        bg_color = "#d4edda"
        status = "OK"
    else:
        color = "#6c757d"
        bg_color = "#e9ecef"
        status = "-"

    rate = resource.rate
    cost = total_hours * rate if rate > 0 else 0
    bar_width = min(alloc_pct, 110)  # Cap display at 110%

    cols = st.columns([3, 5, 2, 2])

    with cols[0]:
        st.markdown(f"**{name}**")

    with cols[1]:
        # Progress bar with percentage overlay
        st.markdown(
            f'''<div style="position:relative;background:#e9ecef;border-radius:6px;height:28px;overflow:hidden;">
                <div style="background:{color};width:{bar_width}%;height:100%;opacity:0.7;"></div>
                <div style="position:absolute;top:0;left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:space-between;padding:0 10px;font-size:0.85em;">
                    <span style="color:#333;font-weight:500;">{total_hours:.0f}h / {max_hours:.0f}h</span>
                    <span style="color:{color};font-weight:bold;">{alloc_pct:.0f}%</span>
                </div>
            </div>''',
            unsafe_allow_html=True
        )

    with cols[2]:
        st.markdown(
            f'<span style="background:{bg_color};color:{color};padding:4px 12px;border-radius:12px;font-size:0.8em;font-weight:600;">{status}</span>',
            unsafe_allow_html=True
        )

    with cols[3]:
        if cost > 0:
            st.markdown(f"${cost:,.0f}")
        else:
            st.markdown("-")


def _render_resource_table(resources: dict, max_hours: float) -> None:
    """Render full resource data table."""
    data = []
    for name, resource in sorted(resources.items()):
        total_hours = resource.total_hours
        rate = resource.rate
        cost = total_hours * rate if rate > 0 else 0
        alloc_pct = (total_hours / max_hours * 100) if max_hours > 0 else 0

        if alloc_pct > 105:
            status = "Over"
        elif alloc_pct < 80 and total_hours > 0:
            status = "Under"
        elif total_hours > 0:
            status = "OK"
        else:
            status = "-"

        data.append({
            "Name": name,
            "Discipline": resource.discipline or "-",
            "Hours": round(total_hours, 1),
            "Max Hours": max_hours,
            "Allocation %": round(alloc_pct, 1),
            "Status": status,
            "Rate": round(rate, 2) if rate > 0 else None,
            "Cost": round(cost, 0) if cost > 0 else None,
        })

    st.dataframe(data, use_container_width=True, height=400)


def _render_sprint_capacity(analysis, plan) -> None:
    """Render sprint capacity view with burndown."""
    st.subheader("Sprint Capacity Analysis")

    if not plan or not plan.sprints:
        st.info("No sprint data available")
        return

    # Sprint comparison chart
    sprint_data = []
    for sprint in plan.sprints:
        sprint_data.append({
            "Sprint": sprint.name,
            "Capacity": sprint.total_hours,
            "Net Capacity": sprint.net_capacity,
            "Load": sprint.sprint_load,
            "Buffer": sprint.buffer_hours,
            "Available": max(0, sprint.net_capacity - sprint.sprint_load),
            "Overflow": max(0, sprint.sprint_load - sprint.net_capacity),
            "Utilization": (sprint.sprint_load / sprint.net_capacity * 100) if sprint.net_capacity > 0 else 0,
            "Status": "PASS" if sprint.status.value == "pass" else "FAIL"
        })

    # Display sprint cards
    cols = st.columns(len(sprint_data))
    for i, data in enumerate(sprint_data):
        with cols[i]:
            status_color = "#28a745" if data["Status"] == "PASS" else "#dc3545"
            st.markdown(
                f"""
                <div style="border: 2px solid {status_color}; border-radius: 10px; padding: 15px; text-align: center;">
                    <h4 style="margin: 0;">{data["Sprint"]}</h4>
                    <p style="color: {status_color}; font-weight: bold; font-size: 1.2em;">{data["Status"]}</p>
                    <p><strong>{data["Utilization"]:.0f}%</strong> utilized</p>
                    <p>{data["Load"]:.0f}h / {data["Net Capacity"]:.0f}h</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")

    # Detailed table
    st.markdown("#### Sprint Details")
    st.dataframe(sprint_data, width="stretch")

    # Sprint burndown visualization (simple bar chart)
    st.markdown("#### Capacity vs Load")
    for data in sprint_data:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.write(f"**{data['Sprint']}**")
        with col2:
            progress = min(data["Utilization"] / 100, 1.0)
            color = "#28a745" if data["Utilization"] <= 80 else "#f39c12" if data["Utilization"] <= 100 else "#dc3545"
            st.markdown(
                f"""
                <div style="background: #e0e0e0; border-radius: 10px; height: 25px; position: relative;">
                    <div style="background: {color}; width: {min(progress * 100, 100)}%; height: 100%; border-radius: 10px;"></div>
                    <span style="position: absolute; right: 10px; top: 3px; font-size: 12px;">{data["Utilization"]:.0f}%</span>
                </div>
                """,
                unsafe_allow_html=True
            )


def _render_project_summary(analysis) -> None:
    """Render project portfolio summary."""
    st.subheader("Project Portfolio")

    if not analysis.projects:
        st.info("No project data available")
        return

    # Project table
    project_data = []
    for name, project in sorted(analysis.projects.items(), key=lambda x: -x[1].total_hours):
        sprints = [s for s, v in project.sprint_allocation.items() if v]

        project_data.append({
            "Project": name[:50] + "..." if len(name) > 50 else name,
            "Priority": project.priority or "N/A",
            "Total Hours": f"{project.total_hours:,.1f}",
            "Resources": len(project.resource_hours),
            "Sprints": ", ".join(sorted(sprints)) if sprints else "Unassigned",
        })

    st.dataframe(project_data, width="stretch", height=400)

    # Top projects by hours
    st.markdown("#### Top Projects by Hours")
    top_projects = sorted(analysis.projects.items(), key=lambda x: -x[1].total_hours)[:10]
    for name, project in top_projects:
        if project.total_hours > 0:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{name[:40]}**" + ("..." if len(name) > 40 else ""))
            with col2:
                st.write(f"{project.total_hours:,.0f}h")


def _render_financial_summary(analysis, metrics: PIMetrics) -> None:
    """Render financial summary."""
    st.subheader("Financial Summary")

    # Overall financial metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total PI Cost", f"${metrics.total_cost:,.0f}")

    with col2:
        avg_rate = metrics.total_cost / metrics.total_allocated_hours if metrics.total_allocated_hours > 0 else 0
        st.metric("Blended Rate", f"${avg_rate:,.2f}/hr")

    with col3:
        cost_per_sprint = metrics.total_cost / metrics.num_sprints if metrics.num_sprints > 0 else 0
        st.metric("Avg Cost/Sprint", f"${cost_per_sprint:,.0f}")

    st.markdown("---")

    # Cost by discipline
    st.markdown("#### Cost Breakdown by Discipline")
    discipline_data = {}
    for name, resource in analysis.resources.items():
        disc = resource.discipline or "Other"
        cost = resource.total_hours * resource.rate if resource.rate > 0 else 0
        discipline_data[disc] = discipline_data.get(disc, 0) + cost

    if discipline_data:
        total = sum(discipline_data.values())
        for disc, cost in sorted(discipline_data.items(), key=lambda x: -x[1]):
            if cost > 0:
                pct = (cost / total * 100) if total > 0 else 0
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{disc}**")
                with col2:
                    st.progress(pct / 100)
                with col3:
                    st.write(f"${cost:,.0f} ({pct:.0f}%)")

    # Cost by sprint
    st.markdown("---")
    st.markdown("#### Cost by Sprint")

    sprint_costs = {}
    for sprint_name in analysis.sprints:
        sprint_costs[sprint_name] = 0
        for resource_name, resource in analysis.resources.items():
            remaining = resource.sprint_remaining.get(sprint_name, 0)
            # Estimate hours allocated = capacity - remaining
            # This is approximate since we don't have exact per-sprint allocation
            if resource.rate > 0 and remaining < 0:
                # Over-allocated resources have negative remaining
                sprint_costs[sprint_name] += abs(remaining) * resource.rate

    for sprint, cost in sorted(sprint_costs.items()):
        st.write(f"- **{sprint}**: ${cost:,.0f}")


def _render_timeline_view(analysis, plan) -> None:
    """Render timeline/Gantt-style view using the roadmap component."""
    from pi_strategist.web.components.roadmap_display import render_roadmap, render_roadmap_summary

    st.subheader("PI Timeline & Roadmap")

    if not analysis.sprints:
        st.info("No timeline data available")
        return

    # Roadmap summary metrics
    render_roadmap_summary(analysis)

    st.markdown("---")

    # Use the new roadmap component for project visualization
    render_roadmap(analysis, plan, key_prefix="dashboard")

    # Releases timeline (if available)
    if analysis.releases:
        st.markdown("---")
        st.markdown("#### Release Schedule")
        for release in analysis.releases:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**{release.name}**")
            with col2:
                st.write(f"STG: {release.staging_date or 'TBD'}")
            with col3:
                st.write(f"PRD: {release.production_date or 'TBD'}")
            if release.description:
                st.caption(release.description[:100])


def _render_risks_warnings(analysis) -> None:
    """Render risks and warnings view."""
    st.subheader("Risks & Warnings")

    # Over-allocated resources
    if analysis.overallocated_resources:
        st.markdown("#### 🔴 Over-Allocated Resources")

        overalloc_data = []
        for resource, sprint, hours in analysis.overallocated_resources:
            overalloc_data.append({
                "Resource": resource,
                "Sprint": sprint,
                "Over-Allocated By": f"{hours:.1f}h",
                "Impact": "High" if hours > 20 else "Medium" if hours > 10 else "Low"
            })

        st.dataframe(overalloc_data, width="stretch")

        # Summary by resource
        resource_overalloc = {}
        for resource, sprint, hours in analysis.overallocated_resources:
            resource_overalloc[resource] = resource_overalloc.get(resource, 0) + hours

        st.markdown("**Most Over-Allocated Resources:**")
        for resource, hours in sorted(resource_overalloc.items(), key=lambda x: -x[1])[:5]:
            st.write(f"- {resource}: {hours:.1f}h total over-allocation")
    else:
        st.success("✅ No over-allocated resources")

    st.markdown("---")

    # All warnings
    if analysis.warnings:
        st.markdown(f"#### ⚠️ Warnings ({len(analysis.warnings)})")

        for warning in analysis.warnings[:20]:
            st.warning(warning)

        if len(analysis.warnings) > 20:
            with st.expander(f"Show {len(analysis.warnings) - 20} more warnings"):
                for warning in analysis.warnings[20:]:
                    st.warning(warning)
    else:
        st.success("✅ No warnings")

    # Errors
    if analysis.errors:
        st.markdown(f"#### ❌ Errors ({len(analysis.errors)})")
        for error in analysis.errors:
            st.error(error)
    else:
        st.success("✅ No errors")
