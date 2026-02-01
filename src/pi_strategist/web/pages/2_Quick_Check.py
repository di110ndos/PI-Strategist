"""Quick text check page for instant red flag detection."""

import sys
from pathlib import Path

# Add src directory to path for Streamlit Cloud deployment
_src_dir = Path(__file__).parent.parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import streamlit as st

from pi_strategist.analyzers.risk_analyzer import RiskAnalyzer
from pi_strategist.models import RedFlagSeverity
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
st.markdown("Paste acceptance criteria text for instant red flag detection - no file upload needed.")

# Color scheme
COLORS = {
    "critical": "#e74c3c",
    "moderate": "#f39c12",
    "low": "#3498db",
}

# Initialize session state
if "quick_check_results" not in st.session_state:
    st.session_state.quick_check_results = None

# Text input
st.markdown("---")
st.subheader("Enter Acceptance Criteria")

sample_text = """The system should be fast and user-friendly.
Users should be able to complete tasks quickly and intuitively.
The application must be secure and handle all edge cases.
Performance should be good under high load.
The UI should look clean and be responsive."""

text_input = st.text_area(
    "Paste your acceptance criteria here:",
    value="",
    height=200,
    placeholder=sample_text,
    help="Enter acceptance criteria text - each line will be analyzed separately",
)

col1, col2 = st.columns([1, 4])

with col1:
    check_button = st.button(
        "🔍 Check",
        type="primary",
        disabled=len(text_input.strip()) == 0,
        width="stretch",
    )

with col2:
    if st.button("📋 Load Sample", width="content"):
        st.session_state.sample_loaded = True
        st.rerun()

# Handle sample loading
if "sample_loaded" in st.session_state and st.session_state.sample_loaded:
    text_input = sample_text
    st.session_state.sample_loaded = False


def run_quick_check(text: str) -> list[tuple[str, list[tuple[str, dict]]]]:
    """Run quick check analysis on text.

    Returns list of (line, flags) tuples.
    """
    analyzer = RiskAnalyzer()
    results = []

    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line:
            flags = analyzer.analyze_text(line)
            results.append((line, flags))

    return results


# Run check when button clicked
if check_button and text_input.strip():
    st.session_state.quick_check_results = run_quick_check(text_input)

# Display results
if st.session_state.quick_check_results:
    results = st.session_state.quick_check_results

    st.markdown("---")
    st.header("Results")

    # Summary counts
    total_flags = sum(len(flags) for _, flags in results)
    lines_with_flags = sum(1 for _, flags in results if flags)
    total_lines = len(results)

    # Count by severity
    critical_count = 0
    moderate_count = 0
    low_count = 0

    for _, flags in results:
        for _, flag_info in flags:
            severity = flag_info.get("severity", RedFlagSeverity.LOW)
            if severity == RedFlagSeverity.CRITICAL:
                critical_count += 1
            elif severity == RedFlagSeverity.MODERATE:
                moderate_count += 1
            else:
                low_count += 1

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Lines Checked", total_lines)

    with col2:
        st.metric("Total Red Flags", total_flags)

    with col3:
        st.metric(
            "Critical",
            critical_count,
            help="Blocking - must be resolved",
        )

    with col4:
        st.metric(
            "Moderate",
            moderate_count,
            help="Clarification needed",
        )

    with col5:
        st.metric(
            "Low",
            low_count,
            help="Nice to clarify",
        )

    st.markdown("---")

    # Results table
    if total_flags > 0:
        # Detailed results
        st.subheader("Detailed Analysis")

        for i, (line, flags) in enumerate(results, 1):
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
            else:
                # No flags for this line
                with st.expander(
                    f"✓ **Line {i}:** {line[:60]}..." if len(line) > 60 else f"✓ **Line {i}:** {line}",
                    expanded=False,
                ):
                    st.success("No red flags detected in this line.")

        # Summary table
        st.markdown("---")
        st.subheader("Summary Table")

        table_data = []
        for line, flags in results:
            for term, flag_info in flags:
                severity = flag_info.get("severity", RedFlagSeverity.LOW)
                table_data.append(
                    {
                        "Severity": severity.value.upper(),
                        "Term": term,
                        "Category": flag_info.get("category", "Unknown"),
                        "Text (truncated)": line[:80] + "..." if len(line) > 80 else line,
                        "Suggestion": flag_info.get("suggestion", ""),
                    }
                )

        if table_data:
            st.dataframe(
                table_data,
                width="stretch",
                column_config={
                    "Severity": st.column_config.TextColumn(
                        "Severity",
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
                    "Text (truncated)": st.column_config.TextColumn(
                        "Text",
                        width="large",
                    ),
                    "Suggestion": st.column_config.TextColumn(
                        "Suggestion",
                        width="large",
                    ),
                },
            )

    else:
        st.success("✓ No red flags detected! Your acceptance criteria appear well-defined.")

    # Clear results button
    st.markdown("---")
    if st.button("🔄 Clear Results"):
        st.session_state.quick_check_results = None
        st.rerun()

# Sidebar with red flag dictionary
with st.sidebar:
    st.markdown("### Common Red Flags")
    st.markdown(
        """
        **Subjective Terms:**
        - fast, quick, simple
        - user-friendly, intuitive
        - robust, efficient
        - responsive, clean

        **Vague Metrics:**
        - high quality, performant
        - scalable, secure
        - reliable, stable
        - maintainable, accessible

        **Undefined Scope:**
        - comprehensive, complete
        - all edge cases, all scenarios
        - full support, etc., and more

        **Comparative Terms:**
        - better, improved
        - enhanced, optimized
        - faster, newer

        **Time Ambiguity:**
        - soon, quickly
        - real-time, immediately

        **Quantity Ambiguity:**
        - many, few, several
        - most, some
        """
    )

    st.markdown("---")
    st.markdown("### Tips")
    st.markdown(
        """
        - Each line is analyzed separately
        - Paste multiple acceptance criteria
        - Look for specific metrics to replace vague terms
        - Use the suggested negotiation scripts in meetings
        """
    )
