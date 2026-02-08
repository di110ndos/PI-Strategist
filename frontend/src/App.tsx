/**
 * Main App component with providers and routing.
 */

import { ChakraProvider, extendTheme, type StyleFunctionProps, Box } from '@chakra-ui/react';
import { mode } from '@chakra-ui/theme-tools';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import ErrorBoundary from './components/common/ErrorBoundary';
import AppShell from './components/layout/AppShell';
import HomePage from './pages/HomePage';
import QuickCheckPage from './pages/QuickCheckPage';
import AnalyzePage from './pages/AnalyzePage';
import ScenariosPage from './pages/ScenariosPage';
import ComparePage from './pages/ComparePage';
import ObjectivesPage from './pages/ObjectivesPage';
import RiskRegisterPage from './pages/RiskRegisterPage';
import NotFoundPage from './pages/NotFoundPage';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

// Extend Chakra theme with custom colors
const theme = extendTheme({
  config: {
    initialColorMode: 'system',
    useSystemColorMode: true,
  },
  colors: {
    brand: {
      50: '#e6fffa',
      100: '#b2f5ea',
      200: '#81e6d9',
      300: '#4fd1c5',
      400: '#38b2ac',
      500: '#00e5cc', // Primary cyan
      600: '#00b8a3',
      700: '#008f7a',
      800: '#006751',
      900: '#003f28',
    },
  },
  styles: {
    global: (props: StyleFunctionProps) => ({
      body: {
        bg: mode('white', 'gray.900')(props),
        color: mode('gray.800', 'gray.100')(props),
      },
    }),
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChakraProvider theme={theme}>
        <BrowserRouter>
          <ErrorBoundary>
            <Box minH="100vh">
              <AppShell>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/analyze" element={<AnalyzePage />} />
                  <Route path="/ded" element={<QuickCheckPage />} />
                  <Route path="/quick-check" element={<Navigate to="/ded" replace />} />
                  <Route path="/scenarios" element={<ScenariosPage />} />
                  <Route path="/objectives" element={<ObjectivesPage />} />
                  <Route path="/risks" element={<RiskRegisterPage />} />
                  <Route path="/compare" element={<ComparePage />} />
                  <Route path="*" element={<NotFoundPage />} />
                </Routes>
              </AppShell>
            </Box>
          </ErrorBoundary>
        </BrowserRouter>
      </ChakraProvider>
    </QueryClientProvider>
  );
}

export default App;
