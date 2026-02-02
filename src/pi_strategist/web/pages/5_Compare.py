"""Compare saved analyses page."""

import sys
from pathlib import Path

# Add src directory to path for Streamlit Cloud deployment
_src_dir = Path(__file__).parent.parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import json
import streamlit as st
from datetime import datetime
from typing import Optional

from pi_strategist.web.components.session_status import render_session_status


# Page config
st.set_page_config(
    page_title="Compare Analyses - PI Strategist",
    page_icon="📊",
    layout="wide",
)

# Render session status in sidebar first
render_session_status()

st.title("📊 Compare Saved Analyses")
st.markdown("Select two saved analyses to compare capacity, utilization, and cost changes.")


def get_saved_analyses_dir() -> Path:
    """Get the directory for saved analyses."""
    save_dir = Path("saved_analyses")
    save_dir.mkdir(exist_ok=True)
    return save_dir


def load_saved_analyses() -> list[dict]:
    """Load all saved analyses from disk."""
    save_dir = get_saved_analyses_dir()
    analyses = []

    for file_path in sorted(save_dir.glob("*.json"), reverse=True):
        try:
            with open(file_path) as f:
                data = json.load(f)
            data["_file_path"] = str(file_path)
            data["_file_name"] = file_path.name
            analyses.append(data)
        except Exception as e:
            st.warning(f"Could not load {file_path.name}: {e}")

    return analyses


def get_analysis_label(analysis: dict) -> str:
    """Generate a display label for an analysis."""
    meta = analysis.get("metadata", {})
    year = meta.get("year", "?")
    quarter = meta.get("quarter", "?")
    name = meta.get("name", "")

    label = f"{year} {quarter}"
    if name:
        label += f" - {name}"
    return label


def render_analysis_summary(analysis: dict, label: str = "") -> None:
    """Render a summary card for a single analysis."""
    meta = analysis.get("metadata", {})
    summary = analysis.get("summary", {})

    if label:
        st.markdown(f"### {label}")

    st.caption(f"Saved: {meta.get('saved_at', 'Unknown')[:10]}")
    st.caption(f"Source: {meta.get('source_file', 'Unknown')}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Resources", summary.get("resources", 0))
    with col2:
        st.metric("Projects", summary.get("projects", 0))
    with col3:
        allocated = summary.get("total_allocated", 0)
        st.metric("Allocated", f"{allocated:,.0f}h")
    with col4:
        capacity = summary.get("total_capacity", 0)
        utilization = (allocated / capacity * 100) if capacity > 0 else 0
        st.metric("Utilization", f"{utilization:.1f}%")


def calculate_cost(analysis: dict) -> float:
    """Calculate total cost from an analysis."""
    resources = analysis.get("resources", {})
    total_cost = 0
    for name, res in resources.items():
        hours = res.get("total_hours", 0)
        rate = res.get("rate", 0)
        total_cost += hours * rate
    return total_cost


def render_comparison(analysis_a: dict, analysis_b: dict) -> None:
    """Render side-by-side comparison of two analyses."""
    label_a = get_analysis_label(analysis_a)
    label_b = get_analysis_label(analysis_b)

    summary_a = analysis_a.get("summary", {})
    summary_b = analysis_b.get("summary", {})

    # Calculate costs
    cost_a = calculate_cost(analysis_a)
    cost_b = calculate_cost(analysis_b)

    # Calculate utilizations
    capacity_a = summary_a.get("total_capacity", 0)
    capacity_b = summary_b.get("total_capacity", 0)
    allocated_a = summary_a.get("total_allocated", 0)
    allocated_b = summary_b.get("total_allocated", 0)
    util_a = (allocated_a / capacity_a * 100) if capacity_a > 0 else 0
    util_b = (allocated_b / capacity_b * 100) if capacity_b > 0 else 0

    st.markdown("---")
    st.header("Comparison Summary")

    # Overview metrics with deltas
    st.markdown("### Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delta_hours = allocated_b - allocated_a
        st.metric(
            "Allocated Hours",
            f"{allocated_b:,.0f}h",
            delta=f"{delta_hours:+,.0f}h",
            delta_color="normal"
        )

    with col2:
        delta_util = util_b - util_a
        st.metric(
            "Utilization",
            f"{util_b:.1f}%",
            delta=f"{delta_util:+.1f}%",
            delta_color="inverse" if util_b > 100 else "normal"
        )

    with col3:
        delta_cost = cost_b - cost_a
        st.metric(
            "Total Cost",
            f"${cost_b:,.0f}",
            delta=f"${delta_cost:+,.0f}",
            delta_color="inverse"
        )

    with col4:
        resources_a = summary_a.get("resources", 0)
        resources_b = summary_b.get("resources", 0)
        delta_resources = resources_b - resources_a
        st.metric(
            "Resources",
            resources_b,
            delta=f"{delta_resources:+d}" if delta_resources != 0 else None,
        )

    # Side-by-side comparison table
    st.markdown("---")
    st.markdown("### Side-by-Side Comparison")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"#### 📍 {label_a}")
        st.markdown(f"- **Allocated:** {allocated_a:,.0f}h")
        st.markdown(f"- **Capacity:** {capacity_a:,.0f}h")
        st.markdown(f"- **Utilization:** {util_a:.1f}%")
        st.markdown(f"- **Cost:** ${cost_a:,.0f}")
        st.markdown(f"- **Resources:** {summary_a.get('resources', 0)}")
        st.markdown(f"- **Projects:** {summary_a.get('projects', 0)}")

    with col_b:
        st.markdown(f"#### 🎯 {label_b}")
        st.markdown(f"- **Allocated:** {allocated_b:,.0f}h")
        st.markdown(f"- **Capacity:** {capacity_b:,.0f}h")
        st.markdown(f"- **Utilization:** {util_b:.1f}%")
        st.markdown(f"- **Cost:** ${cost_b:,.0f}")
        st.markdown(f"- **Resources:** {summary_b.get('resources', 0)}")
        st.markdown(f"- **Projects:** {summary_b.get('projects', 0)}")

    # Resource comparison
    st.markdown("---")
    st.markdown("### Resource Changes")

    resources_a = analysis_a.get("resources", {})
    resources_b = analysis_b.get("resources", {})

    all_resource_names = set(resources_a.keys()) | set(resources_b.keys())

    if all_resource_names:
        # Categorize changes
        added_resources = []
        removed_resources = []
        changed_resources = []

        for name in sorted(all_resource_names):
            in_a = name in resources_a
            in_b = name in resources_b

            if in_a and not in_b:
                res = resources_a[name]
                removed_resources.append({
                    "name": name,
                    "hours": res.get("total_hours", 0),
                    "rate": res.get("rate", 0),
                })
            elif in_b and not in_a:
                res = resources_b[name]
                added_resources.append({
                    "name": name,
                    "hours": res.get("total_hours", 0),
                    "rate": res.get("rate", 0),
                })
            else:
                # Both exist - check for changes
                hours_a = resources_a[name].get("total_hours", 0)
                hours_b = resources_b[name].get("total_hours", 0)
                rate_a = resources_a[name].get("rate", 0)
                rate_b = resources_b[name].get("rate", 0)

                if abs(hours_a - hours_b) > 0.1 or abs(rate_a - rate_b) > 0.1:
                    changed_resources.append({
                        "name": name,
                        "hours_a": hours_a,
                        "hours_b": hours_b,
                        "hours_delta": hours_b - hours_a,
                        "rate_a": rate_a,
                        "rate_b": rate_b,
                    })

        # Display added resources
        if added_resources:
            with st.expander(f"➕ Added Resources ({len(added_resources)})", expanded=True):
                for res in added_resources:
                    cost = res["hours"] * res["rate"]
                    st.success(f"**{res['name']}**: {res['hours']:,.0f}h @ ${res['rate']:,.0f}/hr = ${cost:,.0f}")

        # Display removed resources
        if removed_resources:
            with st.expander(f"➖ Removed Resources ({len(removed_resources)})", expanded=True):
                for res in removed_resources:
                    cost = res["hours"] * res["rate"]
                    st.error(f"**{res['name']}**: {res['hours']:,.0f}h @ ${res['rate']:,.0f}/hr = ${cost:,.0f}")

        # Display changed resources
        if changed_resources:
            with st.expander(f"🔄 Changed Resources ({len(changed_resources)})", expanded=True):
                for res in sorted(changed_resources, key=lambda x: abs(x["hours_delta"]), reverse=True):
                    delta = res["hours_delta"]
                    sign = "+" if delta > 0 else ""
                    color = "green" if delta > 0 else "red"

                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**{res['name']}**")
                    with col2:
                        st.markdown(f"{res['hours_a']:,.0f}h → {res['hours_b']:,.0f}h")
                    with col3:
                        st.markdown(f":{color}[{sign}{delta:,.0f}h]")

        if not added_resources and not removed_resources and not changed_resources:
            st.info("No resource changes detected between analyses.")

    else:
        st.info("No resource data available for comparison.")

    # Project comparison
    st.markdown("---")
    st.markdown("### Project Changes")

    projects_a = analysis_a.get("projects", {})
    projects_b = analysis_b.get("projects", {})

    all_project_names = set(projects_a.keys()) | set(projects_b.keys())

    if all_project_names:
        added_projects = []
        removed_projects = []
        changed_projects = []

        for name in sorted(all_project_names):
            in_a = name in projects_a
            in_b = name in projects_b

            if in_a and not in_b:
                proj = projects_a[name]
                removed_projects.append({
                    "name": name,
                    "hours": proj.get("total_hours", 0),
                })
            elif in_b and not in_a:
                proj = projects_b[name]
                added_projects.append({
                    "name": name,
                    "hours": proj.get("total_hours", 0),
                })
            else:
                hours_a = projects_a[name].get("total_hours", 0)
                hours_b = projects_b[name].get("total_hours", 0)

                if abs(hours_a - hours_b) > 0.1:
                    changed_projects.append({
                        "name": name,
                        "hours_a": hours_a,
                        "hours_b": hours_b,
                        "hours_delta": hours_b - hours_a,
                    })

        # Display added projects
        if added_projects:
            with st.expander(f"➕ Added Projects ({len(added_projects)})", expanded=True):
                for proj in added_projects:
                    st.success(f"**{proj['name'][:60]}{'...' if len(proj['name']) > 60 else ''}**: {proj['hours']:,.0f}h")

        # Display removed projects
        if removed_projects:
            with st.expander(f"➖ Removed Projects ({len(removed_projects)})", expanded=True):
                for proj in removed_projects:
                    st.error(f"**{proj['name'][:60]}{'...' if len(proj['name']) > 60 else ''}**: {proj['hours']:,.0f}h")

        # Display changed projects
        if changed_projects:
            with st.expander(f"🔄 Changed Projects ({len(changed_projects)})", expanded=True):
                for proj in sorted(changed_projects, key=lambda x: abs(x["hours_delta"]), reverse=True)[:20]:
                    delta = proj["hours_delta"]
                    sign = "+" if delta > 0 else ""
                    color = "green" if delta > 0 else "red"

                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        display_name = proj["name"][:50] + "..." if len(proj["name"]) > 50 else proj["name"]
                        st.markdown(f"**{display_name}**")
                    with col2:
                        st.markdown(f"{proj['hours_a']:,.0f}h → {proj['hours_b']:,.0f}h")
                    with col3:
                        st.markdown(f":{color}[{sign}{delta:,.0f}h]")

                if len(changed_projects) > 20:
                    st.caption(f"...and {len(changed_projects) - 20} more projects with changes")

        if not added_projects and not removed_projects and not changed_projects:
            st.info("No project changes detected between analyses.")

    else:
        st.info("No project data available for comparison.")

    # Assessment
    st.markdown("---")
    st.markdown("### Assessment")

    # Determine overall trend
    if delta_hours > 0 and delta_util <= 10:
        st.success(f"✅ Increased allocation by {delta_hours:,.0f}h while maintaining healthy utilization ({util_b:.1f}%)")
    elif delta_hours < 0 and delta_cost < 0:
        st.info(f"📉 Reduced scope by {abs(delta_hours):,.0f}h, saving ${abs(delta_cost):,.0f}")
    elif util_b > 100:
        st.error(f"⚠️ Over-allocated at {util_b:.1f}% - consider reducing scope or adding resources")
    elif delta_cost > 0 and delta_hours <= 0:
        st.warning(f"💰 Cost increased by ${delta_cost:,.0f} without adding hours - check rate changes")
    else:
        st.info(f"📊 Hours: {delta_hours:+,.0f}h | Utilization: {delta_util:+.1f}% | Cost: ${delta_cost:+,.0f}")


# Load saved analyses
analyses = load_saved_analyses()

if len(analyses) < 2:
    st.warning(
        f"**Need at least 2 saved analyses to compare.**\n\n"
        f"Currently have {len(analyses)} saved analysis(es).\n\n"
        f"Go to the Analysis page, run an analysis, and save it to enable comparison."
    )

    if st.button("Go to Analysis Page"):
        st.switch_page("pages/1_Analyze.py")

else:
    # Selection UI
    st.markdown("### Select Analyses to Compare")

    col1, col2 = st.columns(2)

    # Create options with labels
    options = {get_analysis_label(a): i for i, a in enumerate(analyses)}
    option_labels = list(options.keys())

    with col1:
        st.markdown("#### 📍 Baseline (Earlier)")
        selected_a = st.selectbox(
            "Select first analysis",
            options=option_labels,
            index=min(1, len(option_labels) - 1),  # Default to second item (older)
            key="compare_a",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("#### 🎯 Current (Later)")
        selected_b = st.selectbox(
            "Select second analysis",
            options=option_labels,
            index=0,  # Default to first item (newest)
            key="compare_b",
            label_visibility="collapsed"
        )

    if selected_a == selected_b:
        st.warning("Please select two different analyses to compare.")
    else:
        analysis_a = analyses[options[selected_a]]
        analysis_b = analyses[options[selected_b]]

        # Show comparison
        render_comparison(analysis_a, analysis_b)


# Sidebar
with st.sidebar:
    st.markdown("### Saved Analyses")
    st.caption(f"{len(analyses)} analyses available")

    if analyses:
        st.markdown("---")
        for analysis in analyses[:5]:
            label = get_analysis_label(analysis)
            meta = analysis.get("metadata", {})
            st.markdown(f"**{label}**")
            st.caption(f"Saved: {meta.get('saved_at', '?')[:10]}")

        if len(analyses) > 5:
            st.caption(f"...and {len(analyses) - 5} more")

    st.markdown("---")
    st.markdown("### Tips")
    st.markdown(
        """
        - Compare sequential PIs to track trends
        - Look for resource utilization changes
        - Monitor cost trends over time
        - Identify scope creep via project changes
        """
    )
