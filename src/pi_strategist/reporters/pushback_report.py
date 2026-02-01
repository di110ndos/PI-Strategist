"""Pushback report generator for red flag analysis."""

import json
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pi_strategist.models import DEDDocument, RedFlag, RedFlagSeverity


class PushbackReport:
    """Generator for pushback reports on red flags."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize the report generator.

        Args:
            template_dir: Optional custom template directory
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = template_dir
        self._setup_jinja()

    def _setup_jinja(self):
        """Set up Jinja2 environment."""
        if self.template_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            self.env = None

    def generate(
        self,
        red_flags: list[RedFlag],
        ded: Optional[DEDDocument] = None,
        output_format: str = "text",
    ) -> str:
        """Generate a pushback report.

        Args:
            red_flags: List of red flags to report
            ded: Optional DED document for context
            output_format: Output format ('text', 'html', 'json')

        Returns:
            Formatted report string
        """
        if output_format == "json":
            return self._generate_json(red_flags, ded)
        elif output_format == "html":
            return self._generate_html(red_flags, ded)
        else:
            return self._generate_text(red_flags, ded)

    def _generate_text(
        self,
        red_flags: list[RedFlag],
        ded: Optional[DEDDocument] = None,
    ) -> str:
        """Generate text format report."""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("PUSHBACK REPORT - DED Analysis")
        lines.append("=" * 70)
        lines.append("")

        if ded:
            lines.append(f"Document: {ded.filename}")
            lines.append(f"Epics: {len(ded.epics)}")
            lines.append(f"Stories: {len(ded.all_stories)}")
            lines.append(f"Acceptance Criteria: {len(ded.all_acceptance_criteria)}")
            lines.append("")

        # Summary
        summary = self._calculate_summary(red_flags)
        lines.append("Risk Summary:")
        lines.append(f"  Total Red Flags: {summary['total']}")
        lines.append(f"  Critical (blocking acceptance): {summary['critical']}")
        lines.append(f"  Moderate (clarification needed): {summary['moderate']}")
        lines.append(f"  Low (nice to clarify): {summary['low']}")
        lines.append("")
        lines.append("-" * 70)
        lines.append("")

        # Group by story/epic
        grouped = self._group_by_story(red_flags)

        flag_num = 1
        for story_key, flags in grouped.items():
            story_id, story_name = story_key

            lines.append(f"Story: {story_name} ({story_id})")
            lines.append("")

            for rf in flags:
                severity_icon = self._severity_icon(rf.severity)
                lines.append(f"{severity_icon} RED FLAG #{flag_num}")
                lines.append(f"   AC: \"{rf.ac.text}\"")
                lines.append(f"   Issue: {rf.category} - \"{rf.flagged_term}\"")
                lines.append(f"   Suggested Metric: \"{rf.suggested_metric}\"")
                lines.append(f"   Negotiation Script: \"{rf.negotiation_script}\"")
                lines.append("")
                flag_num += 1

            lines.append("-" * 70)
            lines.append("")

        return "\n".join(lines)

    def _generate_html(
        self,
        red_flags: list[RedFlag],
        ded: Optional[DEDDocument] = None,
    ) -> str:
        """Generate HTML format report."""
        summary = self._calculate_summary(red_flags)
        grouped = self._group_by_story(red_flags)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pushback Report - DED Analysis</title>
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
            border-bottom: 2px solid #e74c3c;
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
        .summary-card.critical {{ border-left: 4px solid #e74c3c; }}
        .summary-card.moderate {{ border-left: 4px solid #f39c12; }}
        .summary-card.low {{ border-left: 4px solid #3498db; }}
        .summary-card.total {{ border-left: 4px solid #333; }}
        .summary-number {{
            font-size: 2em;
            font-weight: bold;
        }}
        .story-section {{
            margin: 30px 0;
            border: 1px solid #ddd;
            border-radius: 6px;
        }}
        .story-header {{
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
        }}
        .red-flag {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        .red-flag:last-child {{
            border-bottom: none;
        }}
        .flag-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }}
        .severity-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .severity-critical {{ background: #e74c3c; color: white; }}
        .severity-moderate {{ background: #f39c12; color: white; }}
        .severity-low {{ background: #3498db; color: white; }}
        .ac-text {{
            background: #fff3cd;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-style: italic;
        }}
        .suggestion {{
            background: #d4edda;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .negotiation {{
            background: #cce5ff;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .label {{
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="report">
        <h1>Pushback Report - DED Analysis</h1>
"""

        if ded:
            html += f"""
        <p><strong>Document:</strong> {ded.filename}</p>
        <p><strong>Scope:</strong> {len(ded.epics)} epics, {len(ded.all_stories)} stories, {len(ded.all_acceptance_criteria)} acceptance criteria</p>
"""

        html += f"""
        <div class="summary">
            <div class="summary-card total">
                <div class="summary-number">{summary['total']}</div>
                <div>Total Red Flags</div>
            </div>
            <div class="summary-card critical">
                <div class="summary-number">{summary['critical']}</div>
                <div>Critical</div>
            </div>
            <div class="summary-card moderate">
                <div class="summary-number">{summary['moderate']}</div>
                <div>Moderate</div>
            </div>
            <div class="summary-card low">
                <div class="summary-number">{summary['low']}</div>
                <div>Low</div>
            </div>
        </div>
"""

        flag_num = 1
        for story_key, flags in grouped.items():
            story_id, story_name = story_key

            html += f"""
        <div class="story-section">
            <div class="story-header">{story_name} ({story_id})</div>
"""

            for rf in flags:
                severity_class = rf.severity.value
                html += f"""
            <div class="red-flag">
                <div class="flag-header">
                    <span class="severity-badge severity-{severity_class}">{severity_class.upper()}</span>
                    <strong>Red Flag #{flag_num}: {rf.category}</strong>
                </div>
                <div class="label">Acceptance Criteria:</div>
                <div class="ac-text">"{rf.ac.text}"</div>
                <div class="label">Flagged Term: <code>{rf.flagged_term}</code></div>
                <div class="label">Suggested Metric:</div>
                <div class="suggestion">{rf.suggested_metric}</div>
                <div class="label">Negotiation Script:</div>
                <div class="negotiation">"{rf.negotiation_script}"</div>
            </div>
"""
                flag_num += 1

            html += """
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
        red_flags: list[RedFlag],
        ded: Optional[DEDDocument] = None,
    ) -> str:
        """Generate JSON format report."""
        data = {
            "report_type": "pushback_report",
            "summary": self._calculate_summary(red_flags),
            "document": {
                "filename": ded.filename if ded else None,
                "epics": len(ded.epics) if ded else 0,
                "stories": len(ded.all_stories) if ded else 0,
                "acceptance_criteria": len(ded.all_acceptance_criteria) if ded else 0,
            },
            "red_flags": [
                {
                    "id": i + 1,
                    "ac_id": rf.ac.id,
                    "ac_text": rf.ac.text,
                    "story_id": rf.ac.story_id,
                    "epic_id": rf.ac.epic_id,
                    "flagged_term": rf.flagged_term,
                    "category": rf.category,
                    "severity": rf.severity.value,
                    "suggested_metric": rf.suggested_metric,
                    "negotiation_script": rf.negotiation_script,
                }
                for i, rf in enumerate(red_flags)
            ],
        }

        return json.dumps(data, indent=2)

    def _calculate_summary(self, red_flags: list[RedFlag]) -> dict:
        """Calculate summary statistics."""
        return {
            "total": len(red_flags),
            "critical": len([rf for rf in red_flags if rf.severity == RedFlagSeverity.CRITICAL]),
            "moderate": len([rf for rf in red_flags if rf.severity == RedFlagSeverity.MODERATE]),
            "low": len([rf for rf in red_flags if rf.severity == RedFlagSeverity.LOW]),
        }

    def _group_by_story(
        self,
        red_flags: list[RedFlag],
    ) -> dict[tuple[str, str], list[RedFlag]]:
        """Group red flags by story."""
        grouped: dict[tuple[str, str], list[RedFlag]] = {}

        for rf in red_flags:
            story_id = rf.ac.story_id or "UNKNOWN"
            story_key = (story_id, f"Story {story_id}")

            if story_key not in grouped:
                grouped[story_key] = []
            grouped[story_key].append(rf)

        return grouped

    def _severity_icon(self, severity: RedFlagSeverity) -> str:
        """Get icon for severity level."""
        icons = {
            RedFlagSeverity.CRITICAL: "[X]",
            RedFlagSeverity.MODERATE: "[!]",
            RedFlagSeverity.LOW: "[~]",
        }
        return icons.get(severity, "[?]")

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
