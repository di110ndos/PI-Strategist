"""Tests for the risk analyzer."""

import pytest

from pi_strategist.analyzers.risk_analyzer import RiskAnalyzer
from pi_strategist.models import AcceptanceCriteria, RedFlagSeverity


class TestRiskAnalyzer:
    """Tests for RiskAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a RiskAnalyzer instance."""
        return RiskAnalyzer()

    def test_detects_fast(self, analyzer):
        """Test detection of 'fast' red flag."""
        flags = analyzer.analyze_text("The system should be fast")
        terms = [f[0] for f in flags]
        assert "fast" in terms

    def test_detects_user_friendly(self, analyzer):
        """Test detection of 'user-friendly' red flag."""
        flags = analyzer.analyze_text("The interface should be user-friendly")
        terms = [f[0] for f in flags]
        assert "user-friendly" in terms

    def test_detects_comprehensive(self, analyzer):
        """Test detection of 'comprehensive' red flag."""
        flags = analyzer.analyze_text("Provide comprehensive validation")
        terms = [f[0] for f in flags]
        assert "comprehensive" in terms

    def test_detects_scalable(self, analyzer):
        """Test detection of 'scalable' red flag."""
        flags = analyzer.analyze_text("The architecture must be scalable")
        terms = [f[0] for f in flags]
        assert "scalable" in terms

    def test_detects_secure(self, analyzer):
        """Test detection of 'secure' red flag."""
        flags = analyzer.analyze_text("The system must be secure")
        terms = [f[0] for f in flags]
        assert "secure" in terms

    def test_detects_multiple_flags(self, analyzer):
        """Test detection of multiple red flags."""
        flags = analyzer.analyze_text(
            "The system should be fast, scalable, and user-friendly"
        )
        terms = [f[0] for f in flags]
        assert "fast" in terms
        assert "scalable" in terms
        assert "user-friendly" in terms

    def test_no_flags_for_measurable_criteria(self, analyzer):
        """Test that measurable criteria don't trigger flags."""
        flags = analyzer.analyze_text(
            "The page loads in under 2 seconds at 95th percentile"
        )
        # Should not flag "fast" since it's not present
        terms = [f[0] for f in flags]
        assert "fast" not in terms

    def test_case_insensitive(self, analyzer):
        """Test case-insensitive matching."""
        flags = analyzer.analyze_text("The system should be FAST")
        terms = [f[0] for f in flags]
        assert "fast" in terms

    def test_severity_levels(self, analyzer):
        """Test severity level assignment."""
        # Critical
        flags = analyzer.analyze_text("fast")
        assert flags[0][1]["severity"] == RedFlagSeverity.CRITICAL

        # Moderate
        flags = analyzer.analyze_text("should")
        assert flags[0][1]["severity"] == RedFlagSeverity.MODERATE

        # Low
        flags = analyzer.analyze_text("clean")
        assert flags[0][1]["severity"] == RedFlagSeverity.LOW

    def test_get_suggestion(self, analyzer):
        """Test getting suggestions for terms."""
        suggestion = analyzer.get_suggestion("fast")
        assert "seconds" in suggestion.lower()

    def test_get_negotiation_script(self, analyzer):
        """Test getting negotiation scripts."""
        script = analyzer.get_negotiation_script("fast")
        assert len(script) > 0
        assert "?" in script  # Should be a question

    def test_analyze_criteria(self, analyzer):
        """Test analyzing AcceptanceCriteria objects."""
        ac = AcceptanceCriteria(
            id="AC-001",
            text="The system should be fast and user-friendly",
            story_id="STORY-001",
        )
        flags = analyzer.analyze_criteria(ac)
        assert len(flags) >= 2  # At least 'fast' and 'user-friendly'

    def test_summary(self, analyzer):
        """Test summary generation."""
        ac = AcceptanceCriteria(
            id="AC-001",
            text="The system should be fast, scalable, and secure",
        )
        flags = analyzer.analyze_criteria(ac)
        summary = analyzer.summary(flags)

        assert "total" in summary
        assert "critical" in summary
        assert "moderate" in summary
        assert "low" in summary
        assert summary["total"] >= 3


class TestRedFlagCategories:
    """Tests for red flag category coverage."""

    @pytest.fixture
    def analyzer(self):
        return RiskAnalyzer()

    def test_subjective_terms(self, analyzer):
        """Test subjective term detection."""
        subjective = ["fast", "quick", "user-friendly", "intuitive", "simple", "robust"]
        for term in subjective:
            flags = analyzer.analyze_text(f"The system is {term}")
            assert len(flags) > 0, f"Should detect '{term}'"

    def test_vague_metrics(self, analyzer):
        """Test vague metric detection."""
        vague = ["high quality", "performant", "scalable", "secure", "reliable"]
        for term in vague:
            flags = analyzer.analyze_text(f"The system is {term}")
            assert len(flags) > 0, f"Should detect '{term}'"

    def test_undefined_scope(self, analyzer):
        """Test undefined scope detection."""
        undefined = ["comprehensive", "complete", "all edge cases", "etc"]
        for term in undefined:
            flags = analyzer.analyze_text(f"Handle {term}")
            assert len(flags) > 0, f"Should detect '{term}'"

    def test_comparative_terms(self, analyzer):
        """Test comparative term detection."""
        comparative = ["better", "improved", "enhanced", "optimized", "faster"]
        for term in comparative:
            flags = analyzer.analyze_text(f"Make it {term}")
            assert len(flags) > 0, f"Should detect '{term}'"
