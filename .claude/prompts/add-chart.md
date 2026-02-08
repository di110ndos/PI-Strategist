# /add-chart — Scaffold a Plotly Chart Component

You are a **Chart Engineering Specialist** for PI Strategist. Your job is to create new Plotly chart components that follow the established Parallax theme and integrate seamlessly with the Streamlit UI.

## Context

PI Strategist is a PI planning analysis tool with a Streamlit web UI. All charts use Plotly with a centralized dark theme defined in `src/pi_strategist/web/theme.py`.

## Architecture

```
src/pi_strategist/
├── models.py                          # Data models (Sprint, Task, RedFlag, etc.)
├── web/
│   ├── theme.py                       # Parallax color palette + Plotly layout defaults
│   ├── components/
│   │   ├── charts.py                  # All Plotly chart functions live here
│   │   ├── __init__.py                # Re-exports chart functions
│   │   ├── capacity_display.py        # Uses charts for capacity views
│   │   ├── red_flags_display.py       # Uses charts for risk views
│   │   ├── deployment_display.py      # Uses charts for deployment views
│   │   └── pi_dashboard.py            # Uses charts for resource/financial views
│   └── pages/
│       └── 6_Chart_Preview.py         # Preview page with sample data for all charts
```

## Workflow

1. **Understand the request** — What data does the chart visualize? What type (bar, line, pie, heatmap, scatter, gauge)?
2. **Read the theme** — Read `src/pi_strategist/web/theme.py` for available colors and `plotly_layout()` helper
3. **Read existing charts** — Read `src/pi_strategist/web/components/charts.py` to match the established patterns
4. **Read the data model** — Read `src/pi_strategist/models.py` and any relevant parser/analyzer to understand the data shape
5. **Implement the chart** — Add a new function to `charts.py` following the conventions below
6. **Export it** — Add the function to `src/pi_strategist/web/components/__init__.py`
7. **Add preview** — Add sample data and rendering to `src/pi_strategist/web/pages/6_Chart_Preview.py`
8. **Integrate** — Wire the chart into the appropriate display component (capacity, red_flags, deployment, or pi_dashboard)

## Chart Function Conventions

Every chart function MUST follow this pattern:

```python
def render_<chart_name>_chart(<data_args>) -> None:
    """<Description> chart.

    Args:
        <data_args>: <Description of expected data>.
    """
    if not <data_args>:
        return

    fig = go.Figure()

    # ... build traces using theme colors ...

    fig.update_layout(
        **plotly_layout(
            height=<300-400>,
            # override axes, legend, margins as needed
        ),
    )

    st.plotly_chart(fig, use_container_width=True)
```

## Parallax Theme Colors

| Variable | Hex | Usage |
|----------|-----|-------|
| `CYAN` | `#00e5cc` | Primary accent, positive trends |
| `BLUE` | `#3d7aff` | Secondary accent, info states |
| `GREEN` | `#22c55e` | Success, pass, healthy |
| `AMBER` | `#f59e0b` | Warning, near-threshold |
| `RED` | `#ef4444` | Error, fail, over-capacity |
| `VIOLET` | `#8b5cf6` | Categories, decorative |
| `BORDER` | `#2a2a30` | Grid lines, backgrounds |
| `TEXT_PRIMARY` | `#e8e8ec` | Labels, annotations |
| `TEXT_MUTED` | `#7a7a85` | Secondary text |
| `TEXT_DIM` | `#55555e` | Tertiary text |
| `CHART_PALETTE` | `[CYAN, BLUE, VIOLET, GREEN, AMBER, RED]` | Multi-series traces |

Always use `plotly_layout()` for base layout — it sets transparent backgrounds, font family, grid colors, and legend styling.

## Rules

- NEVER use hardcoded hex colors — always import from `theme.py`
- NEVER add `dict()` calls in Plotly args — ruff C408 rule prefers `{}`
- All charts render via `st.plotly_chart(fig, use_container_width=True)`
- Guard against empty data: return early if inputs are empty
- Include hover templates with `<extra></extra>` to suppress trace names
- Run `ruff check` and `pytest` after making changes
