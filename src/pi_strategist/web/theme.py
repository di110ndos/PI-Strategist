"""Parallax theme — centralized color palette for PI Strategist UI."""

from pi_strategist.models import DeploymentStrategy, RedFlagSeverity

# ─── Primary Brand ────────────────────────────────────────────────
CYAN = "#00e5cc"
BLUE = "#3d7aff"

# ─── Backgrounds ──────────────────────────────────────────────────
BG_BASE = "#0a0a0c"
BG_SURFACE_1 = "#111114"
BG_SURFACE_2 = "#18181c"
BG_SURFACE_3 = "#1e1e24"

# ─── Borders ──────────────────────────────────────────────────────
BORDER = "#2a2a30"
BORDER_LIGHT = "#35353d"

# ─── Text ─────────────────────────────────────────────────────────
TEXT_PRIMARY = "#e8e8ec"
TEXT_MUTED = "#7a7a85"
TEXT_DIM = "#55555e"

# ─── Semantic ─────────────────────────────────────────────────────
AMBER = "#f59e0b"
RED = "#ef4444"
GREEN = "#22c55e"
VIOLET = "#8b5cf6"

# ─── Dim / Translucent Variants ──────────────────────────────────
CYAN_DIM = "rgba(0,229,204,0.15)"
BLUE_DIM = "rgba(61,122,255,0.15)"
AMBER_DIM = "rgba(245,158,11,0.12)"
RED_DIM = "rgba(239,68,68,0.12)"
GREEN_DIM = "rgba(34,197,94,0.12)"
VIOLET_DIM = "rgba(139,92,246,0.12)"

# ─── Semantic Aliases (used across components) ───────────────────
COLORS = {
    "pass": GREEN,
    "fail": RED,
    "warning": AMBER,
    "info": BLUE,
    "accent": CYAN,
}

# ─── Severity Config ─────────────────────────────────────────────
SEVERITY_CONFIG = {
    RedFlagSeverity.CRITICAL: {
        "color": RED,
        "bg_color": RED_DIM,
        "border_color": BORDER_LIGHT,
        "icon": "🚨",
        "label": "Critical",
        "description": "Blocks acceptance — resolve before development",
    },
    RedFlagSeverity.MODERATE: {
        "color": AMBER,
        "bg_color": AMBER_DIM,
        "border_color": BORDER_LIGHT,
        "icon": "⚠️",
        "label": "Moderate",
        "description": "Needs clarification before sprint planning",
    },
    RedFlagSeverity.LOW: {
        "color": BLUE,
        "bg_color": BLUE_DIM,
        "border_color": BORDER_LIGHT,
        "icon": "💡",
        "label": "Low",
        "description": "Nice to clarify during development",
    },
}

# ─── Deployment Strategy Colors ──────────────────────────────────
STRATEGY_COLORS = {
    DeploymentStrategy.FEATURE_FLAG: VIOLET,
    DeploymentStrategy.FULL_DEPLOYMENT: GREEN,
}

# ─── Priority Colors ─────────────────────────────────────────────
PRIORITY_COLORS = {
    1: RED,
    2: AMBER,
    3: GREEN,
}

# ─── Chart Palette (ordered for Plotly traces) ───────────────────
CHART_PALETTE = [CYAN, BLUE, VIOLET, GREEN, AMBER, RED]

# ─── Plotly Layout Defaults ──────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_PRIMARY, family="DM Sans, sans-serif"),
    margin=dict(l=40, r=40, t=40, b=40),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor=BORDER,
        font=dict(color=TEXT_MUTED),
    ),
    xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER_LIGHT),
    yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER_LIGHT),
)


def plotly_layout(**overrides) -> dict:
    """Return a copy of the default Plotly layout merged with overrides."""
    layout = {**PLOTLY_LAYOUT}
    for key, value in overrides.items():
        if isinstance(value, dict) and key in layout and isinstance(layout[key], dict):
            layout[key] = {**layout[key], **value}
        else:
            layout[key] = value
    return layout
