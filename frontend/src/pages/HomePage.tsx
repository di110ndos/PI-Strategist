/**
 * Home Page - Landing page with navigation to features.
 */

import {
  Box,
  Container,
  Heading,
  Text,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  VStack,
  Button,
  useColorModeValue,
} from '@chakra-ui/react';
import { Link } from 'react-router-dom';

// Feature cards data
const features = [
  {
    title: 'Quick Check',
    description: 'Paste text to quickly analyze for red flags, obligations, and SLA metrics.',
    path: '/quick-check',
    icon: '⚡',
    color: 'blue',
  },
  {
    title: 'Full Analysis',
    description: 'Upload DED documents and Excel capacity planners for comprehensive analysis.',
    path: '/analyze',
    icon: '📊',
    color: 'green',
  },
  {
    title: 'Scenarios',
    description: 'Run what-if scenarios to explore capacity and resource options.',
    path: '/scenarios',
    icon: '🔮',
    color: 'purple',
    disabled: true,
  },
  {
    title: 'Compare',
    description: 'Compare saved analyses to track changes over time.',
    path: '/compare',
    icon: '📈',
    color: 'orange',
    disabled: true,
  },
];

export default function HomePage() {
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  return (
    <Box bg={bgColor} minH="100vh">
      <Container maxW="container.xl" py={12}>
        <VStack spacing={12} align="stretch">
          {/* Hero Section */}
          <VStack spacing={4} textAlign="center">
            <Heading size="2xl">PI Strategist</Heading>
            <Text fontSize="xl" color="gray.500" maxW="2xl">
              Analyze PI planning documents for risks, capacity issues, and deployment strategies.
              Get actionable insights to improve your sprint planning.
            </Text>
          </VStack>

          {/* Feature Cards */}
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
            {features.map((feature) => (
              <Card
                key={feature.path}
                bg={cardBg}
                opacity={feature.disabled ? 0.6 : 1}
                cursor={feature.disabled ? 'not-allowed' : 'pointer'}
                _hover={feature.disabled ? {} : { transform: 'translateY(-2px)', shadow: 'lg' }}
                transition="all 0.2s"
              >
                <CardHeader>
                  <VStack align="start" spacing={2}>
                    <Text fontSize="3xl">{feature.icon}</Text>
                    <Heading size="md">{feature.title}</Heading>
                  </VStack>
                </CardHeader>
                <CardBody pt={0}>
                  <VStack align="start" spacing={4}>
                    <Text color="gray.500">{feature.description}</Text>
                    {feature.disabled ? (
                      <Button size="sm" isDisabled>
                        Coming Soon
                      </Button>
                    ) : (
                      <Button
                        as={Link}
                        to={feature.path}
                        size="sm"
                        colorScheme={feature.color}
                      >
                        Get Started
                      </Button>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>

          {/* Info Section */}
          <Card bg={cardBg}>
            <CardBody>
              <VStack spacing={4} textAlign="center">
                <Heading size="sm">About PI Strategist</Heading>
                <Text color="gray.500" maxW="3xl">
                  PI Strategist helps agile teams identify risks in their PI planning documents.
                  It detects vague acceptance criteria, tracks obligations, validates SLA metrics,
                  analyzes capacity, and suggests deployment strategies.
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </VStack>
      </Container>
    </Box>
  );
}
