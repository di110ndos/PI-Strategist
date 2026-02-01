"""CLI application for PI Strategist."""

import os
import sys
from pathlib import Path
from typing import Optional

# Fix Windows console encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from pi_strategist.analyzers.capacity_analyzer import CapacityAnalyzer
from pi_strategist.analyzers.deployment_analyzer import DeploymentAnalyzer
from pi_strategist.analyzers.risk_analyzer import RiskAnalyzer
from pi_strategist.models import AnalysisResult
from pi_strategist.parsers.ded_parser import DEDParser
from pi_strategist.parsers.excel_parser import ExcelParser
from pi_strategist.reporters.capacity_report import CapacityReport
from pi_strategist.reporters.deployment_map import DeploymentMap
from pi_strategist.reporters.pushback_report import PushbackReport

console = Console(force_terminal=True)


@click.group()
@click.version_option(version="1.0.0", prog_name="PI Strategist")
def main():
    """PI Strategist - DED Analysis & Capacity Planning Tool.

    Analyze DEDs for red flags, validate sprint capacity, and generate
    deployment strategies for continuous delivery.
    """
    pass


@main.command()
@click.argument("ded_file", type=click.Path(exists=True))
@click.option(
    "--excel", "-e",
    type=click.Path(exists=True),
    help="Excel capacity planner file",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./output",
    help="Output directory for reports",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["html", "json", "text"]),
    default="html",
    help="Output format",
)
@click.option(
    "--buffer", "-b",
    type=float,
    default=0.20,
    help="Buffer percentage (default: 0.20 = 20%)",
)
def analyze(
    ded_file: str,
    excel: Optional[str],
    output: str,
    format: str,
    buffer: float,
):
    """Analyze a DED document for risks, capacity, and deployment strategy.

    DED_FILE: Path to the DED document (.docx, .md, or .pdf)
    """
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Parse documents
        task = progress.add_task("Parsing DED document...", total=None)
        ded_parser = DEDParser()
        try:
            ded = ded_parser.parse(ded_file)
        except Exception as e:
            console.print(f"[red]Error parsing DED: {e}[/red]")
            sys.exit(1)
        progress.update(task, completed=True)

        capacity_plan = None
        if excel:
            task = progress.add_task("Parsing capacity planner...", total=None)
            excel_parser = ExcelParser(default_buffer=buffer)
            try:
                capacity_plan = excel_parser.parse(excel)
            except Exception as e:
                console.print(f"[red]Error parsing Excel: {e}[/red]")
                sys.exit(1)
            progress.update(task, completed=True)

        # Run analysis
        task = progress.add_task("Analyzing red flags...", total=None)
        risk_analyzer = RiskAnalyzer()
        red_flags = risk_analyzer.analyze(ded)
        progress.update(task, completed=True)

        sprint_analyses = []
        if capacity_plan:
            task = progress.add_task("Validating capacity...", total=None)
            capacity_analyzer = CapacityAnalyzer(default_buffer=buffer)
            sprint_analyses = capacity_analyzer.analyze(capacity_plan, red_flags)
            progress.update(task, completed=True)

            task = progress.add_task("Generating deployment strategy...", total=None)
            deployment_analyzer = DeploymentAnalyzer()
            clusters = deployment_analyzer.analyze(capacity_plan, ded)
            progress.update(task, completed=True)
        else:
            clusters = []

        # Generate reports
        task = progress.add_task("Generating reports...", total=None)

        # Pushback report
        pushback_reporter = PushbackReport()
        pushback_content = pushback_reporter.generate(red_flags, ded, format)
        pushback_path = output_dir / f"pushback_report.{format if format != 'text' else 'txt'}"
        pushback_reporter.save(pushback_content, pushback_path, format)

        # Capacity report
        if sprint_analyses:
            capacity_reporter = CapacityReport()
            capacity_content = capacity_reporter.generate(sprint_analyses, capacity_plan, format)
            capacity_path = output_dir / f"capacity_check.{format if format != 'text' else 'txt'}"
            capacity_reporter.save(capacity_content, capacity_path, format)

        # Deployment map
        if clusters:
            deployment_reporter = DeploymentMap()
            total_tasks = len(capacity_plan.all_tasks) if capacity_plan else 0
            deployment_content = deployment_reporter.generate(clusters, total_tasks, 30.0, format)
            deployment_path = output_dir / f"deployment_map.{format if format != 'text' else 'txt'}"
            deployment_reporter.save(deployment_content, deployment_path, format)

        progress.update(task, completed=True)

    # Display summary
    _display_summary(ded, capacity_plan, red_flags, sprint_analyses, clusters, output_dir)


@main.command()
@click.option(
    "--dir", "-d",
    type=click.Path(exists=True),
    required=True,
    help="Directory containing DED and Excel files",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./output",
    help="Output directory for reports",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["html", "json", "text"]),
    default="html",
    help="Output format",
)
def batch(dir: str, output: str, format: str):
    """Batch process all documents in a directory.

    Processes all .docx, .md, .pdf (DEDs) and .xlsx (capacity planners) files.
    """
    input_dir = Path(dir)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find DED files
    ded_patterns = ["*.docx", "*.md", "*.pdf"]
    ded_files = []
    for pattern in ded_patterns:
        ded_files.extend(input_dir.glob(pattern))

    # Find Excel files
    excel_files = list(input_dir.glob("*.xlsx"))

    if not ded_files:
        console.print("[yellow]No DED files found in directory.[/yellow]")
        return

    console.print(f"Found {len(ded_files)} DED files and {len(excel_files)} Excel files.")

    # Process each DED
    for ded_file in ded_files:
        console.print(f"\n[bold]Processing: {ded_file.name}[/bold]")

        # Try to find matching Excel file
        excel_file = None
        ded_stem = ded_file.stem.lower()
        for ef in excel_files:
            if ded_stem in ef.stem.lower() or ef.stem.lower() in ded_stem:
                excel_file = ef
                break

        # Create output subdirectory
        file_output = output_dir / ded_file.stem
        file_output.mkdir(parents=True, exist_ok=True)

        # Run analysis using click context
        ctx = click.Context(analyze)
        ctx.invoke(
            analyze,
            ded_file=str(ded_file),
            excel=str(excel_file) if excel_file else None,
            output=str(file_output),
            format=format,
            buffer=0.20,
        )


@main.command()
@click.option(
    "--format", "-f",
    type=click.Choice(["html", "json", "text"]),
    default="html",
    help="Output format",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file path",
)
def report(format: str, output: Optional[str]):
    """Generate a combined report from existing analysis.

    This command is used after running 'analyze' to regenerate reports
    in a different format.
    """
    console.print("[yellow]This command requires existing analysis data.[/yellow]")
    console.print("Run 'pi-strategist analyze' first to generate analysis data.")


@main.command()
@click.option(
    "--set-api-key",
    type=str,
    help="Set Anthropic API key for Claude integration",
)
@click.option(
    "--show",
    is_flag=True,
    help="Show current configuration",
)
def config(set_api_key: Optional[str], show: bool):
    """Configure PI Strategist settings."""
    config_dir = Path.home() / ".pi-strategist"
    config_file = config_dir / "config.json"

    if set_api_key:
        config_dir.mkdir(parents=True, exist_ok=True)
        import json

        config_data = {}
        if config_file.exists():
            config_data = json.loads(config_file.read_text())

        config_data["anthropic_api_key"] = set_api_key
        config_file.write_text(json.dumps(config_data, indent=2))
        console.print("[green]API key saved successfully.[/green]")

    if show:
        if config_file.exists():
            import json
            config_data = json.loads(config_file.read_text())
            table = Table(title="Configuration")
            table.add_column("Setting")
            table.add_column("Value")

            for key, value in config_data.items():
                if "key" in key.lower():
                    value = value[:8] + "..." if value else "Not set"
                table.add_row(key, str(value))

            console.print(table)
        else:
            console.print("[yellow]No configuration found.[/yellow]")


@main.command()
@click.argument("text", nargs=-1)
def check(text: tuple):
    """Quick check text for red flags.

    Useful for checking individual acceptance criteria.

    Example: pi-strategist check "The system should be fast and user-friendly"
    """
    if not text:
        console.print("[yellow]Please provide text to check.[/yellow]")
        console.print("Example: pi-strategist check \"The system should be fast\"")
        return

    full_text = " ".join(text)
    console.print(f"\n[bold]Checking:[/bold] \"{full_text}\"\n")

    analyzer = RiskAnalyzer()
    flags = analyzer.analyze_text(full_text)

    if not flags:
        console.print("[green]No red flags found.[/green]")
        return

    table = Table(title="Red Flags Found")
    table.add_column("Term", style="red")
    table.add_column("Category")
    table.add_column("Severity")
    table.add_column("Suggestion")

    for term, info in flags:
        table.add_row(
            term,
            info["category"],
            info["severity"].value.upper(),
            info["suggestion"],
        )

    console.print(table)


def _display_summary(ded, capacity_plan, red_flags, sprint_analyses, clusters, output_dir):
    """Display analysis summary."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Analysis Complete[/bold green]",
        border_style="green",
    ))

    # Document summary
    doc_table = Table(title="Documents Analyzed")
    doc_table.add_column("Document")
    doc_table.add_column("Details")

    doc_table.add_row(
        "DED",
        f"{ded.filename} ({len(ded.epics)} epics, {len(ded.all_stories)} stories)",
    )
    if capacity_plan:
        doc_table.add_row(
            "Capacity Plan",
            f"{capacity_plan.filename} ({len(capacity_plan.sprints)} sprints, {len(capacity_plan.all_tasks)} tasks)",
        )

    console.print(doc_table)
    console.print()

    # Red flags summary
    from pi_strategist.models import RedFlagSeverity

    critical = len([rf for rf in red_flags if rf.severity == RedFlagSeverity.CRITICAL])
    moderate = len([rf for rf in red_flags if rf.severity == RedFlagSeverity.MODERATE])
    low = len([rf for rf in red_flags if rf.severity == RedFlagSeverity.LOW])

    flags_table = Table(title="Red Flags Summary")
    flags_table.add_column("Severity")
    flags_table.add_column("Count", justify="right")

    flags_table.add_row("[red]Critical[/red]", str(critical))
    flags_table.add_row("[yellow]Moderate[/yellow]", str(moderate))
    flags_table.add_row("[blue]Low[/blue]", str(low))
    flags_table.add_row("[bold]Total[/bold]", f"[bold]{len(red_flags)}[/bold]")

    console.print(flags_table)
    console.print()

    # Capacity summary
    if sprint_analyses:
        from pi_strategist.models import SprintStatus

        passing = sum(1 for a in sprint_analyses if a.status == SprintStatus.PASS)
        failing = len(sprint_analyses) - passing

        cap_table = Table(title="Capacity Summary")
        cap_table.add_column("Metric")
        cap_table.add_column("Value", justify="right")

        cap_table.add_row("Passing Sprints", f"[green]{passing}[/green]")
        cap_table.add_row("Failing Sprints", f"[red]{failing}[/red]" if failing else "0")
        cap_table.add_row("Total Sprints", str(len(sprint_analyses)))

        console.print(cap_table)
        console.print()

    # Deployment summary
    if clusters:
        eligible = sum(len(c.tasks) for c in clusters)
        total = len(capacity_plan.all_tasks) if capacity_plan else 0
        percentage = (eligible / total * 100) if total > 0 else 0

        deploy_table = Table(title="CD Strategy Summary")
        deploy_table.add_column("Metric")
        deploy_table.add_column("Value", justify="right")

        deploy_table.add_row("Deployment Clusters", str(len(clusters)))
        deploy_table.add_row("Eligible Tasks", f"{eligible}/{total}")
        deploy_table.add_row(
            "CD Percentage",
            f"[green]{percentage:.1f}%[/green]" if percentage >= 30 else f"[yellow]{percentage:.1f}%[/yellow]",
        )

        console.print(deploy_table)
        console.print()

    # Output files
    console.print(f"[bold]Reports saved to:[/bold] {output_dir.absolute()}")


if __name__ == "__main__":
    main()
