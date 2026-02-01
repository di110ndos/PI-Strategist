"""Full DED analysis page."""

import io
import streamlit as st
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from pi_strategist.parsers.ded_parser import DEDParser
from pi_strategist.parsers.excel_parser import ExcelParser
from pi_strategist.analyzers.risk_analyzer import RiskAnalyzer
from pi_strategist.analyzers.capacity_analyzer import CapacityAnalyzer
from pi_strategist.analyzers.deployment_analyzer import DeploymentAnalyzer
from pi_strategist.reporters.pushback_report import PushbackReport
from pi_strategist.reporters.pdf_report import generate_executive_pdf, ReportConfig
from pi_strategist.web.components.red_flags_display import render_red_flags
from pi_strategist.web.components.capacity_display import render_capacity_analysis
from pi_strategist.web.components.deployment_display import (
    render_deployment_analysis,
    render_strategy_legend,
)
from pi_strategist.web.components.pi_dashboard import render_pi_dashboard
from pi_strategist.web.components.ai_recommendations import render_ai_recommendations
from pi_strategist.web.components.roadmap_display import render_roadmap, render_roadmap_summary
from pi_strategist.parsers.pi_planner_parser import PIPlannerParser


# ============================================================================
# Helper functions for save/load (defined before use)
# ============================================================================

def _get_saved_analyses_dir() -> Path:
    """Get the directory for saved analyses, creating it if needed."""
    save_dir = Path("saved_analyses")
    save_dir.mkdir(exist_ok=True)
    return save_dir


def _render_save_analysis_section():
    """Render the save analysis controls."""
    import json
    from datetime import datetime

    st.markdown("#### Save Current Analysis")

    col1, col2 = st.columns(2)
    with col1:
        current_year = datetime.now().year
        year = st.selectbox(
            "Year",
            options=list(range(current_year - 2, current_year + 3)),
            index=2,  # Default to current year
            key="save_year",
            help="Select the year for this PI"
        )
    with col2:
        quarter = st.selectbox(
            "Quarter/PI",
            options=["Q1 (PI 1-2)", "Q2 (PI 3-4)", "Q3 (PI 5-6)", "Q4 (PI 7-8)",
                     "PI 1", "PI 2", "PI 3", "PI 4", "PI 5", "PI 6"],
            key="save_quarter",
            help="Select the quarter or PI number"
        )

    analysis_name = st.text_input(
        "Analysis Name (optional)",
        placeholder="e.g., CA Lottery, Main Project",
        key="save_name",
        help="Optional name to identify this analysis"
    )

    if st.button("Save Analysis", type="primary", use_container_width=True):
        save_dir = _get_saved_analyses_dir()
        results = st.session_state.analysis_results

        # Create filename
        quarter_clean = quarter.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        name_clean = analysis_name.replace(" ", "_")[:30] if analysis_name else "analysis"
        filename = f"{year}_{quarter_clean}_{name_clean}.json"

        # Prepare data for saving (convert to serializable format)
        save_data = {
            "metadata": {
                "year": year,
                "quarter": quarter,
                "name": analysis_name,
                "saved_at": datetime.now().isoformat(),
                "source_file": st.session_state.get("excel_file_data", {}).get("name", "Unknown"),
            },
            "summary": {},
        }

        # Extract key metrics from PI analysis
        if results.get("pi_analysis"):
            pi = results["pi_analysis"]
            save_data["summary"]["sprints"] = len(pi.sprints)
            save_data["summary"]["resources"] = len(pi.resources)
            save_data["summary"]["projects"] = len(pi.projects)
            save_data["summary"]["total_capacity"] = pi.total_capacity
            save_data["summary"]["total_allocated"] = pi.total_allocated
            save_data["summary"]["warnings_count"] = len(pi.warnings)

            # Save resource data
            save_data["resources"] = {}
            for name, res in pi.resources.items():
                save_data["resources"][name] = {
                    "discipline": res.discipline,
                    "total_hours": res.total_hours,
                    "rate": res.rate,
                    "allocation_pct": (res.total_hours / 488 * 100) if res.total_hours > 0 else 0,
                }

            # Save project data
            save_data["projects"] = {}
            for name, proj in pi.projects.items():
                save_data["projects"][name] = {
                    "priority": proj.priority,
                    "total_hours": proj.total_hours,
                    "sprints": [s for s, v in proj.sprint_allocation.items() if v],
                }

        # Save to file
        save_path = save_dir / filename
        with open(save_path, "w") as f:
            json.dump(save_data, f, indent=2, default=str)

        st.success(f"Saved to {filename}")


def _render_load_analysis_section():
    """Render the load/view saved analyses section."""
    import json

    save_dir = _get_saved_analyses_dir()

    # Get list of saved analyses
    saved_files = sorted(save_dir.glob("*.json"), reverse=True)

    if not saved_files:
        st.caption("No saved analyses yet")
        return

    st.markdown("#### Saved Analyses")

    for file_path in saved_files[:10]:  # Show last 10
        try:
            with open(file_path) as f:
                data = json.load(f)

            meta = data.get("metadata", {})
            summary = data.get("summary", {})

            year = meta.get("year", "?")
            quarter = meta.get("quarter", "?")
            name = meta.get("name", "")
            resources = summary.get("resources", 0)
            projects = summary.get("projects", 0)

            label = f"{year} {quarter}"
            if name:
                label += f" - {name}"

            with st.expander(f"{label}", expanded=False):
                st.caption(f"Saved: {meta.get('saved_at', 'Unknown')[:10]}")
                st.caption(f"Source: {meta.get('source_file', 'Unknown')}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Resources", resources)
                with col2:
                    st.metric("Projects", projects)
                with col3:
                    allocated = summary.get("total_allocated", 0)
                    st.metric("Hours", f"{allocated:,.0f}")

                # Delete button
                if st.button("Delete", key=f"delete_{file_path.name}"):
                    file_path.unlink()
                    st.rerun()

        except Exception as e:
            st.error(f"Error loading {file_path.name}: {e}")


# ============================================================================
# Page config
st.set_page_config(
    page_title="Analysis - PI Strategist",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Full DED Analysis")
st.markdown("Upload your DED document and capacity planner for comprehensive analysis.")

# Initialize session state
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "ded_file_data" not in st.session_state:
    st.session_state.ded_file_data = None
if "excel_file_data" not in st.session_state:
    st.session_state.excel_file_data = None

# File upload section
st.markdown("---")
st.subheader("Upload Files")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### DED Document")
    st.caption("Supported formats: .docx, .md, .txt, .pdf")
    ded_file = st.file_uploader(
        "Upload DED",
        type=["docx", "md", "txt", "pdf"],
        key="ded_upload",
        help="Upload your Design & Engineering Document",
    )
    # Store in session state when uploaded
    if ded_file is not None:
        st.session_state.ded_file_data = {
            "name": ded_file.name,
            "data": ded_file.getvalue(),
            "size": ded_file.size,
        }

with col2:
    st.markdown("#### Capacity Planner")
    st.caption("Supported formats: .xlsx")
    excel_file = st.file_uploader(
        "Upload Capacity Planner",
        type=["xlsx"],
        key="excel_upload",
        help="Upload your sprint capacity planner Excel file",
    )
    # Store in session state when uploaded
    if excel_file is not None:
        st.session_state.excel_file_data = {
            "name": excel_file.name,
            "data": excel_file.getvalue(),
            "size": excel_file.size,
        }

# Analysis settings
st.markdown("---")
st.subheader("Analysis Settings")

col1, col2 = st.columns(2)

with col1:
    buffer_percentage = st.slider(
        "Buffer Percentage",
        min_value=0,
        max_value=50,
        value=20,
        step=5,
        help="""**Buffer Percentage** reserves capacity for unexpected work, meetings, and interruptions.

- **20% (Recommended)**: Standard buffer for most teams
- **10-15%**: For well-established, predictable projects
- **25-30%**: For new teams or high-uncertainty projects

This percentage is subtracted from total capacity to calculate 'Net Capacity' for planning.""",
    )

with col2:
    cd_target = st.slider(
        "CD Target Percentage",
        min_value=10,
        max_value=50,
        value=30,
        step=5,
        help="""**Continuous Delivery Target** is the percentage of tasks that should be deployable independently.

- **30% (Recommended)**: Good balance of CD benefits vs complexity
- **10-20%**: Conservative, for teams new to CD
- **40-50%**: Aggressive, for mature DevOps teams

Higher CD percentage reduces deployment risk but requires more modular architecture.""",
    )

# Analyze button - enabled if either file is uploaded
has_ded = st.session_state.get("ded_file_data") is not None
has_excel = st.session_state.get("excel_file_data") is not None

analyze_button = st.button(
    "🔍 Analyze",
    type="primary",
    disabled=(not has_ded and not has_excel),
    width="stretch",
)

if not has_ded and not has_excel:
    st.caption("Upload a DED document and/or capacity planner to analyze")
else:
    files_ready = []
    if has_ded:
        files_ready.append(f"DED: {st.session_state.ded_file_data['name']}")
    if has_excel:
        files_ready.append(f"Excel: {st.session_state.excel_file_data['name']}")
    st.caption(f"Ready to analyze: {', '.join(files_ready)}")


def save_uploaded_file(file_data: dict) -> Optional[Path]:
    """Save uploaded file data to a temporary location and return the path.

    Args:
        file_data: Dictionary with 'name', 'data', and 'size' keys

    Note:
        On Windows, we must close the file before another process can open it.
        Using delete=False and manually managing cleanup.
    """
    import tempfile
    import os

    if file_data is None:
        return None

    suffix = Path(file_data["name"]).suffix

    # Create temp file, write data, and close it (Windows compatibility)
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, file_data["data"])
    finally:
        os.close(fd)  # Must close before another process can access on Windows

    return Path(tmp_path)


def run_analysis():
    """Run the full analysis pipeline."""
    import traceback

    results = {
        "ded": None,
        "capacity": None,
        "pi_analysis": None,  # Comprehensive PI analysis from PIPlannerParser
        "red_flags": [],
        "capacity_analysis": [],
        "deployment_clusters": [],
        "risk_summary": {},
        "capacity_summary": {},
        "deployment_summary": {},
        "debug_log": [],  # Collect debug messages
    }

    def log_debug(msg: str):
        """Add a debug message to the log."""
        results["debug_log"].append(msg)

    log_debug("Parser version: 2024-02-01-v2 (with grand_total_hours fix)")

    # Get file data from session state
    ded_data = st.session_state.get("ded_file_data")
    excel_data = st.session_state.get("excel_file_data")

    # Log file info
    if ded_data:
        log_debug(f"DED file: {ded_data['name']} ({ded_data['size']} bytes)")
    else:
        log_debug("DED file: None")

    if excel_data:
        log_debug(f"Excel file: {excel_data['name']} ({excel_data['size']} bytes)")
    else:
        log_debug("Excel file: None")

    # Initialize parsers and analyzers
    try:
        ded_parser = DEDParser()
        excel_parser = ExcelParser(default_buffer=buffer_percentage / 100)
        risk_analyzer = RiskAnalyzer()
        capacity_analyzer = CapacityAnalyzer(default_buffer=buffer_percentage / 100)
        deployment_analyzer = DeploymentAnalyzer(cd_target_percentage=cd_target / 100)
        log_debug("Parsers initialized successfully")
    except Exception as e:
        st.error(f"Failed to initialize parsers: {e}")
        log_debug(f"ERROR: {traceback.format_exc()}")
        return results

    # Parse DED (if provided)
    if ded_data:
        with st.spinner("Parsing DED document..."):
            ded_path = save_uploaded_file(ded_data)
            log_debug(f"DED saved to: {ded_path}")
            if ded_path:
                try:
                    results["ded"] = ded_parser.parse(ded_path)
                    log_debug(f"DED parsed: {len(results['ded'].epics)} epics, {len(results['ded'].all_stories)} stories")
                except Exception as e:
                    st.error(f"Error parsing DED: {e}")
                    log_debug(f"ERROR parsing DED: {traceback.format_exc()}")
                finally:
                    try:
                        ded_path.unlink(missing_ok=True)
                    except:
                        pass

        # Analyze red flags
        with st.spinner("Analyzing acceptance criteria..."):
            if results["ded"]:
                try:
                    results["red_flags"] = risk_analyzer.analyze(results["ded"])
                    results["risk_summary"] = risk_analyzer.summary(results["red_flags"])
                    log_debug(f"Found {len(results['red_flags'])} red flags")
                except Exception as e:
                    st.error(f"Error analyzing red flags: {e}")
                    log_debug(f"ERROR analyzing red flags: {traceback.format_exc()}")

    # Parse and analyze capacity if Excel provided
    if excel_data:
        with st.spinner("Parsing capacity planner..."):
            excel_path = save_uploaded_file(excel_data)
            log_debug(f"Excel saved to: {excel_path}")
            if excel_path:
                try:
                    if not excel_path.exists():
                        st.error(f"Temp file does not exist: {excel_path}")
                        log_debug(f"ERROR: Temp file does not exist")
                    else:
                        log_debug(f"File size on disk: {excel_path.stat().st_size} bytes")

                    # First, try the comprehensive PI Planner Parser
                    try:
                        pi_parser = PIPlannerParser(default_buffer=buffer_percentage / 100)
                        pi_plan, pi_analysis = pi_parser.parse_with_analysis(excel_path)
                        results["pi_analysis"] = pi_analysis

                        if pi_analysis:
                            num_resources = len(pi_analysis.resources)
                            log_debug(f"PI Analysis: {len(pi_analysis.sprints)} sprints, {num_resources} resources, {len(pi_analysis.projects)} projects")

                            # Calculate what capacity SHOULD be
                            expected_capacity = num_resources * 488
                            log_debug(f"  Expected capacity: {expected_capacity:.1f}h ({num_resources} × 488h)")
                            log_debug(f"  Actual total_capacity: {pi_analysis.total_capacity:.1f}h")
                            log_debug(f"  Total allocated: {pi_analysis.total_allocated:.1f}h")

                            # Check for grand_total_hours attribute (may not exist in cached version)
                            if hasattr(pi_analysis, 'grand_total_hours'):
                                log_debug(f"  Grand total from spreadsheet: {pi_analysis.grand_total_hours:.1f}h")
                            else:
                                log_debug("  WARNING: grand_total_hours not found - restart app to reload code")

                            # Debug: show calculated sum
                            calc_sum = sum(r.total_hours for r in pi_analysis.resources.values())
                            log_debug(f"  Sum of resource.total_hours: {calc_sum:.1f}h")

                            # Debug: list all resource names to identify extras
                            log_debug(f"  Resource names ({len(pi_analysis.resources)}):")
                            for name in sorted(pi_analysis.resources.keys()):
                                hours = pi_analysis.resources[name].total_hours
                                log_debug(f"    - {name}: {hours:.1f}h")

                            total_cost = sum(
                                r.total_hours * r.rate
                                for r in pi_analysis.resources.values()
                                if r.rate > 0
                            )
                            log_debug(f"  Total cost: ${total_cost:,.2f}")

                            if pi_analysis.warnings:
                                log_debug(f"Found {len(pi_analysis.warnings)} validation warnings")

                            if pi_plan and pi_plan.sprints:
                                results["capacity"] = pi_plan
                    except Exception as e:
                        log_debug(f"PI Planner Parser error: {e}")
                        log_debug(traceback.format_exc())

                    # Also try standard Excel parser
                    results["capacity"] = excel_parser.parse(excel_path)

                    if results["capacity"]:
                        sprint_count = len(results["capacity"].sprints)
                        task_count = len(results["capacity"].all_tasks)
                        log_debug(f"Standard parser: {sprint_count} sprints with {task_count} tasks")

                        for sprint in results["capacity"].sprints:
                            log_debug(f"  {sprint.name}: {sprint.total_hours:.1f}h capacity, {len(sprint.tasks)} tasks")
                    elif not results["pi_analysis"]:
                        log_debug("WARNING: No data extracted from Excel file")
                except Exception as e:
                    st.error(f"Error parsing Excel: {e}")
                    log_debug(f"ERROR parsing Excel: {traceback.format_exc()}")
                finally:
                    try:
                        excel_path.unlink(missing_ok=True)
                    except:
                        pass
            else:
                st.error("Failed to save uploaded Excel file")
                log_debug("ERROR: save_uploaded_file returned None")

        if results["capacity"] and results["capacity"].sprints:
            with st.spinner("Analyzing sprint capacity..."):
                try:
                    results["capacity_analysis"] = capacity_analyzer.analyze(
                        results["capacity"],
                        results["red_flags"],
                    )
                    results["capacity_summary"] = capacity_analyzer.summary(
                        results["capacity_analysis"]
                    )
                    log_debug(f"Capacity analysis complete: {len(results['capacity_analysis'])} sprints analyzed")
                except Exception as e:
                    st.error(f"Error analyzing capacity: {e}")
                    log_debug(f"ERROR analyzing capacity: {traceback.format_exc()}")

            with st.spinner("Analyzing deployment opportunities..."):
                try:
                    results["deployment_clusters"] = deployment_analyzer.analyze(
                        results["capacity"],
                        results["ded"],
                    )
                    results["deployment_summary"] = deployment_analyzer.summary(
                        results["deployment_clusters"],
                        len(results["capacity"].all_tasks),
                    )
                    log_debug(f"Deployment analysis complete: {len(results['deployment_clusters'])} clusters")
                except Exception as e:
                    st.error(f"Error analyzing deployment: {e}")
                    log_debug(f"ERROR analyzing deployment: {traceback.format_exc()}")
        elif results["capacity"]:
            log_debug(f"WARNING: Capacity object exists but has {len(results['capacity'].sprints)} sprints")
        else:
            log_debug("WARNING: No capacity data after parsing")

    return results


# Run analysis when button clicked
if analyze_button:
    st.session_state.analysis_results = run_analysis()

# Display results
if st.session_state.analysis_results:
    results = st.session_state.analysis_results

    st.markdown("---")
    st.header("Analysis Results")

    # Debug info
    has_ded = results.get("ded") is not None
    has_capacity = bool(results.get("capacity_analysis"))
    has_red_flags = bool(results.get("red_flags"))
    has_pi_analysis = results.get("pi_analysis") is not None

    # Show what was analyzed
    analysis_parts = []
    if has_ded:
        analysis_parts.append(f"DED ({len(results['ded'].all_acceptance_criteria)} ACs)")
    if has_pi_analysis:
        pi = results["pi_analysis"]
        analysis_parts.append(f"PI Planning ({len(pi.sprints)} sprints, {len(pi.resources)} resources)")
    if has_capacity:
        analysis_parts.append(f"Capacity ({len(results['capacity_analysis'])} sprints)")
    if has_red_flags:
        analysis_parts.append(f"{len(results['red_flags'])} red flags")

    if analysis_parts:
        st.info(f"Analyzed: {', '.join(analysis_parts)}")
    else:
        st.warning("No data was successfully analyzed. Check the file format.")

    # Create tabs for different analysis sections
    tabs = []

    # PI Dashboard tab first if available (most comprehensive view)
    if has_pi_analysis:
        tabs.append("📊 PI Dashboard")
        tabs.append("🗺️ Roadmap")  # Roadmap tab right after PI Dashboard

    # AI Recommendations tab (available when we have any data)
    if has_pi_analysis or has_capacity or has_red_flags:
        tabs.append("🤖 AI Insights")

    if has_ded:
        tabs.append("🚩 Red Flags")

    if has_capacity:
        tabs.append("📈 Capacity")
        tabs.append("🚀 Deployment")

    tabs.append("📋 Summary")

    # Download tab available when we have red flags OR PI analysis
    if has_red_flags or has_pi_analysis:
        tabs.append("📥 Download")

    # Only show tabs if we have content
    if len(tabs) == 0:
        st.error("No results to display")
    else:
        tab_objects = st.tabs(tabs)
        tab_idx = 0

    # PI Dashboard Tab (if PI analysis available - most comprehensive view)
    if has_pi_analysis:
        with tab_objects[tab_idx]:
            render_pi_dashboard(results["pi_analysis"], results.get("capacity"))
        tab_idx += 1

        # Roadmap Tab (standalone roadmap visualization)
        with tab_objects[tab_idx]:
            st.subheader("Project Roadmap")
            st.markdown("Visual timeline of projects across sprints in the PI.")

            # Summary metrics
            render_roadmap_summary(results["pi_analysis"])

            st.markdown("---")

            # Full roadmap with unique key prefix
            render_roadmap(results["pi_analysis"], results.get("capacity"), key_prefix="standalone")
        tab_idx += 1

    # AI Recommendations Tab
    if has_pi_analysis or has_capacity or has_red_flags:
        with tab_objects[tab_idx]:
            # Get API key from session state settings
            api_key = st.session_state.get("settings", {}).get("api_key", "")
            render_ai_recommendations(
                pi_analysis=results.get("pi_analysis"),
                capacity_plan=results.get("capacity"),
                red_flags=results.get("red_flags"),
                api_key=api_key if api_key else None,
            )
        tab_idx += 1

    # Red Flags Tab (if DED was provided)
    if results["ded"]:
        with tab_objects[tab_idx]:
            st.subheader("Red Flag Analysis")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Epics", len(results["ded"].epics))
            with col2:
                st.metric("Stories", len(results["ded"].all_stories))
            with col3:
                st.metric("Acceptance Criteria", len(results["ded"].all_acceptance_criteria))

            st.markdown("---")

            # Initialize ignored flags in session state
            if "ignored_red_flags" not in st.session_state:
                st.session_state.ignored_red_flags = set()

            # Filter out ignored flags
            all_flags = results["red_flags"]
            active_flags = [
                rf for rf in all_flags
                if f"{rf.flagged_term}|{rf.ac.text[:50]}" not in st.session_state.ignored_red_flags
            ]
            ignored_count = len(all_flags) - len(active_flags)

            # Show ignored count and restore option
            if ignored_count > 0:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"Showing {len(active_flags)} of {len(all_flags)} issues ({ignored_count} hidden)")
                with col2:
                    if st.button("Restore All", key="restore_ignored"):
                        st.session_state.ignored_red_flags = set()
                        st.rerun()

            render_red_flags(active_flags, results["ded"], enable_ignore=True)
        tab_idx += 1

    # Capacity Tab (if available)
    if results["capacity_analysis"]:
        with tab_objects[tab_idx]:
            st.subheader("Capacity Analysis")
            render_capacity_analysis(
                results["capacity_analysis"],
                results["capacity_summary"],
            )
        tab_idx += 1

        # Deployment Tab
        with tab_objects[tab_idx]:
            st.subheader("Deployment Analysis")

            # Strategy legend in sidebar
            with st.sidebar:
                st.markdown("---")
                render_strategy_legend()

            render_deployment_analysis(
                results["deployment_clusters"],
                results["deployment_summary"],
            )
        tab_idx += 1

    # Summary Tab
    with tab_objects[tab_idx]:
        st.subheader("Analysis Summary")

        # Document summary
        if results["ded"]:
            st.markdown("#### Document Overview")
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Filename:** {results['ded'].filename}")
                st.write(f"**Epics:** {len(results['ded'].epics)}")
                st.write(f"**Stories:** {len(results['ded'].all_stories)}")
                st.write(f"**Acceptance Criteria:** {len(results['ded'].all_acceptance_criteria)}")

            with col2:
                risk_summary = results["risk_summary"]
                st.write(f"**Total Red Flags:** {risk_summary.get('total', 0)}")
                st.write(f"**Critical:** {risk_summary.get('critical', 0)}")
                st.write(f"**Moderate:** {risk_summary.get('moderate', 0)}")
                st.write(f"**Low:** {risk_summary.get('low', 0)}")

        # Capacity summary
        if results["capacity_summary"]:
            st.markdown("---")
            st.markdown("#### Capacity Overview")

            cap_summary = results["capacity_summary"]
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Total Sprints:** {cap_summary.get('total_sprints', 0)}")
                st.write(f"**Passing Sprints:** {cap_summary.get('passing_sprints', 0)}")
                st.write(f"**Failing Sprints:** {cap_summary.get('failing_sprints', 0)}")

            with col2:
                st.write(f"**Overall Utilization:** {cap_summary.get('overall_utilization', 0):.1f}%")
                st.write(f"**Total Capacity:** {cap_summary.get('total_capacity_hours', 0):.1f}h")
                st.write(f"**Total Load:** {cap_summary.get('total_load_hours', 0):.1f}h")

        # Deployment summary
        if results["deployment_summary"]:
            st.markdown("---")
            st.markdown("#### Deployment Overview")

            dep_summary = results["deployment_summary"]
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**CD Percentage:** {dep_summary.get('cd_percentage', 0):.1f}%")
                st.write(f"**Status:** {dep_summary.get('status', 'N/A')}")
                st.write(f"**Total Clusters:** {dep_summary.get('total_clusters', 0)}")

            with col2:
                st.write(f"**Eligible Tasks:** {dep_summary.get('eligible_tasks', 0)}")
                st.write(f"**Target Met:** {'Yes' if dep_summary.get('target_met', False) else 'No'}")

    tab_idx += 1

    # Download Tab (available when we have red flags OR PI analysis)
    if has_red_flags or has_pi_analysis:
        with tab_objects[tab_idx]:
            st.subheader("Download Reports")

            # Executive PDF Report (when PI analysis available)
            if has_pi_analysis:
                st.markdown("### 📊 Executive Report (PDF)")
                st.markdown("Generate a professional PDF report for stakeholders.")

                col1, col2 = st.columns([2, 1])

                with col1:
                    report_title = st.text_input(
                        "Report Title",
                        value="PI Planning Executive Report",
                        key="pdf_title"
                    )
                    report_subtitle = st.text_input(
                        "Subtitle (optional)",
                        value="",
                        key="pdf_subtitle",
                        placeholder="e.g., Q1 2026 Planning"
                    )

                with col2:
                    include_resources = st.checkbox("Include Resource Details", value=True)
                    include_financial = st.checkbox("Include Financial Summary", value=True)
                    include_risks = st.checkbox("Include Risk Summary", value=True)

                if st.button("📄 Generate PDF Report", type="primary"):
                    with st.spinner("Generating PDF..."):
                        try:
                            config = ReportConfig(
                                title=report_title,
                                subtitle=report_subtitle,
                                include_resource_details=include_resources,
                                include_financial_summary=include_financial,
                                include_risk_summary=include_risks,
                            )

                            # Get AI summary if available
                            ai_summary = st.session_state.get("ai_summary")

                            pdf_bytes = generate_executive_pdf(
                                pi_analysis=results.get("pi_analysis"),
                                capacity_plan=results.get("capacity"),
                                red_flags=results.get("red_flags"),
                                ai_summary=ai_summary,
                                config=config,
                            )

                            st.download_button(
                                label="⬇️ Download PDF",
                                data=pdf_bytes,
                                file_name="pi_executive_report.pdf",
                                mime="application/pdf",
                                width="stretch",
                            )
                            st.success("PDF generated successfully!")

                        except Exception as e:
                            st.error(f"Failed to generate PDF: {e}")
                            st.info("Make sure fpdf2 is installed: pip install fpdf2")

                st.markdown("---")

            # Red flags reports (when red flags exist)
            if results["red_flags"]:
                st.markdown("### 🚩 Red Flags Reports")

                report_generator = PushbackReport()

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("#### HTML Report")
                    html_report = report_generator.generate(
                        results["red_flags"],
                        results["ded"],
                        output_format="html",
                    )
                    st.download_button(
                        label="📄 Download HTML",
                        data=html_report,
                        file_name="pushback_report.html",
                        mime="text/html",
                        width="stretch",
                    )

                with col2:
                    st.markdown("#### JSON Report")
                    json_report = report_generator.generate(
                        results["red_flags"],
                        results["ded"],
                        output_format="json",
                    )
                    st.download_button(
                        label="📋 Download JSON",
                        data=json_report,
                        file_name="pushback_report.json",
                        mime="application/json",
                        width="stretch",
                    )

                with col3:
                    st.markdown("#### Text Report")
                    text_report = report_generator.generate(
                        results["red_flags"],
                        results["ded"],
                        output_format="text",
                    )
                    st.download_button(
                        label="📝 Download Text",
                        data=text_report,
                        file_name="pushback_report.txt",
                        mime="text/plain",
                        width="stretch",
                    )

                # Preview
                st.markdown("---")
                st.markdown("#### Report Preview")

                preview_format = st.radio(
                    "Preview format:",
                    options=["Text", "HTML (raw)", "JSON"],
                    horizontal=True,
                )

                if preview_format == "Text":
                    st.text(text_report)
                elif preview_format == "HTML (raw)":
                    st.code(html_report, language="html")
                else:
                    st.json(json_report)

    # Debug log section at the bottom (collapsible)
    if results.get("debug_log"):
        st.markdown("---")
        with st.expander("🔧 Debug Log", expanded=False):
            st.caption("Technical details for troubleshooting")
            for log_entry in results["debug_log"]:
                if log_entry.startswith("ERROR"):
                    st.error(log_entry)
                elif log_entry.startswith("WARNING"):
                    st.warning(log_entry)
                else:
                    st.text(log_entry)

# Sidebar info
with st.sidebar:
    st.markdown("---")
    st.markdown("### Tips")
    st.markdown(
        """
        - Upload a DED document to start
        - Excel capacity planner is optional but enables capacity and deployment analysis
        - Adjust buffer percentage based on your team's typical variance
        - Use the tabs to navigate between different analysis views
        """
    )

    st.markdown("---")
    st.markdown("### Actions")

    if st.session_state.analysis_results:
        if st.button("🔄 Clear Results"):
            st.session_state.analysis_results = None
            st.rerun()

    if st.session_state.get("ded_file_data") or st.session_state.get("excel_file_data"):
        if st.button("🗑️ Clear Uploaded Files"):
            st.session_state.ded_file_data = None
            st.session_state.excel_file_data = None
            st.session_state.analysis_results = None
            st.rerun()

    # Save/Load Analysis Section
    st.markdown("---")
    st.markdown("### 💾 Save & Load")

    if st.session_state.analysis_results:
        _render_save_analysis_section()

    _render_load_analysis_section()
