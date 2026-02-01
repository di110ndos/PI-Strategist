# PI Strategist

A dual-mode system for Program Increment (PI) planning analysis: a Claude Code custom agent for interactive analysis and a standalone CLI application for batch processing.

## Features

- **Red Flag Detection**: Identifies ambiguous, subjective, or unmeasurable acceptance criteria in DEDs
- **Capacity Validation**: Validates sprint loading against team capacity with recommendations
- **Deployment Strategy**: Generates CD (Continuous Delivery) deployment clusters and strategies
- **Multiple Input Formats**: Supports Word (.docx), Markdown (.md), PDF, and Excel (.xlsx)
- **Rich Reports**: Generates HTML, JSON, or text reports

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/pi-strategist.git
cd pi-strategist

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Install Dependencies Only

```bash
pip install click python-docx openpyxl pdfplumber jinja2 anthropic pydantic rich
```

## Quick Start

### Analyze a DED Document

```bash
# Basic analysis (DED only)
pi-strategist analyze path/to/your-ded.md

# Full analysis with capacity planner
pi-strategist analyze path/to/your-ded.md --excel path/to/capacity.xlsx

# Specify output format
pi-strategist analyze your-ded.md --format json --output ./reports
```

### Quick Red Flag Check

```bash
# Check individual text for red flags
pi-strategist check "The system should be fast and user-friendly"
```

### Batch Processing

```bash
# Process all documents in a directory
pi-strategist batch --dir ./documents --output ./reports
```

## CLI Commands

### `analyze`

Analyze a DED document for risks, capacity, and deployment strategy.

```bash
pi-strategist analyze <ded-file> [OPTIONS]

Options:
  -e, --excel PATH    Excel capacity planner file
  -o, --output PATH   Output directory for reports (default: ./output)
  -f, --format TEXT   Output format: html, json, text (default: html)
  -b, --buffer FLOAT  Buffer percentage (default: 0.20)
```

### `batch`

Batch process all documents in a directory.

```bash
pi-strategist batch --dir <directory> [OPTIONS]

Options:
  -o, --output PATH   Output directory for reports
  -f, --format TEXT   Output format: html, json, text
```

### `check`

Quick check text for red flags.

```bash
pi-strategist check "your acceptance criteria text here"
```

### `config`

Configure PI Strategist settings.

```bash
# Set API key for Claude integration
pi-strategist config --set-api-key <your-api-key>

# Show current configuration
pi-strategist config --show
```

## Claude Code Agent Integration

PI Strategist includes a custom Claude Code agent for interactive analysis.

### Setup

The agent configuration is located in `.claude/`:

```
.claude/
├── config.json           # Project configuration
├── agents/
│   └── pi-strategist.json  # Agent configuration
└── prompts/
    └── pi-strategist.md    # System prompt
```

### Custom Commands

When using Claude Code with the PI Strategist agent:

- `/analyze-ded` - Full DED analysis with all three reports
- `/check-capacity` - Capacity validation only
- `/find-red-flags` - Risk identification only
- `/deployment-map` - CD strategy only
- `/negotiate` - Generate negotiation scripts for identified red flags

## Reports

PI Strategist generates three types of reports:

### 1. Pushback Report

Identifies red flags in acceptance criteria with:
- Flagged term and category
- Severity level (Critical, Moderate, Low)
- Suggested measurable metric
- Negotiation script for stakeholder discussions

### 2. Capacity Check

Validates sprint loading with:
- Sprint capacity breakdown (total, buffer, net)
- Load vs. capacity analysis
- Pass/Fail status per sprint
- Recommendations for overloaded sprints
- High-risk task identification

### 3. Deployment Map

CD strategy with:
- Task clusters for incremental deployment
- Recommended deployment strategy per cluster
- Deployment timeline
- Rollback plans
- CD percentage vs. target

## Red Flag Categories

| Category | Examples | Severity |
|----------|----------|----------|
| Subjective Terms | fast, user-friendly, simple, robust | Critical |
| Vague Metrics | high quality, performant, scalable, secure | Critical |
| Missing Criteria | works well, looks good, feels right | Moderate |
| Undefined Scope | comprehensive, complete, all edge cases, etc. | Critical |
| Comparative Terms | better, improved, enhanced, optimized | Moderate |
| Time Ambiguity | soon, quickly, real-time, immediately | Moderate |
| Quantity Ambiguity | many, few, several, most, some | Low-Moderate |

## Capacity Formula

```
Net Capacity = Total Hours - (Total Hours × Buffer%)
Sprint Status = PASS if Sprint Load ≤ Net Capacity, else FAIL
```

Default buffer: 20%

## Deployment Strategies

| Strategy | Use Case |
|----------|----------|
| Feature Flag | UI changes, user-facing features |
| Canary | High-risk domains (auth, payment) |
| Blue-Green | API changes, zero-downtime requirements |
| Dark Launch | Analytics, background features |

## Project Structure

```
pi-strategist/
├── .claude/                    # Claude Code agent configuration
│   ├── config.json
│   ├── agents/
│   └── prompts/
├── src/pi_strategist/          # Main package
│   ├── cli.py                  # CLI application
│   ├── models.py               # Data models
│   ├── parsers/                # Document parsers
│   │   ├── ded_parser.py
│   │   └── excel_parser.py
│   ├── analyzers/              # Analysis engines
│   │   ├── risk_analyzer.py
│   │   ├── capacity_analyzer.py
│   │   └── deployment_analyzer.py
│   └── reporters/              # Report generators
│       ├── pushback_report.py
│       ├── capacity_report.py
│       └── deployment_map.py
├── templates/                  # Document templates
├── examples/                   # Sample documents
├── tests/                      # Test suite
├── pyproject.toml              # Project configuration
└── README.md
```

## Writing Good Acceptance Criteria

### Avoid

- "The system should be **fast**" ❌
- "Provide **comprehensive** validation" ❌
- "Ensure **high quality** output" ❌
- "Handle **all edge cases**" ❌

### Prefer

- "The system responds in <2 seconds at 95th percentile" ✓
- "Validates: email format, MX record, disposable domain blocklist" ✓
- "Passes all unit tests with ≥80% coverage" ✓
- "Handles edge cases: empty input, max length, special characters" ✓

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
ruff check src/
```

### Type Checking

```bash
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: https://github.com/yourusername/pi-strategist/issues
- **Documentation**: https://github.com/yourusername/pi-strategist#readme
