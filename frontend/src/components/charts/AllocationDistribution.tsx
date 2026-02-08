/**
 * Histogram of resource allocation percentages with threshold lines and zone coloring.
 * Ported from charts.py:313-360
 */

import LazyPlot from './LazyPlot';
import { AMBER, RED, GREEN, BLUE, BORDER, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface ResourceData {
  total_hours: number;
}

interface Props {
  resources: Record<string, ResourceData>;
}

const PI_MAX = 488.0;

/** Classify a percentage into a color zone. */
function zoneColor(pct: number): string {
  if (pct >= 80 && pct <= 105) return GREEN;   // Optimal
  if ((pct >= 60 && pct < 80) || (pct > 105 && pct <= 120)) return AMBER; // Warning
  return RED; // Critical (< 60% or > 120%)
}

export default function AllocationDistribution({ resources }: Props) {
  if (!resources || Object.keys(resources).length === 0) return null;

  const percentages = Object.values(resources)
    .filter((r) => r.total_hours > 0)
    .map((r) => (r.total_hours / PI_MAX) * 100);

  if (percentages.length === 0) return null;

  // Compute mean
  const mean = percentages.reduce((a, b) => a + b, 0) / percentages.length;

  // Count resources in optimal range (80-105%)
  const optimalCount = percentages.filter((p) => p >= 80 && p <= 105).length;

  // Color each bar by its zone
  const barColors = percentages.map(zoneColor);

  return (
    <LazyPlot
      data={[
        {
          type: 'histogram',
          x: percentages,
          nbinsx: 15,
          marker: { color: barColors, line: { color: BORDER, width: 1 } },
          opacity: 0.85,
          hovertemplate: 'Range: %{x}%<br>Count: %{y}<extra></extra>',
        } as any,
      ]}
      layout={plotlyLayout({
        xaxis: { title: { text: 'Allocation %' }, gridcolor: BORDER },
        yaxis: { title: { text: 'Resources' }, gridcolor: BORDER },
        showlegend: false,
        height: 380,
        shapes: [
          // Threshold lines at 80% and 105%
          { type: 'line', x0: 80, x1: 80, y0: 0, y1: 1, yref: 'paper', line: { dash: 'dash', color: AMBER, width: 1 }, opacity: 0.6 },
          { type: 'line', x0: 105, x1: 105, y0: 0, y1: 1, yref: 'paper', line: { dash: 'dash', color: RED, width: 1 }, opacity: 0.6 },
          // Mean line
          { type: 'line', x0: mean, x1: mean, y0: 0, y1: 1, yref: 'paper', line: { dash: 'dot', color: BLUE, width: 1.5 }, opacity: 0.7 },
        ],
        annotations: [
          { x: 80, y: 1, yref: 'paper', text: '80%', showarrow: false, font: { color: AMBER, size: 10 }, yanchor: 'bottom' },
          { x: 105, y: 1, yref: 'paper', text: '105%', showarrow: false, font: { color: RED, size: 10 }, yanchor: 'bottom' },
          // Mean annotation
          {
            x: mean,
            y: 1,
            yref: 'paper',
            text: `Mean: ${mean.toFixed(0)}%`,
            showarrow: false,
            font: { color: BLUE, size: 10 },
            yanchor: 'bottom',
            yshift: 12,
          },
          // Optimal count annotation
          {
            x: 0.02,
            xref: 'paper',
            y: 0.95,
            yref: 'paper',
            text: `${optimalCount} resource${optimalCount !== 1 ? 's' : ''} in optimal range`,
            showarrow: false,
            font: { color: GREEN, size: 11 },
            xanchor: 'left',
            yanchor: 'top',
            bgcolor: 'rgba(34,197,94,0.1)',
            borderpad: 4,
          },
        ],
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
