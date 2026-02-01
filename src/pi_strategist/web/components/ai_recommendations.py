"""AI Recommendations display component."""

import streamlit as st
from typing import Optional

from pi_strategist.analyzers.ai_advisor import AIAdvisor, AIAnalysisResult, AIRecommendation


# Color scheme for priorities
PRIORITY_COLORS = {
    "high": "#e74c3c",
    "medium": "#f39c12",
    "low": "#3498db",
}

CATEGORY_ICONS = {
    "capacity": "📊",
    "risk": "⚠️",
    "cost": "💰",
    "resource": "👥",
    "general": "💡",
}


def render_ai_recommendations(
    pi_analysis,
    capacity_plan=None,
    red_flags: list = None,
    api_key: Optional[str] = None,
) -> None:
    """Render AI-powered recommendations section.

    Args:
        pi_analysis: PIAnalysis object
        capacity_plan: Optional CapacityPlan object
        red_flags: Optional list of red flags
        api_key: Optional API key (uses env var if not provided)
    """
    st.subheader("🤖 AI-Powered Recommendations")

    # Check for API key
    advisor = AIAdvisor(api_key=api_key)

    if not advisor.is_available:
        st.warning(
            "**AI features require an Anthropic API key.**\n\n"
            "Configure your API key in the Settings page to enable:\n"
            "- Intelligent recommendations\n"
            "- Executive summaries\n"
            "- Rebalancing suggestions"
        )

        # Show what features would be available
        with st.expander("Preview AI Features"):
            st.markdown("""
            **With AI enabled, you'll get:**

            1. **Executive Summary** - Auto-generated overview for leadership
            2. **Smart Recommendations** - Prioritized action items based on your data
            3. **Risk Assessment** - AI-identified concerns and mitigation strategies
            4. **Rebalancing Suggestions** - Specific moves to optimize capacity
            5. **Optimization Opportunities** - Ways to improve efficiency
            """)
        return

    # Analysis controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Run Full Analysis", type="primary", width="stretch"):
            with st.spinner("AI is analyzing your PI data..."):
                result = advisor.analyze_pi_planning(pi_analysis, capacity_plan, red_flags)
                st.session_state.ai_analysis_result = result

    with col2:
        if st.button("📝 Generate Summary", width="stretch"):
            with st.spinner("Generating executive summary..."):
                summary = advisor.generate_executive_summary(pi_analysis, capacity_plan)
                st.session_state.ai_summary = summary

    with col3:
        if st.button("⚖️ Suggest Rebalancing", width="stretch"):
            with st.spinner("Analyzing capacity..."):
                suggestions = advisor.suggest_rebalancing(pi_analysis, capacity_plan)
                st.session_state.ai_rebalancing = suggestions

    st.markdown("---")

    # Display results
    if "ai_analysis_result" in st.session_state and st.session_state.ai_analysis_result:
        _render_analysis_result(st.session_state.ai_analysis_result)

    if "ai_summary" in st.session_state and st.session_state.ai_summary:
        _render_summary(st.session_state.ai_summary)

    if "ai_rebalancing" in st.session_state and st.session_state.ai_rebalancing:
        _render_rebalancing(st.session_state.ai_rebalancing)


def _render_analysis_result(result: AIAnalysisResult) -> None:
    """Render full AI analysis result."""
    if not result.success:
        st.error(f"Analysis failed: {result.error_message}")
        return

    # Executive Summary
    if result.executive_summary:
        st.markdown("### 📋 Executive Summary")
        st.info(result.executive_summary)

    # Risk Assessment
    if result.risk_assessment:
        st.markdown("### ⚠️ Risk Assessment")
        st.warning(result.risk_assessment)

    # Recommendations
    if result.recommendations:
        st.markdown("### 💡 Recommendations")
        _render_recommendations_list(result.recommendations)

    # Optimization Opportunities
    if result.optimization_opportunities:
        st.markdown("### 🚀 Optimization Opportunities")
        for opp in result.optimization_opportunities:
            st.markdown(f"- {opp}")

    # Key Metrics Commentary
    if result.key_metrics_commentary:
        st.markdown("### 📊 Metrics Analysis")
        st.write(result.key_metrics_commentary)


def _render_recommendations_list(recommendations: list[AIRecommendation]) -> None:
    """Render list of recommendations."""
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_recs = sorted(recommendations, key=lambda r: priority_order.get(r.priority, 3))

    for rec in sorted_recs:
        _render_recommendation_card(rec)


def _render_recommendation_card(rec: AIRecommendation) -> None:
    """Render a single recommendation card."""
    priority_color = PRIORITY_COLORS.get(rec.priority, "#666")
    category_icon = CATEGORY_ICONS.get(rec.category, "💡")

    with st.expander(
        f"{category_icon} **{rec.title}** | {rec.priority.upper()}",
        expanded=rec.priority == "high"
    ):
        # Priority badge
        st.markdown(
            f'<span style="background-color: {priority_color}; color: white; '
            f'padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">'
            f'{rec.priority.upper()} PRIORITY</span>',
            unsafe_allow_html=True
        )

        st.markdown(f"**Category:** {rec.category.capitalize()}")

        st.markdown("---")

        # Description
        st.markdown("**Description:**")
        st.write(rec.description)

        # Action items
        if rec.action_items:
            st.markdown("**Action Items:**")
            for i, action in enumerate(rec.action_items, 1):
                st.markdown(f"{i}. {action}")

        # Impact
        if rec.impact:
            st.markdown("**Expected Impact:**")
            st.success(rec.impact)

        # Affected items
        col1, col2 = st.columns(2)

        with col1:
            if rec.affected_resources:
                st.markdown("**Affected Resources:**")
                for resource in rec.affected_resources:
                    st.write(f"- {resource}")

        with col2:
            if rec.affected_sprints:
                st.markdown("**Affected Sprints:**")
                for sprint in rec.affected_sprints:
                    st.write(f"- {sprint}")


def _render_summary(summary: str) -> None:
    """Render executive summary."""
    st.markdown("### 📝 Executive Summary")

    with st.container():
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                 padding: 20px; border-radius: 10px; color: white;">
                <h4 style="margin-top: 0;">AI-Generated Summary</h4>
                <p style="white-space: pre-wrap;">{summary}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Copy button
    st.code(summary, language=None)


def _render_rebalancing(suggestions: list[dict]) -> None:
    """Render rebalancing suggestions."""
    st.markdown("### ⚖️ Rebalancing Suggestions")

    if not suggestions:
        st.info("No rebalancing suggestions available.")
        return

    for i, suggestion in enumerate(suggestions, 1):
        if "error" in suggestion:
            st.error(f"Error: {suggestion['error']}")
            continue

        if "suggestion" in suggestion:
            st.info(suggestion["suggestion"])
            continue

        # Full suggestion with action/reason/priority
        priority = suggestion.get("priority", "medium")
        priority_color = PRIORITY_COLORS.get(priority, "#666")

        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"**{i}. {suggestion.get('action', 'N/A')}**")
                st.caption(f"Reason: {suggestion.get('reason', 'N/A')}")
                if suggestion.get("impact"):
                    st.success(f"Impact: {suggestion['impact']}")

            with col2:
                st.markdown(
                    f'<span style="background-color: {priority_color}; color: white; '
                    f'padding: 4px 8px; border-radius: 4px;">'
                    f'{priority.upper()}</span>',
                    unsafe_allow_html=True
                )

        st.markdown("---")


def render_ai_quick_insights(pi_analysis, capacity_plan=None) -> None:
    """Render quick AI insights without full analysis (uses cached/simple rules)."""
    st.markdown("#### Quick Insights")

    insights = []

    # Calculate utilization
    if pi_analysis and pi_analysis.total_capacity > 0:
        utilization = (pi_analysis.total_allocated / pi_analysis.total_capacity) * 100

        if utilization > 100:
            insights.append(("🔴", f"PI is **over-allocated** by {utilization - 100:.1f}%"))
        elif utilization > 90:
            insights.append(("🟡", f"High utilization at **{utilization:.1f}%** - limited flexibility"))
        elif utilization < 60:
            insights.append(("🔵", f"Low utilization at **{utilization:.1f}%** - consider adding scope"))
        else:
            insights.append(("🟢", f"Healthy utilization at **{utilization:.1f}%**"))

    # Check overallocated resources
    if pi_analysis and pi_analysis.overallocated_resources:
        count = len(pi_analysis.overallocated_resources)
        insights.append(("⚠️", f"**{count} resource(s)** are over-allocated"))

    # Check warnings
    if pi_analysis and pi_analysis.warnings:
        count = len(pi_analysis.warnings)
        insights.append(("📋", f"**{count} warning(s)** identified in data"))

    # Display insights
    for icon, text in insights:
        st.markdown(f"{icon} {text}")

    if not insights:
        st.info("No quick insights available. Run full AI analysis for detailed recommendations.")
