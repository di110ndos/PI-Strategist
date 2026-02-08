/**
 * Vertical bar chart of cost per sprint.
 * Ported from charts.py:478-524
 */

import { Box, Text } from '@chakra-ui/react';
import LazyPlot from './LazyPlot';
import { CYAN, BORDER, TEXT_MUTED, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface Props {
  /** Map of sprint name -> cost */
  costBySprint: Record<string, number>;
}

export default function SprintCostChart({ costBySprint }: Props) {
  if (!costBySprint || Object.keys(costBySprint).length === 0) return null;

  const entries = Object.entries(costBySprint);
  if (!entries.some(([, v]) => v > 0)) {
    return (
      <Box p={4} textAlign="center">
        <Text color="gray.500">No cost data available.</Text>
      </Box>
    );
  }

  const labels = entries.map(([k]) => k);
  const values = entries.map(([, v]) => v);

  return (
    <LazyPlot
      data={[
        {
          type: 'bar',
          x: labels,
          y: values,
          marker: { color: CYAN, line: { width: 0 } },
          opacity: 0.85,
          text: values.map((v) => `$${v.toLocaleString()}`),
          textposition: 'outside',
          textfont: { color: TEXT_MUTED, size: 11 },
          hovertemplate: '%{x}: $%{y:,.0f}<extra></extra>',
        },
      ]}
      layout={plotlyLayout({
        yaxis: { title: { text: 'Cost ($)' }, gridcolor: BORDER },
        xaxis: { title: { text: '' } },
        showlegend: false,
        height: 380,
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
