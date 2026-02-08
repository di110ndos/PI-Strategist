/**
 * Ported from src/pi_strategist/web/theme.py — centralized Plotly theme.
 */

// ─── Primary Brand ────────────────────────────────────────────────
export const CYAN = '#00e5cc';
export const BLUE = '#3d7aff';

// ─── Backgrounds ──────────────────────────────────────────────────
export const BG_BASE = '#0a0a0c';
export const BG_SURFACE_1 = '#111114';
export const BG_SURFACE_2 = '#18181c';
export const BG_SURFACE_3 = '#1e1e24';

// ─── Borders ──────────────────────────────────────────────────────
export const BORDER = '#2a2a30';
export const BORDER_LIGHT = '#35353d';

// ─── Text ─────────────────────────────────────────────────────────
export const TEXT_PRIMARY = '#e8e8ec';
export const TEXT_MUTED = '#7a7a85';
export const TEXT_DIM = '#55555e';

// ─── Semantic ─────────────────────────────────────────────────────
export const AMBER = '#f59e0b';
export const RED = '#ef4444';
export const GREEN = '#22c55e';
export const VIOLET = '#8b5cf6';

// ─── Chart Palette (ordered for Plotly traces) ───────────────────
export const CHART_PALETTE = [CYAN, BLUE, VIOLET, GREEN, AMBER, RED];

// ─── Severity Colors ─────────────────────────────────────────────
export const SEVERITY_COLORS: Record<string, string> = {
  critical: RED,
  moderate: AMBER,
  low: BLUE,
};

// ─── Strategy Colors ─────────────────────────────────────────────
export const STRATEGY_COLORS: Record<string, string> = {
  feature_flag: VIOLET,
  full_deployment: GREEN,
  canary: BLUE,
  blue_green: CYAN,
};

// ─── Plotly Layout Defaults ──────────────────────────────────────
const PLOTLY_LAYOUT: Partial<Plotly.Layout> = {
  autosize: true,
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { color: TEXT_PRIMARY, family: 'DM Sans, Inter, sans-serif' },
  margin: { l: 40, r: 40, t: 40, b: 40 },
  legend: {
    bgcolor: 'rgba(0,0,0,0)',
    bordercolor: BORDER,
    font: { color: TEXT_MUTED },
  },
  xaxis: { gridcolor: BORDER, zerolinecolor: BORDER_LIGHT },
  yaxis: { gridcolor: BORDER, zerolinecolor: BORDER_LIGHT },
};

/**
 * Return a copy of the default Plotly layout merged with overrides.
 * Nested dicts (xaxis, yaxis, margin, font, legend) are shallow-merged.
 */
export function plotlyLayout(overrides: Partial<Plotly.Layout> = {}): Partial<Plotly.Layout> {
  const layout: Record<string, unknown> = { ...PLOTLY_LAYOUT };
  for (const [key, value] of Object.entries(overrides)) {
    if (
      value !== null &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      key in layout &&
      typeof layout[key] === 'object' &&
      layout[key] !== null
    ) {
      layout[key] = { ...(layout[key] as Record<string, unknown>), ...(value as Record<string, unknown>) };
    } else {
      layout[key] = value;
    }
  }
  return layout as Partial<Plotly.Layout>;
}

/** Shared Plotly config — responsive, no mode bar. */
export const PLOTLY_CONFIG: Partial<Plotly.Config> = {
  responsive: true,
  displayModeBar: false,
};
