"""Red flags visualization component with improved UX."""

import streamlit as st
from typing import Optional

from pi_strategist.models import RedFlag, RedFlagSeverity, DEDDocument


# Severity configuration
SEVERITY_CONFIG = {
    RedFlagSeverity.CRITICAL: {
        "color": "#dc3545",
        "bg_color": "#f8d7da",
        "border_color": "#f5c6cb",
        "icon": "🚨",
        "label": "Critical",
        "description": "Blocks acceptance - resolve before development",
    },
    RedFlagSeverity.MODERATE: {
        "color": "#fd7e14",
        "bg_color": "#fff3cd",
        "border_color": "#ffeeba",
        "icon": "⚠️",
        "label": "Moderate",
        "description": "Needs clarification before sprint planning",
    },
    RedFlagSeverity.LOW: {
        "color": "#0d6efd",
        "bg_color": "#cfe2ff",
        "border_color": "#b6d4fe",
        "icon": "💡",
        "label": "Low",
        "description": "Nice to clarify during development",
    },
}


def render_red_flags(
    red_flags: list[RedFlag],
    ded: Optional[DEDDocument] = None,
    show_filters: bool = True,
    enable_ignore: bool = False,
) -> None:
    """Render the red flags analysis display.

    Args:
        red_flags: List of red flags to display
        ded: Optional DED document for context
        show_filters: Whether to show filter controls
        enable_ignore: Whether to show ignore/hide buttons for each flag
    """
    if not red_flags:
        st.success("✅ **No red flags detected!** Your acceptance criteria look well-defined.")
        return

    # Executive summary at the top
    _render_executive_summary(red_flags)

    st.markdown("---")

    # View toggle
    view_mode = st.radio(
        "View",
        ["By Severity", "All Items", "Table"],
        horizontal=True,
        label_visibility="collapsed",
    )

    # Filters (only for non-table views)
    filtered_flags = red_flags
    if show_filters and view_mode != "Table":
        filtered_flags = _render_compact_filters(red_flags)

    # Render based on view mode
    if view_mode == "By Severity":
        _render_grouped_by_severity(filtered_flags, enable_ignore=enable_ignore)
    elif view_mode == "All Items":
        _render_flat_list(filtered_flags, enable_ignore=enable_ignore)
    else:
        render_red_flags_table(filtered_flags)


def _render_executive_summary(red_flags: list[RedFlag]) -> None:
    """Render a clear executive summary."""
    critical = [rf for rf in red_flags if rf.severity == RedFlagSeverity.CRITICAL]
    moderate = [rf for rf in red_flags if rf.severity == RedFlagSeverity.MODERATE]
    low = [rf for rf in red_flags if rf.severity == RedFlagSeverity.LOW]

    # Overall status message
    if critical:
        st.error(
            f"**{len(critical)} critical issue{'s' if len(critical) != 1 else ''} found** "
            f"— These must be resolved before development begins."
        )
    elif moderate:
        st.warning(
            f"**{len(moderate)} item{'s' if len(moderate) != 1 else ''} need clarification** "
            f"— Address these before sprint planning."
        )
    else:
        st.info(
            f"**{len(low)} minor suggestion{'s' if len(low) != 1 else ''}** "
            f"— Consider clarifying during development."
        )

    # Compact metrics row
    cols = st.columns(4)

    with cols[0]:
        st.metric("Total Issues", len(red_flags))

    with cols[1]:
        _render_severity_metric("🚨 Critical", len(critical), "#dc3545")

    with cols[2]:
        _render_severity_metric("⚠️ Moderate", len(moderate), "#fd7e14")

    with cols[3]:
        _render_severity_metric("💡 Low", len(low), "#0d6efd")


def _render_severity_metric(label: str, count: int, color: str) -> None:
    """Render a colored severity metric."""
    if count > 0:
        st.metric(label=label, value=count)
    else:
        st.metric(label=label, value=0)


def _render_compact_filters(red_flags: list[RedFlag]) -> list[RedFlag]:
    """Render compact inline filters."""
    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        severity_filter = st.selectbox(
            "Severity",
            ["All Severities", "Critical", "Moderate", "Low"],
            label_visibility="collapsed",
        )

    with col2:
        categories = sorted(set(rf.category for rf in red_flags))
        category_filter = st.selectbox(
            "Category",
            ["All Categories"] + categories,
            label_visibility="collapsed",
        )

    # Apply filters
    filtered = red_flags

    if severity_filter != "All Severities":
        severity_map = {
            "Critical": RedFlagSeverity.CRITICAL,
            "Moderate": RedFlagSeverity.MODERATE,
            "Low": RedFlagSeverity.LOW,
        }
        filtered = [rf for rf in filtered if rf.severity == severity_map[severity_filter]]

    if category_filter != "All Categories":
        filtered = [rf for rf in filtered if rf.category == category_filter]

    with col3:
        if len(filtered) != len(red_flags):
            st.caption(f"Showing {len(filtered)} of {len(red_flags)} items")

    return filtered


def _render_grouped_by_severity(red_flags: list[RedFlag], enable_ignore: bool = False) -> None:
    """Render red flags grouped by severity level."""
    critical = [rf for rf in red_flags if rf.severity == RedFlagSeverity.CRITICAL]
    moderate = [rf for rf in red_flags if rf.severity == RedFlagSeverity.MODERATE]
    low = [rf for rf in red_flags if rf.severity == RedFlagSeverity.LOW]

    if critical:
        _render_severity_section(critical, RedFlagSeverity.CRITICAL, expanded=True, enable_ignore=enable_ignore)

    if moderate:
        _render_severity_section(moderate, RedFlagSeverity.MODERATE, expanded=not critical, enable_ignore=enable_ignore)

    if low:
        _render_severity_section(low, RedFlagSeverity.LOW, expanded=not critical and not moderate, enable_ignore=enable_ignore)


def _render_severity_section(
    flags: list[RedFlag],
    severity: RedFlagSeverity,
    expanded: bool = False,
    enable_ignore: bool = False,
) -> None:
    """Render a section for a specific severity level."""
    config = SEVERITY_CONFIG[severity]

    with st.expander(
        f"{config['icon']} **{config['label']}** ({len(flags)}) — {config['description']}",
        expanded=expanded,
    ):
        for rf in flags:
            _render_compact_flag_card(rf, show_severity=False, enable_ignore=enable_ignore)


def _render_flat_list(red_flags: list[RedFlag], enable_ignore: bool = False) -> None:
    """Render all flags in a flat list."""
    for rf in red_flags:
        _render_compact_flag_card(rf, show_severity=True, enable_ignore=enable_ignore)


def _render_compact_flag_card(rf: RedFlag, show_severity: bool = True, enable_ignore: bool = False) -> None:
    """Render a single red flag in a compact, scannable card format."""
    config = SEVERITY_CONFIG[rf.severity]
    icon = config['icon'] if show_severity else ''

    # Create a unique key for this flag
    flag_key = f"{rf.flagged_term}|{rf.ac.text[:50]}"

    # Build header text using Streamlit native components
    with st.container():
        # Header row with severity indicator and ignore button
        if enable_ignore:
            if show_severity:
                header_cols = st.columns([0.05, 0.80, 0.15])
            else:
                header_cols = st.columns([0.85, 0.15])
        else:
            header_cols = st.columns([0.05, 0.95]) if show_severity else [st.container()]

        if show_severity:
            with header_cols[0]:
                st.markdown(f"**{icon}**")
            col_for_text = header_cols[1]
        else:
            col_for_text = header_cols[0]

        with col_for_text:
            st.markdown(
                f"**`{rf.flagged_term}`** · {rf.category}",
            )

        # Ignore button (if enabled)
        if enable_ignore:
            ignore_col = header_cols[-1]
            with ignore_col:
                if st.button("✕ Hide", key=f"ignore_{hash(flag_key)}", help="Hide this suggestion"):
                    if "ignored_red_flags" not in st.session_state:
                        st.session_state.ignored_red_flags = set()
                    st.session_state.ignored_red_flags.add(flag_key)
                    st.rerun()

        # Details in two columns
        col1, col2 = st.columns([3, 2])

        with col1:
            # Original text (truncated if long)
            ac_text = rf.ac.text
            if len(ac_text) > 200:
                ac_text = ac_text[:200] + "..."
            st.caption(f"Found in: {ac_text}")

            # Story/Epic reference if available
            refs = []
            if rf.ac.story_id:
                refs.append(f"Story: `{rf.ac.story_id}`")
            if rf.ac.epic_id:
                refs.append(f"Epic: `{rf.ac.epic_id}`")
            if refs:
                st.caption(" | ".join(refs))

        with col2:
            st.markdown("**Replace with:**")
            st.code(rf.suggested_metric, language=None)

        # Negotiation script (collapsible)
        with st.expander("💬 How to discuss this", expanded=False):
            st.info(rf.negotiation_script)

        st.divider()


def render_red_flags_table(red_flags: list[RedFlag]) -> None:
    """Render red flags in a sortable table format."""
    if not red_flags:
        st.info("No red flags to display.")
        return

    # Create data for table with severity emoji for visual scanning
    data = []
    for rf in red_flags:
        config = SEVERITY_CONFIG[rf.severity]
        data.append(
            {
                "Sev": config["icon"],
                "Term": rf.flagged_term,
                "Category": rf.category,
                "In Acceptance Criteria": (
                    rf.ac.text[:80] + "..." if len(rf.ac.text) > 80 else rf.ac.text
                ),
                "Suggested Replacement": rf.suggested_metric,
            }
        )

    st.dataframe(
        data,
        use_container_width=True,
        column_config={
            "Sev": st.column_config.TextColumn(
                "⚡",
                help="Severity: 🚨 Critical, ⚠️ Moderate, 💡 Low",
                width="small",
            ),
            "Term": st.column_config.TextColumn(
                "Flagged Term",
                width="small",
            ),
            "Category": st.column_config.TextColumn(
                "Category",
                width="medium",
            ),
            "In Acceptance Criteria": st.column_config.TextColumn(
                "Found In",
                width="large",
            ),
            "Suggested Replacement": st.column_config.TextColumn(
                "Replace With",
                width="large",
            ),
        },
        hide_index=True,
    )


def render_quick_summary(red_flags: list[RedFlag]) -> None:
    """Render a minimal summary for dashboard use."""
    if not red_flags:
        st.success("✅ No issues found")
        return

    critical = len([rf for rf in red_flags if rf.severity == RedFlagSeverity.CRITICAL])
    moderate = len([rf for rf in red_flags if rf.severity == RedFlagSeverity.MODERATE])
    low = len([rf for rf in red_flags if rf.severity == RedFlagSeverity.LOW])

    parts = []
    if critical:
        parts.append(f"🚨 {critical} critical")
    if moderate:
        parts.append(f"⚠️ {moderate} moderate")
    if low:
        parts.append(f"💡 {low} low")

    st.markdown(" · ".join(parts))
