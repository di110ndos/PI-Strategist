# PI Strategist

A full-stack application for Program Increment (PI) planning analysis, powered by AI. Upload capacity planners and DED documents, get instant analysis of risks, capacity, and deployment readiness, then ask Claude for strategic recommendations.

## Architecture

```
┌─────────────────────────────┐       ┌──────────────────────────────────┐
│  React Frontend (Vite)      │       │  FastAPI Backend                 │
│                             │ HTTP  │                                  │
│  Chakra UI + React Query    │◄─────►│  Parsers ─► Analyzers ─► API    │
│  Plotly Charts              │       │                    │             │
│  Zustand State              │       │              Claude API          │
└─────────────────────────────┘       │              (Opus 4.6)          │
                                      └──────────────────────────────────┘
```

**Frontend:** React 19, TypeScript, Vite, Chakra UI v2, React Router v7, React Query v5, Zustand, react-plotly.js

**Backend:** Python 3.10+, FastAPI, Pydantic, aiosqlite, Anthropic SDK

**AI Model:** Claude Opus 4.6 via Anthropic API

## How AI Is Used

PI Strategist uses Claude as an AI advisor that reads your PI planning data and provides strategic analysis. All AI features are optional — the core analysis (capacity validation, red flag detection, deployment mapping) runs locally without any API calls.

### What Gets Sent to Claude

When you use AI features, the backend builds a structured context from your parsed data and sends it to Claude. This includes:

- Resource names, hours allocated, hourly rates
- Project names, sprint allocations, priorities
- Sprint capacity vs. load numbers
- Red flags detected in DED documents (term, category, severity)

Raw uploaded files are **never** sent — only the structured analysis results after parsing.

### AI Features

#### 1. Full Analysis (Generate Insights)

The primary AI feature. Sends all analysis data to Claude with a prompt asking it to act as an expert PI Planning advisor with SAFe/Agile knowledge. Claude returns structured JSON containing:

- **Executive Summary** — 2-3 paragraph leadership-ready overview with specific numbers
- **Recommendations** — Categorized (capacity/risk/cost/resource) with priority levels, action items, impact assessments, and affected resources/sprints
- **Risk Assessment** — Overall risk level and key concerns
- **Optimization Opportunities** — Specific areas for improvement
- **Key Metrics Commentary** — Analysis of the numbers

The response is parsed through three strategies (direct JSON parse, markdown code block extraction, greedy regex match) for robustness.

#### 2. Sprint Rebalancing

Identifies overloaded sprints (>100% utilization) and underloaded sprints (<70%), then asks Claude to suggest 3-5 specific rebalancing actions like "Move X hours from Sprint Y to Sprint Z" with reasons and priority levels.

#### 3. Follow-up Chat

After generating insights, users can ask follow-up questions in a chat interface. The backend builds a conversation by:

1. Injecting the full analysis context as a system preamble
2. Including truncated previous AI insights (max 3000 chars)
3. Appending the last 5 conversation exchanges for continuity
4. Adding the new question

Claude's responses are tailored for a PM/account manager audience — focusing on delivery risk, budget implications, and stakeholder-ready talking points.

### Prompt Engineering

Each AI feature uses a purpose-built prompt:

| Feature | Persona | Output Format | Max Tokens |
|---------|---------|---------------|------------|
| Full Analysis | "Expert PI Planning advisor with deep knowledge of SAFe, Agile, and resource management" | Structured JSON with specific schema | 2000 |
| Executive Summary | "PI Planning advisor" generating for leadership | Free-form text, 3-4 paragraphs | 1000 |
| Rebalancing | Capacity-focused advisor | JSON array of actions | 1000 |
| Chat | "Expert PI Planning advisor assisting PMs and account managers" | Conversational text | 1500 |

### Reliability

- **Retry logic** — API calls use exponential backoff (2-30s delays, 3 attempts) via tenacity for timeout and connection errors
- **Timeout** — Full analysis has a 120-second timeout
- **Graceful degradation** — If no API key is configured, the app works normally with AI buttons disabled
- **Error sanitization** — API keys are stripped from all error messages before returning to the client

### API Key Configuration

Set your Anthropic API key in `backend/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

The backend loads this via Pydantic Settings on startup. The `/health` endpoint reports whether AI is configured (`ai_configured: true/false`).

## Features

### Core Analysis (No AI Required)

- **Red Flag Detection** — Identifies ambiguous, subjective, or unmeasurable acceptance criteria in DED documents
- **Capacity Validation** — Validates sprint loading against team capacity with pass/fail per sprint
- **Deployment Strategy** — Generates CD deployment clusters and strategy recommendations
- **Resource Heatmap** — Visual heat map of resource allocation across sprints
- **Cost Analysis** — Cost breakdowns by discipline and sprint

### AI-Powered (Requires API Key)

- **Strategic Insights** — Full analysis with categorized recommendations
- **Sprint Rebalancing** — Specific actions to fix overloaded sprints
- **Follow-up Chat** — Ask questions about your analysis data
- **Recommendation Filters** — Filter AI recommendations by priority and category

### Input Formats

- Excel capacity planners (.xlsx)
- Word DED documents (.docx)
- PDF documents (.pdf)
- Markdown (.md)

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- An Anthropic API key (optional, for AI features)

### Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install the core package in editable mode
pip install -e ..

# Configure environment
cp .env.example .env  # then edit .env with your API key

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend runs at `http://localhost:5173` and the API at `http://localhost:8000`.

### CLI (Legacy)

The original CLI is still available:

```bash
pip install -e .

# Analyze a DED with capacity planner
pi-strategist analyze path/to/ded.md --excel path/to/capacity.xlsx

# Quick red flag check
pi-strategist check "The system should be fast and user-friendly"
```

## Project Structure

```
pi-strategist/
├── frontend/                          # React + TypeScript SPA
│   ├── src/
│   │   ├── api/                       # API client and endpoint functions
│   │   │   └── endpoints/
│   │   │       ├── analysis.ts        # Analysis + AI insights API calls
│   │   │       └── files.ts           # File upload API calls
│   │   ├── components/
│   │   │   ├── analysis/              # Analysis result tabs
│   │   │   │   ├── AIInsightsTab.tsx   # AI insights, filters, rebalancing, chat
│   │   │   │   ├── SummaryTab.tsx      # Overview with charts
│   │   │   │   ├── CapacityTab.tsx     # Sprint capacity details
│   │   │   │   ├── RedFlagsTab.tsx     # DED red flags
│   │   │   │   ├── DeploymentTab.tsx   # CD deployment strategy
│   │   │   │   └── PIDashboardTab.tsx  # Resource heatmap and costs
│   │   │   ├── charts/                # Plotly chart components (lazy-loaded)
│   │   │   ├── common/                # FileUpload, ErrorBoundary
│   │   │   └── layout/                # AppShell, NavLink
│   │   ├── hooks/useAnalysis.ts       # React Query hooks (including AI mutations)
│   │   ├── pages/                     # Route pages
│   │   ├── store/                     # Zustand state management
│   │   ├── types/                     # TypeScript interfaces
│   │   └── utils/                     # CSV/PDF export utilities
│   └── package.json
│
├── backend/                           # FastAPI REST API
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── analysis.py        # POST /analysis/full, CRUD /analyses
│   │   │   │   ├── ai_insights.py     # POST /ai/insights, POST /ai/chat
│   │   │   │   ├── files.py           # File upload/download
│   │   │   │   ├── health.py          # Health check
│   │   │   │   └── quick_check.py     # Quick red flag check
│   │   │   └── router.py             # Route aggregation
│   │   ├── core/
│   │   │   ├── database.py            # SQLite via aiosqlite
│   │   │   ├── file_storage.py        # File upload storage
│   │   │   └── logging.py            # Structured logging
│   │   ├── services/                  # Business logic services
│   │   ├── config.py                  # Pydantic Settings (.env loading)
│   │   └── main.py                    # FastAPI app with lifespan
│   ├── tests/                         # Backend test suite
│   └── requirements.txt
│
├── src/pi_strategist/                 # Core Python analysis library
│   ├── analyzers/
│   │   ├── ai_advisor.py              # AIAdvisor class (Claude API wrapper)
│   │   ├── risk_analyzer.py           # Red flag detection
│   │   ├── capacity_analyzer.py       # Sprint capacity validation
│   │   └── deployment_analyzer.py     # CD strategy generation
│   ├── parsers/                       # Document parsers (docx, xlsx, pdf, md)
│   ├── reporters/                     # Report generators (HTML, JSON, text)
│   └── cli.py                         # CLI entry point
│
├── tests/                             # Core library tests
├── pyproject.toml                     # Python package config
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check (includes AI status) |
| POST | `/api/v1/files/upload` | Upload Excel/Word/PDF files |
| GET | `/api/v1/files` | List uploaded files |
| POST | `/api/v1/analysis/full` | Run full analysis on uploaded files |
| GET | `/api/v1/analyses` | List saved analyses |
| GET | `/api/v1/analyses/{id}` | Get a saved analysis |
| POST | `/api/v1/ai/insights` | Generate AI insights (full, summary, or rebalancing) |
| POST | `/api/v1/ai/chat` | Follow-up chat about analysis results |
| POST | `/api/v1/quick-check` | Quick red flag check on raw text |

## Security Notice

**This tool is intended for internal use with non-sensitive planning data.**

### AI Data Processing

When AI features are enabled, planning data (resource names, hours, rates, allocations, project details) is sent to Anthropic's Claude API. Ensure this complies with your organization's data handling policies.

### What Is NOT Sent to Claude

- Raw uploaded files (only parsed/structured data)
- API keys or credentials
- User session data

### Data Cleanup

After completing your planning session:
1. Delete uploaded files via the UI or clear `backend/uploads/`
2. Clear downloaded reports from your local machine
3. Delete the SQLite database at `backend/uploads/pi_strategist.db` if needed

## Development

### Running Tests

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# Core library tests
pytest tests/
```

### Code Quality

```bash
# Frontend
cd frontend && npm run lint

# Backend
black backend/
ruff check backend/
```

## License

MIT License - see LICENSE file for details.
