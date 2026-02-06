"""Quick check service - wraps RiskAnalyzer for text analysis."""

import sys
from pathlib import Path

# Add the src directory to the path so we can import pi_strategist
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from pi_strategist.analyzers.risk_analyzer import RiskAnalyzer

from app.models.responses import (
    QuickCheckResponse,
    RedFlagItem,
    LineRedFlags,
    ObligationItem,
    ObligationsResult,
    SLAFindingItem,
    SLAResult,
)


class QuickCheckService:
    """Service for quick text analysis."""

    def __init__(self):
        self.risk_analyzer = RiskAnalyzer()

    def analyze_text(self, text: str) -> QuickCheckResponse:
        """Run full analysis on text and return structured response."""
        # Use the existing full_analysis method
        results = self.risk_analyzer.full_analysis(text)

        # Transform red flags
        red_flags_by_line: dict[int, LineRedFlags] = {}

        for flag_tuple in results.get("red_flags", []):
            # flag_tuple is (line, term, category, severity, suggestion, negotiation)
            if len(flag_tuple) >= 6:
                line, term, category, severity, suggestion, negotiation = flag_tuple[:6]
                line_num = 1  # Default line number

                # Try to find line number
                lines = text.split("\n")
                for i, l in enumerate(lines, 1):
                    if line in l or l in line:
                        line_num = i
                        break

                if line_num not in red_flags_by_line:
                    red_flags_by_line[line_num] = LineRedFlags(
                        line=line[:200],  # Truncate long lines
                        line_number=line_num,
                        flags=[],
                    )

                red_flags_by_line[line_num].flags.append(
                    RedFlagItem(
                        term=term,
                        category=category,
                        severity=severity,
                        suggested_metric=suggestion,
                        negotiation_script=negotiation,
                    )
                )

        # Transform obligations
        obligations_data = results.get("obligations", {})
        obligations_list = []

        for ob in obligations_data.get("obligations", []):
            if hasattr(ob, "text"):
                obligations_list.append(
                    ObligationItem(
                        text=ob.text,
                        obligation_type=ob.obligation_type,
                        keyword=ob.keyword,
                    )
                )
            elif isinstance(ob, dict):
                obligations_list.append(
                    ObligationItem(
                        text=ob.get("text", ""),
                        obligation_type=ob.get("obligation_type", "unknown"),
                        keyword=ob.get("keyword", ""),
                    )
                )

        obligations = ObligationsResult(
            total=obligations_data.get("total", 0),
            binding_count=obligations_data.get("binding_count", 0),
            commitment_count=obligations_data.get("commitment_count", 0),
            negative_count=obligations_data.get("negative_count", 0),
            obligations=obligations_list,
        )

        # Transform SLA findings
        sla_data = results.get("sla", {})
        sla_findings = []

        for finding in sla_data.get("findings", []):
            if hasattr(finding, "text"):
                sla_findings.append(
                    SLAFindingItem(
                        text=finding.text,
                        metric_type=finding.metric_type,
                        value=finding.value,
                        is_valid=finding.is_valid,
                        issues=finding.issues if hasattr(finding, "issues") else [],
                    )
                )
            elif isinstance(finding, dict):
                sla_findings.append(
                    SLAFindingItem(
                        text=finding.get("text", ""),
                        metric_type=finding.get("metric_type", "unknown"),
                        value=finding.get("value"),
                        is_valid=finding.get("is_valid", False),
                        issues=finding.get("issues", []),
                    )
                )

        sla = SLAResult(
            total=sla_data.get("total", 0),
            valid_count=sla_data.get("valid_count", 0),
            invalid_count=sla_data.get("invalid_count", 0),
            findings=sla_findings,
        )

        # Build summary
        red_flag_list = list(red_flags_by_line.values())
        total_flags = sum(len(rf.flags) for rf in red_flag_list)
        critical_count = sum(
            1 for rf in red_flag_list for f in rf.flags if f.severity == "critical"
        )
        moderate_count = sum(
            1 for rf in red_flag_list for f in rf.flags if f.severity == "moderate"
        )
        low_count = sum(
            1 for rf in red_flag_list for f in rf.flags if f.severity == "low"
        )

        summary = {
            "red_flags": {
                "total": total_flags,
                "critical": critical_count,
                "moderate": moderate_count,
                "low": low_count,
            },
            "obligations": {
                "total": obligations.total,
                "binding": obligations.binding_count,
                "commitment": obligations.commitment_count,
            },
            "sla": {
                "total": sla.total,
                "valid": sla.valid_count,
                "invalid": sla.invalid_count,
            },
        }

        return QuickCheckResponse(
            red_flags=red_flag_list,
            obligations=obligations,
            sla=sla,
            summary=summary,
        )


# Global service instance
quick_check_service = QuickCheckService()
