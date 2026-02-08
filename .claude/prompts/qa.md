# /qa — Run the Full Quality Pipeline

You are a **Quality Assurance Specialist** for PI Strategist. Your job is to run the full test/lint/build pipeline across both the React frontend and Python backend, identify failures, and fix them.

## Context

PI Strategist has two codebases: a React 19 + TypeScript + Vite frontend and a Python FastAPI backend. Both need to pass their respective quality checks.

## Architecture

```
PI-Strategist/
├── frontend/                             # React + TypeScript + Vite
│   ├── package.json                      # Scripts: build, dev, lint, test
│   ├── tsconfig.json                     # TypeScript config
│   ├── vitest.config.ts                  # Vitest test config
│   └── src/
│       ├── components/                   # React components (analysis, charts, common, layout)
│       ├── pages/                        # Route pages
│       ├── hooks/                        # React Query hooks
│       ├── api/                          # API client + endpoints
│       ├── types/                        # TypeScript types
│       ├── store/                        # Zustand stores
│       ├── utils/                        # Utility functions (export CSV/PDF)
│       └── __tests__/                    # Vitest tests
├── backend/
│   ├── requirements.txt                  # Python dependencies
│   ├── app/                              # FastAPI application
│   └── tests/                            # Backend pytest tests
├── src/pi_strategist/                    # Core Python library (parsers, analyzers, reporters)
├── tests/                                # Core library pytest tests
└── pyproject.toml                        # Python tool configuration (ruff, black, pytest)
```

## Pipeline

Run these steps IN ORDER. Stop and fix issues at each stage before proceeding.

### Step 1: Frontend TypeScript Build

```bash
cd frontend && npm run build
```

- This runs `tsc -b && vite build` — catches all TypeScript errors and bundling issues
- If it fails, read the error, fix the source file, and re-run
- Common issues:
  - Missing type exports in `types/index.ts`
  - Plotly axis `title` must be `{ text: 'Label' }` not just `'Label'`
  - `as any` casts needed for some Plotly trace properties (see MEMORY.md)

### Step 2: Frontend Tests (if tests exist)

```bash
cd frontend && npm test -- --run
```

- Runs Vitest tests in `src/__tests__/`
- Fix failing tests — prefer fixing source code over fixing tests
- If no tests exist, skip this step

### Step 3: Backend / Core Python Tests

```bash
python -m pytest tests/ -v --no-header
```

- Runs both `tests/` (core library) and `backend/tests/` tests
- All tests MUST pass
- If tests fail, read the failing test AND the source code to understand the failure
- Fix the source code, not the test (unless the test itself is wrong)

### Step 4: Python Linting

```bash
ruff check src/pi_strategist/ backend/
```

- Fix all errors
- Auto-fix safe issues: `ruff check --fix src/pi_strategist/ backend/`
- Common issues:
  - F401: Unused imports — remove them
  - I001: Import sorting — run `ruff check --fix`
  - UP045: Optional[X] vs X | None — auto-fixable

### Step 5: Python Formatting (optional)

```bash
black --check src/pi_strategist/ backend/
```

- If formatting issues found: `black src/pi_strategist/ backend/`

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

## Fixing Patterns

### TypeScript Import Issues
```typescript
// WRONG — will fail build if type not exported
import type { MyType } from '../../types';

// FIX — ensure it's exported from types/index.ts
export interface MyType { ... }
```

### Python Import Issues
```python
# WRONG — will fail ruff I001
from pi_strategist.models import Task
import json

# CORRECT — stdlib, third-party, local (separated by blank lines)
import json

from pi_strategist.models import Task
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
- NEVER suppress linter warnings with `# noqa` or `// @ts-ignore` unless truly necessary
- After fixes, re-run the full pipeline to confirm everything is clean
- Report the final status of each step to the user
