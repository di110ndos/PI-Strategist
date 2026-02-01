"""PDF Executive Report Generator."""

import io
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False


@dataclass
class ReportConfig:
    """Configuration for PDF report generation."""
    title: str = "PI Planning Executive Report"
    subtitle: str = ""
    author: str = "PI Strategist"
    include_recommendations: bool = True
    include_resource_details: bool = True
    include_risk_summary: bool = True
    include_financial_summary: bool = True


class PDFReport(FPDF if HAS_FPDF else object):
    """Custom PDF class with header/footer."""

    def __init__(self, config: ReportConfig):
        if not HAS_FPDF:
            raise RuntimeError("fpdf2 package not installed. Run: pip install fpdf2")

        super().__init__()
        self.config = config
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        """Page header."""
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(60, 60, 60)
        self.cell(0, 10, self.config.title, ln=True, align="L")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="L")
        self.ln(5)
        # Line
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        """Page footer."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | {self.config.author}", align="C")


class ExecutiveReportGenerator:
    """Generate PDF executive reports for PI planning."""

    # Colors
    COLORS = {
        "primary": (52, 152, 219),      # Blue
        "success": (40, 167, 69),        # Green
        "warning": (243, 156, 18),       # Orange
        "danger": (231, 76, 60),         # Red
        "dark": (52, 73, 94),            # Dark gray
        "light": (236, 240, 241),        # Light gray
        "white": (255, 255, 255),
    }

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()

    def generate(
        self,
        pi_analysis,
        capacity_plan=None,
        red_flags: list = None,
        ai_summary: str = None,
    ) -> bytes:
        """Generate PDF executive report.

        Args:
            pi_analysis: PIAnalysis object
            capacity_plan: Optional CapacityPlan object
            red_flags: Optional list of red flags
            ai_summary: Optional AI-generated summary

        Returns:
            PDF content as bytes
        """
        if not HAS_FPDF:
            raise RuntimeError("fpdf2 package not installed. Run: pip install fpdf2")

        pdf = PDFReport(self.config)
        pdf.alias_nb_pages()
        pdf.add_page()

        # Title page content
        self._add_title_section(pdf, pi_analysis)

        # Executive Summary
        if ai_summary:
            self._add_executive_summary(pdf, ai_summary)
        else:
            self._add_auto_summary(pdf, pi_analysis, capacity_plan)

        # Key Metrics Dashboard
        self._add_metrics_dashboard(pdf, pi_analysis, capacity_plan)

        # Resource Summary
        if self.config.include_resource_details and pi_analysis:
            pdf.add_page()
            self._add_resource_summary(pdf, pi_analysis)

        # Risk Summary
        if self.config.include_risk_summary:
            self._add_risk_summary(pdf, pi_analysis, red_flags)

        # Financial Summary
        if self.config.include_financial_summary and pi_analysis:
            pdf.add_page()
            self._add_financial_summary(pdf, pi_analysis)

        # Recommendations
        if self.config.include_recommendations and pi_analysis:
            self._add_recommendations(pdf, pi_analysis, capacity_plan)

        # Output
        return bytes(pdf.output())

    def _add_title_section(self, pdf: PDFReport, pi_analysis) -> None:
        """Add title section."""
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(*self.COLORS["dark"])
        pdf.cell(0, 15, "PI Planning Report", ln=True, align="C")

        if self.config.subtitle:
            pdf.set_font("Helvetica", "", 14)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 10, self.config.subtitle, ln=True, align="C")

        pdf.ln(10)

        # Quick stats boxes
        if pi_analysis:
            self._add_stat_boxes(pdf, pi_analysis)

        pdf.ln(10)

    def _add_stat_boxes(self, pdf: PDFReport, pi_analysis) -> None:
        """Add quick stat boxes."""
        total_cost = sum(
            r.total_hours * r.rate
            for r in pi_analysis.resources.values()
            if r.rate > 0
        )
        utilization = (pi_analysis.total_allocated / pi_analysis.total_capacity * 100) if pi_analysis.total_capacity > 0 else 0

        stats = [
            ("Sprints", str(len(pi_analysis.sprints)), self.COLORS["primary"]),
            ("Resources", str(len(pi_analysis.resources)), self.COLORS["primary"]),
            ("Utilization", f"{utilization:.0f}%", self.COLORS["success"] if utilization <= 100 else self.COLORS["danger"]),
            ("Total Cost", f"${total_cost:,.0f}", self.COLORS["dark"]),
        ]

        box_width = 45
        start_x = 15
        y = pdf.get_y()

        for i, (label, value, color) in enumerate(stats):
            x = start_x + (i * (box_width + 3))

            # Box background
            pdf.set_fill_color(*color)
            pdf.rect(x, y, box_width, 20, "F")

            # Value
            pdf.set_xy(x, y + 3)
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(*self.COLORS["white"])
            pdf.cell(box_width, 8, value, align="C")

            # Label
            pdf.set_xy(x, y + 11)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(box_width, 6, label, align="C")

        pdf.set_y(y + 25)

    def _add_executive_summary(self, pdf: PDFReport, summary: str) -> None:
        """Add AI-generated executive summary."""
        self._add_section_header(pdf, "Executive Summary")

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*self.COLORS["dark"])
        pdf.multi_cell(0, 6, summary)
        pdf.ln(5)

    def _add_auto_summary(self, pdf: PDFReport, pi_analysis, capacity_plan) -> None:
        """Add auto-generated summary when AI is not available."""
        self._add_section_header(pdf, "Executive Summary")

        if not pi_analysis:
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 10, "No PI analysis data available.", ln=True)
            return

        utilization = (pi_analysis.total_allocated / pi_analysis.total_capacity * 100) if pi_analysis.total_capacity > 0 else 0
        total_cost = sum(r.total_hours * r.rate for r in pi_analysis.resources.values() if r.rate > 0)

        # Generate summary text
        summary_parts = []

        summary_parts.append(
            f"This PI includes {len(pi_analysis.sprints)} sprints with {len(pi_analysis.resources)} "
            f"resources across {len(pi_analysis.projects)} projects."
        )

        if utilization > 100:
            summary_parts.append(
                f"The current plan is OVER-ALLOCATED at {utilization:.1f}% utilization, "
                f"which poses a significant risk to delivery."
            )
        elif utilization > 90:
            summary_parts.append(
                f"Utilization is HIGH at {utilization:.1f}%, leaving limited buffer for unexpected work."
            )
        else:
            summary_parts.append(
                f"Utilization is HEALTHY at {utilization:.1f}%, providing adequate buffer."
            )

        summary_parts.append(f"Total planned cost is ${total_cost:,.0f}.")

        if pi_analysis.overallocated_resources:
            count = len(pi_analysis.overallocated_resources)
            summary_parts.append(
                f"WARNING: {count} resource allocation(s) exceed capacity and require attention."
            )

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*self.COLORS["dark"])
        pdf.multi_cell(0, 6, " ".join(summary_parts))
        pdf.ln(5)

    def _add_metrics_dashboard(self, pdf: PDFReport, pi_analysis, capacity_plan) -> None:
        """Add key metrics dashboard."""
        self._add_section_header(pdf, "Key Metrics")

        if not pi_analysis:
            return

        # Create metrics table
        metrics = [
            ["Metric", "Value", "Status"],
            ["Total Capacity", f"{pi_analysis.total_capacity:,.0f} hours", ""],
            ["Total Allocated", f"{pi_analysis.total_allocated:,.0f} hours", ""],
        ]

        utilization = (pi_analysis.total_allocated / pi_analysis.total_capacity * 100) if pi_analysis.total_capacity > 0 else 0
        status = "OK" if utilization <= 100 else "OVER"
        metrics.append(["Utilization", f"{utilization:.1f}%", status])

        metrics.append(["Resources", str(len(pi_analysis.resources)), ""])
        metrics.append(["Projects", str(len(pi_analysis.projects)), ""])

        if pi_analysis.overallocated_resources:
            metrics.append(["Over-Allocated", str(len(pi_analysis.overallocated_resources)), "WARNING"])

        self._add_table(pdf, metrics)
        pdf.ln(5)

    def _add_resource_summary(self, pdf: PDFReport, pi_analysis) -> None:
        """Add resource summary section."""
        self._add_section_header(pdf, "Resource Allocation Summary")

        if not pi_analysis.resources:
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 10, "No resource data available.", ln=True)
            return

        # Group by discipline
        disciplines = {}
        for name, resource in pi_analysis.resources.items():
            disc = resource.discipline or "Other"
            if disc not in disciplines:
                disciplines[disc] = {"count": 0, "hours": 0, "cost": 0}
            disciplines[disc]["count"] += 1
            disciplines[disc]["hours"] += resource.total_hours
            disciplines[disc]["cost"] += resource.total_hours * resource.rate if resource.rate > 0 else 0

        # Create table
        table_data = [["Discipline", "Resources", "Hours", "Cost"]]
        for disc, data in sorted(disciplines.items(), key=lambda x: -x[1]["hours"]):
            table_data.append([
                disc,
                str(data["count"]),
                f"{data['hours']:,.0f}",
                f"${data['cost']:,.0f}"
            ])

        self._add_table(pdf, table_data)

        # Top resources
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Top 10 Resources by Hours", ln=True)

        top_resources = sorted(
            pi_analysis.resources.items(),
            key=lambda x: -x[1].total_hours
        )[:10]

        top_table = [["Resource", "Discipline", "Hours", "Rate", "Cost"]]
        for name, resource in top_resources:
            cost = resource.total_hours * resource.rate if resource.rate > 0 else 0
            top_table.append([
                name[:30],
                (resource.discipline or "N/A")[:15],
                f"{resource.total_hours:,.0f}",
                f"${resource.rate:,.0f}" if resource.rate > 0 else "N/A",
                f"${cost:,.0f}"
            ])

        self._add_table(pdf, top_table)

    def _add_risk_summary(self, pdf: PDFReport, pi_analysis, red_flags) -> None:
        """Add risk summary section."""
        self._add_section_header(pdf, "Risk Summary")

        risks = []

        # Over-allocation risks
        if pi_analysis and pi_analysis.overallocated_resources:
            risks.append(("HIGH", f"{len(pi_analysis.overallocated_resources)} resources are over-allocated"))

        # Utilization risk
        if pi_analysis and pi_analysis.total_capacity > 0:
            utilization = (pi_analysis.total_allocated / pi_analysis.total_capacity * 100)
            if utilization > 100:
                risks.append(("HIGH", f"Overall utilization is {utilization:.1f}% (over capacity)"))
            elif utilization > 90:
                risks.append(("MEDIUM", f"High utilization at {utilization:.1f}% limits flexibility"))

        # Red flags
        if red_flags:
            critical = len([rf for rf in red_flags if rf.severity.value == "critical"])
            moderate = len([rf for rf in red_flags if rf.severity.value == "moderate"])
            if critical > 0:
                risks.append(("HIGH", f"{critical} critical red flags in acceptance criteria"))
            if moderate > 0:
                risks.append(("MEDIUM", f"{moderate} moderate red flags need clarification"))

        # Warnings
        if pi_analysis and pi_analysis.warnings:
            risks.append(("LOW", f"{len(pi_analysis.warnings)} data validation warnings"))

        if risks:
            table_data = [["Severity", "Risk"]]
            for severity, description in risks:
                table_data.append([severity, description])
            self._add_table(pdf, table_data)
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 10, "No significant risks identified.", ln=True)

        pdf.ln(5)

    def _add_financial_summary(self, pdf: PDFReport, pi_analysis) -> None:
        """Add financial summary section."""
        self._add_section_header(pdf, "Financial Summary")

        if not pi_analysis:
            return

        total_cost = sum(
            r.total_hours * r.rate
            for r in pi_analysis.resources.values()
            if r.rate > 0
        )

        total_hours = pi_analysis.total_allocated
        blended_rate = total_cost / total_hours if total_hours > 0 else 0

        # Financial metrics
        metrics = [
            ["Metric", "Value"],
            ["Total PI Cost", f"${total_cost:,.0f}"],
            ["Total Hours", f"{total_hours:,.0f}"],
            ["Blended Rate", f"${blended_rate:,.2f}/hour"],
        ]

        if len(pi_analysis.sprints) > 0:
            cost_per_sprint = total_cost / len(pi_analysis.sprints)
            metrics.append(["Avg Cost/Sprint", f"${cost_per_sprint:,.0f}"])

        self._add_table(pdf, metrics)

        # Cost by discipline
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Cost by Discipline", ln=True)

        discipline_costs = {}
        for name, resource in pi_analysis.resources.items():
            disc = resource.discipline or "Other"
            cost = resource.total_hours * resource.rate if resource.rate > 0 else 0
            discipline_costs[disc] = discipline_costs.get(disc, 0) + cost

        cost_table = [["Discipline", "Cost", "% of Total"]]
        for disc, cost in sorted(discipline_costs.items(), key=lambda x: -x[1]):
            pct = (cost / total_cost * 100) if total_cost > 0 else 0
            cost_table.append([disc, f"${cost:,.0f}", f"{pct:.1f}%"])

        self._add_table(pdf, cost_table)

    def _add_recommendations(self, pdf: PDFReport, pi_analysis, capacity_plan) -> None:
        """Add recommendations section."""
        self._add_section_header(pdf, "Recommendations")

        recommendations = []

        # Generate recommendations based on data
        if pi_analysis:
            utilization = (pi_analysis.total_allocated / pi_analysis.total_capacity * 100) if pi_analysis.total_capacity > 0 else 0

            if utilization > 100:
                recommendations.append(
                    "CRITICAL: Reduce scope or add resources to bring utilization below 100%."
                )

            if pi_analysis.overallocated_resources:
                recommendations.append(
                    f"Address {len(pi_analysis.overallocated_resources)} over-allocated resources by redistributing work."
                )

            if utilization > 90:
                recommendations.append(
                    "Consider adding 10-15% buffer for unexpected work and meetings."
                )

            if len(pi_analysis.warnings) > 5:
                recommendations.append(
                    "Review and resolve data validation warnings to improve planning accuracy."
                )

        if not recommendations:
            recommendations.append("PI planning appears healthy. Continue monitoring progress.")

        pdf.set_font("Helvetica", "", 11)
        for i, rec in enumerate(recommendations, 1):
            pdf.multi_cell(0, 6, f"{i}. {rec}")
            pdf.ln(2)

    def _add_section_header(self, pdf: PDFReport, title: str) -> None:
        """Add a section header."""
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*self.COLORS["primary"])
        pdf.cell(0, 10, title, ln=True)
        pdf.set_draw_color(*self.COLORS["primary"])
        pdf.line(10, pdf.get_y(), 60, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(*self.COLORS["dark"])

    def _add_table(self, pdf: PDFReport, data: list[list[str]]) -> None:
        """Add a simple table."""
        if not data:
            return

        pdf.set_font("Helvetica", "", 10)

        # Calculate column widths
        num_cols = len(data[0])
        col_width = 190 / num_cols

        # Header row
        pdf.set_fill_color(*self.COLORS["light"])
        pdf.set_font("Helvetica", "B", 10)
        for cell in data[0]:
            pdf.cell(col_width, 8, str(cell), border=1, fill=True, align="C")
        pdf.ln()

        # Data rows
        pdf.set_font("Helvetica", "", 10)
        for row in data[1:]:
            for cell in row:
                pdf.cell(col_width, 7, str(cell), border=1, align="C")
            pdf.ln()


def generate_executive_pdf(
    pi_analysis,
    capacity_plan=None,
    red_flags: list = None,
    ai_summary: str = None,
    config: Optional[ReportConfig] = None,
) -> bytes:
    """Convenience function to generate PDF report.

    Returns:
        PDF content as bytes
    """
    generator = ExecutiveReportGenerator(config)
    return generator.generate(pi_analysis, capacity_plan, red_flags, ai_summary)
