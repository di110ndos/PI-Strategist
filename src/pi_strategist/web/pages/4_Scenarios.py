"""What-If Scenario Planning page."""

import streamlit as st
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional

from pi_strategist.parsers.pi_planner_parser import PIAnalysis, Resource
from pi_strategist.web.components.session_status import render_session_status


# Page config
st.set_page_config(
    page_title="Scenarios - PI Strategist",
    page_icon="🔮",
    layout="wide",
)

# Render session status in sidebar first
render_session_status()

st.title("🔮 What-If Scenario Planning")
st.markdown("Simulate changes to your PI plan and compare different scenarios.")


@dataclass
class Scenario:
    """A what-if scenario with modifications."""
    name: str
    description: str = ""
    base_analysis: Optional[PIAnalysis] = None

    # Modifications
    resource_adjustments: dict[str, float] = field(default_factory=dict)  # resource -> hours delta
    removed_resources: list[str] = field(default_factory=list)
    added_resources: list[dict] = field(default_factory=list)  # [{name, hours, rate}]
    removed_projects: list[str] = field(default_factory=list)  # Projects to remove
    task_moves: list[dict] = field(default_factory=list)  # [{task, from_sprint, to_sprint}]

    # Calculated results (after applying modifications)
    modified_capacity: float = 0.0
    modified_allocated: float = 0.0
    modified_cost: float = 0.0
    utilization_delta: float = 0.0
    cost_delta: float = 0.0


# Initialize session state
if "scenarios" not in st.session_state:
    st.session_state.scenarios = {}

if "active_scenario" not in st.session_state:
    st.session_state.active_scenario = None

if "base_pi_analysis" not in st.session_state:
    st.session_state.base_pi_analysis = None

if "pending_delete_scenario" not in st.session_state:
    st.session_state.pending_delete_scenario = None

if "pending_clear_all" not in st.session_state:
    st.session_state.pending_clear_all = False


# ============================================================================
# Confirmation Dialogs
# ============================================================================

@st.dialog("Confirm Delete Scenario")
def confirm_delete_scenario(scenario_name: str):
    """Show confirmation dialog before deleting a scenario."""
    st.warning(f'Are you sure you want to delete **"{scenario_name}"**?')
    st.caption("This action cannot be undone.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pending_delete_scenario = None
            st.rerun()
    with col2:
        if st.button("Delete", type="primary", use_container_width=True):
            del st.session_state.scenarios[scenario_name]
            st.session_state.pending_delete_scenario = None
            st.toast(f'Scenario "{scenario_name}" deleted', icon="🗑️")
            st.rerun()


@st.dialog("Confirm Clear All Scenarios")
def confirm_clear_all():
    """Show confirmation dialog before clearing all scenarios."""
    count = len(st.session_state.scenarios)
    st.warning(f"Are you sure you want to delete all **{count}** scenarios?")
    st.caption("This action cannot be undone.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pending_clear_all = False
            st.rerun()
    with col2:
        if st.button("Clear All", type="primary", use_container_width=True):
            st.session_state.scenarios = {}
            st.session_state.pending_clear_all = False
            st.toast("All scenarios cleared", icon="🗑️")
            st.rerun()


# ============================================================================
# Helper Functions (defined before use)
# ============================================================================

def get_base_analysis() -> Optional[PIAnalysis]:
    """Get base PI analysis from analysis results."""
    if st.session_state.base_pi_analysis:
        return st.session_state.base_pi_analysis

    # Try to get from analysis results
    if "analysis_results" in st.session_state and st.session_state.analysis_results:
        pi_analysis = st.session_state.analysis_results.get("pi_analysis")
        if pi_analysis:
            st.session_state.base_pi_analysis = pi_analysis
            return pi_analysis

    return None


def calculate_scenario_impact(scenario: Scenario) -> Scenario:
    """Calculate the impact of a scenario's modifications."""
    if not scenario.base_analysis:
        return scenario

    base = scenario.base_analysis

    # Start with base values
    scenario.modified_capacity = base.total_capacity
    scenario.modified_allocated = base.total_allocated

    # Calculate base cost
    base_cost = sum(
        r.total_hours * r.rate
        for r in base.resources.values()
        if r.rate > 0
    )

    modified_cost = base_cost

    # Apply resource adjustments
    for resource_name, hours_delta in scenario.resource_adjustments.items():
        if resource_name in base.resources:
            resource = base.resources[resource_name]
            scenario.modified_allocated += hours_delta
            if resource.rate > 0:
                modified_cost += hours_delta * resource.rate

    # Apply removed resources
    for resource_name in scenario.removed_resources:
        if resource_name in base.resources:
            resource = base.resources[resource_name]
            scenario.modified_allocated -= resource.total_hours
            if resource.rate > 0:
                modified_cost -= resource.total_hours * resource.rate

    # Apply added resources
    for added in scenario.added_resources:
        hours = added.get("hours", 0)
        rate = added.get("rate", 0)
        scenario.modified_allocated += hours
        modified_cost += hours * rate

    # Apply removed projects - subtract hours and cost for each resource on that project
    for project_name in scenario.removed_projects:
        if project_name in base.projects:
            project = base.projects[project_name]
            # Subtract hours for each resource allocated to this project
            for resource_name, hours in project.resource_hours.items():
                scenario.modified_allocated -= hours
                # Calculate cost reduction based on resource's rate
                if resource_name in base.resources:
                    resource = base.resources[resource_name]
                    if resource.rate > 0:
                        modified_cost -= hours * resource.rate

    scenario.modified_cost = modified_cost

    # Calculate deltas
    base_utilization = (base.total_allocated / base.total_capacity * 100) if base.total_capacity > 0 else 0
    modified_utilization = (scenario.modified_allocated / scenario.modified_capacity * 100) if scenario.modified_capacity > 0 else 0

    scenario.utilization_delta = modified_utilization - base_utilization
    scenario.cost_delta = modified_cost - base_cost

    return scenario


def _render_resource_adjustments(scenario: Scenario) -> None:
    """Render resource adjustment controls."""
    st.markdown("#### Adjust Existing Resources")
    st.caption("Use sliders to increase or decrease hours for each resource")

    if not scenario.base_analysis:
        return

    # Group by discipline
    disciplines = {}
    for name, resource in scenario.base_analysis.resources.items():
        disc = resource.discipline or "Other"
        if disc not in disciplines:
            disciplines[disc] = []
        disciplines[disc].append((name, resource))

    for disc, resources in sorted(disciplines.items()):
        with st.expander(f"**{disc}** ({len(resources)} resources)"):
            for name, resource in resources:
                current_adjustment = scenario.resource_adjustments.get(name, 0)

                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**{name}**")
                    st.caption(f"Base: {resource.total_hours:.0f}h @ ${resource.rate:.0f}/hr")

                with col2:
                    # Slider for adjustment (-50% to +50%)
                    # Handle resources with 0 hours
                    if resource.total_hours > 0:
                        max_adjust = resource.total_hours * 0.5
                        adjustment = st.slider(
                            f"Adjust hours",
                            min_value=-max_adjust,
                            max_value=max_adjust,
                            value=float(current_adjustment),
                            step=8.0,
                            key=f"adj_{scenario.name}_{name}",
                            label_visibility="collapsed"
                        )
                        scenario.resource_adjustments[name] = adjustment
                    else:
                        st.caption("No hours allocated")
                        adjustment = 0

                with col3:
                    new_hours = resource.total_hours + adjustment
                    delta_color = "green" if adjustment > 0 else "red" if adjustment < 0 else "gray"
                    st.markdown(
                        f'<span style="color: {delta_color}">'
                        f'{adjustment:+.0f}h → {new_hours:.0f}h</span>',
                        unsafe_allow_html=True
                    )


def _render_resource_management(scenario: Scenario) -> None:
    """Render add/remove resource controls."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ➕ Add Resources")

        with st.form(key=f"add_resource_{scenario.name}"):
            new_name = st.text_input("Resource Name", placeholder="e.g., Contractor 1")
            new_hours = st.number_input("Hours", min_value=0, max_value=500, value=160)
            new_rate = st.number_input("Hourly Rate ($)", min_value=0, max_value=500, value=100)

            if st.form_submit_button("Add Resource"):
                if new_name:
                    scenario.added_resources.append({
                        "name": new_name,
                        "hours": new_hours,
                        "rate": new_rate
                    })
                    st.session_state.scenarios[scenario.name] = calculate_scenario_impact(scenario)
                    st.toast(f'Added resource "{new_name}"', icon="➕")
                    st.rerun()

        # Show added resources
        if scenario.added_resources:
            st.markdown("**Added:**")
            for i, added in enumerate(scenario.added_resources):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"- {added['name']}: {added['hours']}h @ ${added['rate']}/hr")
                with col_b:
                    if st.button("❌", key=f"rm_added_{scenario.name}_{i}"):
                        scenario.added_resources.pop(i)
                        st.session_state.scenarios[scenario.name] = calculate_scenario_impact(scenario)
                        st.rerun()

    with col2:
        st.markdown("#### ➖ Remove Resources")

        if scenario.base_analysis:
            available = [
                name for name in scenario.base_analysis.resources.keys()
                if name not in scenario.removed_resources
            ]

            selected = st.multiselect(
                "Select resources to remove",
                options=available,
                default=scenario.removed_resources,
                key=f"remove_{scenario.name}"
            )

            scenario.removed_resources = selected

            # Show impact of removals
            if scenario.removed_resources:
                st.markdown("**Removal Impact:**")
                total_removed_hours = 0
                total_removed_cost = 0
                for name in scenario.removed_resources:
                    resource = scenario.base_analysis.resources.get(name)
                    if resource:
                        total_removed_hours += resource.total_hours
                        total_removed_cost += resource.total_hours * resource.rate
                st.warning(f"-{total_removed_hours:.0f}h, -${total_removed_cost:,.0f}")


def _render_project_removal(scenario: Scenario) -> None:
    """Render project removal controls."""
    st.markdown("#### Remove Projects")
    st.caption("Select projects to remove from this scenario - all associated hours and costs will be subtracted")

    if not scenario.base_analysis or not scenario.base_analysis.projects:
        st.info("No project data available")
        return

    base = scenario.base_analysis

    # Get list of projects with their hours and costs
    project_options = []
    project_info = {}
    for project_name, project in sorted(base.projects.items(), key=lambda x: -x[1].total_hours):
        if project.total_hours > 0:
            # Calculate cost for this project
            project_cost = 0
            for resource_name, hours in project.resource_hours.items():
                if resource_name in base.resources:
                    resource = base.resources[resource_name]
                    if resource.rate > 0:
                        project_cost += hours * resource.rate

            project_options.append(project_name)
            project_info[project_name] = {
                "hours": project.total_hours,
                "cost": project_cost,
                "resources": len(project.resource_hours)
            }

    if not project_options:
        st.info("No projects with allocated hours found")
        return

    # Multi-select for projects to remove
    selected = st.multiselect(
        "Select projects to remove from scenario",
        options=project_options,
        default=scenario.removed_projects,
        key=f"remove_projects_{scenario.name}",
        format_func=lambda x: f"{x[:40]}{'...' if len(x) > 40 else ''} ({project_info[x]['hours']:.0f}h, ${project_info[x]['cost']:,.0f})"
    )

    scenario.removed_projects = selected

    # Show impact summary
    if scenario.removed_projects:
        st.markdown("---")
        st.markdown("**Removal Impact:**")

        total_hours = 0
        total_cost = 0

        for project_name in scenario.removed_projects:
            info = project_info.get(project_name, {})
            hours = info.get("hours", 0)
            cost = info.get("cost", 0)
            resources = info.get("resources", 0)

            total_hours += hours
            total_cost += cost

            with st.expander(f"**{project_name[:50]}**" + ("..." if len(project_name) > 50 else ""), expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Hours", f"-{hours:,.0f}h")
                with col2:
                    st.metric("Cost", f"-${cost:,.0f}")
                with col3:
                    st.metric("Resources", resources)

        st.error(f"**Total Impact:** -{total_hours:,.0f}h, -${total_cost:,.0f}")


def _render_scenario_impact(scenario: Scenario) -> None:
    """Render scenario impact analysis."""
    # Recalculate
    scenario = calculate_scenario_impact(scenario)

    if not scenario.base_analysis:
        return

    base = scenario.base_analysis
    base_cost = sum(r.total_hours * r.rate for r in base.resources.values() if r.rate > 0)
    base_utilization = (base.total_allocated / base.total_capacity * 100) if base.total_capacity > 0 else 0
    modified_utilization = (scenario.modified_allocated / scenario.modified_capacity * 100) if scenario.modified_capacity > 0 else 0

    # =========================================================================
    # Scenario Changes Summary - What's being applied
    # =========================================================================
    st.markdown("### 📋 Scenario Changes")

    has_changes = False

    # Removed Projects
    if scenario.removed_projects:
        has_changes = True
        st.markdown("#### 🗑️ Projects Removed")
        for project_name in scenario.removed_projects:
            if project_name in base.projects:
                project = base.projects[project_name]
                # Calculate project cost
                project_cost = sum(
                    hours * base.resources[res].rate
                    for res, hours in project.resource_hours.items()
                    if res in base.resources and base.resources[res].rate > 0
                )
                st.markdown(
                    f"- **{project_name[:50]}{'...' if len(project_name) > 50 else ''}** "
                    f"→ -{project.total_hours:,.0f}h, -${project_cost:,.0f}"
                )

    # Removed Resources
    if scenario.removed_resources:
        has_changes = True
        st.markdown("#### 👤 Resources Removed")
        for resource_name in scenario.removed_resources:
            if resource_name in base.resources:
                resource = base.resources[resource_name]
                cost = resource.total_hours * resource.rate if resource.rate > 0 else 0
                st.markdown(f"- **{resource_name}** → -{resource.total_hours:,.0f}h, -${cost:,.0f}")

    # Added Resources
    if scenario.added_resources:
        has_changes = True
        st.markdown("#### ➕ Resources Added")
        for added in scenario.added_resources:
            name = added.get("name", "Unknown")
            hours = added.get("hours", 0)
            rate = added.get("rate", 0)
            cost = hours * rate
            st.markdown(f"- **{name}** → +{hours:,.0f}h, +${cost:,.0f}")

    # Resource Adjustments (only show non-zero)
    adjustments = {k: v for k, v in scenario.resource_adjustments.items() if abs(v) > 0}
    if adjustments:
        has_changes = True
        st.markdown("#### 🔧 Resource Hour Adjustments")
        for resource_name, delta in sorted(adjustments.items(), key=lambda x: x[1]):
            if resource_name in base.resources:
                resource = base.resources[resource_name]
                cost_delta = delta * resource.rate if resource.rate > 0 else 0
                sign = "+" if delta > 0 else ""
                st.markdown(f"- **{resource_name}** → {sign}{delta:,.0f}h, {sign}${cost_delta:,.0f}")

    if not has_changes:
        st.info("No changes applied to this scenario yet. Use the other tabs to modify resources or remove projects.")

    st.markdown("---")

    # =========================================================================
    # Impact Summary - Results
    # =========================================================================
    st.markdown("### 📊 Impact Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Allocated Hours",
            f"{scenario.modified_allocated:,.0f}h",
            delta=f"{scenario.modified_allocated - base.total_allocated:+,.0f}h",
            delta_color="normal"
        )

    with col2:
        st.metric(
            "Utilization",
            f"{modified_utilization:.1f}%",
            delta=f"{scenario.utilization_delta:+.1f}%",
            delta_color="inverse" if modified_utilization > 100 else "normal"
        )

    with col3:
        st.metric(
            "Total Cost",
            f"${scenario.modified_cost:,.0f}",
            delta=f"${scenario.cost_delta:+,.0f}",
            delta_color="inverse"
        )

    # =========================================================================
    # Before vs After Comparison
    # =========================================================================
    st.markdown("---")
    st.markdown("### 📈 Before vs After")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📍 Baseline (Current Plan)**")
        st.markdown(f"- **Hours:** {base.total_allocated:,.0f}h")
        st.markdown(f"- **Utilization:** {base_utilization:.1f}%")
        st.markdown(f"- **Cost:** ${base_cost:,.0f}")

    with col2:
        st.markdown("**🎯 With This Scenario**")
        st.markdown(f"- **Hours:** {scenario.modified_allocated:,.0f}h")
        st.markdown(f"- **Utilization:** {modified_utilization:.1f}%")
        st.markdown(f"- **Cost:** ${scenario.modified_cost:,.0f}")

    # =========================================================================
    # Status Assessment
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🎯 Assessment")

    # Warnings
    if modified_utilization > 100:
        st.error(f"⚠️ This scenario results in over-allocation ({modified_utilization:.1f}%)")
    elif modified_utilization > 90:
        st.warning(f"⚡ High utilization ({modified_utilization:.1f}%) - limited flexibility")
    elif modified_utilization < 60:
        st.info(f"📉 Low utilization ({modified_utilization:.1f}%) - capacity available")
    else:
        st.success(f"✅ Healthy utilization ({modified_utilization:.1f}%)")


def _render_live_impact_panel(scenario: Scenario) -> None:
    """Render compact live impact preview panel that updates in real-time."""
    # Recalculate on every render for live updates
    scenario = calculate_scenario_impact(scenario)
    st.session_state.scenarios[scenario.name] = scenario

    if not scenario.base_analysis:
        st.info("No baseline data available")
        return

    base = scenario.base_analysis
    base_cost = sum(r.total_hours * r.rate for r in base.resources.values() if r.rate > 0)
    base_utilization = (base.total_allocated / base.total_capacity * 100) if base.total_capacity > 0 else 0
    modified_utilization = (scenario.modified_allocated / scenario.modified_capacity * 100) if scenario.modified_capacity > 0 else 0

    st.markdown("### 📊 Live Impact Preview")

    # Health status indicator
    if modified_utilization > 100:
        st.error(f"🔴 Over-allocated ({modified_utilization:.1f}%)")
    elif modified_utilization > 90:
        st.warning(f"🟡 High utilization ({modified_utilization:.1f}%)")
    elif modified_utilization < 60:
        st.info(f"🔵 Low utilization ({modified_utilization:.1f}%)")
    else:
        st.success(f"🟢 Healthy ({modified_utilization:.1f}%)")

    # 3 key metrics with deltas
    col1, col2, col3 = st.columns(3)

    with col1:
        hours_delta = scenario.modified_allocated - base.total_allocated
        st.metric(
            "Hours",
            f"{scenario.modified_allocated:,.0f}h",
            delta=f"{hours_delta:+,.0f}h" if hours_delta != 0 else None,
            delta_color="normal"
        )

    with col2:
        st.metric(
            "Utilization",
            f"{modified_utilization:.1f}%",
            delta=f"{scenario.utilization_delta:+.1f}%" if scenario.utilization_delta != 0 else None,
            delta_color="inverse" if modified_utilization > 100 else "normal"
        )

    with col3:
        st.metric(
            "Cost",
            f"${scenario.modified_cost:,.0f}",
            delta=f"${scenario.cost_delta:+,.0f}" if scenario.cost_delta != 0 else None,
            delta_color="inverse"
        )

    # Compact list of active changes
    st.markdown("---")
    st.markdown("#### Active Changes")

    has_changes = False

    # Removed Projects
    if scenario.removed_projects:
        has_changes = True
        with st.container():
            st.markdown(f"**🗑️ Removed Projects** ({len(scenario.removed_projects)})")
            for project_name in scenario.removed_projects[:3]:  # Show first 3
                st.caption(f"• {project_name[:35]}{'...' if len(project_name) > 35 else ''}")
            if len(scenario.removed_projects) > 3:
                st.caption(f"  ...and {len(scenario.removed_projects) - 3} more")

    # Removed Resources
    if scenario.removed_resources:
        has_changes = True
        st.markdown(f"**👤 Removed Resources** ({len(scenario.removed_resources)})")
        for resource_name in scenario.removed_resources[:3]:
            st.caption(f"• {resource_name}")
        if len(scenario.removed_resources) > 3:
            st.caption(f"  ...and {len(scenario.removed_resources) - 3} more")

    # Added Resources
    if scenario.added_resources:
        has_changes = True
        st.markdown(f"**➕ Added Resources** ({len(scenario.added_resources)})")
        for added in scenario.added_resources[:3]:
            st.caption(f"• {added['name']}: {added['hours']}h @ ${added['rate']}/hr")
        if len(scenario.added_resources) > 3:
            st.caption(f"  ...and {len(scenario.added_resources) - 3} more")

    # Resource Adjustments (only show non-zero)
    adjustments = {k: v for k, v in scenario.resource_adjustments.items() if abs(v) > 0}
    if adjustments:
        has_changes = True
        st.markdown(f"**🔧 Hour Adjustments** ({len(adjustments)})")
        sorted_adjustments = sorted(adjustments.items(), key=lambda x: abs(x[1]), reverse=True)
        for resource_name, delta in sorted_adjustments[:3]:
            sign = "+" if delta > 0 else ""
            st.caption(f"• {resource_name}: {sign}{delta:,.0f}h")
        if len(adjustments) > 3:
            st.caption(f"  ...and {len(adjustments) - 3} more")

    if not has_changes:
        st.caption("No modifications yet. Use the panels on the left to make changes.")

    # Before vs After summary
    st.markdown("---")
    st.markdown("#### Baseline vs Scenario")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📍 Baseline**")
        st.caption(f"Hours: {base.total_allocated:,.0f}h")
        st.caption(f"Util: {base_utilization:.1f}%")
        st.caption(f"Cost: ${base_cost:,.0f}")

    with col2:
        st.markdown("**🎯 Scenario**")
        st.caption(f"Hours: {scenario.modified_allocated:,.0f}h")
        st.caption(f"Util: {modified_utilization:.1f}%")
        st.caption(f"Cost: ${scenario.modified_cost:,.0f}")


def _render_scenario_editor(scenario: Scenario) -> None:
    """Render the scenario editor with side-by-side layout."""
    # Scenario header
    col1, col2 = st.columns([4, 1])

    with col1:
        new_name = st.text_input("Scenario Name", value=scenario.name, key=f"name_{scenario.name}")
        if new_name != scenario.name:
            # Rename scenario
            old_name = scenario.name
            scenario.name = new_name
            st.session_state.scenarios[new_name] = scenario
            del st.session_state.scenarios[old_name]

    with col2:
        st.write("")  # Spacing
        if st.button("🗑️ Delete", key=f"del_{scenario.name}"):
            st.session_state.pending_delete_scenario = scenario.name
            st.rerun()

    scenario.description = st.text_area(
        "Description",
        value=scenario.description,
        key=f"desc_{scenario.name}",
        height=60
    )

    st.markdown("---")

    # Count active modifications for badge labels
    num_removed_projects = len(scenario.removed_projects)
    num_removed_resources = len(scenario.removed_resources)
    num_added_resources = len(scenario.added_resources)
    num_adjustments = len([v for v in scenario.resource_adjustments.values() if abs(v) > 0])

    # Two-column layout: Modifications on left, Live Impact on right
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.markdown("### 🔧 Modifications")

        # Remove Projects expander
        projects_label = f"📁 Remove Projects ({num_removed_projects})" if num_removed_projects else "📁 Remove Projects"
        with st.expander(projects_label, expanded=num_removed_projects > 0):
            _render_project_removal(scenario)

        # Adjust Resource Hours expander
        adjustments_label = f"👥 Adjust Resource Hours ({num_adjustments})" if num_adjustments else "👥 Adjust Resource Hours"
        with st.expander(adjustments_label, expanded=num_adjustments > 0):
            _render_resource_adjustments(scenario)

        # Add/Remove Resources expander
        resources_count = num_added_resources + num_removed_resources
        resources_label = f"➕ Add/Remove Resources ({resources_count})" if resources_count else "➕ Add/Remove Resources"
        with st.expander(resources_label, expanded=resources_count > 0):
            _render_resource_management(scenario)

    with right_col:
        _render_live_impact_panel(scenario)


def _render_scenario_comparison(scenarios: list[Scenario], base_analysis: PIAnalysis, base_cost: float) -> None:
    """Render comparison of all scenarios."""
    st.markdown("### 📊 Scenario Comparison")

    if not scenarios:
        st.info("Create scenarios to compare them here.")
        return

    # Recalculate all scenarios
    for scenario in scenarios:
        calculate_scenario_impact(scenario)

    base_utilization = (base_analysis.total_allocated / base_analysis.total_capacity * 100) if base_analysis.total_capacity > 0 else 0

    # Comparison table
    comparison_data = []

    # Add baseline
    comparison_data.append({
        "Scenario": "📍 Baseline",
        "Allocated": f"{base_analysis.total_allocated:,.0f}h",
        "Utilization": f"{base_utilization:.1f}%",
        "Cost": f"${base_cost:,.0f}",
        "Cost Delta": "-",
        "Status": "🟢" if base_utilization <= 100 else "🔴"
    })

    # Add scenarios
    for scenario in scenarios:
        modified_util = (scenario.modified_allocated / scenario.modified_capacity * 100) if scenario.modified_capacity > 0 else 0
        status = "🟢" if modified_util <= 100 else "🔴" if modified_util > 110 else "🟡"

        comparison_data.append({
            "Scenario": scenario.name,
            "Allocated": f"{scenario.modified_allocated:,.0f}h",
            "Utilization": f"{modified_util:.1f}%",
            "Cost": f"${scenario.modified_cost:,.0f}",
            "Cost Delta": f"${scenario.cost_delta:+,.0f}",
            "Status": status
        })

    st.dataframe(comparison_data, width="stretch", hide_index=True)

    # Visual bars
    st.markdown("#### Utilization Comparison")

    for scenario in scenarios:
        modified_util = (scenario.modified_allocated / scenario.modified_capacity * 100) if scenario.modified_capacity > 0 else 0
        color = "#28a745" if modified_util <= 80 else "#f39c12" if modified_util <= 100 else "#dc3545"

        col1, col2 = st.columns([1, 3])
        with col1:
            st.write(f"**{scenario.name}**")
        with col2:
            st.markdown(
                f"""
                <div style="background: #e0e0e0; border-radius: 10px; height: 25px; position: relative;">
                    <div style="background: {color}; width: {min(modified_util, 100)}%; height: 100%; border-radius: 10px;"></div>
                    <span style="position: absolute; right: 10px; top: 3px; font-size: 12px;">{modified_util:.0f}%</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Recommendation
    st.markdown("---")
    st.markdown("#### 💡 Recommendation")

    # Find best scenario (highest utilization under 100%)
    valid_scenarios = [s for s in scenarios if (s.modified_allocated / s.modified_capacity * 100) <= 100]

    if valid_scenarios:
        best = max(valid_scenarios, key=lambda s: s.modified_allocated / s.modified_capacity)
        best_util = (best.modified_allocated / best.modified_capacity * 100)
        st.success(
            f"**{best.name}** provides the best balance with {best_util:.1f}% utilization "
            f"and a cost impact of ${best.cost_delta:+,.0f}"
        )
    else:
        st.warning("All scenarios result in over-allocation. Consider reducing scope or adding resources.")


# ============================================================================
# Main Content
# ============================================================================

base_analysis = get_base_analysis()

if not base_analysis:
    st.warning(
        "**No PI analysis data available.**\n\n"
        "Please go to the Analysis page and upload your capacity planner Excel file first. "
        "The scenario planner uses that data as the baseline for simulations."
    )

    if st.button("Go to Analysis Page"):
        st.switch_page("pages/1_Analyze.py")

else:
    # Show baseline metrics
    st.markdown("### 📊 Baseline Metrics")

    base_cost = sum(
        r.total_hours * r.rate
        for r in base_analysis.resources.values()
        if r.rate > 0
    )
    base_utilization = (base_analysis.total_allocated / base_analysis.total_capacity * 100) if base_analysis.total_capacity > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Capacity", f"{base_analysis.total_capacity:,.0f}h")
    with col2:
        st.metric("Total Allocated", f"{base_analysis.total_allocated:,.0f}h")
    with col3:
        st.metric("Utilization", f"{base_utilization:.1f}%")
    with col4:
        st.metric("Total Cost", f"${base_cost:,.0f}")

    st.markdown("---")

    # Scenario management header
    st.markdown("### 🔮 Scenarios")

    # Scenario tabs
    if st.session_state.scenarios:
        scenario_names = list(st.session_state.scenarios.keys())
        tabs = st.tabs(scenario_names + ["📊 Compare All"])

        for i, scenario_name in enumerate(scenario_names):
            with tabs[i]:
                scenario = st.session_state.scenarios[scenario_name]
                _render_scenario_editor(scenario)

        # Comparison tab
        with tabs[-1]:
            _render_scenario_comparison(list(st.session_state.scenarios.values()), base_analysis, base_cost)

    else:
        st.info("No scenarios created yet. Use the sidebar to create a new scenario or start from a template.")


# Sidebar
with st.sidebar:
    # New Scenario button (prominent)
    if base_analysis:
        if st.button("➕ New Scenario", type="primary", use_container_width=True):
            scenario_num = len(st.session_state.scenarios) + 1
            new_scenario = Scenario(
                name=f"Scenario {scenario_num}",
                base_analysis=base_analysis,
            )
            st.session_state.scenarios[new_scenario.name] = new_scenario
            st.session_state.active_scenario = new_scenario.name
            st.toast(f'Created "{new_scenario.name}"', icon="✨")
            st.rerun()

        st.markdown("---")

        # Quick Start Templates (always visible)
        st.markdown("### Quick Start Templates")

        if st.button("🔻 Reduce 10% Capacity", use_container_width=True):
            scenario = Scenario(
                name="Reduced Capacity",
                description="Simulate 10% reduction in team capacity",
                base_analysis=base_analysis,
            )
            for name, resource in base_analysis.resources.items():
                scenario.resource_adjustments[name] = -resource.total_hours * 0.10
            st.session_state.scenarios[scenario.name] = calculate_scenario_impact(scenario)
            st.toast('Created "Reduced Capacity" scenario', icon="✨")
            st.rerun()

        if st.button("➕ Add Contractor", use_container_width=True):
            scenario = Scenario(
                name="Added Contractor",
                description="Add a contractor resource",
                base_analysis=base_analysis,
                added_resources=[{"name": "Contractor", "hours": 160, "rate": 150}]
            )
            st.session_state.scenarios[scenario.name] = calculate_scenario_impact(scenario)
            st.toast('Created "Added Contractor" scenario', icon="✨")
            st.rerun()

        if st.button("⚡ Aggressive Timeline", use_container_width=True):
            scenario = Scenario(
                name="Aggressive Timeline",
                description="Increase allocation by 20%",
                base_analysis=base_analysis,
            )
            for name, resource in base_analysis.resources.items():
                scenario.resource_adjustments[name] = resource.total_hours * 0.20
            st.session_state.scenarios[scenario.name] = calculate_scenario_impact(scenario)
            st.toast('Created "Aggressive Timeline" scenario', icon="✨")
            st.rerun()

        if st.button("🗑️ Remove a Project", use_container_width=True):
            largest_project = None
            largest_hours = 0
            for name, project in base_analysis.projects.items():
                if project.total_hours > largest_hours:
                    largest_hours = project.total_hours
                    largest_project = name

            scenario = Scenario(
                name="Project Removal",
                description="Evaluate impact of removing a project from the PI",
                base_analysis=base_analysis,
                removed_projects=[largest_project] if largest_project else []
            )
            st.session_state.scenarios[scenario.name] = calculate_scenario_impact(scenario)
            st.toast('Created "Project Removal" scenario', icon="✨")
            st.rerun()

    st.markdown("---")

    # Quick Actions (when scenarios exist)
    if st.session_state.scenarios:
        st.markdown("### Quick Actions")

        if st.button("🗑️ Clear All Scenarios", use_container_width=True):
            st.session_state.pending_clear_all = True
            st.rerun()

        if st.button("📋 Export Summary", use_container_width=True):
            # Generate summary text
            summary = "# Scenario Planning Summary\n\n"
            for scenario in st.session_state.scenarios.values():
                summary += f"## {scenario.name}\n"
                summary += f"{scenario.description}\n\n"
                summary += f"- Cost Delta: ${scenario.cost_delta:+,.0f}\n"
                summary += f"- Utilization Delta: {scenario.utilization_delta:+.1f}%\n\n"

            st.download_button(
                "📥 Download Summary",
                data=summary,
                file_name="scenario_summary.md",
                mime="text/markdown",
                use_container_width=True
            )

        st.markdown("---")

    # Tips section
    st.markdown("### Tips")
    st.markdown(
        """
        **When to use scenarios:**
        - Evaluating resource changes
        - Planning for contingencies
        - Comparing cost options

        **Best practices:**
        - Start with realistic adjustments
        - Consider both cost and utilization
        - Document your assumptions
        """
    )


# Handle confirmation dialogs
if st.session_state.pending_delete_scenario:
    confirm_delete_scenario(st.session_state.pending_delete_scenario)

if st.session_state.pending_clear_all:
    confirm_clear_all()
