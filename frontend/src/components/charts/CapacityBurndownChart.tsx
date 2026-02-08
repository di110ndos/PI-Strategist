/**
 * Grouped bar chart: net capacity vs sprint load per sprint.
 * Ported from charts.py:33-77
 */

import { Box, Text } from '@chakra-ui/react';
import LazyPlot from './LazyPlot';
import { CYAN, BLUE, RED, AMBER, BORDER, TEXT_DIM, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface SprintData {
  sprint: { name: string; net_capacity: number; sprint_load: number };
}

interface Props {
  analyses: SprintData[];
}

export default function CapacityBurndownChart({ analyses }: Props) {
  if (!analyses || analyses.length === 0) {
    return (
      <Box p={4} textAlign="center">
        <Text color="gray.500">No sprint data available for capacity chart.</Text>
      </Box>
    );
  }

  const sprintNames = analyses.map((a) => a.sprint.name);
  const capacities = analyses.map((a) => a.sprint.net_capacity);
  const loads = analyses.map((a) => a.sprint.sprint_load);

  // Build overflow annotations for sprints that exceed capacity
  const overflowAnnotations: Partial<Plotly.Layout>['annotations'] = [];
  loads.forEach((ld, i) => {
    if (ld > capacities[i]) {
      const overflow = ld - capacities[i];
      overflowAnnotations.push({
        x: sprintNames[i],
        y: ld,
        text: `+${overflow.toFixed(0)}h`,
        showarrow: false,
        font: { color: RED, size: 11, family: 'DM Sans, Inter, sans-serif' },
        yanchor: 'bottom',
        yshift: 4,
      });
    }
  });

  // Max capacity value for the 100% capacity reference line
  const maxCapacity = Math.max(...capacities);

  return (
    <LazyPlot
      data={[
        {
          type: 'bar',
          name: 'Net Capacity',
          x: sprintNames,
          y: capacities,
          marker: { color: CYAN, line: { width: 0 } },
          opacity: 0.85,
        },
        {
          type: 'bar',
          name: 'Sprint Load',
          x: sprintNames,
          y: loads,
          marker: {
            color: loads.map((ld, i) => (ld > capacities[i] ? RED : BLUE)),
            line: { width: 0 },
          },
          opacity: 0.85,
        },
      ]}
      layout={plotlyLayout({
        barmode: 'group',
        yaxis: { title: { text: 'Hours' }, gridcolor: BORDER },
        xaxis: { title: { text: '' } },
        legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 },
        height: 350,
        shapes: [
          // Horizontal dashed line at the average capacity level (100% capacity reference)
          {
            type: 'line',
            x0: 0,
            x1: 1,
            xref: 'paper',
            y0: maxCapacity,
            y1: maxCapacity,
            line: { dash: 'dash', color: AMBER, width: 1.5 },
            opacity: 0.6,
          },
        ],
        annotations: [
          // 100% capacity label
          {
            x: 1,
            xref: 'paper',
            y: maxCapacity,
            text: 'Max Capacity',
            showarrow: false,
            font: { color: TEXT_DIM, size: 10 },
            xanchor: 'right',
            yanchor: 'bottom',
          },
          // Overflow annotations above overloaded bars
          ...overflowAnnotations,
        ],
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
