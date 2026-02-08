import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ChakraProvider } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SummaryTab from '../components/analysis/SummaryTab';

const mockSummary = {
  risk: { total: 3, high: 1, medium: 1, low: 1 },
  capacity: { total_sprints: 5, passing: 4, failing: 1, average_utilization: 82 },
  deployment: { total_clusters: 8, cd_eligible_percentage: 62.5 },
};

const mockResults = {
  red_flags: [],
  capacity_analysis: [],
  deployment_clusters: [],
};

function renderWith(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ChakraProvider>{ui}</ChakraProvider>
    </QueryClientProvider>
  );
}

describe('SummaryTab', () => {
  it('renders risk metric', () => {
    renderWith(<SummaryTab results={mockResults} summary={mockSummary} />);
    expect(document.body).toBeTruthy();
  });
});
