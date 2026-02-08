/**
 * Capacity Analysis tab component.
 */

import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  Card,
  CardBody,
  SimpleGrid,
  Progress,
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
  Icon,
  useColorModeValue,
} from '@chakra-ui/react';
import { AlertTriangle } from 'lucide-react';
import { CapacityBurndownChart, UtilizationTrendChart } from '../charts';

interface SprintAnalysis {
  sprint: {
    name: string;
    total_hours: number;
    net_capacity: number;
    sprint_load: number;
    buffer_hours: number;
    tasks: Array<{ id: string; name: string; hours: number }>;
  };
  status: string;
  utilization_percent: number;
  overflow_hours: number;
  high_risk_tasks: Array<{ id: string; name: string; hours: number }>;
  recommendations: Array<{
    task: { id: string; name: string; hours: number };
    from_sprint: string;
    to_sprint: string;
    reason: string;
    priority: number;
  }>;
}

interface CapacityTabProps {
  capacityAnalysis: SprintAnalysis[];
}

export default function CapacityTab({ capacityAnalysis }: CapacityTabProps) {
  if (!capacityAnalysis || capacityAnalysis.length === 0) {
    return (
      <Alert status="info" borderRadius="md">
        <AlertIcon />
        No capacity data available. Upload an Excel capacity planner to see sprint analysis.
      </Alert>
    );
  }

  // Calculate summary
  const totalSprints = capacityAnalysis.length;
  const passingSprints = capacityAnalysis.filter((a) => a.status === 'pass').length;
  const failingSprints = totalSprints - passingSprints;
  const totalCapacity = capacityAnalysis.reduce((sum, a) => sum + a.sprint.net_capacity, 0);
  const totalLoad = capacityAnalysis.reduce((sum, a) => sum + a.sprint.sprint_load, 0);
  const overallUtilization = totalCapacity > 0 ? (totalLoad / totalCapacity) * 100 : 0;

  // Collect all recommendations
  const allRecommendations = capacityAnalysis.flatMap((a) => a.recommendations);

  return (
    <VStack spacing={6} align="stretch">
      {/* Summary Stats */}
      <StatGroup>
        <Stat>
          <StatLabel>Total Sprints</StatLabel>
          <StatNumber>{totalSprints}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Passing</StatLabel>
          <StatNumber color="green.500">{passingSprints}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Overloaded</StatLabel>
          <StatNumber color={failingSprints > 0 ? 'red.500' : 'green.500'}>
            {failingSprints}
          </StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Overall Utilization</StatLabel>
          <StatNumber
            color={
              overallUtilization > 100
                ? 'red.500'
                : overallUtilization > 80
                ? 'orange.500'
                : 'green.500'
            }
          >
            {overallUtilization.toFixed(1)}%
          </StatNumber>
        </Stat>
      </StatGroup>

      {/* Charts */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card>
          <CardBody>
            <Text fontWeight="bold" mb={2}>Capacity vs Load</Text>
            <CapacityBurndownChart analyses={capacityAnalysis} />
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Text fontWeight="bold" mb={2}>Utilization Trend</Text>
            <UtilizationTrendChart analyses={capacityAnalysis} />
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Status Alert */}
      {failingSprints > 0 ? (
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          <Text>
            <strong>{failingSprints} sprint{failingSprints !== 1 ? 's' : ''} overloaded</strong>
            {' '}&mdash; Consider rebalancing tasks or adjusting scope.
          </Text>
        </Alert>
      ) : overallUtilization > 80 ? (
        <Alert status="warning" borderRadius="md">
          <AlertIcon />
          <Text>
            Utilization is high at {overallUtilization.toFixed(1)}%. Limited buffer for unexpected work.
          </Text>
        </Alert>
      ) : (
        <Alert status="success" borderRadius="md">
          <AlertIcon />
          <Text>All sprints within capacity. Healthy utilization at {overallUtilization.toFixed(1)}%.</Text>
        </Alert>
      )}

      {/* Sprint Cards */}
      <Text fontWeight="bold" fontSize="lg">
        Sprint Details
      </Text>
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
        {capacityAnalysis.map((analysis, idx) => (
          <SprintCard key={idx} analysis={analysis} />
        ))}
      </SimpleGrid>

      {/* Recommendations */}
      {allRecommendations.length > 0 && (
        <>
          <Text fontWeight="bold" fontSize="lg" mt={4}>
            Recommendations
          </Text>
          <VStack spacing={3} align="stretch">
            {allRecommendations
              .sort((a, b) => a.priority - b.priority)
              .map((rec, idx) => (
                <RecommendationCard key={idx} recommendation={rec} />
              ))}
          </VStack>
        </>
      )}
    </VStack>
  );
}

// Sprint Card Component
function SprintCard({ analysis }: { analysis: SprintAnalysis }) {
  const { sprint, status, utilization_percent, overflow_hours, high_risk_tasks } = analysis;
  const cardBg = useColorModeValue('white', 'gray.800');
  const isPassing = status === 'pass';

  const progressColor = utilization_percent <= 80 ? 'green' : utilization_percent <= 100 ? 'orange' : 'red';

  return (
    <Card bg={cardBg}>
      <CardBody>
        <VStack align="stretch" spacing={4}>
          {/* Header */}
          <HStack justify="space-between">
            <HStack spacing={2}>
              <Box
                w="10px"
                h="10px"
                borderRadius="full"
                bg={
                  utilization_percent > 105
                    ? 'red.500'
                    : utilization_percent > 100
                    ? 'orange.400'
                    : utilization_percent >= 80
                    ? 'yellow.400'
                    : 'green.400'
                }
                boxShadow={
                  utilization_percent > 105
                    ? '0 0 6px rgba(239,68,68,0.6)'
                    : utilization_percent > 100
                    ? '0 0 6px rgba(251,146,60,0.5)'
                    : utilization_percent >= 80
                    ? '0 0 6px rgba(250,204,21,0.4)'
                    : '0 0 6px rgba(74,222,128,0.4)'
                }
              />
              <Text fontWeight="bold" fontSize="lg">
                {sprint.name}
              </Text>
            </HStack>
            <HStack spacing={2}>
              <Badge
                colorScheme={
                  utilization_percent > 105
                    ? 'red'
                    : utilization_percent > 100
                    ? 'orange'
                    : utilization_percent >= 80
                    ? 'yellow'
                    : 'green'
                }
                variant="subtle"
                fontSize="xs"
              >
                {utilization_percent > 105
                  ? 'Over'
                  : utilization_percent > 100
                  ? 'Near Limit'
                  : utilization_percent >= 80
                  ? 'High'
                  : 'Healthy'}
              </Badge>
              <Badge colorScheme={isPassing ? 'green' : 'red'} fontSize="sm">
                {isPassing ? 'PASS' : 'FAIL'}
              </Badge>
            </HStack>
          </HStack>

          {/* Progress Bar */}
          <Box>
            <Progress
              value={Math.min(utilization_percent, 100)}
              colorScheme={progressColor}
              borderRadius="full"
              size="lg"
            />
            <HStack justify="space-between" mt={1}>
              <Text fontSize="sm" color="gray.500">
                {sprint.sprint_load.toFixed(1)}h / {sprint.net_capacity.toFixed(1)}h
              </Text>
              <Text
                fontSize="sm"
                fontWeight="bold"
                color={`${progressColor}.500`}
              >
                {utilization_percent.toFixed(1)}%
              </Text>
            </HStack>
          </Box>

          {/* Metrics */}
          <SimpleGrid columns={3} spacing={2}>
            <Box>
              <Text fontSize="xs" color="gray.500">
                Net Capacity
              </Text>
              <Text fontWeight="medium">{sprint.net_capacity.toFixed(1)}h</Text>
            </Box>
            <Box>
              <Text fontSize="xs" color="gray.500">
                Sprint Load
              </Text>
              <Text fontWeight="medium">{sprint.sprint_load.toFixed(1)}h</Text>
            </Box>
            <Box>
              <Text fontSize="xs" color="gray.500">
                Overflow
              </Text>
              <Text
                fontWeight="medium"
                color={overflow_hours > 0 ? 'red.500' : 'green.500'}
              >
                {overflow_hours > 0 ? '+' : ''}{overflow_hours.toFixed(1)}h
              </Text>
            </Box>
          </SimpleGrid>

          {/* Task count */}
          <Text fontSize="sm" color="gray.500">
            Tasks: {sprint.tasks.length} | Buffer: {sprint.buffer_hours.toFixed(1)}h
          </Text>

          {/* High Risk Tasks */}
          {high_risk_tasks.length > 0 && (
            <Accordion allowToggle size="sm">
              <AccordionItem border="none">
                <AccordionButton px={0}>
                  <HStack spacing={1}>
                    <Icon as={AlertTriangle} boxSize={4} color="orange.400" />
                    <Text fontSize="sm" color="orange.400">
                      High Risk Tasks ({high_risk_tasks.length})
                    </Text>
                  </HStack>
                  <AccordionIcon ml={2} />
                </AccordionButton>
                <AccordionPanel px={0}>
                  <VStack align="stretch" spacing={1}>
                    {high_risk_tasks.map((task, idx) => (
                      <Text key={idx} fontSize="sm">
                        &bull; <strong>{task.id}</strong>: {task.name} ({task.hours}h)
                      </Text>
                    ))}
                  </VStack>
                </AccordionPanel>
              </AccordionItem>
            </Accordion>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

// Recommendation Card Component
function RecommendationCard({
  recommendation,
}: {
  recommendation: {
    task: { id: string; name: string; hours: number };
    from_sprint: string;
    to_sprint: string;
    reason: string;
    priority: number;
  };
}) {
  const cardBg = useColorModeValue('gray.50', 'gray.700');
  const priorityColors: Record<number, string> = {
    1: 'red',
    2: 'orange',
    3: 'blue',
  };
  const priorityLabels: Record<number, string> = {
    1: 'High',
    2: 'Medium',
    3: 'Low',
  };

  return (
    <Card bg={cardBg} size="sm">
      <CardBody>
        <HStack justify="space-between" flexWrap="wrap">
          <VStack align="start" spacing={1}>
            <Text fontWeight="medium">
              Move task <Badge>{recommendation.task.id}</Badge> from{' '}
              {recommendation.from_sprint} &rarr; {recommendation.to_sprint}
            </Text>
            <Text fontSize="sm" color="gray.500">
              {recommendation.reason}
            </Text>
            <Text fontSize="xs" color="gray.400">
              Task: {recommendation.task.name} ({recommendation.task.hours}h)
            </Text>
          </VStack>
          <Badge colorScheme={priorityColors[recommendation.priority] || 'gray'}>
            Priority: {priorityLabels[recommendation.priority] || 'Unknown'}
          </Badge>
        </HStack>
      </CardBody>
    </Card>
  );
}
