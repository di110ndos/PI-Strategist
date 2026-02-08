/**
 * 5x5 Risk Heat Map — Probability (y-axis) vs Impact (x-axis).
 * Cell color: green (low, 1-6) -> yellow (medium, 7-12) -> orange (high, 13-18) -> red (critical, 19-25).
 */

import { Box, Text } from '@chakra-ui/react';
import LazyPlot from './LazyPlot';
import { plotlyLayout, PLOTLY_CONFIG, TEXT_MUTED, TEXT_DIM } from './plotlyDefaults';
import type { Risk } from '../../types';

interface Props {
  risks: Risk[];
}

export default function RiskHeatMap({ risks }: Props) {
  if (!risks || risks.length === 0) {
    return (
      <Box p={4} textAlign="center">
        <Text color="gray.500">No risk data available for heat map.</Text>
      </Box>
    );
  }

  // Build 5x5 grid: rows = probability (1-5), cols = impact (1-5)
  const grid: number[][] = Array.from({ length: 5 }, () => Array(5).fill(0));

  for (const risk of risks) {
    const pIdx = Math.min(Math.max(risk.probability, 1), 5) - 1;
    const iIdx = Math.min(Math.max(risk.impact, 1), 5) - 1;
    grid[pIdx][iIdx]++;
  }

  // Build hover text
  const hoverText: string[][] = [];
  for (let p = 0; p < 5; p++) {
    const row: string[] = [];
    for (let i = 0; i < 5; i++) {
      const score = (p + 1) * (i + 1);
      row.push(
        `Probability: ${p + 1}<br>Impact: ${i + 1}<br>Risk Score: ${score}<br>Count: ${grid[p][i]}`
      );
    }
    hoverText.push(row);
  }

  // Build color matrix based on risk score (probability * impact)
  const colorMatrix: number[][] = [];
  for (let p = 0; p < 5; p++) {
    const row: number[] = [];
    for (let i = 0; i < 5; i++) {
      row.push((p + 1) * (i + 1));
    }
    colorMatrix.push(row);
  }

  // Annotation text (show count in each cell, or empty for 0)
  const annotations: Partial<Plotly.Annotations>[] = [];
  for (let p = 0; p < 5; p++) {
    for (let i = 0; i < 5; i++) {
      annotations.push({
        x: i,
        y: p,
        text: grid[p][i] > 0 ? String(grid[p][i]) : '',
        showarrow: false,
        font: { color: '#ffffff', size: 16, family: 'DM Sans, Inter, sans-serif' },
        xref: 'x',
        yref: 'y',
      });
    }
  }

  const labels = ['1', '2', '3', '4', '5'];

  return (
    <LazyPlot
      data={[
        {
          type: 'heatmap',
          z: colorMatrix,
          x: labels,
          y: labels,
          hovertext: hoverText as any,
          hovertemplate: '%{hovertext}<extra></extra>',
          zmin: 1,
          zmax: 25,
          colorscale: [
            [0.0, '#22c55e'],
            [0.24, '#22c55e'],
            [0.28, '#eab308'],
            [0.48, '#eab308'],
            [0.52, '#f97316'],
            [0.72, '#f97316'],
            [0.76, '#ef4444'],
            [1.0, '#ef4444'],
          ] as any,
          showscale: true,
          colorbar: {
            title: { text: 'Risk Score', font: { color: TEXT_MUTED } },
            tickfont: { color: TEXT_DIM },
            tickvals: [3, 9, 15, 22],
            ticktext: ['Low', 'Medium', 'High', 'Critical'],
          },
        },
      ]}
      layout={plotlyLayout({
        height: 380,
        xaxis: {
          title: { text: 'Impact' },
          tickvals: [0, 1, 2, 3, 4],
          ticktext: ['1', '2', '3', '4', '5'],
        },
        yaxis: {
          title: { text: 'Probability' },
          tickvals: [0, 1, 2, 3, 4],
          ticktext: ['1', '2', '3', '4', '5'],
        },
        annotations,
        margin: { l: 60, r: 80, t: 20, b: 50 },
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
