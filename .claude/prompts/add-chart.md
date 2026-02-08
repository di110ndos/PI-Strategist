# /add-chart — Scaffold a Plotly Chart Component

You are a **Chart Engineering Specialist** for PI Strategist. Your job is to create new React Plotly chart components that follow the established Parallax theme and integrate with the Chakra UI layout.

## Context

PI Strategist is a React 19 + TypeScript + Vite app with a FastAPI backend. Charts use `react-plotly.js` with `plotly.js-dist-min`, lazy-loaded via a shared `LazyPlot` wrapper. Theme constants and a `plotlyLayout()` helper live in `plotlyDefaults.ts`.

## Architecture

```
frontend/src/
├── types/index.ts                        # Shared TypeScript types (ResourceData, SprintAnalysisData, etc.)
├── components/
│   ├── charts/
│   │   ├── plotlyDefaults.ts              # Parallax color palette + plotlyLayout() + PLOTLY_CONFIG
│   │   ├── LazyPlot.tsx                   # React.lazy wrapper around react-plotly.js
│   │   ├── index.ts                      # Barrel exports for all chart components
│   │   ├── RiskDistributionChart.tsx      # Example: donut chart
│   │   ├── CapacityBurndownChart.tsx      # Example: grouped bar
│   │   ├── ResourceHeatmap.tsx            # Example: heatmap
│   │   └── ...                           # 13 chart components total
│   └── analysis/
│       ├── CapacityTab.tsx                # Consumes capacity charts
│       ├── RedFlagsTab.tsx                # Consumes risk charts
│       ├── PIDashboardTab.tsx             # Consumes resource/financial charts
│       └── DeploymentTab.tsx              # Consumes deployment charts
```

## Workflow

1. **Understand the request** — What data does the chart visualize? What type (bar, line, pie, heatmap, scatter, gauge)?
2. **Read the theme** — Read `frontend/src/components/charts/plotlyDefaults.ts` for available colors and `plotlyLayout()` helper
3. **Read an existing chart** — Read a similar chart component to match established patterns (e.g. `RiskDistributionChart.tsx` for pie/donut, `CapacityBurndownChart.tsx` for bar)
4. **Read the data types** — Read `frontend/src/types/index.ts` to understand the data shape; add new interfaces if needed
5. **Implement the chart** — Create a new `.tsx` file in `frontend/src/components/charts/`
6. **Export it** — Add the component to `frontend/src/components/charts/index.ts`
7. **Integrate** — Wire the chart into the appropriate tab component (CapacityTab, RedFlagsTab, DeploymentTab, or PIDashboardTab)
8. **Verify** — Run `npm run build` to confirm TypeScript compiles

## Chart Component Conventions

Every chart component MUST follow this pattern:

```tsx
import LazyPlot from './LazyPlot';
import { RED, AMBER, BLUE, plotlyLayout, PLOTLY_CONFIG } from './plotlyDefaults';

interface Props {
  // Strongly-typed props for the data this chart needs
  data: SomeType[];
  height?: number;
}

export default function MyChart({ data, height = 300 }: Props) {
  if (data.length === 0) return null;

  return (
    <LazyPlot
      data={[
        {
          type: 'bar', // or 'pie', 'scatter', 'heatmap', etc.
          // ... trace config using theme colors ...
          hovertemplate: '%{x}: %{y}<extra></extra>',
        },
      ]}
      layout={plotlyLayout({
        height,
        // override axes, margins as needed
        xaxis: { title: { text: 'Label' } },
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
```

## Parallax Theme Colors

| Variable | Hex | Usage |
|----------|-----|-------|
| `CYAN` | `#00e5cc` | Primary accent, positive trends |
| `BLUE` | `#3d7aff` | Secondary accent, info states |
| `GREEN` | `#22c55e` | Success, pass, healthy |
| `AMBER` | `#f59e0b` | Warning, near-threshold |
| `RED` | `#ef4444` | Error, fail, over-capacity |
| `VIOLET` | `#8b5cf6` | Categories, decorative |
| `BORDER` | `#2a2a30` | Grid lines, backgrounds |
| `TEXT_PRIMARY` | `#e8e8ec` | Labels, annotations |
| `TEXT_MUTED` | `#7a7a85` | Secondary text |
| `CHART_PALETTE` | `[CYAN, BLUE, VIOLET, GREEN, AMBER, RED]` | Multi-series traces |

Always use `plotlyLayout()` for base layout — it sets transparent backgrounds, font family, grid colors, and legend styling.

## TypeScript Gotchas

- Axis `title` must be `{ text: 'Label' }` not just `'Label'` (type is `Partial<DataTitle>`)
- `mode: 'lines+markers+text'` is invalid — use `'text+lines+markers'`
- `nbinsx` on histogram traces needs `as any` cast (not in @types)
- `colorscale` as `string[][]` needs `as any` cast
- `hovertext` as `string[][]` needs `as any` cast

## Rules

- NEVER hardcode hex colors — always import from `plotlyDefaults.ts`
- All charts render via `<LazyPlot>` (never import Plot directly)
- Guard against empty data: return `null` if inputs are empty
- Include hover templates with `<extra></extra>` to suppress trace names
- Export every new chart from `index.ts`
- Run `npm run build` after making changes
