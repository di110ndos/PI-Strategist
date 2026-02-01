"""Roadmap/Gantt visualization component for PI planning."""

import streamlit as st
from typing import Optional

# Color scheme for sprints
SPRINT_COLORS = ["#3498db", "#9b59b6", "#1abc9c", "#e74c3c", "#f39c12", "#2ecc71"]

# Priority colors
PRIORITY_COLORS = {
    1: "#e74c3c",  # High priority - red
    2: "#f39c12",  # Medium-high - orange
    3: "#3498db",  # Medium - blue
    4: "#2ecc71",  # Lower - green
    5: "#95a5a6",  # Low - gray
}


def render_roadmap(analysis, plan=None, key_prefix: str = "") -> None:
    """Render project roadmap as a Gantt-style timeline.

    Args:
        analysis: PIAnalysis object from parser
        plan: Optional CapacityPlan object
        key_prefix: Unique prefix for widget keys to avoid duplicates
    """
    if not analysis or not analysis.sprints:
        st.info("No sprint data available for roadmap visualization.")
        return

    # Get sprint order
    sprint_names = sorted(analysis.sprints.keys(), key=_sprint_sort_key)

    if not sprint_names:
        st.info("No sprints found in the analysis.")
        return

    # View mode selector with unique key
    view_key = f"{key_prefix}_roadmap_view" if key_prefix else "roadmap_view"
    view_mode = st.radio("View Mode", ["Timeline", "Table"], horizontal=True, key=view_key)

    st.markdown("---")

    if view_mode == "Timeline":
        _render_gantt_view(analysis, sprint_names)
    else:
        _render_table_view(analysis, sprint_names)


def _sprint_sort_key(sprint_name: str) -> tuple:
    """Sort key for sprint names (Sprint 1, Sprint 2, etc.)."""
    import re
    match = re.search(r'(\d+)', sprint_name)
    if match:
        return (0, int(match.group(1)))
    return (1, sprint_name)


def _render_gantt_view(analysis, sprint_names: list[str]) -> None:
    """Render Gantt-style timeline visualization."""
    # Render sprint headers
    _render_sprint_headers(sprint_names, analysis.sprints)

    st.markdown("")

    # Render project rows
    if not analysis.projects:
        st.info("No projects found in the roadmap.")
        return

    # Sort projects by priority then by name
    sorted_projects = sorted(
        analysis.projects.items(),
        key=lambda x: (x[1].priority or 999, x[0])
    )

    for project_name, project in sorted_projects:
        if not project.sprint_allocation:
            continue

        _render_project_row(project_name, project, sprint_names)


def _render_sprint_headers(sprint_names: list[str], sprints_data: dict) -> None:
    """Render sprint header row with date ranges and capacity."""
    # Create columns: first for project name, rest for sprints
    cols = st.columns([2] + [1] * len(sprint_names))

    with cols[0]:
        st.markdown("**Project**")

    for i, sprint_name in enumerate(sprint_names):
        with cols[i + 1]:
            sprint_info = sprints_data.get(sprint_name, {})
            date_range = sprint_info.get("date_range", "")
            capacity = sprint_info.get("capacity", 0)
            color = SPRINT_COLORS[i % len(SPRINT_COLORS)]

            # Sprint header box
            st.markdown(
                f"""
                <div style="background: {color}; color: white; padding: 8px;
                     border-radius: 6px; text-align: center; font-size: 0.85em;">
                    <strong>{sprint_name}</strong><br/>
                    <span style="font-size: 0.8em;">{date_range}</span><br/>
                    <span style="font-size: 0.75em;">{capacity:.0f}h</span>
                </div>
                """,
                unsafe_allow_html=True
            )


def _render_project_row(project_name: str, project, sprint_names: list[str]) -> None:
    """Render a single project row across sprints."""
    cols = st.columns([2] + [1] * len(sprint_names))

    with cols[0]:
        priority = project.priority or 0
        priority_color = PRIORITY_COLORS.get(priority, "#95a5a6")
        priority_badge = f"P{priority}" if priority else ""

        # Truncate long project names
        display_name = project_name[:35] + "..." if len(project_name) > 35 else project_name

        st.markdown(
            f"""
            <div style="padding: 5px 0;">
                <span style="background: {priority_color}; color: white; padding: 2px 6px;
                     border-radius: 3px; font-size: 0.75em; margin-right: 5px;">{priority_badge}</span>
                <span style="font-size: 0.9em;" title="{project_name}">{display_name}</span>
                <br/>
                <span style="font-size: 0.75em; color: #666;">{project.total_hours:.0f}h</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Determine which sprints this project spans
    active_sprints = set()
    for sprint in sprint_names:
        if project.sprint_allocation.get(sprint):
            active_sprints.add(sprint)
        # Also check for sprint number variations
        for alloc_sprint in project.sprint_allocation:
            if project.sprint_allocation[alloc_sprint]:
                # Normalize sprint names for comparison
                if _normalize_sprint(alloc_sprint) == _normalize_sprint(sprint):
                    active_sprints.add(sprint)

    for i, sprint_name in enumerate(sprint_names):
        with cols[i + 1]:
            if sprint_name in active_sprints:
                # Project is active in this sprint - show colored bar
                color = SPRINT_COLORS[i % len(SPRINT_COLORS)]
                st.markdown(
                    f"""
                    <div style="background: {color}; height: 28px;
                         border-radius: 4px; margin: 8px 0; opacity: 0.8;"></div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Empty placeholder
                st.markdown(
                    """
                    <div style="background: #f5f5f5; height: 28px;
                         border-radius: 4px; margin: 8px 0;"></div>
                    """,
                    unsafe_allow_html=True
                )


def _normalize_sprint(sprint_name: str) -> str:
    """Normalize sprint name for comparison."""
    import re
    match = re.search(r'sprint\s*(\d+)', sprint_name.lower())
    if match:
        return f"sprint{match.group(1)}"
    return sprint_name.lower().strip()


def _render_table_view(analysis, sprint_names: list[str]) -> None:
    """Render roadmap as a table (alternative view)."""
    if not analysis.projects:
        st.info("No projects found.")
        return

    data = []
    for name, project in sorted(analysis.projects.items(), key=lambda x: (x[1].priority or 999, x[0])):
        if not project.sprint_allocation:
            continue

        row = {
            "Priority": f"P{project.priority}" if project.priority else "",
            "Project": name[:50],
            "Hours": f"{project.total_hours:.0f}",
            "Cost": f"${project.total_hours * 175:.0f}" if project.total_hours > 0 else "",  # Estimate
        }

        # Add sprint columns
        for sprint in sprint_names:
            active = any(
                project.sprint_allocation.get(s)
                for s in project.sprint_allocation
                if _normalize_sprint(s) == _normalize_sprint(sprint)
            )
            row[sprint] = "X" if active else ""

        data.append(row)

    if data:
        st.dataframe(data, use_container_width=True, height=400)
    else:
        st.info("No project data to display.")


def render_roadmap_summary(analysis) -> None:
    """Render summary metrics for the roadmap."""
    if not analysis:
        return

    col1, col2, col3, col4 = st.columns(4)

    total_projects = len([p for p in analysis.projects.values() if p.sprint_allocation])
    total_hours = sum(p.total_hours for p in analysis.projects.values())
    num_sprints = len(analysis.sprints)

    with col1:
        st.metric("Total Projects", total_projects)

    with col2:
        st.metric("Total Hours", f"{total_hours:.0f}h")

    with col3:
        st.metric("Sprints", num_sprints)

    with col4:
        avg_hours = total_hours / total_projects if total_projects > 0 else 0
        st.metric("Avg Hours/Project", f"{avg_hours:.0f}h")
