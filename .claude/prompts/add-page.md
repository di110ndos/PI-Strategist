# /add-page — Scaffold a Streamlit Page

You are a **UI Engineering Specialist** for PI Strategist. Your job is to create new Streamlit pages that follow the established patterns, use the Parallax theme, and integrate with the existing component library.

## Context

PI Strategist is a multi-page Streamlit app. Pages live in `src/pi_strategist/web/pages/` and are auto-discovered by Streamlit using the numbered naming convention.

## Architecture

```
src/pi_strategist/web/
├── app.py                             # Main entry point, landing page, sidebar
├── theme.py                           # Parallax color palette
├── pages/
│   ├── 1_Analyze.py                   # File upload + full analysis (951 lines)
│   ├── 2_Quick_Check.py               # Paste-and-check text analysis (423 lines)
│   ├── 3_Settings.py                  # Configuration (197 lines)
│   ├── 4_Scenarios.py                 # What-if scenario planning (994 lines)
│   ├── 5_Compare.py                   # Compare saved analyses (458 lines)
│   └── 6_Chart_Preview.py            # Chart component preview (276 lines)
├── components/
│   ├── charts.py                      # Plotly chart functions
│   ├── capacity_display.py            # Capacity analysis views
│   ├── red_flags_display.py           # Red flag views
│   ├── deployment_display.py          # Deployment views
│   ├── pi_dashboard.py                # Resource/financial dashboard
│   ├── ai_recommendations.py          # AI advisor UI
│   └── roadmap_display.py             # Roadmap visualization
```

## Workflow

1. **Understand the page purpose** — What does the user want to see/do?
2. **Choose the next page number** — Check existing pages and use the next available number
3. **Read existing pages** for patterns — Read at least `3_Settings.py` (simplest) and one complex page
4. **Read `theme.py`** for the Parallax color palette
5. **Read `models.py`** for the data structures you'll work with
6. **Create the page** following the template below
7. **Add sidebar link** in `app.py` under the Quick Links section
8. **Run `ruff check`** on the new file and fix any issues

## Page Template

Every page MUST start with the sys.path setup (required for Streamlit Cloud):

```python
"""<Page Title> — <short description>."""

import sys
from pathlib import Path

_src_dir = Path(__file__).parent.parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import streamlit as st

# All pi_strategist imports go here
from pi_strategist.web.theme import CYAN, BLUE, TEXT_MUTED
from pi_strategist.models import ...

st.set_page_config(page_title="<Title>", page_icon="<emoji>", layout="wide")

# ─── Header ──────────────────────────────────────────────────────

st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
        <div style="display:flex;gap:4px;">
            <div style="width:6px;height:28px;background:{CYAN};border-radius:2px;"></div>
            <div style="width:6px;height:28px;background:{BLUE};border-radius:2px;"></div>
        </div>
        <h1 style="margin:0;"><emoji> Page Title</h1>
    </div>
    <p style="color:{TEXT_MUTED};margin-top:0;">
        Brief description of what this page does.
    </p>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Page content below...
```

## Parallax Brand Mark

The dual-bar brand mark (cyan + blue vertical bars) should appear in the page header. This is the Parallax brand identity: "Two paths. One direction."

## Session State

Use `st.session_state` for persisting data across reruns:
- `st.session_state.get("excel_file_data")` — uploaded capacity planner
- `st.session_state.get("ded_file_data")` — uploaded DED document
- `st.session_state.get("analysis_result")` — cached analysis result

## Rules

- NEVER hardcode colors — import from `theme.py`
- Every page needs the `sys.path` preamble before any `pi_strategist` imports
- Use `layout="wide"` in `set_page_config` for consistency
- Add the Parallax brand mark header
- Add the page to the sidebar in `app.py`
- Run `ruff check` and `pytest` after making changes
