/**
 * Global error boundary — catches render errors and shows a friendly fallback.
 */

import { Component } from 'react';
import type { ReactNode, ErrorInfo } from 'react';
import { Box, Heading, Text, Button, VStack, Alert, AlertIcon } from '@chakra-ui/react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box px={{ base: 4, md: 6, lg: 8 }} py={16} textAlign="center">
          <VStack spacing={6}>
            <Alert status="error" borderRadius="md" maxW="lg" mx="auto">
              <AlertIcon />
              Something went wrong rendering this page.
            </Alert>
            <Heading size="md">Unexpected Error</Heading>
            <Text color="gray.500" maxW="md">
              The application encountered an error. You can try reloading the page
              or returning to the home page.
            </Text>
            {this.state.error && (
              <Text fontSize="sm" color="red.400" fontFamily="mono" maxW="lg">
                {this.state.error.message}
              </Text>
            )}
            <VStack spacing={3}>
              <Button colorScheme="blue" onClick={this.handleReset}>
                Try Again
              </Button>
              <Button variant="outline" as="a" href="/">
                Go Home
              </Button>
            </VStack>
          </VStack>
        </Box>
      );
    }

    return this.props.children;
  }
}
