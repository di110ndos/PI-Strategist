/**
 * Quick Check Page - Analyze text for red flags, obligations, and SLA metrics.
 */

import { useState } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  Textarea,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  VStack,
  HStack,
  Badge,
  Card,
  CardBody,
  CardHeader,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Alert,
  AlertIcon,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Code,
  Spinner,
  useColorModeValue,
} from '@chakra-ui/react';
import { useQuickCheck } from '../hooks/useQuickCheck';
import type { QuickCheckResponse, RedFlagItem } from '../types';

// Sample text for demo
const SAMPLE_TEXT = `The system shall be fast and user-friendly.
The application must handle all requests efficiently.
Users should be able to login quickly.
The API will respond in a timely manner.
System uptime shall be 99.9%.
Response time must be under 200ms.
The solution should be scalable and secure.`;

// Severity colors
const severityColors: Record<string, string> = {
  critical: 'red',
  moderate: 'orange',
  low: 'blue',
};

export default function QuickCheckPage() {
  const [text, setText] = useState('');
  const [results, setResults] = useState<QuickCheckResponse | null>(null);

  const { mutate: analyze, isPending } = useQuickCheck();

  const handleAnalyze = () => {
    if (!text.trim()) return;

    analyze(
      { text },
      {
        onSuccess: (data) => {
          setResults(data);
        },
        onError: (error) => {
          console.error('Analysis failed:', error);
        },
      }
    );
  };

  const handleLoadSample = () => {
    setText(SAMPLE_TEXT);
  };

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Quick Check
          </Heading>
          <Text color="gray.500">
            Paste acceptance criteria or requirements text to analyze for red flags,
            obligations, and SLA metrics.
          </Text>
        </Box>

        {/* Input Section */}
        <Card bg={cardBg}>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste your acceptance criteria here..."
                minH="200px"
                fontFamily="mono"
                fontSize="sm"
              />
              <HStack>
                <Button
                  colorScheme="blue"
                  onClick={handleAnalyze}
                  isLoading={isPending}
                  loadingText="Analyzing..."
                  isDisabled={!text.trim()}
                >
                  Analyze
                </Button>
                <Button variant="outline" onClick={handleLoadSample}>
                  Load Sample
                </Button>
                {text && (
                  <Button variant="ghost" onClick={() => setText('')}>
                    Clear
                  </Button>
                )}
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Loading State */}
        {isPending && (
          <Box textAlign="center" py={8}>
            <Spinner size="xl" color="blue.500" />
            <Text mt={4} color="gray.500">
              Analyzing text...
            </Text>
          </Box>
        )}

        {/* Results */}
        {results && !isPending && (
          <VStack spacing={6} align="stretch">
            {/* Summary Stats */}
            <StatGroup>
              <Stat>
                <StatLabel>Red Flags</StatLabel>
                <StatNumber color="red.500">
                  {results.summary.red_flags.total}
                </StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Critical</StatLabel>
                <StatNumber color="red.600">
                  {results.summary.red_flags.critical}
                </StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Obligations</StatLabel>
                <StatNumber color="purple.500">
                  {results.summary.obligations.total}
                </StatNumber>
              </Stat>
              <Stat>
                <StatLabel>SLA Metrics</StatLabel>
                <StatNumber color="green.500">
                  {results.summary.sla.total}
                </StatNumber>
              </Stat>
            </StatGroup>

            {/* Tabs for Results */}
            <Tabs colorScheme="blue" bg={cardBg} borderRadius="lg" p={4}>
              <TabList>
                <Tab>
                  Red Flags{' '}
                  <Badge ml={2} colorScheme="red">
                    {results.summary.red_flags.total}
                  </Badge>
                </Tab>
                <Tab>
                  Obligations{' '}
                  <Badge ml={2} colorScheme="purple">
                    {results.summary.obligations.total}
                  </Badge>
                </Tab>
                <Tab>
                  SLA/SLO{' '}
                  <Badge ml={2} colorScheme="green">
                    {results.summary.sla.total}
                  </Badge>
                </Tab>
              </TabList>

              <TabPanels>
                {/* Red Flags Tab */}
                <TabPanel>
                  {results.red_flags.length === 0 ? (
                    <Alert status="success">
                      <AlertIcon />
                      No red flags detected in your text!
                    </Alert>
                  ) : (
                    <Accordion allowMultiple>
                      {results.red_flags.map((lineFlags, idx) => (
                        <AccordionItem key={idx}>
                          <AccordionButton>
                            <Box flex="1" textAlign="left">
                              <HStack>
                                <Text fontWeight="medium" noOfLines={1}>
                                  Line {lineFlags.line_number}
                                </Text>
                                {lineFlags.flags.map((flag, i) => (
                                  <Badge
                                    key={i}
                                    colorScheme={severityColors[flag.severity]}
                                  >
                                    {flag.term}
                                  </Badge>
                                ))}
                              </HStack>
                            </Box>
                            <AccordionIcon />
                          </AccordionButton>
                          <AccordionPanel>
                            <VStack align="stretch" spacing={4}>
                              <Code p={2} display="block" whiteSpace="pre-wrap">
                                {lineFlags.line}
                              </Code>
                              {lineFlags.flags.map((flag, i) => (
                                <RedFlagCard key={i} flag={flag} />
                              ))}
                            </VStack>
                          </AccordionPanel>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  )}
                </TabPanel>

                {/* Obligations Tab */}
                <TabPanel>
                  {results.obligations.total === 0 ? (
                    <Alert status="info">
                      <AlertIcon />
                      No obligation statements found.
                    </Alert>
                  ) : (
                    <VStack align="stretch" spacing={4}>
                      <HStack spacing={4}>
                        <Badge colorScheme="red">
                          Binding: {results.obligations.binding_count}
                        </Badge>
                        <Badge colorScheme="orange">
                          Commitment: {results.obligations.commitment_count}
                        </Badge>
                        <Badge colorScheme="gray">
                          Negative: {results.obligations.negative_count}
                        </Badge>
                      </HStack>
                      {results.obligations.obligations.map((ob, idx) => (
                        <Card key={idx} size="sm">
                          <CardBody>
                            <HStack justify="space-between" mb={2}>
                              <Badge>{ob.obligation_type}</Badge>
                              <Code>{ob.keyword}</Code>
                            </HStack>
                            <Text>{ob.text}</Text>
                          </CardBody>
                        </Card>
                      ))}
                    </VStack>
                  )}
                </TabPanel>

                {/* SLA Tab */}
                <TabPanel>
                  {results.sla.total === 0 ? (
                    <Alert status="info">
                      <AlertIcon />
                      No SLA/SLO metrics found.
                    </Alert>
                  ) : (
                    <VStack align="stretch" spacing={4}>
                      <HStack spacing={4}>
                        <Badge colorScheme="green">
                          Valid: {results.sla.valid_count}
                        </Badge>
                        <Badge colorScheme="red">
                          Invalid: {results.sla.invalid_count}
                        </Badge>
                      </HStack>
                      {results.sla.findings.map((finding, idx) => (
                        <Card key={idx} size="sm">
                          <CardBody>
                            <HStack justify="space-between" mb={2}>
                              <Badge
                                colorScheme={finding.is_valid ? 'green' : 'red'}
                              >
                                {finding.metric_type}
                              </Badge>
                              {finding.value && <Code>{finding.value}</Code>}
                            </HStack>
                            <Text>{finding.text}</Text>
                            {finding.issues.length > 0 && (
                              <Alert status="warning" mt={2} size="sm">
                                <AlertIcon />
                                {finding.issues.join(', ')}
                              </Alert>
                            )}
                          </CardBody>
                        </Card>
                      ))}
                    </VStack>
                  )}
                </TabPanel>
              </TabPanels>
            </Tabs>
          </VStack>
        )}
      </VStack>
    </Container>
  );
}

// Red Flag Card Component
function RedFlagCard({ flag }: { flag: RedFlagItem }) {
  const cardBg = useColorModeValue('gray.50', 'gray.700');

  return (
    <Card bg={cardBg} size="sm">
      <CardHeader pb={2}>
        <HStack justify="space-between">
          <HStack>
            <Badge colorScheme={severityColors[flag.severity]} fontSize="sm">
              {flag.severity.toUpperCase()}
            </Badge>
            <Code fontWeight="bold">{flag.term}</Code>
          </HStack>
          <Text fontSize="sm" color="gray.500">
            {flag.category}
          </Text>
        </HStack>
      </CardHeader>
      <CardBody pt={0}>
        <VStack align="stretch" spacing={3}>
          <Box>
            <Text fontSize="sm" fontWeight="medium" color="gray.500">
              Suggested Replacement:
            </Text>
            <Code p={2} display="block" colorScheme="green">
              {flag.suggested_metric}
            </Code>
          </Box>
          <Box>
            <Text fontSize="sm" fontWeight="medium" color="gray.500">
              How to Discuss:
            </Text>
            <Text fontSize="sm" fontStyle="italic">
              {flag.negotiation_script}
            </Text>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
}
