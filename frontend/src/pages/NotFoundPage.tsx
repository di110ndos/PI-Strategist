/**
 * 404 Not Found page.
 */

import { Box, Heading, Text, Button, VStack } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <Box px={{ base: 4, md: 6, lg: 8 }} py={16} textAlign="center">
      <VStack spacing={6}>
        <Heading size="2xl" color="gray.600">404</Heading>
        <Heading size="md">Page Not Found</Heading>
        <Text color="gray.500" maxW="md">
          The page you are looking for does not exist or has been moved.
        </Text>
        <Button colorScheme="blue" onClick={() => navigate('/')}>
          Go Home
        </Button>
      </VStack>
    </Box>
  );
}
