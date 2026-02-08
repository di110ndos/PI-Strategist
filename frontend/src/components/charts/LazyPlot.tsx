/**
 * Lazy-loaded Plotly wrapper with Skeleton fallback.
 */

import React, { Suspense } from 'react';
import { Skeleton } from '@chakra-ui/react';
import type { PlotParams } from 'react-plotly.js';

const Plot = React.lazy(() => import('react-plotly.js'));

export default function LazyPlot(props: PlotParams) {
  return (
    <Suspense fallback={<Skeleton height={props.style?.height || '300px'} borderRadius="md" />}>
      <Plot {...props} />
    </Suspense>
  );
}
