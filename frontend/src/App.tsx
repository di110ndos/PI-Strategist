/**
 * Main App component with providers and routing.
 */

import { ChakraProvider, extendTheme, Box } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import HomePage from './pages/HomePage';
import QuickCheckPage from './pages/QuickCheckPage';

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
    initialColorMode: 'dark',
    useSystemColorMode: false,
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
    global: {
      body: {
        bg: 'gray.900',
        color: 'gray.100',
      },
    },
  },
});

// Navigation component
function Navigation() {
  return (
    <Box
      as="nav"
      bg="gray.800"
      px={6}
      py={4}
      borderBottom="1px"
      borderColor="gray.700"
    >
      <Box display="flex" gap={6} alignItems="center" maxW="container.xl" mx="auto">
        <Link to="/">
          <Box fontWeight="bold" fontSize="lg" color="brand.500">
            PI Strategist
          </Box>
        </Link>
        <Link to="/quick-check">
          <Box _hover={{ color: 'brand.400' }}>Quick Check</Box>
        </Link>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChakraProvider theme={theme}>
        <BrowserRouter>
          <Box minH="100vh" bg="gray.900">
            <Navigation />
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/quick-check" element={<QuickCheckPage />} />
            </Routes>
          </Box>
        </BrowserRouter>
      </ChakraProvider>
    </QueryClientProvider>
  );
}

export default App;
