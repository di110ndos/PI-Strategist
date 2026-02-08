"""Tests for the AI advisor (unit tests without API calls)."""

import pytest
from unittest.mock import patch, MagicMock

from pi_strategist.analyzers.ai_advisor import AIAdvisor, AIAnalysisResult, AIRecommendation


class TestAIAdvisorInit:
    """Tests for AIAdvisor initialization."""

    def test_init_without_key(self):
        """Advisor initializes without API key."""
        advisor = AIAdvisor(api_key=None)
        assert not advisor.is_available

    def test_init_with_key(self):
        """Advisor initializes with API key."""
        advisor = AIAdvisor(api_key="test-key-123")
        # is_available depends on whether anthropic package is installed
        assert isinstance(advisor.is_available, bool)

    def test_init_with_empty_key(self):
        """Advisor with empty key is not available."""
        advisor = AIAdvisor(api_key="")
        assert not advisor.is_available


class TestAIAnalysisResult:
    """Tests for AIAnalysisResult dataclass."""

    def test_default_values(self):
        """Default result has empty fields and success=True."""
        result = AIAnalysisResult(
            executive_summary="",
            recommendations=[],
            risk_assessment="",
            optimization_opportunities=[],
            key_metrics_commentary="",
            success=True,
            error_message="",
        )
        assert result.success is True
        assert result.error_message == ""

    def test_error_result(self):
        """Error result captures message."""
        result = AIAnalysisResult(
            executive_summary="",
            recommendations=[],
            risk_assessment="",
            optimization_opportunities=[],
            key_metrics_commentary="",
            success=False,
            error_message="API call failed",
        )
        assert not result.success
        assert "API call failed" in result.error_message


class TestAIRecommendation:
    """Tests for AIRecommendation dataclass."""

    def test_create_recommendation(self):
        """Can create a recommendation with all fields."""
        rec = AIRecommendation(
            category="capacity",
            priority="high",
            title="Reduce Sprint 2 load",
            description="Sprint 2 is 120% utilized",
            action_items=["Move T3 to Sprint 3", "Reduce scope"],
            impact="Prevents burnout",
            affected_resources=["Dev Team A"],
            affected_sprints=["Sprint 2"],
        )
        assert rec.category == "capacity"
        assert rec.priority == "high"
        assert len(rec.action_items) == 2


class TestResponseParsing:
    """Tests for _parse_response method."""

    @pytest.fixture
    def advisor(self):
        return AIAdvisor(api_key="test-key")

    def test_parse_valid_json(self, advisor):
        """Parser handles valid JSON response."""
        json_str = '''{
            "executive_summary": "Good plan overall",
            "recommendations": [
                {
                    "category": "risk",
                    "priority": "high",
                    "title": "Address vague ACs",
                    "description": "Several acceptance criteria are vague",
                    "action_items": ["Add metrics to AC-001"],
                    "impact": "Medium",
                    "affected_resources": [],
                    "affected_sprints": ["Sprint 1"]
                }
            ],
            "risk_assessment": "Moderate risk",
            "optimization_opportunities": ["Shift tasks from S2 to S3"],
            "key_metrics_commentary": "Utilization is high"
        }'''
        result = advisor._parse_response(json_str)
        assert result.success
        assert "Good plan" in result.executive_summary
        assert len(result.recommendations) == 1

    def test_parse_json_in_code_block(self, advisor):
        """Parser extracts JSON from markdown code block."""
        response = '''Here is the analysis:

```json
{
    "executive_summary": "Plan looks solid",
    "recommendations": [],
    "risk_assessment": "Low risk",
    "optimization_opportunities": [],
    "key_metrics_commentary": "All sprints under capacity"
}
```'''
        result = advisor._parse_response(response)
        assert result.success
        assert "solid" in result.executive_summary

    def test_parse_invalid_json(self, advisor):
        """Parser handles invalid JSON gracefully."""
        result = advisor._parse_response("This is not JSON at all")
        # Should still return a result (possibly with error or with the text as summary)
        assert isinstance(result, AIAnalysisResult)

    def test_parse_partial_json(self, advisor):
        """Parser handles JSON missing some fields."""
        json_str = '{"executive_summary": "Brief summary"}'
        result = advisor._parse_response(json_str)
        assert isinstance(result, AIAnalysisResult)


class TestContextBuilding:
    """Tests for context building methods."""

    @pytest.fixture
    def advisor(self):
        return AIAdvisor(api_key="test-key")

    def test_build_analysis_context(self, advisor):
        """Context builder produces string from mock data."""
        mock_analysis = MagicMock()
        mock_analysis.sprints = {}
        mock_analysis.resources = {}
        mock_analysis.projects = {}
        mock_analysis.total_capacity = 800
        mock_analysis.total_allocated = 600
        mock_analysis.total_remaining = 200
        mock_analysis.overallocated_resources = []
        mock_analysis.warnings = []

        context = advisor._build_analysis_context(mock_analysis, None, None)
        assert isinstance(context, str)
        assert len(context) > 0

    def test_build_summary_context(self, advisor):
        """Summary context builder produces string."""
        mock_analysis = MagicMock()
        mock_analysis.sprints = {}
        mock_analysis.resources = {}
        mock_analysis.total_capacity = 800
        mock_analysis.total_allocated = 600

        context = advisor._build_summary_context(mock_analysis, None)
        assert isinstance(context, str)
        assert len(context) > 0
