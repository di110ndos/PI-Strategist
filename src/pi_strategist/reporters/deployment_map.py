"""Deployment map generator for CD strategy."""

import json
from pathlib import Path
from typing import Optional

from pi_strategist.models import DeploymentCluster, DeploymentStrategy


class DeploymentMap:
    """Generator for deployment map reports."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize the report generator.

        Args:
            template_dir: Optional custom template directory
        """
        self.template_dir = template_dir

    def generate(
        self,
        clusters: list[DeploymentCluster],
        total_tasks: int,
        target_percentage: float = 30.0,
        output_format: str = "text",
    ) -> str:
        """Generate a deployment map report.

        Args:
            clusters: List of deployment clusters
            total_tasks: Total number of tasks in PI
            target_percentage: Target CD percentage
            output_format: Output format ('text', 'html', 'json')

        Returns:
            Formatted report string
        """
        if output_format == "json":
            return self._generate_json(clusters, total_tasks, target_percentage)
        elif output_format == "html":
            return self._generate_html(clusters, total_tasks, target_percentage)
        else:
            return self._generate_text(clusters, total_tasks, target_percentage)

    def _generate_text(
        self,
        clusters: list[DeploymentCluster],
        total_tasks: int,
        target_percentage: float,
    ) -> str:
        """Generate text format report."""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("DEPLOYMENT MAP - Continuous Delivery Strategy")
        lines.append("=" * 70)
        lines.append("")

        # Clusters
        for i, cluster in enumerate(clusters, 1):
            strategy_name = self._format_strategy(cluster.strategy)

            lines.append(f"Cluster {i}: {cluster.name} (Deploy {cluster.deploy_timing})")
            for task in cluster.tasks:
                lines.append(f"  - {task.id}: {task.name}")

            lines.append(f"  Strategy: {strategy_name}")

            if cluster.dependencies:
                lines.append(f"  Dependencies: {', '.join(cluster.dependencies)}")
            else:
                lines.append("  Dependencies: None")

            lines.append(f"  Rollback Plan: {cluster.rollback_plan}")
            lines.append("")
            lines.append("-" * 70)
            lines.append("")

        # Summary
        eligible = sum(len(c.tasks) for c in clusters)
        percentage = (eligible / total_tasks * 100) if total_tasks > 0 else 0
        status = "ON TRACK" if percentage >= target_percentage else "BELOW TARGET"
        status_icon = "[OK]" if percentage >= target_percentage else "[!!]"

        lines.append("=" * 70)
        lines.append(f"CD Achievement: {eligible}/{total_tasks} tasks ({percentage:.1f}%) eligible for early deploy")
        lines.append(f"Target: {target_percentage:.0f}% of tasks deployed before PI demo")
        lines.append(f"Status: {status_icon} {status}")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _generate_html(
        self,
        clusters: list[DeploymentCluster],
        total_tasks: int,
        target_percentage: float,
    ) -> str:
        """Generate HTML format report."""
        eligible = sum(len(c.tasks) for c in clusters)
        percentage = (eligible / total_tasks * 100) if total_tasks > 0 else 0
        on_track = percentage >= target_percentage

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deployment Map - CD Strategy</title>
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
            border-bottom: 2px solid #9b59b6;
            padding-bottom: 10px;
        }}
        .summary-banner {{
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
            text-align: center;
        }}
        .summary-banner.on-track {{
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            border: 1px solid #28a745;
        }}
        .summary-banner.below-target {{
            background: linear-gradient(135deg, #fff3cd, #ffeeba);
            border: 1px solid #ffc107;
        }}
        .summary-number {{
            font-size: 3em;
            font-weight: bold;
        }}
        .summary-banner.on-track .summary-number {{ color: #28a745; }}
        .summary-banner.below-target .summary-number {{ color: #856404; }}
        .progress-bar {{
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
            position: relative;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #9b59b6, #8e44ad);
            transition: width 0.5s;
        }}
        .progress-target {{
            position: absolute;
            top: 0;
            height: 100%;
            width: 2px;
            background: #333;
        }}
        .progress-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            color: #666;
        }}
        .cluster-card {{
            border: 1px solid #ddd;
            border-radius: 6px;
            margin: 20px 0;
            overflow: hidden;
        }}
        .cluster-header {{
            padding: 15px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .cluster-timing {{
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .cluster-body {{
            padding: 15px;
        }}
        .task-list {{
            list-style: none;
            padding: 0;
            margin: 0 0 15px 0;
        }}
        .task-list li {{
            padding: 8px 12px;
            background: #f8f9fa;
            margin: 5px 0;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
        }}
        .task-id {{
            font-weight: bold;
            color: #667eea;
        }}
        .strategy-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .strategy-feature_flag {{ background: #e3f2fd; color: #1565c0; }}
        .strategy-full_deployment {{ background: #e8f5e9; color: #2e7d32; }}
        .meta-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 0.9em;
            color: #666;
        }}
        .meta-info .label {{
            font-weight: bold;
        }}
        .timeline {{
            display: flex;
            justify-content: space-between;
            margin: 30px 0;
            position: relative;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 4px;
            background: #ddd;
        }}
        .timeline-item {{
            text-align: center;
            position: relative;
            flex: 1;
        }}
        .timeline-dot {{
            width: 40px;
            height: 40px;
            background: #667eea;
            border-radius: 50%;
            margin: 0 auto 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            position: relative;
            z-index: 1;
        }}
        .timeline-label {{
            font-size: 0.8em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="report">
        <h1>Deployment Map - Continuous Delivery Strategy</h1>

        <div class="summary-banner {'on-track' if on_track else 'below-target'}">
            <div class="summary-number">{percentage:.0f}%</div>
            <div>Tasks Eligible for Early Deployment</div>
            <div style="margin-top: 10px;">
                <strong>{eligible}</strong> of <strong>{total_tasks}</strong> tasks |
                Target: {target_percentage:.0f}% |
                Status: <strong>{'ON TRACK' if on_track else 'BELOW TARGET'}</strong>
            </div>
        </div>

        <div class="progress-bar">
            <div class="progress-fill" style="width: {min(percentage, 100)}%"></div>
            <div class="progress-target" style="left: {target_percentage}%"></div>
        </div>
        <div class="progress-labels">
            <span>0%</span>
            <span>Target: {target_percentage:.0f}%</span>
            <span>100%</span>
        </div>
"""

        if clusters:
            html += """
        <h2>Deployment Timeline</h2>
        <div class="timeline">
"""
            for i, cluster in enumerate(clusters, 1):
                html += f"""
            <div class="timeline-item">
                <div class="timeline-dot">{i}</div>
                <div class="timeline-label">{cluster.deploy_timing}<br><small>{cluster.name}</small></div>
            </div>
"""
            html += """
        </div>
"""

        html += """
        <h2>Deployment Clusters</h2>
"""

        for i, cluster in enumerate(clusters, 1):
            strategy_class = cluster.strategy.value
            strategy_name = self._format_strategy(cluster.strategy)

            html += f"""
        <div class="cluster-card">
            <div class="cluster-header">
                <span><strong>Cluster {i}:</strong> {cluster.name}</span>
                <span class="cluster-timing">{cluster.deploy_timing}</span>
            </div>
            <div class="cluster-body">
                <span class="strategy-badge strategy-{strategy_class}">{strategy_name}</span>

                <ul class="task-list">
"""
            for task in cluster.tasks:
                html += f"""
                    <li>
                        <span class="task-id">{task.id}</span>
                        <span>{task.name}</span>
                    </li>
"""
            html += """
                </ul>

                <div class="meta-info">
                    <div>
                        <span class="label">Dependencies:</span>
                        <span>"""

            if cluster.dependencies:
                html += ", ".join(cluster.dependencies)
            else:
                html += "None"

            html += f"""</span>
                    </div>
                    <div>
                        <span class="label">Rollback:</span>
                        <span>{cluster.rollback_plan}</span>
                    </div>
                </div>
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
        clusters: list[DeploymentCluster],
        total_tasks: int,
        target_percentage: float,
    ) -> str:
        """Generate JSON format report."""
        eligible = sum(len(c.tasks) for c in clusters)
        percentage = (eligible / total_tasks * 100) if total_tasks > 0 else 0

        data = {
            "report_type": "deployment_map",
            "summary": {
                "total_clusters": len(clusters),
                "eligible_tasks": eligible,
                "total_tasks": total_tasks,
                "cd_percentage": round(percentage, 1),
                "target_percentage": target_percentage,
                "on_track": percentage >= target_percentage,
                "status": "ON TRACK" if percentage >= target_percentage else "BELOW TARGET",
            },
            "clusters": [
                {
                    "name": c.name,
                    "deploy_timing": c.deploy_timing,
                    "strategy": c.strategy.value,
                    "strategy_description": self._format_strategy(c.strategy),
                    "tasks": [
                        {"id": t.id, "name": t.name, "hours": t.hours}
                        for t in c.tasks
                    ],
                    "dependencies": c.dependencies,
                    "rollback_plan": c.rollback_plan,
                }
                for c in clusters
            ],
        }

        return json.dumps(data, indent=2)

    def _format_strategy(self, strategy: DeploymentStrategy) -> str:
        """Format strategy name for display."""
        names = {
            DeploymentStrategy.FEATURE_FLAG: "Feature Flag",
            DeploymentStrategy.FULL_DEPLOYMENT: "Full Deployment",
        }
        return names.get(strategy, strategy.value)

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
