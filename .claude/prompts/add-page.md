# /add-page — Scaffold a React Page

You are a **UI Engineering Specialist** for PI Strategist. Your job is to create new React pages that follow the established patterns, use Chakra UI, and integrate with the existing layout and routing.

## Context

PI Strategist is a React 19 + TypeScript + Vite app using Chakra UI v2, React Router v7, React Query v5, and Zustand. Pages live in `frontend/src/pages/` and are routed via `App.tsx`. The layout uses `AppShell.tsx` (sticky nav + hamburger drawer) wrapping all routes.

## Architecture

```
frontend/src/
├── App.tsx                               # Providers (Chakra, React Query, Router) + Routes
├── types/index.ts                        # Shared TypeScript types
├── api/
│   ├── client.ts                         # Axios instance
│   └── endpoints/
│       ├── analysis.ts                   # Analysis + AI insights API
│       └── files.ts                      # File upload API
├── hooks/
│   └── useAnalysis.ts                    # React Query mutation/query hooks
├── store/
│   └── analysisStore.ts                  # Zustand store for analysis state
├── components/
│   ├── layout/
│   │   ├── AppShell.tsx                  # Sticky nav + hamburger drawer
│   │   └── NavLink.tsx                   # Nav link component
│   ├── analysis/                         # Tab components for Analyze page
│   ├── charts/                           # Plotly chart components
│   └── common/                           # Shared components (FileUpload, ErrorBoundary)
├── pages/
│   ├── HomePage.tsx                      # Landing page
│   ├── AnalyzePage.tsx                   # File upload + full analysis (tabbed)
│   ├── QuickCheckPage.tsx                # Paste-and-check text analysis
│   ├── ScenariosPage.tsx                 # What-if scenario planning
│   ├── ComparePage.tsx                   # Compare saved analyses
│   └── NotFoundPage.tsx                  # 404 page
```

## Routing

Routes are defined in `App.tsx` inside `<Routes>`:
```tsx
<Route path="/my-page" element={<MyPage />} />
```

Navigation links are defined in `AppShell.tsx` in the `NAV_ITEMS` array:
```tsx
{ to: '/my-page', label: 'My Page', icon: <SomeIcon size={16} /> }
```

## Workflow

1. **Understand the page purpose** — What does the user want to see/do?
2. **Read existing pages** for patterns — Read `QuickCheckPage.tsx` (simplest) and one complex page like `AnalyzePage.tsx`
3. **Read `types/index.ts`** for existing data types
4. **Create the page** in `frontend/src/pages/` following the conventions below
5. **Add the route** in `App.tsx` inside the `<Routes>` block
6. **Add the nav link** in `AppShell.tsx` in the `NAV_ITEMS` array (pick an icon from `lucide-react`)
7. **Add API/hooks** if the page needs backend calls — endpoint in `api/endpoints/`, hook in `hooks/`
8. **Verify** — Run `npm run build` to confirm TypeScript compiles

## Page Template

Every page MUST follow this pattern:

```tsx
/**
 * MyPage — short description.
 */

import {
  Box,
  VStack,
  Heading,
  Text,
  // ... other Chakra imports
} from '@chakra-ui/react';
import { SomeIcon } from 'lucide-react';

export default function MyPage() {
  return (
    <Box px={{ base: 4, md: 6, lg: 8 }} py={6}>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg">Page Title</Heading>
          <Text color="gray.500" mt={1}>Brief description of what this page does.</Text>
        </Box>

        {/* Page content */}
      </VStack>
    </Box>
  );
}
```

## Layout Conventions

- All pages use `Box px={{ base: 4, md: 6, lg: 8 }}` for full-width responsive padding
- Use `VStack spacing={6} align="stretch"` for vertical page layout
- Use `SimpleGrid columns={{ base: 1, md: 2 }}` for responsive grids
- All `TabList` components should have `flexWrap="wrap"` for mobile
- All `Table` components should be wrapped in `<Box overflowX="auto">`
- Icons come from `lucide-react` (tree-shakeable stroke icons)

## State Management

- **Server state**: Use React Query hooks (`useMutation`, `useQuery`) — see `hooks/useAnalysis.ts`
- **Client state**: Use Zustand stores — see `store/analysisStore.ts`
- **Local state**: Use `useState` for component-local UI state

## Rules

- Use Chakra UI components — never raw HTML elements for UI
- Icons from `lucide-react` only — never import from other icon libraries
- All pages get full-width layout with responsive padding (not `Container maxW`)
- Add the route AND the nav link when creating a new page
- Run `npm run build` after making changes
