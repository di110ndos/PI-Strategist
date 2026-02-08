/**
 * Histogram of resource allocation percentages with threshold lines.
 * Ported from charts.py:313-360
 */

import LazyPlot from './LazyPlot';
import { CYAN, AMBER, RED, BORDER, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface ResourceData {
  total_hours: number;
}

interface Props {
  resources: Record<string, ResourceData>;
}

const PI_MAX = 488.0;

export default function AllocationDistribution({ resources }: Props) {
  if (!resources || Object.keys(resources).length === 0) return null;

  const percentages = Object.values(resources)
    .filter((r) => r.total_hours > 0)
    .map((r) => (r.total_hours / PI_MAX) * 100);

  if (percentages.length === 0) return null;

  return (
    <LazyPlot
      data={[
        {
          type: 'histogram',
          x: percentages,
          nbinsx: 15,
          marker: { color: CYAN, line: { color: BORDER, width: 1 } },
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
          { type: 'line', x0: 80, x1: 80, y0: 0, y1: 1, yref: 'paper', line: { dash: 'dash', color: AMBER, width: 1 }, opacity: 0.6 },
          { type: 'line', x0: 105, x1: 105, y0: 0, y1: 1, yref: 'paper', line: { dash: 'dash', color: RED, width: 1 }, opacity: 0.6 },
        ],
        annotations: [
          { x: 80, y: 1, yref: 'paper', text: '80%', showarrow: false, font: { color: AMBER, size: 10 }, yanchor: 'bottom' },
          { x: 105, y: 1, yref: 'paper', text: '105%', showarrow: false, font: { color: RED, size: 10 }, yanchor: 'bottom' },
        ],
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
