/**
 * Plotly gauge indicator for CD readiness percentage.
 * Ported from deployment_display.py:75-94
 */

import LazyPlot from './LazyPlot';
import { GREEN, AMBER, RED, TEXT_PRIMARY, TEXT_MUTED, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface Props {
  percentage: number;
  target?: number;
}

export default function DeploymentReadinessGauge({ percentage, target = 30 }: Props) {
  const targetMet = percentage >= target;

  return (
    <LazyPlot
      data={[
        {
          type: 'indicator',
          mode: 'gauge+number',
          value: percentage,
          number: { suffix: '%', font: { color: TEXT_PRIMARY, size: 28 } },
          gauge: {
            axis: { range: [0, 100], tickcolor: TEXT_MUTED, dtick: 20 },
            bar: { color: targetMet ? GREEN : percentage >= 20 ? AMBER : RED },
            bgcolor: 'rgba(0,0,0,0)',
            bordercolor: 'rgba(0,0,0,0)',
            steps: [
              { range: [0, 20], color: 'rgba(239,68,68,0.1)' },
              { range: [20, target], color: 'rgba(245,158,11,0.1)' },
              { range: [target, 100], color: 'rgba(34,197,94,0.1)' },
            ],
            threshold: {
              line: { color: TEXT_MUTED, width: 2 },
              thickness: 0.75,
              value: target,
            },
          },
        },
      ]}
      layout={plotlyLayout({
        height: 200,
        margin: { l: 30, r: 30, t: 30, b: 10 },
        annotations: [
          {
            text: targetMet ? 'Target Met' : 'Below Target',
            x: 0.5,
            y: 0,
            font: { color: targetMet ? GREEN : AMBER, size: 13 },
            showarrow: false,
          },
        ],
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
