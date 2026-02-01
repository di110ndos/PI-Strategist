"""AI-powered advisor using Claude for PI planning recommendations."""

import json
import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


@dataclass
class AIRecommendation:
    """A single AI-generated recommendation."""
    category: str  # "capacity", "risk", "cost", "resource", "general"
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    action_items: list[str] = field(default_factory=list)
    impact: str = ""  # Expected impact of following recommendation
    affected_resources: list[str] = field(default_factory=list)
    affected_sprints: list[str] = field(default_factory=list)


@dataclass
class AIAnalysisResult:
    """Complete AI analysis result."""
    executive_summary: str = ""
    recommendations: list[AIRecommendation] = field(default_factory=list)
    risk_assessment: str = ""
    optimization_opportunities: list[str] = field(default_factory=list)
    key_metrics_commentary: str = ""
    success: bool = True
    error_message: str = ""


class AIAdvisor:
    """AI-powered advisor for PI planning using Claude."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI advisor.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = None

    @property
    def is_available(self) -> bool:
        """Check if AI features are available."""
        return HAS_ANTHROPIC and bool(self.api_key)

    def _get_client(self):
        """Get or create Anthropic client."""
        if not self.is_available:
            raise RuntimeError("Anthropic API not available. Install anthropic package and set API key.")

        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def analyze_pi_planning(
        self,
        pi_analysis,
        capacity_plan=None,
        red_flags: list = None,
    ) -> AIAnalysisResult:
        """Analyze PI planning data and generate recommendations.

        Args:
            pi_analysis: PIAnalysis object with resource/sprint/project data
            capacity_plan: Optional CapacityPlan object
            red_flags: Optional list of red flags from DED analysis

        Returns:
            AIAnalysisResult with recommendations and insights
        """
        if not self.is_available:
            return AIAnalysisResult(
                success=False,
                error_message="AI features not available. Please configure your Anthropic API key in Settings."
            )

        try:
            # Build context for Claude
            context = self._build_analysis_context(pi_analysis, capacity_plan, red_flags)

            # Call Claude for analysis
            response = self._call_claude(context)

            # Parse response into structured result
            result = self._parse_response(response)

            return result

        except Exception as e:
            return AIAnalysisResult(
                success=False,
                error_message=f"AI analysis failed: {str(e)}"
            )

    def generate_executive_summary(
        self,
        pi_analysis,
        capacity_plan=None,
    ) -> str:
        """Generate an executive summary of the PI planning.

        Returns:
            Executive summary text
        """
        if not self.is_available:
            return "AI summary not available. Configure API key in Settings."

        try:
            context = self._build_summary_context(pi_analysis, capacity_plan)

            client = self._get_client()
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""You are a PI Planning advisor. Generate a concise executive summary (3-4 paragraphs) for leadership based on this data:

{context}

Focus on:
1. Overall health of the PI (capacity vs allocation)
2. Key risks and concerns
3. Resource utilization highlights
4. Top recommendations

Keep it professional and actionable. Use specific numbers from the data."""
                    }
                ]
            )

            return message.content[0].text

        except Exception as e:
            return f"Could not generate summary: {str(e)}"

    def suggest_rebalancing(
        self,
        pi_analysis,
        capacity_plan,
    ) -> list[dict]:
        """Suggest specific task/resource rebalancing actions.

        Returns:
            List of rebalancing suggestions with from/to/reason
        """
        if not self.is_available:
            return []

        try:
            # Find overloaded sprints and resources
            overloaded = []
            underloaded = []

            if capacity_plan:
                for sprint in capacity_plan.sprints:
                    utilization = (sprint.sprint_load / sprint.net_capacity * 100) if sprint.net_capacity > 0 else 0
                    if utilization > 100:
                        overloaded.append({
                            "sprint": sprint.name,
                            "overflow": sprint.sprint_load - sprint.net_capacity,
                            "utilization": utilization
                        })
                    elif utilization < 70:
                        underloaded.append({
                            "sprint": sprint.name,
                            "available": sprint.net_capacity - sprint.sprint_load,
                            "utilization": utilization
                        })

            if not overloaded:
                return [{"suggestion": "No rebalancing needed - all sprints are within capacity."}]

            context = f"""
Overloaded Sprints: {json.dumps(overloaded, indent=2)}
Underloaded Sprints: {json.dumps(underloaded, indent=2)}

Over-allocated Resources: {pi_analysis.overallocated_resources if pi_analysis else 'None'}
"""

            client = self._get_client()
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Based on this PI capacity data, suggest specific rebalancing actions:

{context}

Provide 3-5 specific, actionable suggestions in this JSON format:
[
  {{"action": "Move X hours from Sprint Y to Sprint Z", "reason": "...", "priority": "high/medium/low", "impact": "..."}}
]

Only return valid JSON array."""
                    }
                ]
            )

            # Parse JSON response
            response_text = message.content[0].text
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return [{"suggestion": response_text}]

        except Exception as e:
            return [{"error": str(e)}]

    def _build_analysis_context(self, pi_analysis, capacity_plan, red_flags) -> str:
        """Build context string for Claude analysis."""
        sections = []

        # PI Analysis data
        if pi_analysis:
            sections.append("=== PI ANALYSIS DATA ===")
            sections.append(f"Total Sprints: {len(pi_analysis.sprints)}")
            sections.append(f"Total Resources: {len(pi_analysis.resources)}")
            sections.append(f"Total Projects: {len(pi_analysis.projects)}")
            sections.append(f"Total Capacity: {pi_analysis.total_capacity:.1f} hours")
            sections.append(f"Total Allocated: {pi_analysis.total_allocated:.1f} hours")

            # Calculate utilization
            utilization = (pi_analysis.total_allocated / pi_analysis.total_capacity * 100) if pi_analysis.total_capacity > 0 else 0
            sections.append(f"Overall Utilization: {utilization:.1f}%")

            # Resource summary
            sections.append("\n--- Resources ---")
            total_cost = 0
            for name, resource in list(pi_analysis.resources.items())[:10]:  # Top 10
                cost = resource.total_hours * resource.rate if resource.rate > 0 else 0
                total_cost += cost
                sections.append(f"  {name}: {resource.total_hours:.0f}h @ ${resource.rate:.0f}/hr = ${cost:,.0f}")
            sections.append(f"  Total Cost: ${total_cost:,.0f}")

            # Over-allocated resources
            if pi_analysis.overallocated_resources:
                sections.append("\n--- Over-Allocated Resources ---")
                for resource, sprint, hours in pi_analysis.overallocated_resources[:5]:
                    sections.append(f"  {resource} in {sprint}: {hours:.1f}h over")

            # Warnings
            if pi_analysis.warnings:
                sections.append("\n--- Warnings ---")
                for warning in pi_analysis.warnings[:10]:
                    sections.append(f"  - {warning}")

        # Capacity Plan data
        if capacity_plan:
            sections.append("\n=== SPRINT CAPACITY ===")
            for sprint in capacity_plan.sprints:
                utilization = (sprint.sprint_load / sprint.net_capacity * 100) if sprint.net_capacity > 0 else 0
                status = "OVERLOADED" if utilization > 100 else "OK"
                sections.append(f"  {sprint.name}: {sprint.sprint_load:.0f}h / {sprint.net_capacity:.0f}h ({utilization:.0f}%) - {status}")

        # Red flags
        if red_flags:
            sections.append("\n=== RED FLAGS (DED Issues) ===")
            sections.append(f"Total Red Flags: {len(red_flags)}")
            critical = len([rf for rf in red_flags if rf.severity.value == "critical"])
            moderate = len([rf for rf in red_flags if rf.severity.value == "moderate"])
            sections.append(f"  Critical: {critical}, Moderate: {moderate}")

        return "\n".join(sections)

    def _build_summary_context(self, pi_analysis, capacity_plan) -> str:
        """Build context for executive summary."""
        return self._build_analysis_context(pi_analysis, capacity_plan, None)

    def _call_claude(self, context: str) -> str:
        """Call Claude API for full analysis."""
        client = self._get_client()

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are an expert PI Planning advisor with deep knowledge of SAFe, Agile, and resource management. Analyze this PI planning data and provide actionable recommendations.

{context}

Provide your analysis in the following JSON format:
{{
  "executive_summary": "2-3 paragraph summary for leadership",
  "risk_assessment": "Overall risk level and key concerns",
  "recommendations": [
    {{
      "category": "capacity|risk|cost|resource|general",
      "priority": "high|medium|low",
      "title": "Short title",
      "description": "Detailed description",
      "action_items": ["Action 1", "Action 2"],
      "impact": "Expected impact",
      "affected_resources": ["Resource names if applicable"],
      "affected_sprints": ["Sprint names if applicable"]
    }}
  ],
  "optimization_opportunities": ["Opportunity 1", "Opportunity 2"],
  "key_metrics_commentary": "Commentary on the key metrics"
}}

Focus on practical, actionable insights. Be specific with numbers and names from the data."""
                }
            ]
        )

        return message.content[0].text

    def _parse_response(self, response: str) -> AIAnalysisResult:
        """Parse Claude's response into structured result."""
        import re

        result = AIAnalysisResult()

        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                result.executive_summary = data.get("executive_summary", "")
                result.risk_assessment = data.get("risk_assessment", "")
                result.optimization_opportunities = data.get("optimization_opportunities", [])
                result.key_metrics_commentary = data.get("key_metrics_commentary", "")

                # Parse recommendations
                for rec_data in data.get("recommendations", []):
                    rec = AIRecommendation(
                        category=rec_data.get("category", "general"),
                        priority=rec_data.get("priority", "medium"),
                        title=rec_data.get("title", ""),
                        description=rec_data.get("description", ""),
                        action_items=rec_data.get("action_items", []),
                        impact=rec_data.get("impact", ""),
                        affected_resources=rec_data.get("affected_resources", []),
                        affected_sprints=rec_data.get("affected_sprints", []),
                    )
                    result.recommendations.append(rec)
            else:
                # If no JSON found, use raw text as summary
                result.executive_summary = response

        except json.JSONDecodeError:
            result.executive_summary = response

        return result
