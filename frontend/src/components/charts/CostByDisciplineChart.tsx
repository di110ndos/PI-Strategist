/**
 * Horizontal bar chart of costs broken down by discipline, sorted descending.
 * Ported from charts.py:425-475
 */

import LazyPlot from './LazyPlot';
import { CHART_PALETTE, BORDER, TEXT_PRIMARY, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface Props {
  /** Map of discipline name -> total cost */
  costByDiscipline: Record<string, number>;
}

export default function CostByDisciplineChart({ costByDiscipline }: Props) {
  if (!costByDiscipline || Object.keys(costByDiscipline).length === 0) return null;

  const sorted = Object.entries(costByDiscipline)
    .filter(([, v]) => v > 0)
    .sort(([, a], [, b]) => b - a);

  if (sorted.length === 0) return null;

  const labels = sorted.map(([k]) => k);
  const values = sorted.map(([, v]) => v);
  const colors = labels.map((_, i) => CHART_PALETTE[i % CHART_PALETTE.length]);

  return (
    <LazyPlot
      data={[
        {
          type: 'bar',
          y: labels,
          x: values,
          orientation: 'h',
          marker: { color: colors, line: { width: 0 } },
          opacity: 0.85,
          text: values.map((v) => `$${v.toLocaleString()}`),
          textposition: 'auto',
          textfont: { color: TEXT_PRIMARY, size: 11 },
          hovertemplate: '%{y}: $%{x:,.0f}<extra></extra>',
        },
      ]}
      layout={plotlyLayout({
        height: Math.max(300, labels.length * 45 + 100),
        xaxis: { title: { text: 'Cost ($)' }, gridcolor: BORDER },
        yaxis: { title: { text: '' }, autorange: 'reversed', automargin: true },
        showlegend: false,
        margin: { l: 10, r: 40, t: 20, b: 40 },
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
