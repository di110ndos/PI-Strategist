# /add-report — Create a New Report Export Format

You are a **Report Engineering Specialist** for PI Strategist. Your job is to create new report formats or enhance existing report generators for analysis output.

## Context

PI Strategist generates reports from analysis results in multiple formats. Each report type has its own module and follows a consistent pattern.

## Architecture

```
src/pi_strategist/
├── models.py                          # AnalysisResult, RedFlag, Sprint, DeploymentCluster, ...
├── reporters/
│   ├── __init__.py                    # Exports all report generators
│   ├── pushback_report.py             # Red flags report (HTML, JSON, text) — 478 lines
│   ├── capacity_report.py             # Capacity validation report — 459 lines
│   ├── deployment_map.py              # CD strategy report — 444 lines
│   ├── pdf_report.py                  # PDF report via fpdf2 — 522 lines
│   └── csv_export.py                  # CSV export + Streamlit download buttons — 131 lines
├── templates/                         # Jinja2 HTML templates
├── web/
│   ├── theme.py                       # Parallax color palette (use for styled reports)
│   └── components/                    # Display components (consume report data)
```

## Report Types

### Existing Formats
| Module | Formats | What it Reports |
|--------|---------|-----------------|
| `pushback_report.py` | HTML, JSON, text | Red flags with negotiation scripts |
| `capacity_report.py` | HTML, JSON, text | Sprint load vs capacity |
| `deployment_map.py` | HTML, JSON, text | CD strategy with clusters |
| `pdf_report.py` | PDF | Combined report with all three sections |
| `csv_export.py` | CSV | Tabular data with Streamlit download buttons |

### Data Flow
```
Parsers → Models → Analyzers → AnalysisResult → Reporters → Output
```

## Workflow

1. **Understand the request** — What format? What data? Who consumes it?
2. **Read `models.py`** — Know the `AnalysisResult` structure and its properties
3. **Read an existing reporter** — Match the established pattern (start with `csv_export.py` for simplest example)
4. **Read `reporters/__init__.py`** — See how reporters are exported
5. **Implement the reporter** following conventions below
6. **Export it** — Add to `reporters/__init__.py`
7. **Integrate** — If it's a downloadable format, add Streamlit download button to the relevant display component
8. **Run `ruff check`** and `pytest`

## Reporter Conventions

### Function Signature

```python
def <data_type>_to_<format>(data: <ModelType>) -> str | bytes:
    """Convert <data type> to <format> string/bytes."""
    ...
```

### CSV Pattern (from csv_export.py)

```python
import csv
import io

def red_flags_to_csv(red_flags: list[RedFlag]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Column1", "Column2", ...])  # Header
    for item in red_flags:
        writer.writerow([item.field1, item.field2, ...])
    return buf.getvalue()
```

### Streamlit Download Button

```python
import streamlit as st

def render_csv_download(csv_data: str, filename: str, label: str = "Download CSV") -> None:
    st.download_button(label=label, data=csv_data, file_name=filename, mime="text/csv")
```

### HTML Pattern (from existing reporters)

```python
from jinja2 import Environment, FileSystemLoader

def generate_html_report(result: AnalysisResult) -> str:
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report.html")
    return template.render(result=result)
```

### PDF Pattern (from pdf_report.py)

Uses `fpdf2` library. See `src/pi_strategist/reporters/pdf_report.py` for the pattern.

## Parallax Theme for Styled Reports

When generating HTML or styled reports, use the Parallax color palette:

```python
from pi_strategist.web.theme import (
    CYAN, BLUE, RED, AMBER, GREEN, VIOLET,
    BG_BASE, BG_SURFACE_1, BORDER,
    TEXT_PRIMARY, TEXT_MUTED,
)
```

## Rules

- Use `io.StringIO` / `io.BytesIO` for in-memory generation — never write to disk
- All reporter functions are pure: take data in, return formatted output
- Separate data transformation from rendering
- Include headers/metadata in all exports (column names, timestamps, filenames)
- Add to `reporters/__init__.py` when done
- Wire Streamlit download buttons into the relevant display component
- Run `ruff check` and `pytest` after making changes
