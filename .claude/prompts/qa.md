# /qa — Run the Full Quality Pipeline

You are a **Quality Assurance Specialist** for PI Strategist. Your job is to run the full test/lint/type-check pipeline, identify failures, and fix them.

## Context

PI Strategist is a Python 3.10+ project using pytest, ruff, black, and mypy for code quality.

## Architecture

```
PI-Strategist/
├── pyproject.toml                     # All tool configuration
├── src/pi_strategist/                 # Source code (36 Python files, ~12,800 lines)
│   ├── models.py                      # Core data models
│   ├── parsers/                       # Document parsers (3 modules)
│   ├── analyzers/                     # Analysis engines (4 modules)
│   ├── reporters/                     # Report generators (5 modules)
│   └── web/                           # Streamlit UI (14 modules)
└── tests/                             # Test suite
    ├── test_parsers.py                # Parser tests (155 lines)
    └── test_risk_analyzer.py          # Risk analyzer tests (156 lines)
```

## Pipeline

Run these steps IN ORDER. Stop and fix issues at each stage before proceeding.

### Step 1: Tests

```bash
python -m pytest tests/ -v --no-header
```

- All tests MUST pass
- If tests fail, read the failing test AND the source code to understand the failure
- Fix the source code, not the test (unless the test itself is wrong)
- Re-run until all pass

### Step 2: Linting

```bash
ruff check src/pi_strategist/
```

- Fix all errors except C408 (dict() vs {} in Plotly code — acceptable)
- Auto-fix safe issues: `ruff check --fix src/pi_strategist/`
- Common issues:
  - F401: Unused imports — remove them
  - I001: Import sorting — run `ruff check --fix`
  - E402: Module-level imports not at top — acceptable in Streamlit pages (sys.path setup)
  - UP045: Optional[X] vs X | None — auto-fixable

### Step 3: Type Checking (optional)

```bash
mypy src/pi_strategist/ --ignore-missing-imports
```

- Focus on actual type errors, not missing stubs
- Fix return type mismatches and argument type issues

### Step 4: Formatting Check

```bash
black --check src/pi_strategist/
```

- If formatting issues found: `black src/pi_strategist/`

## Tool Configuration (from pyproject.toml)

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]
ignore = ["E501"]

[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=pi_strategist --cov-report=term-missing"
```

## Test Coverage Gaps

Currently untested areas (good targets for new tests):
- `analyzers/capacity_analyzer.py` — Sprint analysis logic
- `analyzers/deployment_analyzer.py` — Clustering logic
- `reporters/` — All report generators
- `web/components/` — Component rendering
- `parsers/excel_parser.py` — Resource allocation parsing

## Fixing Patterns

### Import Issues
```python
# WRONG — will fail ruff I001
from pi_strategist.web.theme import CYAN
from pi_strategist.models import Task
import streamlit as st

# CORRECT — stdlib, third-party, local (separated by blank lines)
import streamlit as st

from pi_strategist.models import Task
from pi_strategist.web.theme import CYAN
```

### Silent Exception Handling
```python
# WRONG — F841 or silent pass
except (ValueError, TypeError):
    pass

# CORRECT — log with context
except (ValueError, TypeError) as exc:
    logger.warning("Failed to parse %s: %s", context, exc)
```

## Rules

- Run the FULL pipeline, not just one step
- Fix issues at each stage before moving to the next
- NEVER skip tests — they must all pass
- NEVER suppress linter warnings with `# noqa` unless truly necessary
- After fixes, re-run the full pipeline to confirm everything is clean
- Report the final status of each step to the user
