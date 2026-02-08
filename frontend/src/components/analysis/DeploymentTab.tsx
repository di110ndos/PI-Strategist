/**
 * Deployment Analysis tab component.
 */

import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  Card,
  CardBody,
  CardHeader,
  SimpleGrid,
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
import { Flag, Rocket, Bird, RefreshCw } from 'lucide-react';
import { DeploymentReadinessGauge, DeploymentStrategyChart } from '../charts';

interface DeploymentCluster {
  name: string;
  strategy: string;
  tasks: Array<{ id: string; name: string; hours: number }>;
  deploy_timing?: string;
  dependencies?: string[];
  rollback_plan?: string;
}

interface DeploymentTabProps {
  deploymentClusters: DeploymentCluster[];
}

const strategyColors: Record<string, string> = {
  feature_flag: 'purple',
  full_deployment: 'green',
  canary: 'blue',
  blue_green: 'cyan',
};

const strategyIcons: Record<string, typeof Flag> = {
  feature_flag: Flag,
  full_deployment: Rocket,
  canary: Bird,
  blue_green: RefreshCw,
};

export default function DeploymentTab({ deploymentClusters }: DeploymentTabProps) {
  const cardBg = useColorModeValue('white', 'gray.800');

  if (!deploymentClusters || deploymentClusters.length === 0) {
    return (
      <Alert status="info" borderRadius="md">
        <AlertIcon />
        No deployment clusters available. Upload an Excel capacity planner to see deployment analysis.
      </Alert>
    );
  }

  // Calculate stats
  const totalClusters = deploymentClusters.length;
  const totalTasks = deploymentClusters.reduce((sum, c) => sum + c.tasks.length, 0);

  // Count by strategy
  const strategyCount: Record<string, number> = {};
  const strategyTasks: Record<string, number> = {};
  deploymentClusters.forEach((cluster) => {
    const strategy = cluster.strategy || 'unknown';
    strategyCount[strategy] = (strategyCount[strategy] || 0) + 1;
    strategyTasks[strategy] = (strategyTasks[strategy] || 0) + cluster.tasks.length;
  });

  const featureFlagTasks = strategyTasks['feature_flag'] || 0;
  const cdPercentage = totalTasks > 0 ? (featureFlagTasks / totalTasks) * 100 : 0;

  return (
    <VStack spacing={6} align="stretch">
      {/* Summary Stats */}
      <StatGroup>
        <Stat>
          <StatLabel>Total Clusters</StatLabel>
          <StatNumber>{totalClusters}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Total Tasks</StatLabel>
          <StatNumber>{totalTasks}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>CD Eligible</StatLabel>
          <StatNumber color="purple.500">{cdPercentage.toFixed(1)}%</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Feature Flags</StatLabel>
          <StatNumber color="purple.500">{strategyCount['feature_flag'] || 0}</StatNumber>
        </Stat>
      </StatGroup>

      {/* Gauge + Strategy Chart */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card bg={cardBg}>
          <CardBody>
            <Text fontWeight="bold" mb={2}>Continuous Delivery Readiness</Text>
            <DeploymentReadinessGauge percentage={cdPercentage} />
          </CardBody>
        </Card>
        <Card bg={cardBg}>
          <CardBody>
            <Text fontWeight="bold" mb={2}>Strategy Distribution</Text>
            <DeploymentStrategyChart clusters={deploymentClusters} />
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Strategy Breakdown */}
      <Card bg={cardBg}>
        <CardHeader pb={2}>
          <Text fontWeight="bold">Strategy Breakdown</Text>
        </CardHeader>
        <CardBody pt={0}>
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            {Object.entries(strategyCount).map(([strategy, count]) => {
              const StratIcon = strategyIcons[strategy] || Rocket;
              return (
                <Box key={strategy} p={3} borderRadius="md" bg={useColorModeValue('gray.50', 'gray.700')}>
                  <HStack>
                    <Icon as={StratIcon} boxSize={5} />
                    <VStack align="start" spacing={0}>
                      <Text fontSize="sm" color="gray.500" textTransform="capitalize">
                        {strategy.replace('_', ' ')}
                      </Text>
                      <Text fontWeight="bold">{count} clusters</Text>
                      <Text fontSize="xs" color="gray.400">
                        {strategyTasks[strategy] || 0} tasks
                      </Text>
                    </VStack>
                  </HStack>
                </Box>
              );
            })}
          </SimpleGrid>
        </CardBody>
      </Card>

      {/* Cluster Details */}
      <Text fontWeight="bold" fontSize="lg">
        Deployment Clusters
      </Text>

      <Accordion allowMultiple>
        {deploymentClusters.map((cluster, idx) => {
          const StratIcon = strategyIcons[cluster.strategy] || Rocket;
          return (
            <AccordionItem key={idx} border="none" mb={2}>
              <AccordionButton
                bg={useColorModeValue('gray.100', 'gray.700')}
                borderRadius="md"
                _hover={{ bg: useColorModeValue('gray.200', 'gray.600') }}
              >
                <Box flex="1" textAlign="left">
                  <HStack>
                    <Icon as={StratIcon} boxSize={5} />
                    <Text fontWeight="bold">{cluster.name}</Text>
                    <Badge colorScheme={strategyColors[cluster.strategy] || 'gray'}>
                      {(cluster.strategy || 'unknown').replace('_', ' ')}
                    </Badge>
                    <Badge variant="outline">{cluster.tasks.length} tasks</Badge>
                  </HStack>
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel pb={4}>
                <ClusterDetails cluster={cluster} />
              </AccordionPanel>
            </AccordionItem>
          );
        })}
      </Accordion>
    </VStack>
  );
}

// Cluster Details Component
function ClusterDetails({ cluster }: { cluster: DeploymentCluster }) {
  const cardBg = useColorModeValue('gray.50', 'gray.700');

  return (
    <VStack align="stretch" spacing={4} mt={2}>
      {/* Tasks */}
      <Box>
        <Text fontWeight="medium" mb={2}>Tasks in this cluster:</Text>
        <VStack align="stretch" spacing={1}>
          {cluster.tasks.map((task, idx) => (
            <HStack key={idx} justify="space-between" p={2} bg={cardBg} borderRadius="md">
              <Text fontSize="sm">
                <Badge mr={2}>{task.id}</Badge>
                {task.name}
              </Text>
              <Text fontSize="sm" color="gray.500">{task.hours}h</Text>
            </HStack>
          ))}
        </VStack>
      </Box>

      {/* Deploy Timing */}
      {cluster.deploy_timing && (
        <Box>
          <Text fontWeight="medium" mb={1}>Deploy Timing:</Text>
          <Text fontSize="sm" color="gray.500">{cluster.deploy_timing}</Text>
        </Box>
      )}

      {/* Dependencies */}
      {cluster.dependencies && cluster.dependencies.length > 0 && (
        <Box>
          <Text fontWeight="medium" mb={1}>Dependencies:</Text>
          <HStack spacing={2} flexWrap="wrap">
            {cluster.dependencies.map((dep, idx) => (
              <Badge key={idx} variant="outline">{dep}</Badge>
            ))}
          </HStack>
        </Box>
      )}

      {/* Rollback Plan */}
      {cluster.rollback_plan && (
        <Box>
          <Text fontWeight="medium" mb={1}>Rollback Plan:</Text>
          <Alert status="info" fontSize="sm">
            <AlertIcon />
            {cluster.rollback_plan}
          </Alert>
        </Box>
      )}
    </VStack>
  );
}
