"""Chart Preview — demo page to visualize all Plotly chart components."""

import sys
from pathlib import Path

_src_dir = Path(__file__).parent.parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import streamlit as st

from pi_strategist.models import (
    AcceptanceCriteria,
    DeploymentCluster,
    DeploymentStrategy,
    RedFlag,
    RedFlagSeverity,
    Sprint,
    SprintStatus,
    Task,
)
from pi_strategist.analyzers.capacity_analyzer import SprintAnalysis
from pi_strategist.parsers.pi_planner_parser import PIAnalysis, Project, Resource
from pi_strategist.web.theme import CYAN, BLUE, TEXT_MUTED
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
from pi_strategist.reporters.csv_export import (
    red_flags_to_csv,
    capacity_to_csv,
    deployment_to_csv,
    resources_to_csv,
    render_csv_download,
)

st.set_page_config(page_title="Chart Preview", page_icon="📈", layout="wide")

# ─── Header ──────────────────────────────────────────────────────

st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
        <div style="display:flex;gap:4px;">
            <div style="width:6px;height:28px;background:{CYAN};border-radius:2px;"></div>
            <div style="width:6px;height:28px;background:{BLUE};border-radius:2px;"></div>
        </div>
        <h1 style="margin:0;">Chart Preview</h1>
    </div>
    <p style="color:{TEXT_MUTED};margin-top:0;">
        Live preview of all Plotly chart components with the Parallax theme.
    </p>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")


# ─── Sample Data Factories ───────────────────────────────────────


def _sample_sprint_analyses() -> list[SprintAnalysis]:
    sprints_raw = [
        ("Sprint 1", 200, [("API Design", 30), ("DB Schema", 25), ("Auth Service", 40), ("Unit Tests", 20)]),
        ("Sprint 2", 200, [("API Endpoints", 45), ("Frontend Shell", 35), ("Integration", 30), ("Perf Testing", 25)]),
        ("Sprint 3", 180, [("Dashboard UI", 50), ("Reporting", 35), ("Search", 40), ("Bug Fixes", 20)]),
        ("Sprint 4", 180, [("Deploy Pipeline", 30), ("Monitoring", 25), ("Docs", 15), ("Hardening", 45), ("Load Test", 30)]),
    ]
    analyses = []
    for name, total, task_list in sprints_raw:
        tasks = [Task(id=f"T-{i}", name=n, hours=h, sprint=name) for i, (n, h) in enumerate(task_list, 1)]
        sprint = Sprint(name=name, total_hours=total, buffer_percentage=0.20, tasks=tasks)
        load = sprint.sprint_load
        net = sprint.net_capacity
        analyses.append(SprintAnalysis(
            sprint=sprint,
            status=SprintStatus.PASS if load <= net else SprintStatus.FAIL,
            overflow_hours=load - net,
            utilization_percent=(load / net * 100) if net > 0 else 0,
            recommendations=[],
            high_risk_tasks=[t for t in tasks if t.hours >= 40],
        ))
    return analyses


def _sample_red_flags() -> list[RedFlag]:
    flags = []
    samples = [
        ("fast", "Subjective Terms", RedFlagSeverity.CRITICAL, "The system should be fast"),
        ("user-friendly", "Subjective Terms", RedFlagSeverity.CRITICAL, "The UI must be user-friendly"),
        ("scalable", "Vague Metrics", RedFlagSeverity.CRITICAL, "The API should be scalable"),
        ("high quality", "Vague Metrics", RedFlagSeverity.MODERATE, "Code should be high quality"),
        ("performant", "Vague Metrics", RedFlagSeverity.MODERATE, "The backend must be performant"),
        ("works well", "Missing Criteria", RedFlagSeverity.MODERATE, "Integration works well with system"),
        ("looks good", "Missing Criteria", RedFlagSeverity.MODERATE, "The dashboard looks good"),
        ("comprehensive", "Undefined Scope", RedFlagSeverity.LOW, "Provide comprehensive logging"),
        ("improved", "Comparative Terms", RedFlagSeverity.LOW, "Improved search experience"),
        ("better", "Comparative Terms", RedFlagSeverity.LOW, "Better error handling"),
        ("robust", "Subjective Terms", RedFlagSeverity.CRITICAL, "Build a robust system"),
        ("complete", "Undefined Scope", RedFlagSeverity.MODERATE, "Complete test coverage"),
    ]
    for i, (term, cat, sev, text) in enumerate(samples, 1):
        flags.append(RedFlag(
            severity=sev,
            flagged_term=term,
            category=cat,
            ac=AcceptanceCriteria(id=f"AC-{i:03d}", text=text, story_id=f"STORY-{(i % 4) + 1:03d}", epic_id="EPIC-001"),
            suggested_metric=f"Replace '{term}' with a measurable metric",
            negotiation_script=f"Can we define what '{term}' means quantitatively?",
        ))
    return flags


def _sample_deployment_clusters() -> list[DeploymentCluster]:
    return [
        DeploymentCluster(
            name="Auth Module", strategy=DeploymentStrategy.FEATURE_FLAG, deploy_timing="Sprint 1 End",
            tasks=[Task(id="T-1", name="OAuth2 Flow", hours=20, sprint="Sprint 1"),
                   Task(id="T-2", name="JWT Tokens", hours=15, sprint="Sprint 1"),
                   Task(id="T-3", name="SSO Integration", hours=25, sprint="Sprint 1")],
            dependencies=[], rollback_plan="Disable feature flag",
        ),
        DeploymentCluster(
            name="Dashboard v2", strategy=DeploymentStrategy.FEATURE_FLAG, deploy_timing="Sprint 2 End",
            tasks=[Task(id="T-4", name="Charts", hours=30, sprint="Sprint 2"),
                   Task(id="T-5", name="Filters", hours=20, sprint="Sprint 2")],
            dependencies=["Auth Module"], rollback_plan="Revert to v1 flag",
        ),
        DeploymentCluster(
            name="Search Overhaul", strategy=DeploymentStrategy.FULL_DEPLOYMENT, deploy_timing="Sprint 3 End",
            tasks=[Task(id="T-6", name="Elasticsearch Migration", hours=40, sprint="Sprint 3"),
                   Task(id="T-7", name="Query Parser", hours=20, sprint="Sprint 3"),
                   Task(id="T-8", name="Index Rebuild", hours=15, sprint="Sprint 3"),
                   Task(id="T-9", name="Search UI", hours=25, sprint="Sprint 3")],
            dependencies=[], rollback_plan="Full rollback to legacy search",
        ),
        DeploymentCluster(
            name="Monitoring Stack", strategy=DeploymentStrategy.FULL_DEPLOYMENT, deploy_timing="Sprint 4 End",
            tasks=[Task(id="T-10", name="Prometheus Setup", hours=20, sprint="Sprint 4"),
                   Task(id="T-11", name="Grafana Dashboards", hours=15, sprint="Sprint 4")],
            dependencies=[], rollback_plan="Revert infrastructure changes",
        ),
    ]


def _sample_pi_analysis() -> PIAnalysis:
    sprints = {
        "Sprint 1": {"capacity": 800},
        "Sprint 2": {"capacity": 780},
        "Sprint 3": {"capacity": 750},
        "Sprint 4": {"capacity": 720},
    }
    resources = {}
    team = [
        ("Alice Chen", "Backend Engineering", 150, {"Sprint 1": 120, "Sprint 2": 130, "Sprint 3": 110, "Sprint 4": 100}),
        ("Bob Martinez", "Backend Engineering", 140, {"Sprint 1": 110, "Sprint 2": 100, "Sprint 3": 120, "Sprint 4": 130}),
        ("Carol Wu", "Frontend Engineering", 125, {"Sprint 1": 80, "Sprint 2": 100, "Sprint 3": 120, "Sprint 4": 110}),
        ("Dave Park", "Frontend Engineering", 125, {"Sprint 1": 90, "Sprint 2": 110, "Sprint 3": 100, "Sprint 4": 105}),
        ("Eve Johnson", "Quality Assurance", 130, {"Sprint 1": 60, "Sprint 2": 80, "Sprint 3": 100, "Sprint 4": 120}),
        ("Frank Lee", "DevOps", 160, {"Sprint 1": 140, "Sprint 2": 130, "Sprint 3": 120, "Sprint 4": 110}),
        ("Grace Kim", "Business Analysis", 120, {"Sprint 1": 100, "Sprint 2": 90, "Sprint 3": 80, "Sprint 4": 70}),
        ("Hank Patel", "Project Management", 110, {"Sprint 1": 80, "Sprint 2": 70, "Sprint 3": 60, "Sprint 4": 50}),
        ("Iris Torres", "Design", 100, {"Sprint 1": 90, "Sprint 2": 80, "Sprint 3": 70, "Sprint 4": 60}),
        ("Jack Rivera", "Backend Engineering", 145, {"Sprint 1": 130, "Sprint 2": 120, "Sprint 3": 115, "Sprint 4": 100}),
        ("Karen Zhao", "Quality Assurance", 130, {"Sprint 1": 70, "Sprint 2": 90, "Sprint 3": 110, "Sprint 4": 115}),
        ("Leo Nguyen", "Frontend Engineering", 135, {"Sprint 1": 100, "Sprint 2": 110, "Sprint 3": 105, "Sprint 4": 95}),
    ]
    for name, disc, rate, sprint_hrs in team:
        total = sum(sprint_hrs.values())
        resources[name] = Resource(
            name=name, discipline=disc, rate=rate,
            total_hours=total, sprint_hours=sprint_hrs,
        )

    projects = {
        "Auth Platform": Project(name="Auth Platform", priority=1, total_hours=420,
                                  sprint_allocation={"Sprint 1": True, "Sprint 2": True}),
        "Dashboard v2": Project(name="Dashboard v2", priority=2, total_hours=580,
                                 sprint_allocation={"Sprint 2": True, "Sprint 3": True}),
        "Search Overhaul": Project(name="Search Overhaul", priority=1, total_hours=350,
                                    sprint_allocation={"Sprint 3": True, "Sprint 4": True}),
        "Monitoring": Project(name="Monitoring", priority=3, total_hours=210,
                               sprint_allocation={"Sprint 4": True}),
    }

    return PIAnalysis(sprints=sprints, resources=resources, projects=projects)


# ─── Page Layout ─────────────────────────────────────────────────

# Generate sample data
analyses = _sample_sprint_analyses()
red_flags = _sample_red_flags()
clusters = _sample_deployment_clusters()
pi_analysis = _sample_pi_analysis()

# ─── Capacity Section ────────────────────────────────────────────
st.header("Capacity Analysis")

cap_col1, cap_col2 = st.columns(2)
with cap_col1:
    st.markdown("#### Capacity vs Load")
    render_capacity_burndown_chart(analyses)
with cap_col2:
    st.markdown("#### Utilization Trend")
    render_utilization_trend_chart(analyses)

render_csv_download(capacity_to_csv(analyses), "capacity_preview.csv", "Download Capacity CSV")

st.markdown("---")

# ─── Red Flags Section ───────────────────────────────────────────
st.header("Red Flag Analysis")

rf_col1, rf_col2 = st.columns(2)
with rf_col1:
    st.markdown("#### Severity Distribution")
    render_risk_distribution_chart(red_flags)
with rf_col2:
    st.markdown("#### By Category")
    render_risk_by_category_chart(red_flags)

render_csv_download(red_flags_to_csv(red_flags), "red_flags_preview.csv", "Download Red Flags CSV")

st.markdown("---")

# ─── Deployment Section ──────────────────────────────────────────
st.header("Deployment Strategy")

dep_col1, dep_col2 = st.columns([1, 2])
with dep_col1:
    st.markdown("#### Strategy Breakdown")
    render_deployment_strategy_chart(clusters)
with dep_col2:
    st.markdown("#### Cluster Summary")
    for c in clusters:
        strategy_label = c.strategy.value.replace("_", " ").title()
        st.markdown(f"- **{c.name}** — {strategy_label} ({len(c.tasks)} tasks, {c.deploy_timing})")

render_csv_download(deployment_to_csv(clusters), "deployment_preview.csv", "Download Deployment CSV")

st.markdown("---")

# ─── Resource Section ────────────────────────────────────────────
st.header("Resource Allocation")

res_col1, res_col2 = st.columns(2)
with res_col1:
    st.markdown("#### Allocation Distribution")
    render_allocation_distribution_chart(pi_analysis)
with res_col2:
    st.markdown("#### Resource Heatmap (Hours per Sprint)")
    render_resource_heatmap(pi_analysis)

render_csv_download(resources_to_csv(pi_analysis.resources), "resources_preview.csv", "Download Resources CSV")

st.markdown("---")

# ─── Financial Section ───────────────────────────────────────────
st.header("Financial Overview")

fin_col1, fin_col2 = st.columns(2)
with fin_col1:
    st.markdown("#### Cost by Discipline")
    render_cost_by_discipline_chart(pi_analysis)
with fin_col2:
    st.markdown("#### Cost by Sprint")
    render_sprint_cost_chart(pi_analysis)
