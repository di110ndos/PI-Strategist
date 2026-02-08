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

  return (
    <LazyPlot
      data={[
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
      ]}
      layout={plotlyLayout({
        yaxis: {
          title: { text: 'Utilization %' },
          gridcolor: BORDER,
          range: [0, maxUtil + 15],
        },
        xaxis: { title: { text: '' } },
        showlegend: false,
        height: 300,
        shapes: [
          // Threshold bands
          { type: 'rect', x0: 0, x1: 1, xref: 'paper', y0: 0, y1: 80, fillcolor: GREEN, opacity: 0.05, line: { width: 0 } },
          { type: 'rect', x0: 0, x1: 1, xref: 'paper', y0: 80, y1: 100, fillcolor: AMBER, opacity: 0.05, line: { width: 0 } },
          { type: 'rect', x0: 0, x1: 1, xref: 'paper', y0: 100, y1: maxUtil + 15, fillcolor: RED, opacity: 0.05, line: { width: 0 } },
          // 100% threshold line
          { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 100, y1: 100, line: { dash: 'dash', color: RED, width: 1 }, opacity: 0.5 },
        ],
        annotations: [
          { x: 1, xref: 'paper', y: 100, text: '100% capacity', showarrow: false, font: { color: TEXT_DIM, size: 10 }, xanchor: 'right', yanchor: 'bottom' },
        ],
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
