"""Quick text check page for instant red flag detection."""

import sys
from pathlib import Path

# Add src directory to path for Streamlit Cloud deployment
_src_dir = Path(__file__).parent.parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import streamlit as st

from pi_strategist.analyzers.risk_analyzer import RiskAnalyzer
from pi_strategist.models import RedFlagSeverity, ObligationType, SLAMetricType
from pi_strategist.web.components.session_status import render_session_status


# Page config
st.set_page_config(
    page_title="Quick Check - PI Strategist",
    page_icon="⚡",
    layout="wide",
)

# Render session status in sidebar first
render_session_status()

st.title("⚡ Quick Check")
st.markdown("Paste acceptance criteria or contract text for instant analysis - no file upload needed.")

# Color scheme
COLORS = {
    "critical": "#e74c3c",
    "moderate": "#f39c12",
    "low": "#3498db",
}

OBLIGATION_COLORS = {
    "shall": "#9b59b6",
    "must": "#e74c3c",
    "will": "#3498db",
    "shall not": "#8e44ad",
    "must not": "#c0392b",
    "will not": "#2980b9",
}

SLA_COLORS = {
    "uptime": "#27ae60",
    "availability": "#27ae60",
    "response_time": "#f39c12",
    "latency": "#f39c12",
    "throughput": "#3498db",
    "error_rate": "#e74c3c",
    "recovery_time": "#9b59b6",
}

# Initialize session state
if "quick_check_results" not in st.session_state:
    st.session_state.quick_check_results = None

# Text input
st.markdown("---")
st.subheader("Enter Text to Analyze")

sample_text = """The system should be fast and user-friendly.
Users should be able to complete tasks quickly and intuitively.
The application must be secure and handle all edge cases.
Performance should be good under high load.
The UI should look clean and be responsive.
The vendor shall provide 99.9% uptime.
The system must respond within 200ms.
The contractor will deliver all documentation.
Service availability shall not fall below 99.5%."""

text_input = st.text_area(
    "Paste your acceptance criteria or contract text here:",
    value="",
    height=200,
    placeholder="",
    help="Enter text to analyze for red flags, obligations, and SLA metrics",
)

col1, col2 = st.columns([1, 4])

with col1:
    check_button = st.button(
        "🔍 Analyze",
        type="primary",
        disabled=len(text_input.strip()) == 0,
        use_container_width=True,
    )

with col2:
    if st.button("📋 Load Sample", help="Load sample text with red flags, obligations, and SLAs"):
        st.session_state.sample_loaded = True
        st.rerun()

# Handle sample loading
if "sample_loaded" in st.session_state and st.session_state.sample_loaded:
    text_input = sample_text
    st.session_state.sample_loaded = False


def run_full_analysis(text: str) -> dict:
    """Run complete analysis on text including red flags, obligations, and SLAs."""
    analyzer = RiskAnalyzer()
    return analyzer.full_analysis(text)


# Run check when button clicked
if check_button and text_input.strip():
    st.session_state.quick_check_results = run_full_analysis(text_input)
    st.session_state.analyzed_text = text_input

# Display results
if st.session_state.quick_check_results:
    results = st.session_state.quick_check_results

    st.markdown("---")
    st.header("Analysis Results")

    # Create tabs for different analysis types
    tab1, tab2, tab3 = st.tabs(["🚩 Red Flags", "📋 Obligations", "📊 SLA/SLO Metrics"])

    # ==================== Red Flags Tab ====================
    with tab1:
        red_flag_results = results.get("red_flags", [])

        # Count flags
        total_flags = sum(len(item["flags"]) for item in red_flag_results)
        critical_count = 0
        moderate_count = 0
        low_count = 0

        for item in red_flag_results:
            for _, flag_info in item["flags"]:
                severity = flag_info.get("severity", RedFlagSeverity.LOW)
                if severity == RedFlagSeverity.CRITICAL:
                    critical_count += 1
                elif severity == RedFlagSeverity.MODERATE:
                    moderate_count += 1
                else:
                    low_count += 1

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Red Flags", total_flags)
        with col2:
            st.metric("Critical", critical_count, help="Blocking - must be resolved")
        with col3:
            st.metric("Moderate", moderate_count, help="Clarification needed")
        with col4:
            st.metric("Low", low_count, help="Nice to clarify")

        if total_flags > 0:
            st.markdown("---")
            st.subheader("Detailed Red Flags")

            for i, item in enumerate(red_flag_results, 1):
                line = item["line"]
                flags = item["flags"]

                if flags:
                    with st.expander(
                        f"**Line {i}:** {line[:60]}..." if len(line) > 60 else f"**Line {i}:** {line}",
                        expanded=True,
                    ):
                        st.markdown("**Original Text:**")
                        st.info(f'"{line}"')

                        st.markdown("**Red Flags Found:**")

                        for term, flag_info in flags:
                            severity = flag_info.get("severity", RedFlagSeverity.LOW)
                            severity_color = COLORS.get(severity.value, "#666")
                            category = flag_info.get("category", "Unknown")
                            suggestion = flag_info.get("suggestion", "")
                            negotiation = flag_info.get("negotiation", "")

                            col1, col2 = st.columns([1, 3])

                            with col1:
                                st.markdown(
                                    f'<span style="background-color: {severity_color}; color: white; '
                                    f'padding: 2px 8px; border-radius: 4px; font-size: 0.9em;">'
                                    f"{severity.value.upper()}</span>",
                                    unsafe_allow_html=True,
                                )
                                st.code(term)

                            with col2:
                                st.markdown(f"**Category:** {category}")
                                st.success(f"**Suggestion:** {suggestion}")
                                st.warning(f"**Negotiation:** {negotiation}")

                            st.markdown("---")

            # Summary table
            st.subheader("Summary Table")
            table_data = []
            for item in red_flag_results:
                line = item["line"]
                for term, flag_info in item["flags"]:
                    severity = flag_info.get("severity", RedFlagSeverity.LOW)
                    table_data.append({
                        "Severity": severity.value.upper(),
                        "Term": term,
                        "Category": flag_info.get("category", "Unknown"),
                        "Text": line[:80] + "..." if len(line) > 80 else line,
                    })

            if table_data:
                st.dataframe(table_data, use_container_width=True)
        else:
            st.success("✓ No red flags detected! Your text appears well-defined.")

    # ==================== Obligations Tab ====================
    with tab2:
        obligation_results = results.get("obligations", {})
        obligations = obligation_results.get("obligations", [])

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Obligations", obligation_results.get("total", 0))
        with col2:
            st.metric(
                "Binding (shall/must)",
                obligation_results.get("binding_count", 0),
                help="Legally binding language"
            )
        with col3:
            st.metric(
                "Commitments (will)",
                obligation_results.get("commitment_count", 0),
                help="Future commitments"
            )

        if obligations:
            st.markdown("---")
            st.subheader("Detected Obligations")

            # Group by subject
            by_subject = obligation_results.get("by_subject", {})

            for subject, obls in by_subject.items():
                with st.expander(f"**{subject.title()}** ({len(obls)} obligations)", expanded=True):
                    for obl in obls:
                        obl_type = obl.obligation_type.value
                        color = OBLIGATION_COLORS.get(obl_type, "#666")

                        col1, col2 = st.columns([1, 4])

                        with col1:
                            st.markdown(
                                f'<span style="background-color: {color}; color: white; '
                                f'padding: 2px 8px; border-radius: 4px; font-size: 0.9em;">'
                                f"{obl_type.upper()}</span>",
                                unsafe_allow_html=True,
                            )

                        with col2:
                            if obl.is_negative:
                                st.error(f"**{obl.subject}** {obl_type} **{obl.action}**")
                            else:
                                st.info(f"**{obl.subject}** {obl_type} **{obl.action}**")

                        st.caption(f"Source: _{obl.source_line}_")
                        st.markdown("---")

            # Obligations table
            st.subheader("Obligations Summary Table")
            table_data = []
            for obl in obligations:
                table_data.append({
                    "Type": obl.obligation_type.value.upper(),
                    "Subject": obl.subject.title(),
                    "Action": obl.action,
                    "Negative": "Yes" if obl.is_negative else "No",
                })

            if table_data:
                st.dataframe(table_data, use_container_width=True)
        else:
            st.info("No obligation statements (shall/must/will) detected in the text.")

    # ==================== SLA/SLO Tab ====================
    with tab3:
        sla_results = results.get("sla", {})
        findings = sla_results.get("findings", [])

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("SLA Metrics Found", sla_results.get("total", 0))
        with col2:
            st.metric("Valid", sla_results.get("valid_count", 0))
        with col3:
            st.metric(
                "With Warnings",
                sla_results.get("with_warnings", 0),
                help="Metrics that may need review"
            )

        if findings:
            st.markdown("---")
            st.subheader("Detected SLA/SLO Metrics")

            # Group by type
            by_type = sla_results.get("by_type", {})

            for metric_type, items in by_type.items():
                color = SLA_COLORS.get(metric_type, "#666")
                display_name = metric_type.replace("_", " ").title()

                with st.expander(f"**{display_name}** ({len(items)} found)", expanded=True):
                    for finding in items:
                        col1, col2, col3 = st.columns([1, 2, 3])

                        with col1:
                            st.markdown(
                                f'<span style="background-color: {color}; color: white; '
                                f'padding: 2px 8px; border-radius: 4px; font-size: 0.9em;">'
                                f"{display_name}</span>",
                                unsafe_allow_html=True,
                            )

                        with col2:
                            st.metric(
                                label="Value",
                                value=f"{finding.value} {finding.unit}",
                            )

                        with col3:
                            if finding.warning:
                                st.warning(f"⚠️ {finding.warning}")
                            elif finding.is_valid:
                                st.success("✓ Well-defined metric")
                            else:
                                st.error("✗ Invalid metric")

                        st.caption(f"Source: _{finding.source_line}_")
                        st.markdown("---")

            # SLA table
            st.subheader("SLA/SLO Summary Table")
            table_data = []
            for finding in findings:
                table_data.append({
                    "Metric Type": finding.metric_type.value.replace("_", " ").title(),
                    "Value": finding.value,
                    "Unit": finding.unit,
                    "Valid": "Yes" if finding.is_valid else "No",
                    "Warning": finding.warning or "-",
                })

            if table_data:
                st.dataframe(table_data, use_container_width=True)
        else:
            st.info("No SLA/SLO metrics (uptime, response time, etc.) detected in the text.")

    # Clear results button
    st.markdown("---")
    if st.button("🔄 Clear Results"):
        st.session_state.quick_check_results = None
        st.rerun()

# Sidebar with reference information
with st.sidebar:
    st.markdown("### Analysis Types")

    st.markdown("**🚩 Red Flags**")
    st.caption("Detects vague or ambiguous language in requirements")

    st.markdown("**📋 Obligations**")
    st.caption("Tracks shall/must/will statements and who is responsible")

    st.markdown("**📊 SLA/SLO**")
    st.caption("Extracts uptime, response time, and other service metrics")

    st.markdown("---")

    st.markdown("### Obligation Keywords")
    st.markdown(
        """
        - **shall** - Binding requirement
        - **must** - Mandatory requirement
        - **will** - Future commitment
        - **shall not** - Prohibition
        - **must not** - Prohibition
        """
    )

    st.markdown("---")

    st.markdown("### SLA Metrics Detected")
    st.markdown(
        """
        - Uptime (99.9%, etc.)
        - Availability
        - Response time
        - Latency
        - Throughput (TPS, RPS)
        - Error rate
        - Recovery time (RTO)
        """
    )

    st.markdown("---")

    st.markdown("### Tips")
    st.markdown(
        """
        - Paste contract clauses or requirements
        - Review obligations by responsible party
        - Check SLA warnings for unrealistic targets
        - Use red flag suggestions for negotiations
        """
    )
