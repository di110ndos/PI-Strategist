/**
 * Grouped bar chart: net capacity vs sprint load per sprint.
 * Ported from charts.py:33-77
 */

import { Box, Text } from '@chakra-ui/react';
import LazyPlot from './LazyPlot';
import { CYAN, BLUE, RED, BORDER, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

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
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
