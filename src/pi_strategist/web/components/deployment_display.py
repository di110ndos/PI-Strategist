"""Deployment analysis visualization component."""

import streamlit as st
from typing import Optional

from pi_strategist.models import DeploymentCluster, DeploymentStrategy
from pi_strategist.web.theme import COLORS, STRATEGY_COLORS, BORDER, BORDER_LIGHT, TEXT_MUTED
from pi_strategist.web.components.charts import render_deployment_strategy_chart
from pi_strategist.reporters.csv_export import deployment_to_csv, render_csv_download


def render_deployment_analysis(
    clusters: list[DeploymentCluster],
    summary: Optional[dict] = None,
) -> None:
    """Render the deployment analysis display.

    Args:
        clusters: List of deployment clusters to display
        summary: Optional summary dictionary
    """
    if not clusters:
        st.warning("No deployment clusters identified.")
        return

    # Summary with CD gauge
    _render_summary_metrics(clusters, summary)

    st.markdown("---")

    # Strategy breakdown chart
    chart_col1, chart_col2 = st.columns([1, 2])
    with chart_col1:
        st.markdown("#### Strategy Breakdown")
        render_deployment_strategy_chart(clusters)
    with chart_col2:
        # Deployment timeline
        st.markdown("#### Deployment Timeline")
        _render_timeline(clusters)

    st.markdown("---")

    # Cluster details
    st.subheader("Cluster Details")
    _render_cluster_cards(clusters)

    # CSV export
    st.markdown("---")
    render_csv_download(deployment_to_csv(clusters), "deployment_clusters.csv", "Download Deployment CSV")


def _render_summary_metrics(
    clusters: list[DeploymentCluster],
    summary: Optional[dict] = None,
) -> None:
    """Render summary metrics including CD percentage gauge."""
    if summary is None:
        eligible = sum(len(c.tasks) for c in clusters)
        total = eligible  # Without external context, assume all tasks are in clusters
        percentage = 100.0
        target_met = True
    else:
        eligible = summary.get("eligible_tasks", 0)
        total = summary.get("total_tasks", 0)
        percentage = summary.get("cd_percentage", 0)
        target_met = summary.get("target_met", False)
        target_percentage = summary.get("target_percentage", 30)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # CD Percentage Gauge
        st.markdown("#### Continuous Delivery Readiness")

        gauge_color = COLORS["pass"] if target_met else COLORS["warning"] if percentage >= 20 else COLORS["fail"]

        st.markdown(
            f"""
            <div style="text-align: center; margin: 20px 0;">
                <div style="position: relative; width: 200px; height: 100px; margin: 0 auto;
                     background: linear-gradient(to right, {COLORS['fail']} 0%, {COLORS['warning']} 50%, {COLORS['pass']} 100%);
                     border-radius: 200px 200px 0 0; overflow: hidden;">
                    <div style="position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
                         width: 160px; height: 80px; background: {BORDER}; border-radius: 200px 200px 0 0;"></div>
                    <div style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
                         font-size: 2em; font-weight: bold; color: {gauge_color};">{percentage:.1f}%</div>
                </div>
                <div style="font-size: 0.9em; color: {TEXT_MUTED}; margin-top: 5px;">
                    {"✓ Target Met" if target_met else "⚠ Below Target"}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.metric(
            label="Eligible Tasks",
            value=eligible,
            help="Tasks identified for early deployment",
        )
        st.metric(
            label="Total Tasks",
            value=total,
        )

    with col3:
        st.metric(
            label="Clusters",
            value=len(clusters),
        )

        # Strategy breakdown if available
        if summary and "strategies" in summary:
            st.markdown("**Strategies:**")
            for strategy, count in summary["strategies"].items():
                st.caption(f"{strategy}: {count}")


def _render_timeline(clusters: list[DeploymentCluster]) -> None:
    """Render deployment timeline."""
    if not clusters:
        return

    # Create timeline visualization
    for i, cluster in enumerate(clusters):
        strategy_color = STRATEGY_COLORS.get(cluster.strategy, "{TEXT_MUTED}")

        cols = st.columns([1, 4])

        with cols[0]:
            st.markdown(
                f"""
                <div style="background-color: {strategy_color}; color: white;
                     padding: 10px; border-radius: 8px; text-align: center;
                     font-weight: bold;">
                    {cluster.deploy_timing}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with cols[1]:
            st.markdown(f"**{cluster.name}**")
            st.caption(
                f"{len(cluster.tasks)} tasks | Strategy: {cluster.strategy.value.replace('_', ' ').title()}"
            )

        # Timeline connector
        if i < len(clusters) - 1:
            st.markdown(
                """
                <div style="margin-left: 40px; border-left: 3px solid {BORDER_LIGHT}; height: 20px;"></div>
                """,
                unsafe_allow_html=True,
            )


def _render_cluster_cards(clusters: list[DeploymentCluster]) -> None:
    """Render detailed cluster cards."""
    for cluster in clusters:
        _render_cluster_card(cluster)


def _render_cluster_card(cluster: DeploymentCluster) -> None:
    """Render a single cluster card."""
    strategy_color = STRATEGY_COLORS.get(cluster.strategy, "{TEXT_MUTED}")
    strategy_name = cluster.strategy.value.replace("_", " ").title()

    with st.expander(f"**{cluster.name}** | {strategy_name} | {len(cluster.tasks)} tasks"):
        # Strategy badge
        st.markdown(
            f"""
            <span style="background-color: {strategy_color}; color: white;
                 padding: 4px 12px; border-radius: 4px; font-size: 0.9em;">
                {strategy_name}
            </span>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Deployment Timing:**")
            st.write(cluster.deploy_timing)

            st.markdown("**Rollback Plan:**")
            st.info(cluster.rollback_plan)

        with col2:
            if cluster.dependencies:
                st.markdown("**External Dependencies:**")
                for dep in cluster.dependencies:
                    st.write(f"- {dep}")
            else:
                st.markdown("**External Dependencies:**")
                st.write("None - can be deployed independently")

        st.markdown("---")

        # Tasks table
        st.markdown("**Tasks in Cluster:**")

        task_data = [
            {
                "ID": task.id,
                "Name": task.name,
                "Hours": task.hours,
                "Sprint": task.sprint,
            }
            for task in cluster.tasks
        ]

        st.dataframe(task_data, use_container_width=True)


def render_deployment_table(clusters: list[DeploymentCluster]) -> None:
    """Render deployment data in a table format."""
    if not clusters:
        st.info("No deployment clusters to display.")
        return

    data = []
    for cluster in clusters:
        data.append(
            {
                "Cluster": cluster.name,
                "Strategy": cluster.strategy.value.replace("_", " ").title(),
                "Timing": cluster.deploy_timing,
                "Tasks": len(cluster.tasks),
                "Dependencies": len(cluster.dependencies),
                "Rollback": cluster.rollback_plan[:50] + "..." if len(cluster.rollback_plan) > 50 else cluster.rollback_plan,
            }
        )

    st.dataframe(data, use_container_width=True)


def render_strategy_legend() -> None:
    """Render a legend for deployment strategies."""
    st.markdown("#### Deployment Strategies")

    strategies = [
        (DeploymentStrategy.FEATURE_FLAG, "Feature Flag", "Toggle features on/off for specific users or groups - allows instant rollback"),
        (DeploymentStrategy.FULL_DEPLOYMENT, "Full Deployment", "Deploy complete feature to all users - requires full testing before release"),
    ]

    for strategy, name, description in strategies:
        color = STRATEGY_COLORS.get(strategy, "{TEXT_MUTED}")
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; margin: 5px 0;">
                <span style="background-color: {color}; width: 20px; height: 20px;
                     border-radius: 4px; display: inline-block; margin-right: 10px;"></span>
                <strong>{name}:</strong>&nbsp;{description}
            </div>
            """,
            unsafe_allow_html=True,
        )
