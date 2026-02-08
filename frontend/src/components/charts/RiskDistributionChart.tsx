/**
 * Donut chart showing red flag severity distribution.
 * Ported from charts.py:138-183
 */

import LazyPlot from './LazyPlot';
import { RED, AMBER, BLUE, BORDER, TEXT_PRIMARY, TEXT_MUTED, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface Props {
  critical: number;
  moderate: number;
  low: number;
  height?: number;
}

export default function RiskDistributionChart({ critical, moderate, low, height = 280 }: Props) {
  const total = critical + moderate + low;
  if (total === 0) return null;

  const labels: string[] = [];
  const values: number[] = [];
  const colors: string[] = [];

  if (critical > 0) { labels.push('Critical'); values.push(critical); colors.push(RED); }
  if (moderate > 0) { labels.push('Moderate'); values.push(moderate); colors.push(AMBER); }
  if (low > 0) { labels.push('Low'); values.push(low); colors.push(BLUE); }

  return (
    <LazyPlot
      data={[
        {
          type: 'pie',
          labels,
          values,
          hole: 0.55,
          marker: { colors, line: { color: BORDER, width: 2 } },
          textinfo: 'label+value',
          textfont: { color: TEXT_PRIMARY, size: 13 },
          hovertemplate: '%{label}: %{value} issues<extra></extra>',
        },
      ]}
      layout={plotlyLayout({
        showlegend: false,
        height,
        margin: { l: 20, r: 20, t: 20, b: 20 },
        annotations: [
          {
            text: `<b>${total}</b><br><span style='font-size:11px;color:${TEXT_MUTED}'>total</span>`,
            x: 0.5,
            y: 0.5,
            font: { size: 22, color: TEXT_PRIMARY },
            showarrow: false,
          },
        ],
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
