/**
 * Gantt-style chart: projects x sprints showing allocation.
 * Ported from roadmap_display.py:59-171
 */

import { Box, Text } from '@chakra-ui/react';
import LazyPlot from './LazyPlot';
import { CHART_PALETTE, BORDER, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface ProjectData {
  total_hours: number;
  priority?: number;
  sprint_allocation?: Record<string, number>;
}

interface Props {
  projects: Record<string, ProjectData>;
  sprints: string[];
}

export default function ProjectTimeline({ projects, sprints }: Props) {
  if (!projects || Object.keys(projects).length === 0 || !sprints || sprints.length === 0) {
    return (
      <Box p={4} textAlign="center">
        <Text color="gray.500">No project timeline data available.</Text>
      </Box>
    );
  }

  const sprintNames = [...sprints].sort();

  // Sort projects by priority then name
  const sortedProjects = Object.entries(projects)
    .filter(([, p]) => p.sprint_allocation && Object.keys(p.sprint_allocation).length > 0)
    .sort(([aName, a], [bName, b]) => {
      const priA = a.priority || 999;
      const priB = b.priority || 999;
      return priA !== priB ? priA - priB : aName.localeCompare(bName);
    })
    .slice(0, 30); // Limit for readability

  if (sortedProjects.length === 0) return null;

  const projectNames = sortedProjects.map(([name]) => name.length > 35 ? name.slice(0, 32) + '...' : name);

  // Build traces per sprint (stacked bars for Gantt effect)
  const traces = sprintNames.map((sprint, si) => ({
    type: 'bar' as const,
    name: sprint,
    y: projectNames,
    x: sortedProjects.map(([, p]) => {
      const hours = p.sprint_allocation?.[sprint] || 0;
      return hours > 0 ? hours : 0;
    }),
    orientation: 'h' as const,
    marker: { color: CHART_PALETTE[si % CHART_PALETTE.length] },
    opacity: 0.85,
    hovertemplate: `%{y}<br>${sprint}: %{x:.0f}h<extra></extra>`,
  }));

  return (
    <LazyPlot
      data={traces}
      layout={plotlyLayout({
        barmode: 'stack',
        height: Math.max(400, sortedProjects.length * 36 + 120),
        xaxis: { title: { text: 'Hours' }, gridcolor: BORDER },
        yaxis: { title: { text: '' }, autorange: 'reversed', automargin: true },
        legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 },
        margin: { l: 10, r: 40, t: 50, b: 40 },
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
