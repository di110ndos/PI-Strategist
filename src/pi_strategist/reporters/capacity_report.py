"""Capacity report generator for sprint loading analysis."""

import json
from pathlib import Path
from typing import Optional

from pi_strategist.analyzers.capacity_analyzer import SprintAnalysis
from pi_strategist.models import CapacityPlan, SprintStatus


class CapacityReport:
    """Generator for capacity check reports."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize the report generator.

        Args:
            template_dir: Optional custom template directory
        """
        self.template_dir = template_dir

    def generate(
        self,
        analyses: list[SprintAnalysis],
        capacity_plan: Optional[CapacityPlan] = None,
        output_format: str = "text",
    ) -> str:
        """Generate a capacity check report.

        Args:
            analyses: List of sprint analyses
            capacity_plan: Optional capacity plan for context
            output_format: Output format ('text', 'html', 'json')

        Returns:
            Formatted report string
        """
        if output_format == "json":
            return self._generate_json(analyses, capacity_plan)
        elif output_format == "html":
            return self._generate_html(analyses, capacity_plan)
        else:
            return self._generate_text(analyses, capacity_plan)

    def _generate_text(
        self,
        analyses: list[SprintAnalysis],
        capacity_plan: Optional[CapacityPlan] = None,
    ) -> str:
        """Generate text format report."""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("CAPACITY CHECK - Sprint Loading")
        lines.append("=" * 70)
        lines.append("")

        if capacity_plan:
            lines.append(f"Source: {capacity_plan.filename}")
            lines.append(f"Total Sprints: {len(capacity_plan.sprints)}")
            lines.append(f"Total Tasks: {len(capacity_plan.all_tasks)}")
            lines.append("")

        # Overall summary
        summary = self._calculate_summary(analyses)
        lines.append("Overall Summary:")
        lines.append(f"  Passing Sprints: {summary['passing']} / {summary['total']}")
        lines.append(f"  Overall Utilization: {summary['utilization']:.1f}%")
        lines.append(f"  Total Capacity: {summary['total_capacity']:.1f}h")
        lines.append(f"  Total Load: {summary['total_load']:.1f}h")
        lines.append("")
        lines.append("-" * 70)

        # Sprint details
        for analysis in analyses:
            sprint = analysis.sprint
            status_icon = "[PASS]" if analysis.status == SprintStatus.PASS else "[FAIL]"

            lines.append("")
            lines.append(f"Sprint: {sprint.name}")
            lines.append("+" + "-" * 40 + "+")
            lines.append(f"| Total Hours:    {sprint.total_hours:>6.1f}              |")
            lines.append(f"| Buffer ({sprint.buffer_percentage*100:.0f}%):   {sprint.buffer_hours:>6.1f}              |")
            lines.append(f"| Net Capacity:   {sprint.net_capacity:>6.1f}              |")
            lines.append(f"| Sprint Load:    {sprint.sprint_load:>6.1f}              |")
            lines.append(f"| Utilization:    {analysis.utilization_percent:>5.1f}%              |")
            lines.append(f"| Status:         {status_icon:>16} |")
            lines.append("+" + "-" * 40 + "+")

            if analysis.status == SprintStatus.FAIL:
                lines.append(f"  Overloaded by: {analysis.overflow_hours:.1f} hours")

            if analysis.recommendations:
                lines.append("")
                lines.append("  Recommendations:")
                for rec in analysis.recommendations:
                    lines.append(f"    - Move {rec.task.id} ({rec.task.hours}h) to {rec.to_sprint}")
                    lines.append(f"      Reason: {rec.reason}")

            if analysis.high_risk_tasks:
                lines.append("")
                lines.append("  High-Risk Tasks (contain red flags):")
                for task in analysis.high_risk_tasks:
                    lines.append(f"    - {task.id}: {task.name}")

            lines.append("")
            lines.append("-" * 70)

        return "\n".join(lines)

    def _generate_html(
        self,
        analyses: list[SprintAnalysis],
        capacity_plan: Optional[CapacityPlan] = None,
    ) -> str:
        """Generate HTML format report."""
        summary = self._calculate_summary(analyses)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Capacity Check - Sprint Loading</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .report {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }}
        .summary-number {{
            font-size: 2em;
            font-weight: bold;
        }}
        .sprint-card {{
            border: 1px solid #ddd;
            border-radius: 6px;
            margin: 20px 0;
            overflow: hidden;
        }}
        .sprint-header {{
            padding: 15px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .sprint-header.pass {{
            background: #d4edda;
            border-bottom: 1px solid #c3e6cb;
        }}
        .sprint-header.fail {{
            background: #f8d7da;
            border-bottom: 1px solid #f5c6cb;
        }}
        .status-badge {{
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .status-pass {{ background: #28a745; color: white; }}
        .status-fail {{ background: #dc3545; color: white; }}
        .sprint-body {{
            padding: 15px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .metric-label {{
            font-size: 0.8em;
            color: #666;
        }}
        .capacity-bar {{
            height: 20px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .capacity-fill {{
            height: 100%;
            transition: width 0.3s;
        }}
        .capacity-fill.under {{ background: #28a745; }}
        .capacity-fill.over {{ background: #dc3545; }}
        .recommendations {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 4px;
            margin-top: 15px;
        }}
        .recommendations h4 {{
            margin-top: 0;
            color: #856404;
        }}
        .high-risk {{
            background: #f8d7da;
            padding: 15px;
            border-radius: 4px;
            margin-top: 15px;
        }}
        .high-risk h4 {{
            margin-top: 0;
            color: #721c24;
        }}
        ul {{
            margin: 0;
            padding-left: 20px;
        }}
    </style>
</head>
<body>
    <div class="report">
        <h1>Capacity Check - Sprint Loading</h1>
"""

        if capacity_plan:
            html += f"""
        <p><strong>Source:</strong> {capacity_plan.filename} |
           <strong>Sprints:</strong> {len(capacity_plan.sprints)} |
           <strong>Tasks:</strong> {len(capacity_plan.all_tasks)}</p>
"""

        html += f"""
        <div class="summary">
            <div class="summary-card">
                <div class="summary-number">{summary['passing']}/{summary['total']}</div>
                <div>Passing Sprints</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{summary['utilization']:.0f}%</div>
                <div>Utilization</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{summary['total_capacity']:.0f}h</div>
                <div>Total Capacity</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{summary['total_load']:.0f}h</div>
                <div>Total Load</div>
            </div>
        </div>
"""

        for analysis in analyses:
            sprint = analysis.sprint
            status_class = "pass" if analysis.status == SprintStatus.PASS else "fail"
            status_text = "PASS" if analysis.status == SprintStatus.PASS else "FAIL"
            bar_class = "under" if analysis.status == SprintStatus.PASS else "over"
            bar_width = min(analysis.utilization_percent, 150)

            html += f"""
        <div class="sprint-card">
            <div class="sprint-header {status_class}">
                <span>{sprint.name}</span>
                <span class="status-badge status-{status_class}">{status_text}</span>
            </div>
            <div class="sprint-body">
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{sprint.total_hours:.0f}h</div>
                        <div class="metric-label">Total Hours</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{sprint.net_capacity:.0f}h</div>
                        <div class="metric-label">Net Capacity</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{sprint.sprint_load:.0f}h</div>
                        <div class="metric-label">Sprint Load</div>
                    </div>
                </div>
                <div class="capacity-bar">
                    <div class="capacity-fill {bar_class}" style="width: {bar_width}%"></div>
                </div>
                <p style="text-align: center; margin: 5px 0; color: #666;">
                    {analysis.utilization_percent:.1f}% utilization
                    (Buffer: {sprint.buffer_percentage*100:.0f}%)
                </p>
"""

            if analysis.status == SprintStatus.FAIL:
                html += f"""
                <p style="text-align: center; color: #dc3545; font-weight: bold;">
                    Overloaded by {analysis.overflow_hours:.1f} hours
                </p>
"""

            if analysis.recommendations:
                html += """
                <div class="recommendations">
                    <h4>Recommendations</h4>
                    <ul>
"""
                for rec in analysis.recommendations:
                    html += f"""
                        <li>Move <strong>{rec.task.id}</strong> ({rec.task.hours}h) to {rec.to_sprint}<br>
                        <small>{rec.reason}</small></li>
"""
                html += """
                    </ul>
                </div>
"""

            if analysis.high_risk_tasks:
                html += """
                <div class="high-risk">
                    <h4>High-Risk Tasks (require early validation)</h4>
                    <ul>
"""
                for task in analysis.high_risk_tasks:
                    html += f"""
                        <li><strong>{task.id}</strong>: {task.name}</li>
"""
                html += """
                    </ul>
                </div>
"""

            html += """
            </div>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def _generate_json(
        self,
        analyses: list[SprintAnalysis],
        capacity_plan: Optional[CapacityPlan] = None,
    ) -> str:
        """Generate JSON format report."""
        data = {
            "report_type": "capacity_check",
            "summary": self._calculate_summary(analyses),
            "source": {
                "filename": capacity_plan.filename if capacity_plan else None,
                "sprints": len(capacity_plan.sprints) if capacity_plan else 0,
                "tasks": len(capacity_plan.all_tasks) if capacity_plan else 0,
            },
            "sprints": [
                {
                    "name": a.sprint.name,
                    "total_hours": a.sprint.total_hours,
                    "buffer_percentage": a.sprint.buffer_percentage,
                    "buffer_hours": a.sprint.buffer_hours,
                    "net_capacity": a.sprint.net_capacity,
                    "sprint_load": a.sprint.sprint_load,
                    "utilization_percent": round(a.utilization_percent, 1),
                    "status": a.status.value,
                    "overflow_hours": round(a.overflow_hours, 1),
                    "tasks": [
                        {"id": t.id, "name": t.name, "hours": t.hours}
                        for t in a.sprint.tasks
                    ],
                    "recommendations": [
                        {
                            "task_id": r.task.id,
                            "from_sprint": r.from_sprint,
                            "to_sprint": r.to_sprint,
                            "reason": r.reason,
                        }
                        for r in a.recommendations
                    ],
                    "high_risk_tasks": [
                        {"id": t.id, "name": t.name}
                        for t in a.high_risk_tasks
                    ],
                }
                for a in analyses
            ],
        }

        return json.dumps(data, indent=2)

    def _calculate_summary(self, analyses: list[SprintAnalysis]) -> dict:
        """Calculate summary statistics."""
        total = len(analyses)
        passing = sum(1 for a in analyses if a.status == SprintStatus.PASS)
        total_capacity = sum(a.sprint.net_capacity for a in analyses)
        total_load = sum(a.sprint.sprint_load for a in analyses)
        utilization = (total_load / total_capacity * 100) if total_capacity > 0 else 0

        return {
            "total": total,
            "passing": passing,
            "failing": total - passing,
            "utilization": utilization,
            "total_capacity": total_capacity,
            "total_load": total_load,
        }

    def save(
        self,
        content: str,
        output_path: Path,
        output_format: str = "html",
    ):
        """Save report to file.

        Args:
            content: Report content
            output_path: Path to save to
            output_format: Format for file extension
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        extension = {"html": ".html", "json": ".json", "text": ".txt"}.get(output_format, ".txt")

        if not output_path.suffix:
            output_path = output_path.with_suffix(extension)

        output_path.write_text(content, encoding="utf-8")
