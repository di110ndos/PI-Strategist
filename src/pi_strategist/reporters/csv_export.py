"""CSV export utilities for PI Strategist analysis results."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

import streamlit as st

from pi_strategist.models import (
    DeploymentCluster,
    RedFlag,
)

if TYPE_CHECKING:
    from pi_strategist.analyzers.capacity_analyzer import SprintAnalysis


def red_flags_to_csv(red_flags: list[RedFlag]) -> str:
    """Convert red flags to CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Severity", "Flagged Term", "Category",
        "Acceptance Criteria", "Story ID", "Epic ID",
        "Suggested Metric", "Negotiation Script",
    ])
    for rf in red_flags:
        writer.writerow([
            rf.severity.value,
            rf.flagged_term,
            rf.category,
            rf.ac.text,
            rf.ac.story_id or "",
            rf.ac.epic_id or "",
            rf.suggested_metric,
            rf.negotiation_script,
        ])
    return buf.getvalue()


def capacity_to_csv(analyses: list[SprintAnalysis]) -> str:
    """Convert capacity analyses to CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Sprint", "Status", "Total Hours", "Net Capacity",
        "Sprint Load", "Buffer Hours", "Utilization %",
        "Overflow Hours", "Task Count",
    ])
    for a in analyses:
        s = a.sprint
        writer.writerow([
            s.name,
            "PASS" if a.status.value == "pass" else "FAIL",
            f"{s.total_hours:.1f}",
            f"{s.net_capacity:.1f}",
            f"{s.sprint_load:.1f}",
            f"{s.buffer_hours:.1f}",
            f"{a.utilization_percent:.1f}",
            f"{a.overflow_hours:.1f}",
            len(s.tasks),
        ])
    return buf.getvalue()


def deployment_to_csv(clusters: list[DeploymentCluster]) -> str:
    """Convert deployment clusters to CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Cluster", "Strategy", "Timing", "Task Count",
        "Dependencies", "Rollback Plan",
    ])
    for c in clusters:
        writer.writerow([
            c.name,
            c.strategy.value.replace("_", " ").title(),
            c.deploy_timing,
            len(c.tasks),
            "; ".join(c.dependencies),
            c.rollback_plan,
        ])
    return buf.getvalue()


def resources_to_csv(resources: dict, pi_max_hours: float = 488.0) -> str:
    """Convert resource data to CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Name", "Discipline", "Total Hours", "Max Hours",
        "Allocation %", "Status", "Rate", "Cost",
    ])
    for name, resource in sorted(resources.items()):
        total = resource.total_hours
        alloc = (total / pi_max_hours * 100) if pi_max_hours > 0 else 0
        rate = resource.rate
        cost = total * rate if rate > 0 else 0

        if alloc > 105:
            status = "Over"
        elif alloc < 80 and total > 0:
            status = "Under"
        elif total > 0:
            status = "OK"
        else:
            status = "-"

        writer.writerow([
            name,
            resource.discipline or "-",
            f"{total:.1f}",
            f"{pi_max_hours:.0f}",
            f"{alloc:.1f}",
            status,
            f"{rate:.2f}" if rate > 0 else "",
            f"{cost:.0f}" if cost > 0 else "",
        ])
    return buf.getvalue()


def render_csv_download(csv_data: str, filename: str, label: str = "Download CSV") -> None:
    """Render a Streamlit download button for CSV data."""
    st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
    )
