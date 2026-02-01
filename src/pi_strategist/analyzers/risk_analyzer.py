"""Risk analyzer for identifying red flags in acceptance criteria."""

import re
from typing import Optional

from pi_strategist.models import (
    AcceptanceCriteria,
    DEDDocument,
    RedFlag,
    RedFlagSeverity,
)


class RiskAnalyzer:
    """Analyzer for identifying ambiguous or unmeasurable acceptance criteria."""

    # Red flag dictionary with categories, severity, and suggestions
    RED_FLAGS = {
        # Subjective terms - CRITICAL
        "fast": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "responds in <{X} seconds at 95th percentile",
            "negotiation": "To ensure we're aligned on performance expectations, can we define 'fast' as a specific response time? For example, '<2 seconds at 95th percentile'?",
        },
        "quick": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "completes in <{X} seconds",
            "negotiation": "What specific time threshold defines 'quick' for this feature?",
        },
        "user-friendly": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "requires <={X} clicks to complete primary action",
            "negotiation": "Can we define 'user-friendly' in measurable terms? For example, 'users can complete the action in 3 clicks or fewer'?",
        },
        "intuitive": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "{X}% of users complete task without help on first attempt",
            "negotiation": "How should we measure 'intuitive'? Perhaps through usability testing with a success rate threshold?",
        },
        "simple": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "requires no more than {X} steps",
            "negotiation": "What makes something 'simple' in this context? Can we specify the maximum number of steps?",
        },
        "easy": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "achievable in <{X} minutes by target user",
            "negotiation": "Can we quantify 'easy'? For instance, 'new users complete the task in under 5 minutes'?",
        },
        "robust": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "handles {X} error scenarios gracefully without data loss",
            "negotiation": "What specific error conditions should the system handle to be considered 'robust'?",
        },
        "efficient": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "uses <{X}MB memory and <{Y}% CPU",
            "negotiation": "What resource constraints define 'efficient' for this feature?",
        },
        "responsive": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "UI responds to input within {X}ms",
            "negotiation": "What response time threshold makes the UI 'responsive'? Industry standard is often 100ms.",
        },
        "clean": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.LOW,
            "suggestion": "follows {coding standard} with 0 linting errors",
            "negotiation": "What coding standards or style guides define 'clean' code for this project?",
        },
        "elegant": {
            "category": "Subjective Term",
            "severity": RedFlagSeverity.LOW,
            "suggestion": "implements using {X} or fewer components/functions",
            "negotiation": "Can we define measurable criteria for 'elegant' implementation?",
        },
        # Vague metrics - CRITICAL
        "high quality": {
            "category": "Vague Metric",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "passes all unit tests with >={X}% coverage",
            "negotiation": "What specific quality metrics should we target? Test coverage, code review approval, etc.?",
        },
        "performant": {
            "category": "Vague Metric",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "handles {X} requests/second with <{Y}ms latency",
            "negotiation": "What performance benchmarks define 'performant'? Let's specify throughput and latency targets.",
        },
        "scalable": {
            "category": "Vague Metric",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "supports {X} concurrent users with <{Y}% latency degradation",
            "negotiation": "To what scale should the system handle? Let's define user counts and acceptable degradation.",
        },
        "secure": {
            "category": "Vague Metric",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "passes OWASP Top 10 scan with 0 critical/high findings",
            "negotiation": "What security standards should we meet? OWASP Top 10, SOC2 compliance, specific penetration test criteria?",
        },
        "reliable": {
            "category": "Vague Metric",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "achieves {X}% uptime over {Y} period",
            "negotiation": "What uptime/availability target defines 'reliable'? 99.9%, 99.99%?",
        },
        "stable": {
            "category": "Vague Metric",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "runs for {X} hours without crashes or memory leaks",
            "negotiation": "What stability criteria should we test against? Runtime duration, error rates?",
        },
        "maintainable": {
            "category": "Vague Metric",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "code complexity score <{X}, documentation coverage >={Y}%",
            "negotiation": "How do we measure 'maintainable'? Cyclomatic complexity, documentation requirements?",
        },
        "accessible": {
            "category": "Vague Metric",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "meets WCAG {X} Level {Y} compliance",
            "negotiation": "What accessibility standard should we target? WCAG 2.1 Level AA is common.",
        },
        # Missing criteria - MODERATE to CRITICAL
        "works well": {
            "category": "Missing Criteria",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "passes acceptance test suite with {X}% pass rate",
            "negotiation": "What specific functionality defines 'works well'? Let's enumerate the test scenarios.",
        },
        "looks good": {
            "category": "Missing Criteria",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "matches approved design mockups with <{X}px deviation",
            "negotiation": "Are there design mockups or style guides that define 'looks good'?",
        },
        "feels right": {
            "category": "Missing Criteria",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "receives >={X}/5 rating in user testing",
            "negotiation": "Can we define 'feels right' through user testing with specific satisfaction metrics?",
        },
        "appropriate": {
            "category": "Missing Criteria",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "meets criteria defined in {specification document}",
            "negotiation": "What makes something 'appropriate' here? Can we reference specific requirements?",
        },
        "reasonable": {
            "category": "Missing Criteria",
            "severity": RedFlagSeverity.LOW,
            "suggestion": "within {X}% of baseline/benchmark",
            "negotiation": "What benchmark or baseline defines 'reasonable'?",
        },
        # Undefined scope - CRITICAL
        "comprehensive": {
            "category": "Undefined Scope",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "covers scenarios {A}, {B}, {C} as defined in test matrix",
            "negotiation": "Can we enumerate what 'comprehensive' includes? Let's create a test matrix.",
        },
        "complete": {
            "category": "Undefined Scope",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "implements all items in {requirements list}",
            "negotiation": "What checklist defines 'complete'? Let's document the full scope.",
        },
        "all edge cases": {
            "category": "Undefined Scope",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "handles edge cases {1}, {2}, {3} as documented",
            "negotiation": "Which edge cases should be handled? Let's document them explicitly.",
        },
        "all scenarios": {
            "category": "Undefined Scope",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "supports scenarios defined in {use case document}",
            "negotiation": "Can we enumerate 'all scenarios'? An exhaustive list prevents scope creep.",
        },
        "full support": {
            "category": "Undefined Scope",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "supports features {X}, {Y}, {Z}",
            "negotiation": "What features constitute 'full support'? Let's list them.",
        },
        "etc": {
            "category": "Undefined Scope",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "specifically: {enumerate remaining items}",
            "negotiation": "Can we replace 'etc' with an explicit list of items?",
        },
        "and more": {
            "category": "Undefined Scope",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "specifically: {enumerate additional items}",
            "negotiation": "What does 'and more' include? Let's document it explicitly.",
        },
        # Comparative terms - MODERATE
        "better": {
            "category": "Comparative Term",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "{X}% improvement over baseline of {Y}",
            "negotiation": "Better than what baseline? By what metric and how much?",
        },
        "improved": {
            "category": "Comparative Term",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "achieves {X}% improvement in {metric}",
            "negotiation": "What's the baseline for comparison and target improvement percentage?",
        },
        "enhanced": {
            "category": "Comparative Term",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "adds capabilities {A}, {B}, {C}",
            "negotiation": "What specific enhancements are included? Let's enumerate them.",
        },
        "optimized": {
            "category": "Comparative Term",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "reduces {metric} by {X}% from current {Y}",
            "negotiation": "Optimized for what metric? What's the current baseline and target?",
        },
        "faster": {
            "category": "Comparative Term",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "{X}% faster than current {Y}ms",
            "negotiation": "Faster by how much compared to what baseline?",
        },
        "newer": {
            "category": "Comparative Term",
            "severity": RedFlagSeverity.LOW,
            "suggestion": "uses version {X} or later",
            "negotiation": "What specific version or date defines 'newer'?",
        },
        # Time-based ambiguity - MODERATE
        "soon": {
            "category": "Time Ambiguity",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "within {X} seconds/minutes/days",
            "negotiation": "What specific timeframe defines 'soon'?",
        },
        "quickly": {
            "category": "Time Ambiguity",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "within {X} seconds",
            "negotiation": "How quickly? Let's specify seconds or milliseconds.",
        },
        "real-time": {
            "category": "Time Ambiguity",
            "severity": RedFlagSeverity.CRITICAL,
            "suggestion": "updates within {X}ms of data change",
            "negotiation": "'Real-time' means different things in different contexts. What latency is acceptable?",
        },
        "immediately": {
            "category": "Time Ambiguity",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "within {X}ms",
            "negotiation": "What response time qualifies as 'immediate'?",
        },
        # Quantity ambiguity - MODERATE
        "many": {
            "category": "Quantity Ambiguity",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "at least {X}",
            "negotiation": "Can we specify the minimum number instead of 'many'?",
        },
        "few": {
            "category": "Quantity Ambiguity",
            "severity": RedFlagSeverity.LOW,
            "suggestion": "no more than {X}",
            "negotiation": "What's the maximum that qualifies as 'few'?",
        },
        "several": {
            "category": "Quantity Ambiguity",
            "severity": RedFlagSeverity.LOW,
            "suggestion": "{X} to {Y}",
            "negotiation": "Can we specify the exact range instead of 'several'?",
        },
        "most": {
            "category": "Quantity Ambiguity",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": ">={X}%",
            "negotiation": "What percentage defines 'most'? 51%? 80%? 95%?",
        },
        "some": {
            "category": "Quantity Ambiguity",
            "severity": RedFlagSeverity.LOW,
            "suggestion": "at least {X}",
            "negotiation": "How many is 'some'? Let's specify a minimum.",
        },
        # Assumption indicators - MODERATE
        "should": {
            "category": "Uncertain Requirement",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "must {specific behavior}",
            "negotiation": "Is this a firm requirement? Can we change 'should' to 'must' with specific criteria?",
        },
        "might": {
            "category": "Uncertain Requirement",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "{will/will not} {specific behavior}",
            "negotiation": "Is this in scope? Let's clarify if this is a requirement or not.",
        },
        "could": {
            "category": "Uncertain Requirement",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "{must/must not} {specific behavior}",
            "negotiation": "Is this optional or required? Let's clarify the scope.",
        },
        "may": {
            "category": "Uncertain Requirement",
            "severity": RedFlagSeverity.MODERATE,
            "suggestion": "{must/must not} {specific behavior}",
            "negotiation": "Is this a requirement or a permission? Let's clarify.",
        },
    }

    def __init__(self):
        """Initialize the risk analyzer."""
        # Compile regex patterns for efficiency
        self._patterns = {}
        for term in self.RED_FLAGS:
            # Create pattern that matches whole words
            pattern = r"\b" + re.escape(term) + r"\b"
            self._patterns[term] = re.compile(pattern, re.IGNORECASE)

    def analyze(self, document: DEDDocument) -> list[RedFlag]:
        """Analyze a DED document for red flags.

        Args:
            document: Parsed DED document

        Returns:
            List of identified red flags
        """
        red_flags = []

        for ac in document.all_acceptance_criteria:
            flags = self.analyze_criteria(ac)
            red_flags.extend(flags)

        # Sort by severity (critical first)
        severity_order = {
            RedFlagSeverity.CRITICAL: 0,
            RedFlagSeverity.MODERATE: 1,
            RedFlagSeverity.LOW: 2,
        }
        red_flags.sort(key=lambda rf: severity_order[rf.severity])

        return red_flags

    def analyze_criteria(self, ac: AcceptanceCriteria) -> list[RedFlag]:
        """Analyze a single acceptance criterion for red flags.

        Args:
            ac: Acceptance criterion to analyze

        Returns:
            List of red flags found in the AC
        """
        red_flags = []
        text = ac.text

        for term, pattern in self._patterns.items():
            if pattern.search(text):
                flag_info = self.RED_FLAGS[term]
                red_flag = RedFlag(
                    ac=ac,
                    flagged_term=term,
                    category=flag_info["category"],
                    severity=flag_info["severity"],
                    suggested_metric=flag_info["suggestion"],
                    negotiation_script=flag_info["negotiation"],
                )
                red_flags.append(red_flag)

        return red_flags

    def analyze_text(self, text: str) -> list[tuple[str, dict]]:
        """Analyze arbitrary text for red flags.

        Args:
            text: Text to analyze

        Returns:
            List of (flagged_term, flag_info) tuples
        """
        found = []

        for term, pattern in self._patterns.items():
            if pattern.search(text):
                found.append((term, self.RED_FLAGS[term]))

        return found

    def get_suggestion(self, term: str, context: Optional[str] = None) -> str:
        """Get a suggestion for replacing a red flag term.

        Args:
            term: The flagged term
            context: Optional context for better suggestions

        Returns:
            Suggested replacement metric
        """
        term_lower = term.lower()
        if term_lower in self.RED_FLAGS:
            return self.RED_FLAGS[term_lower]["suggestion"]
        return f"specific measurable criteria for '{term}'"

    def get_negotiation_script(self, term: str) -> str:
        """Get a negotiation script for discussing a red flag.

        Args:
            term: The flagged term

        Returns:
            Suggested negotiation dialogue
        """
        term_lower = term.lower()
        if term_lower in self.RED_FLAGS:
            return self.RED_FLAGS[term_lower]["negotiation"]
        return f"Can we define specific, measurable criteria for '{term}'?"

    def summary(self, red_flags: list[RedFlag]) -> dict:
        """Generate a summary of red flags.

        Args:
            red_flags: List of red flags

        Returns:
            Summary dictionary
        """
        return {
            "total": len(red_flags),
            "critical": len([rf for rf in red_flags if rf.severity == RedFlagSeverity.CRITICAL]),
            "moderate": len([rf for rf in red_flags if rf.severity == RedFlagSeverity.MODERATE]),
            "low": len([rf for rf in red_flags if rf.severity == RedFlagSeverity.LOW]),
            "categories": self._count_categories(red_flags),
            "most_common_terms": self._most_common_terms(red_flags),
        }

    def _count_categories(self, red_flags: list[RedFlag]) -> dict[str, int]:
        """Count red flags by category."""
        counts: dict[str, int] = {}
        for rf in red_flags:
            counts[rf.category] = counts.get(rf.category, 0) + 1
        return counts

    def _most_common_terms(self, red_flags: list[RedFlag], top_n: int = 5) -> list[tuple[str, int]]:
        """Get most common flagged terms."""
        counts: dict[str, int] = {}
        for rf in red_flags:
            counts[rf.flagged_term] = counts.get(rf.flagged_term, 0) + 1

        sorted_terms = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_terms[:top_n]
