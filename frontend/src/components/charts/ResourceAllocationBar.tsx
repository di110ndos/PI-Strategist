/**
 * Stacked bar showing optimal/under/over allocation counts.
 * Ported from pi_dashboard.py:233-249
 */

import LazyPlot from './LazyPlot';
import { GREEN, AMBER, RED, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface ResourceData {
  total_hours: number;
}

interface Props {
  resources: Record<string, ResourceData>;
}

const PI_MAX = 488.0;

export default function ResourceAllocationBar({ resources }: Props) {
  if (!resources || Object.keys(resources).length === 0) return null;

  let optimal = 0;
  let under = 0;
  let over = 0;

  for (const r of Object.values(resources)) {
    const pct = (r.total_hours / PI_MAX) * 100;
    if (pct < 80) under++;
    else if (pct <= 105) optimal++;
    else over++;
  }

  const total = optimal + under + over;
  if (total === 0) return null;

  return (
    <LazyPlot
      data={[
        {
          type: 'bar',
          name: `Optimal (${optimal})`,
          x: [optimal],
          y: ['Allocation'],
          orientation: 'h',
          marker: { color: GREEN },
          hovertemplate: `Optimal: ${optimal} resources<extra></extra>`,
        },
        {
          type: 'bar',
          name: `Under (${under})`,
          x: [under],
          y: ['Allocation'],
          orientation: 'h',
          marker: { color: AMBER },
          hovertemplate: `Under-allocated: ${under} resources<extra></extra>`,
        },
        {
          type: 'bar',
          name: `Over (${over})`,
          x: [over],
          y: ['Allocation'],
          orientation: 'h',
          marker: { color: RED },
          hovertemplate: `Over-allocated: ${over} resources<extra></extra>`,
        },
      ]}
      layout={plotlyLayout({
        barmode: 'stack',
        height: 180,
        xaxis: { title: { text: 'Resources' }, showgrid: false },
        yaxis: { showticklabels: false },
        legend: { orientation: 'h', yanchor: 'bottom', y: 1.1, xanchor: 'center', x: 0.5 },
        margin: { l: 10, r: 10, t: 40, b: 30 },
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
