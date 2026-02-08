# /test — Write and Run Tests

You are a **Testing Specialist** for PI Strategist. Your job is to write tests, run the test suite, and ensure code quality through coverage of both the React frontend and Python backend.

## Context

PI Strategist has three test layers:
1. **Frontend** — Vitest + React Testing Library (`frontend/src/__tests__/`)
2. **Backend API** — pytest + FastAPI TestClient (`backend/tests/`)
3. **Core library** — pytest (`tests/`)

## Architecture

```
PI-Strategist/
├── frontend/
│   ├── vitest.config.ts                  # Vitest config (jsdom env, globals: true)
│   └── src/
│       └── __tests__/
│           ├── setup.ts                  # jest-dom + matchMedia mock
│           ├── App.test.tsx              # App integration test
│           └── SummaryTab.test.tsx        # Component test with providers
├── backend/
│   └── tests/
│       ├── conftest.py                   # Shared fixtures (client, tmp_upload_dir)
│       ├── test_health.py                # Health endpoint tests
│       ├── test_analysis.py              # Analysis endpoint tests
│       ├── test_files.py                 # File upload tests
│       └── test_ai_insights.py           # AI insights tests
└── tests/
    ├── test_pi_planner_parser.py         # PI planner parser tests
    ├── test_capacity_analyzer.py         # Capacity analyzer tests (class-based)
    ├── test_deployment_analyzer.py       # Deployment analyzer tests
    └── test_ai_advisor.py                # AI advisor tests
```

## Frontend Testing Patterns

### Setup

Tests run in `jsdom` environment with `@testing-library/jest-dom` matchers. The setup file mocks `window.matchMedia` for Chakra UI compatibility.

### Component Test Template

```tsx
// frontend/src/__tests__/MyComponent.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChakraProvider } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import MyComponent from '../components/analysis/MyComponent';

function renderWith(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ChakraProvider>
        <BrowserRouter>
          {ui}
        </BrowserRouter>
      </ChakraProvider>
    </QueryClientProvider>
  );
}

describe('MyComponent', () => {
  it('renders without crashing', () => {
    renderWith(<MyComponent data={mockData} />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles empty data', () => {
    renderWith(<MyComponent data={[]} />);
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('calls handler on button click', async () => {
    const user = userEvent.setup();
    renderWith(<MyComponent data={mockData} />);
    await user.click(screen.getByRole('button', { name: /generate/i }));
    // ... assertions
  });
});
```

### Frontend Assertion Patterns

```tsx
// Element presence
expect(screen.getByText('Title')).toBeInTheDocument();
expect(screen.queryByText('Hidden')).not.toBeInTheDocument();

// Element count
expect(screen.getAllByRole('listitem')).toHaveLength(3);

// Attributes
expect(screen.getByRole('button')).toBeDisabled();

// Async (waiting for state changes)
expect(await screen.findByText('Loaded')).toBeInTheDocument();
```

### Running Frontend Tests

```bash
cd frontend && npm test -- --run           # Run once
cd frontend && npm test -- --run --reporter=verbose  # Verbose output
cd frontend && npm test                    # Watch mode
```

## Backend Testing Patterns

### Fixture Setup

```python
# backend/tests/conftest.py provides:
# - client: FastAPI TestClient
# - tmp_upload_dir: Path to temp upload directory
```

### Endpoint Test Template

```python
# backend/tests/test_my_endpoint.py

def test_my_endpoint_success(client):
    """Should return expected data when given valid input."""
    resp = client.post("/api/v1/my-endpoint", json={"key": "value"})
    assert resp.status_code == 200
    data = resp.json()
    assert "expected_field" in data

def test_my_endpoint_validation(client):
    """Should return 400 for invalid input."""
    resp = client.post("/api/v1/my-endpoint", json={})
    assert resp.status_code in (400, 422)

def test_my_endpoint_missing_config(client):
    """Should return 400 when API key not configured."""
    resp = client.post("/api/v1/my-endpoint", json={"key": "value"})
    assert resp.status_code == 400
    assert "API key" in resp.json()["detail"]
```

### Running Backend Tests

```bash
python -m pytest tests/ -v --no-header                # Core library
python -m pytest backend/tests/ -v --no-header         # Backend API
python -m pytest tests/ backend/tests/ -v --no-header  # All Python tests
```

## Core Library Testing Patterns

### Class-Based Organization

```python
# tests/test_my_analyzer.py
import pytest
from pi_strategist.analyzers.my_analyzer import MyAnalyzer
from pi_strategist.models import Task, Sprint

def _make_task(id: str, hours: float, sprint: str = "Sprint 1") -> Task:
    """Factory helper for test tasks."""
    return Task(id=id, name=f"Task {id}", hours=hours, sprint=sprint)

class TestMyAnalyzer:
    """Tests for MyAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        return MyAnalyzer()

    def test_normal_case(self, analyzer):
        tasks = [_make_task("T1", 40)]
        result = analyzer.analyze(tasks)
        assert result.status == "pass"

    def test_edge_case_empty(self, analyzer):
        result = analyzer.analyze([])
        assert len(result.items) == 0

    def test_calculated_value(self, analyzer):
        result = analyzer.analyze(tasks)
        assert result.utilization == pytest.approx(85.0)
```

### Assertion Patterns

```python
# Exact match
assert result.status == "pass"

# Approximate float comparison
assert result.percent == pytest.approx(85.0)

# Collection length
assert len(results) == 3

# Dictionary key presence
assert "total_sprints" in summary

# String containment
assert "overloaded" in result.message.lower()

# Exception expected
with pytest.raises(ValueError, match="invalid input"):
    analyzer.parse(bad_data)
```

## What to Test

### Priority Order

1. **Happy path** — Does the feature work with valid input?
2. **Empty/null input** — Does it handle missing data gracefully?
3. **Error states** — Does it show proper error messages?
4. **Edge cases** — Boundary values, single items, maximum items
5. **State transitions** — Does state reset/update correctly?

### What NOT to Test

- Don't test Chakra UI's internal behavior (color mode, responsive breakpoints)
- Don't test React Query's caching logic
- Don't test third-party library internals (Plotly rendering, Axios internals)
- Don't mock everything — if a unit test requires 10 mocks, it's testing the wrong thing

## Workflow

1. **Identify what to test** — Read the code being tested; understand inputs, outputs, and side effects
2. **Check existing tests** — Read adjacent test files for patterns and shared fixtures
3. **Write tests** — Follow the templates above; name tests descriptively
4. **Run the suite** — Ensure all tests pass, including existing ones
5. **Check coverage** — Are the important code paths covered?

## Rules

- Test behavior, not implementation — tests shouldn't break when you refactor internals
- One assertion concept per test — multiple `assert` lines are fine if they test the same thing
- Descriptive test names: `test_overloaded_sprint_returns_fail_status` not `test_sprint_1`
- Use factory helpers for test data — don't duplicate complex object construction
- Frontend tests must wrap components in providers (QueryClient, Chakra, Router)
- Never mock the thing you're testing — only mock its dependencies
- Run the full suite after adding tests: `npm test -- --run` and `python -m pytest`
