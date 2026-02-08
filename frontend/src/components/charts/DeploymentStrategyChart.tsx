/**
 * Donut chart showing deployment strategy distribution.
 * Ported from charts.py:366-419
 */

import LazyPlot from './LazyPlot';
import { VIOLET, GREEN, BLUE, CYAN, BORDER, TEXT_PRIMARY, TEXT_MUTED, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface Cluster {
  strategy: string;
  tasks: Array<{ id: string; name: string; hours: number }>;
}

interface Props {
  clusters: Cluster[];
}

const STRATEGY_COLOR_MAP: Record<string, string> = {
  feature_flag: VIOLET,
  full_deployment: GREEN,
  canary: BLUE,
  blue_green: CYAN,
};

export default function DeploymentStrategyChart({ clusters }: Props) {
  if (!clusters || clusters.length === 0) return null;

  const strategyTasks: Record<string, number> = {};
  for (const cluster of clusters) {
    const name = (cluster.strategy || 'unknown').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    strategyTasks[name] = (strategyTasks[name] || 0) + cluster.tasks.length;
  }

  const labels = Object.keys(strategyTasks);
  const values = Object.values(strategyTasks);
  const totalTasks = values.reduce((s, v) => s + v, 0);

  // Build color map from raw strategy keys
  const colorMap: Record<string, string> = {};
  for (const cluster of clusters) {
    const name = (cluster.strategy || 'unknown').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    colorMap[name] = STRATEGY_COLOR_MAP[cluster.strategy] || VIOLET;
  }
  const colors = labels.map((l) => colorMap[l] || VIOLET);

  return (
    <LazyPlot
      data={[
        {
          type: 'pie',
          labels,
          values,
          hole: 0.5,
          marker: { colors, line: { color: BORDER, width: 2 } },
          textinfo: 'label+value',
          textfont: { color: TEXT_PRIMARY },
          hovertemplate: '%{label}: %{value} tasks<extra></extra>',
        },
      ]}
      layout={plotlyLayout({
        showlegend: false,
        height: 360,
        margin: { l: 20, r: 20, t: 20, b: 20 },
        annotations: [
          {
            text: `<b>${totalTasks}</b><br><span style='font-size:11px;color:${TEXT_MUTED}'>tasks</span>`,
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
