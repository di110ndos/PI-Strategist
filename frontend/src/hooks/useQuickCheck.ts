/**
 * React Query hook for quick check analysis.
 */

import { useMutation } from '@tanstack/react-query';
import { quickCheckApi, type QuickCheckRequest } from '../api/endpoints/quickCheck';
import type { QuickCheckResponse } from '../types';

export function useQuickCheck() {
  return useMutation<QuickCheckResponse, Error, QuickCheckRequest>({
    mutationFn: quickCheckApi.analyze,
  });
}

export default useQuickCheck;
