/**
 * Summary tab component showing overview of all analysis results.
 */

import {
  Box,
  VStack,
  HStack,
  Text,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Divider,
  useColorModeValue,
} from '@chakra-ui/react';

interface SummaryTabProps {
  results: {
    ded?: {
      filename: string;
      epics?: unknown[];
    };
    red_flags?: unknown[];
    capacity_analysis?: Array<{ status: string; utilization_percent: number }>;
    deployment_clusters?: unknown[];
    pi_analysis?: {
      resources?: Record<string, unknown>;
      projects?: Record<string, unknown>;
      sprints?: string[];
    };
  };
  summary: {
    risk: { total: number; critical: number; moderate: number; low: number };
    capacity: { total_sprints: number; passing: number; failing: number };
    deployment: { clusters: number };
  };
}

export default function SummaryTab({ results, summary }: SummaryTabProps) {
  const cardBg = useColorModeValue('white', 'gray.800');

  // Calculate additional metrics
  const redFlagScore = summary.risk.total === 0
    ? 100
    : Math.max(0, 100 - (summary.risk.critical * 20 + summary.risk.moderate * 10 + summary.risk.low * 5));

  const capacityScore = summary.capacity.total_sprints > 0
    ? Math.round((summary.capacity.passing / summary.capacity.total_sprints) * 100)
    : 100;

  const overallScore = Math.round((redFlagScore + capacityScore) / 2);

  const resourceCount = results.pi_analysis?.resources
    ? Object.keys(results.pi_analysis.resources).length
    : 0;

  const projectCount = results.pi_analysis?.projects
    ? Object.keys(results.pi_analysis.projects).length
    : 0;

  const sprintCount = results.pi_analysis?.sprints?.length || 0;

  return (
    <VStack spacing={6} align="stretch">
      {/* Overall Health Score */}
      <Card bg={cardBg}>
        <CardBody>
          <VStack spacing={4}>
            <Heading size="md">PI Health Score</Heading>
            <Box
              w="120px"
              h="120px"
              borderRadius="full"
              border="8px solid"
              borderColor={
                overallScore >= 80 ? 'green.400' :
                overallScore >= 60 ? 'orange.400' : 'red.400'
              }
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              <Text fontSize="3xl" fontWeight="bold">
                {overallScore}
              </Text>
            </Box>
            <Text color="gray.500">
              {overallScore >= 80 ? 'Looking good! Ready for development.' :
               overallScore >= 60 ? 'Some issues to address before starting.' :
               'Significant issues require attention.'}
            </Text>
          </VStack>
        </CardBody>
      </Card>

      {/* Key Metrics Grid */}
      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
        <MetricCard
          label="Red Flags"
          value={summary.risk.total}
          status={summary.risk.critical > 0 ? 'error' : summary.risk.moderate > 0 ? 'warning' : 'success'}
          helpText={`${summary.risk.critical} critical`}
        />
        <MetricCard
          label="Sprint Status"
          value={`${summary.capacity.passing}/${summary.capacity.total_sprints}`}
          status={summary.capacity.failing > 0 ? 'error' : 'success'}
          helpText={summary.capacity.failing > 0 ? `${summary.capacity.failing} overloaded` : 'All passing'}
        />
        <MetricCard
          label="Resources"
          value={resourceCount}
          status="info"
          helpText="Team members"
        />
        <MetricCard
          label="Projects"
          value={projectCount}
          status="info"
          helpText={`Across ${sprintCount} sprints`}
        />
      </SimpleGrid>

      {/* Detailed Breakdown */}
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
        {/* Risk Summary */}
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Heading size="sm">🚩 Risk Analysis</Heading>
          </CardHeader>
          <CardBody pt={0}>
            <VStack align="stretch" spacing={3}>
              <HStack justify="space-between">
                <Text>Total Issues</Text>
                <Badge colorScheme={summary.risk.total > 0 ? 'red' : 'green'}>
                  {summary.risk.total}
                </Badge>
              </HStack>
              <Divider />
              <HStack justify="space-between">
                <Text fontSize="sm">🚨 Critical</Text>
                <Text fontWeight="bold" color="red.500">{summary.risk.critical}</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">⚠️ Moderate</Text>
                <Text fontWeight="bold" color="orange.500">{summary.risk.moderate}</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">💡 Low</Text>
                <Text fontWeight="bold" color="blue.500">{summary.risk.low}</Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Capacity Summary */}
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Heading size="sm">📈 Capacity Analysis</Heading>
          </CardHeader>
          <CardBody pt={0}>
            <VStack align="stretch" spacing={3}>
              <HStack justify="space-between">
                <Text>Total Sprints</Text>
                <Badge>{summary.capacity.total_sprints}</Badge>
              </HStack>
              <Divider />
              <HStack justify="space-between">
                <Text fontSize="sm">✅ Passing</Text>
                <Text fontWeight="bold" color="green.500">{summary.capacity.passing}</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">❌ Overloaded</Text>
                <Text fontWeight="bold" color={summary.capacity.failing > 0 ? 'red.500' : 'green.500'}>
                  {summary.capacity.failing}
                </Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">📊 Capacity Score</Text>
                <Text fontWeight="bold">{capacityScore}%</Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* File Info */}
      {results.ded?.filename && (
        <Card bg={cardBg} size="sm">
          <CardBody>
            <HStack>
              <Text color="gray.500">Analyzed Document:</Text>
              <Badge variant="outline">{results.ded.filename}</Badge>
            </HStack>
          </CardBody>
        </Card>
      )}
    </VStack>
  );
}

// Metric Card Component
function MetricCard({
  label,
  value,
  status,
  helpText,
}: {
  label: string;
  value: string | number;
  status: 'success' | 'warning' | 'error' | 'info';
  helpText?: string;
}) {
  const cardBg = useColorModeValue('white', 'gray.800');
  const statusColors = {
    success: 'green.500',
    warning: 'orange.500',
    error: 'red.500',
    info: 'blue.500',
  };

  return (
    <Card bg={cardBg}>
      <CardBody>
        <Stat>
          <StatLabel>{label}</StatLabel>
          <StatNumber color={statusColors[status]}>{value}</StatNumber>
          {helpText && <StatHelpText>{helpText}</StatHelpText>}
        </Stat>
      </CardBody>
    </Card>
  );
}
