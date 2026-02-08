/**
 * 2D heatmap: resources x sprints showing allocation intensity.
 * Ported from charts.py:234-310
 */

import { Box, Text } from '@chakra-ui/react';
import LazyPlot from './LazyPlot';
import { BLUE, GREEN, AMBER, RED, TEXT_MUTED, TEXT_DIM, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface ResourceData {
  total_hours: number;
  sprint_hours?: Record<string, number>;
}

interface Props {
  resources: Record<string, ResourceData>;
  sprints: string[];
}

const TARGET_HOURS_PER_SPRINT = 122.0;

export default function ResourceHeatmap({ resources, sprints }: Props) {
  if (!resources || Object.keys(resources).length === 0) {
    return (
      <Box p={4} textAlign="center">
        <Text color="gray.500">No resource data available for heatmap.</Text>
      </Box>
    );
  }
  if (!sprints || sprints.length === 0) {
    return (
      <Box p={4} textAlign="center">
        <Text color="gray.500">No sprint data available for heatmap.</Text>
      </Box>
    );
  }

  const sprintNames = [...sprints].sort();
  const resourceNames = Object.entries(resources)
    .sort(([, a], [, b]) => b.total_hours - a.total_hours)
    .slice(0, 25)
    .map(([name]) => name);

  const zData: number[][] = [];
  const hoverText: string[][] = [];

  for (const rname of resourceNames) {
    const resource = resources[rname];
    const row: number[] = [];
    const hoverRow: string[] = [];
    for (const sprint of sprintNames) {
      const hours = resource.sprint_hours?.[sprint] || 0;
      const pct = TARGET_HOURS_PER_SPRINT > 0 ? (hours / TARGET_HOURS_PER_SPRINT) * 100 : 0;
      row.push(pct);
      const status = pct < 80 ? 'Under' : pct <= 105 ? 'OK' : 'Over';
      hoverRow.push(`${rname}<br>${sprint}: ${hours.toFixed(0)}h (${pct.toFixed(0)}%)<br>Status: ${status}`);
    }
    zData.push(row);
    hoverText.push(hoverRow);
  }

  return (
    <LazyPlot
      data={[
        {
          type: 'heatmap',
          z: zData,
          x: sprintNames,
          y: resourceNames,
          hovertext: hoverText as any,
          hovertemplate: '%{hovertext}<extra></extra>',
          zmin: 0,
          zmax: 150,
          colorscale: [
            [0.0, '#1e1e2e'],
            [0.25, BLUE],
            [0.53, GREEN],
            [0.70, GREEN],
            [0.85, AMBER],
            [1.0, RED],
          ] as any,
          colorbar: {
            title: { text: '% of Target', font: { color: TEXT_MUTED } },
            tickfont: { color: TEXT_DIM },
            tickvals: [0, 50, 80, 100, 120, 150],
            ticktext: ['0%', '50%', '80%', '100%', '120%', '150%+'],
          },
        },
      ]}
      layout={plotlyLayout({
        height: Math.max(400, resourceNames.length * 32 + 100),
        xaxis: { title: { text: '' }, side: 'top' },
        yaxis: { title: { text: '' }, autorange: 'reversed', automargin: true },
        margin: { l: 10, r: 40, t: 60, b: 20 },
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
