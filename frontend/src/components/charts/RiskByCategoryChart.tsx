/**
 * Horizontal stacked bar chart of red flags grouped by category.
 * Ported from charts.py:186-228
 */

import LazyPlot from './LazyPlot';
import { RED, AMBER, BLUE, BORDER, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface RedFlag {
  category: string;
  severity: string;
}

interface Props {
  redFlags: RedFlag[];
}

export default function RiskByCategoryChart({ redFlags }: Props) {
  if (!redFlags || redFlags.length === 0) return null;

  const categories: Record<string, Record<string, number>> = {};
  for (const rf of redFlags) {
    const cat = rf.category;
    const sev = rf.severity;
    if (!categories[cat]) categories[cat] = { critical: 0, moderate: 0, low: 0 };
    categories[cat][sev] = (categories[cat][sev] || 0) + 1;
  }

  const sortedCats = Object.keys(categories).sort(
    (a, b) => {
      const sumA = Object.values(categories[a]).reduce((s, v) => s + v, 0);
      const sumB = Object.values(categories[b]).reduce((s, v) => s + v, 0);
      return sumB - sumA;
    }
  );

  const traces = [
    { name: 'Critical', color: RED, key: 'critical' },
    { name: 'Moderate', color: AMBER, key: 'moderate' },
    { name: 'Low', color: BLUE, key: 'low' },
  ];

  return (
    <LazyPlot
      data={traces.map((t) => ({
        type: 'bar' as const,
        name: t.name,
        y: sortedCats,
        x: sortedCats.map((c) => categories[c][t.key] || 0),
        orientation: 'h' as const,
        marker: { color: t.color },
        opacity: 0.85,
      }))}
      layout={plotlyLayout({
        barmode: 'stack',
        height: Math.max(300, sortedCats.length * 45 + 100),
        xaxis: { title: { text: 'Count' }, gridcolor: BORDER },
        yaxis: { title: { text: '' }, autorange: 'reversed', automargin: true },
        legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 },
        margin: { l: 10, r: 40, t: 40, b: 40 },
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
