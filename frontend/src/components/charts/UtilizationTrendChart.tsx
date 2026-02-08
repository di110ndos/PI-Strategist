/**
 * Line chart with threshold bands showing utilization % across sprints.
 * Ported from charts.py:80-132
 */

import { Box, Text } from '@chakra-ui/react';
import LazyPlot from './LazyPlot';
import { CYAN, GREEN, AMBER, RED, BORDER, TEXT_MUTED, TEXT_DIM, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface SprintData {
  sprint: { name: string };
  utilization_percent: number;
}

interface Props {
  analyses: SprintData[];
}

/**
 * Simple linear regression returning slope and intercept.
 * x-values are 0-indexed integers representing sprint positions.
 */
function linearFit(ys: number[]): { slope: number; intercept: number } {
  const n = ys.length;
  if (n < 2) return { slope: 0, intercept: ys[0] ?? 0 };
  let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
  for (let i = 0; i < n; i++) {
    sumX += i;
    sumY += ys[i];
    sumXY += i * ys[i];
    sumXX += i * i;
  }
  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

export default function UtilizationTrendChart({ analyses }: Props) {
  if (!analyses || analyses.length === 0) {
    return (
      <Box p={4} textAlign="center">
        <Text color="gray.500">No sprint data available for utilization trend.</Text>
      </Box>
    );
  }

  const sprintNames = analyses.map((a) => a.sprint.name);
  const utilizations = analyses.map((a) => a.utilization_percent);
  const maxUtil = Math.max(...utilizations, 100);

  // Compute linear trend line values
  const { slope, intercept } = linearFit(utilizations);
  const trendValues = utilizations.map((_, i) => intercept + slope * i);
  const trendDirection = slope > 0.5 ? 'trending up' : slope < -0.5 ? 'trending down' : 'stable';

  return (
    <LazyPlot
      data={[
        // Main utilization line
        {
          type: 'scatter',
          x: sprintNames,
          y: utilizations,
          mode: 'text+lines+markers',
          text: utilizations.map((u) => `${u.toFixed(0)}%`),
          textposition: 'top center',
          textfont: { color: TEXT_MUTED, size: 11 },
          line: { color: CYAN, width: 3 },
          marker: {
            size: 10,
            color: utilizations.map((u) => (u <= 80 ? GREEN : u <= 100 ? AMBER : RED)),
            line: { color: CYAN, width: 2 },
          },
          name: 'Utilization',
        },
        // Linear trend line
        ...(utilizations.length >= 2
          ? [
              {
                type: 'scatter' as const,
                x: sprintNames,
                y: trendValues,
                mode: 'lines' as const,
                line: { color: AMBER, width: 1.5, dash: 'dot' as const },
                name: `Trend (${trendDirection})`,
                hoverinfo: 'skip' as const,
              },
            ]
          : []),
      ]}
      layout={plotlyLayout({
        yaxis: {
          title: { text: 'Utilization %' },
          gridcolor: BORDER,
          range: [0, maxUtil + 15],
        },
        xaxis: { title: { text: '' } },
        showlegend: utilizations.length >= 2,
        legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1, font: { size: 10 } },
        height: 300,
        shapes: [
          // Subtle background bands
          { type: 'rect', x0: 0, x1: 1, xref: 'paper', y0: 0, y1: 80, fillcolor: GREEN, opacity: 0.05, line: { width: 0 } },
          { type: 'rect', x0: 0, x1: 1, xref: 'paper', y0: 100, y1: maxUtil + 15, fillcolor: RED, opacity: 0.05, line: { width: 0 } },
          // Optimal zone band (80-100%) — more visible green shading
          {
            type: 'rect',
            x0: 0,
            x1: 1,
            xref: 'paper',
            y0: 80,
            y1: 100,
            fillcolor: GREEN,
            opacity: 0.12,
            line: { width: 0 },
          },
          // 100% threshold line
          { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 100, y1: 100, line: { dash: 'dash', color: RED, width: 1 }, opacity: 0.5 },
        ],
        annotations: [
          { x: 1, xref: 'paper', y: 100, text: '100% capacity', showarrow: false, font: { color: TEXT_DIM, size: 10 }, xanchor: 'right', yanchor: 'bottom' },
          // Optimal zone label
          {
            x: 0.01,
            xref: 'paper',
            y: 90,
            text: 'Optimal Zone',
            showarrow: false,
            font: { color: GREEN, size: 9 },
            xanchor: 'left',
            opacity: 0.7,
          },
        ],
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
