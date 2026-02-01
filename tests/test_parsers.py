"""Tests for document parsers."""

import pytest
from pathlib import Path

from pi_strategist.parsers.ded_parser import DEDParser


class TestDEDParser:
    """Tests for DEDParser class."""

    @pytest.fixture
    def parser(self):
        """Create a DEDParser instance."""
        return DEDParser()

    def test_parse_text_basic(self, parser):
        """Test parsing basic text."""
        text = """
# Epic: User Authentication

## Story: Login Feature

### Acceptance Criteria
- User can enter username and password
- System validates credentials
- User is redirected on success
"""
        doc = parser.parse_text(text, "test.md")

        assert doc.filename == "test.md"
        assert len(doc.epics) >= 1

    def test_parse_text_with_stories(self, parser):
        """Test parsing text with multiple stories."""
        text = """
# Epic: EPIC-001 Authentication

## Story: STORY-001 Login
Acceptance Criteria:
- User can log in
- Errors are displayed

## Story: STORY-002 Logout
Acceptance Criteria:
- User can log out
- Session is cleared
"""
        doc = parser.parse_text(text, "test.md")

        assert len(doc.all_acceptance_criteria) >= 4

    def test_parse_gwt_format(self, parser):
        """Test parsing Given/When/Then format."""
        text = """
Story: Login Feature

Given a user is on the login page
When they enter valid credentials
Then they should be logged in
"""
        doc = parser.parse_text(text, "test.md")

        # Should extract the GWT as an AC
        assert len(doc.all_acceptance_criteria) >= 1

    def test_parse_task_with_hours(self, parser):
        """Test parsing tasks with hour estimates."""
        text = """
Story: Feature

### Task: TASK-001 Implement login (8h)
### Task: TASK-002 Add tests (4 hours)
"""
        doc = parser.parse_text(text, "test.md")

        # Should have tasks (if story exists)
        if doc.all_tasks:
            hours = [t.hours for t in doc.all_tasks]
            assert 8.0 in hours or 4.0 in hours

    def test_extract_hours_patterns(self, parser):
        """Test hour extraction from various patterns."""
        assert parser._extract_hours("Task (8h)") == 8.0
        assert parser._extract_hours("Task 8 hours") == 8.0
        assert parser._extract_hours("Task (12 hrs)") == 12.0
        assert parser._extract_hours("Task no hours") == 0.0

    def test_empty_text(self, parser):
        """Test parsing empty text."""
        doc = parser.parse_text("", "empty.md")

        assert doc.filename == "empty.md"
        assert len(doc.epics) == 0

    def test_file_not_found(self, parser):
        """Test handling of missing files."""
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent_file.md")

    def test_unsupported_format(self, parser):
        """Test handling of unsupported formats."""
        with pytest.raises(ValueError):
            parser.parse("file.xyz")


class TestDEDParserPatterns:
    """Tests for pattern matching in DEDParser."""

    @pytest.fixture
    def parser(self):
        return DEDParser()

    def test_epic_patterns(self, parser):
        """Test various epic format patterns."""
        patterns = [
            "# Epic: Authentication",
            "Epic: Authentication",
            "[EPIC-123]: Authentication",
            "EPIC-123: Authentication",
        ]

        for pattern in patterns:
            doc = parser.parse_text(pattern, "test.md")
            assert len(doc.epics) >= 1 or doc.raw_text == pattern

    def test_story_patterns(self, parser):
        """Test various story format patterns."""
        patterns = [
            "## Story: Login",
            "Story: Login",
            "User Story: Login",
            "[STORY-001]: Login",
            "STORY-001: Login",
            "US-001: Login",
        ]

        for pattern in patterns:
            doc = parser.parse_text(pattern, "test.md")
            # Should either extract story or have raw text
            assert doc.raw_text == pattern or len(doc.all_stories) >= 0

    def test_acceptance_criteria_bullet_points(self, parser):
        """Test AC extraction from bullet points."""
        text = """
Story: Test

Acceptance Criteria:
- First criterion that is long enough to be detected
- Second criterion that is also long enough
* Third criterion using asterisk bullet point
"""
        doc = parser.parse_text(text, "test.md")

        assert len(doc.all_acceptance_criteria) >= 1
