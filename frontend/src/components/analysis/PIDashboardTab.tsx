/**
 * PI Dashboard tab component - comprehensive overview of PI health.
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
  Heading,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  CircularProgress,
  CircularProgressLabel,
  Alert,
  AlertIcon,
  Icon,
  Tooltip,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  Gauge,
  Rocket,
  Activity,
  DollarSign,
  Clock,
  Users,
  BarChart3,
  TrendingUp,
  FolderOpen,
} from 'lucide-react';
import {
  ResourceHeatmap,
  AllocationDistribution,
  CapacityBurndownChart,
  UtilizationTrendChart,
  CostByDisciplineChart,
  SprintCostChart,
  ProjectTimeline,
  ResourceAllocationBar,
  LazyPlot,
} from '../charts';
import { CHART_PALETTE, BORDER, plotlyLayout, PLOTLY_CONFIG } from '../charts/plotlyDefaults';

interface AnalysisSummary {
  risk: {
    total: number;
    high: number;
    medium: number;
    low: number;
  };
  capacity: {
    total_sprints: number;
    passing: number;
    failing: number;
    average_utilization: number;
  };
  deployment?: {
    total_clusters: number;
    cd_eligible_percentage: number;
  };
}

interface AnalysisResults {
  red_flags?: any[];
  capacity_analysis?: any[];
  deployment_clusters?: any[];
  financial_summary?: {
    total_hours: number;
    total_cost: number;
    cost_by_sprint?: Record<string, number>;
    cost_by_role?: Record<string, number>;
  };
  timeline?: {
    start_date?: string;
    end_date?: string;
    total_weeks?: number;
    sprints?: any[];
  };
  pi_analysis?: {
    resources?: Record<string, {
      total_hours: number;
      rate?: number;
      discipline?: string;
      sprint_hours?: Record<string, number>;
    }>;
    projects?: Record<string, {
      total_hours: number;
      priority?: number;
      sprint_allocation?: Record<string, number>;
    }>;
    sprints?: string[];
  };
}

interface PIDashboardTabProps {
  results: AnalysisResults;
  summary: AnalysisSummary;
}

function getScoreStatus(score: number): { label: string; color: string } {
  if (score >= 80) return { label: 'Healthy', color: 'green.500' };
  if (score >= 60) return { label: 'Moderate', color: 'yellow.600' };
  if (score >= 40) return { label: 'At Risk', color: 'orange.500' };
  return { label: 'Critical', color: 'red.500' };
}

function HealthScoreCard({ score, label, icon, tooltip, colorScheme: cs }: { score: number; label: string; icon: any; tooltip: string; colorScheme?: string }) {
  const getColorScheme = (s: number) => {
    if (s >= 80) return 'green';
    if (s >= 60) return 'yellow';
    if (s >= 40) return 'orange';
    return 'red';
  };

  const colorScheme = cs || getColorScheme(score);
  const cardBg = useColorModeValue('white', 'gray.800');
  const statusInfo = getScoreStatus(score);

  return (
    <Tooltip label={tooltip} fontSize="sm" placement="top" hasArrow maxW="280px">
      <Card bg={cardBg} cursor="help">
        <CardBody textAlign="center" py={5}>
          <CircularProgress
            value={score}
            size="100px"
            thickness="10px"
            color={`${colorScheme}.400`}
            trackColor={useColorModeValue(`${colorScheme}.50`, `${colorScheme}.900`)}
          >
            <CircularProgressLabel fontSize="xl" fontWeight="bold">
              {score}%
            </CircularProgressLabel>
          </CircularProgress>
          <HStack justify="center" mt={3} spacing={1.5}>
            <Icon as={icon} boxSize={4} color={`${colorScheme}.500`} />
            <Text fontWeight="semibold" fontSize="sm" color="gray.500">
              {label}
            </Text>
          </HStack>
          <Text fontSize="xs" fontWeight="bold" color={statusInfo.color} mt={1}>
            {statusInfo.label}
          </Text>
        </CardBody>
      </Card>
    </Tooltip>
  );
}

export default function PIDashboardTab({ results, summary }: PIDashboardTabProps) {
  const cardBg = useColorModeValue('white', 'gray.800');
  const subtleBg = useColorModeValue('gray.50', 'gray.700');

  // Calculate health scores
  const calculateCapacityScore = () => {
    if (summary.capacity.total_sprints === 0) return 100;
    const passRate = summary.capacity.passing / summary.capacity.total_sprints;
    const utilizationPenalty = Math.abs(summary.capacity.average_utilization - 80) / 100;
    return Math.round(passRate * 100 - utilizationPenalty * 20);
  };

  const calculateDeploymentScore = () => {
    if (!summary.deployment) return 70;
    return Math.min(100, Math.round(summary.deployment.cd_eligible_percentage * 2 + 40));
  };

  const capacityScore = calculateCapacityScore();
  const deploymentScore = calculateDeploymentScore();
  const overallScore = Math.round((capacityScore + deploymentScore) / 2);

  const getOverallStatus = () => {
    if (overallScore >= 80) return { text: 'Healthy', color: 'green' };
    if (overallScore >= 60) return { text: 'Moderate Risk', color: 'yellow' };
    if (overallScore >= 40) return { text: 'At Risk', color: 'orange' };
    return { text: 'Critical', color: 'red' };
  };

  const status = getOverallStatus();

  // Extract PI analysis data for charts
  const piResources = results.pi_analysis?.resources;
  const piProjects = results.pi_analysis?.projects;
  const piSprints = results.pi_analysis?.sprints;

  // Build cost by discipline
  const costByDiscipline: Record<string, number> = {};
  if (piResources) {
    for (const r of Object.values(piResources)) {
      const disc = r.discipline || 'Other';
      const cost = r.total_hours * (r.rate || 0);
      if (cost > 0) {
        costByDiscipline[disc] = (costByDiscipline[disc] || 0) + cost;
      }
    }
  }

  return (
    <VStack spacing={6} align="stretch">
      {/* Overall Status Banner */}
      <Alert
        status={status.color === 'green' ? 'success' : status.color === 'yellow' ? 'warning' : 'error'}
        borderRadius="md"
        py={4}
      >
        <AlertIcon boxSize={6} />
        <HStack justify="space-between" flex={1} flexWrap="wrap" gap={2}>
          <Text fontWeight="bold" fontSize="lg">PI Health Status: {status.text}</Text>
          <Badge colorScheme={status.color} fontSize="md" px={4} py={1.5} borderRadius="md">
            {overallScore}% Overall Health
          </Badge>
        </HStack>
      </Alert>

      {/* Health Score Cards */}
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        <HealthScoreCard
          score={overallScore}
          label="Overall Health"
          icon={Activity}
          tooltip="Average of Capacity and Deployment scores. 80%+ = Healthy, 60-79% = Moderate Risk, 40-59% = At Risk, <40% = Critical."
        />
        <HealthScoreCard
          score={capacityScore}
          label="Capacity Score"
          icon={Gauge}
          tooltip="Based on sprint pass rate and how close average utilization is to the 80% target. More passing sprints and utilization near 80% = higher score."
        />
        <HealthScoreCard
          score={deploymentScore}
          label="Deployment Score"
          icon={Rocket}
          tooltip="Based on the percentage of tasks eligible for continuous delivery. Higher CD eligibility = higher score. No deployment data defaults to 70%."
        />
      </SimpleGrid>

      {/* Key Metrics */}
      <Card bg={cardBg}>
        <CardHeader pb={2}>
          <HStack>
            <Icon as={BarChart3} boxSize={5} color="blue.500" />
            <Heading size="sm">Key Metrics</Heading>
          </HStack>
        </CardHeader>
        <CardBody pt={0}>
          <SimpleGrid columns={{ base: 2, md: 3 }} spacing={6}>
            <Stat>
              <StatLabel>Sprint Health</StatLabel>
              <StatNumber color={summary.capacity.failing > 0 ? 'orange.500' : 'green.500'}>
                {summary.capacity.passing}/{summary.capacity.total_sprints}
              </StatNumber>
              <StatHelpText>sprints passing</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Avg Utilization</StatLabel>
              <StatNumber>{summary.capacity.average_utilization.toFixed(1)}%</StatNumber>
              <StatHelpText>target: 80%</StatHelpText>
            </Stat>
            {summary.deployment && (
              <Stat>
                <StatLabel>CD Eligible</StatLabel>
                <StatNumber color="purple.500">
                  {summary.deployment.cd_eligible_percentage.toFixed(1)}%
                </StatNumber>
                <StatHelpText>of tasks</StatHelpText>
              </Stat>
            )}
          </SimpleGrid>
        </CardBody>
      </Card>

      {/* Sprint Trend Charts */}
      {results.capacity_analysis && results.capacity_analysis.length > 0 && (
        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
          <Card bg={cardBg}>
            <CardHeader pb={2}>
              <HStack>
                <Icon as={TrendingUp} boxSize={5} color="blue.500" />
                <Heading size="sm">Capacity vs Load</Heading>
              </HStack>
            </CardHeader>
            <CardBody pt={0}>
              <CapacityBurndownChart analyses={results.capacity_analysis} />
            </CardBody>
          </Card>
          <Card bg={cardBg}>
            <CardHeader pb={2}>
              <HStack>
                <Icon as={Activity} boxSize={5} color="cyan.500" />
                <Heading size="sm">Utilization Trend</Heading>
              </HStack>
            </CardHeader>
            <CardBody pt={0}>
              <UtilizationTrendChart analyses={results.capacity_analysis} />
            </CardBody>
          </Card>
        </SimpleGrid>
      )}

      {/* Resource Allocation Bar */}
      {piResources && Object.keys(piResources).length > 0 && (
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <HStack>
              <Icon as={Users} boxSize={5} color="teal.500" />
              <Heading size="sm">Resource Allocation Overview</Heading>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            <ResourceAllocationBar resources={piResources} />
          </CardBody>
        </Card>
      )}

      {/* Resource Heatmap */}
      {piResources && piSprints && piSprints.length > 0 && (
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <HStack>
              <Icon as={Activity} boxSize={5} color="orange.500" />
              <Heading size="sm">Resource Heatmap</Heading>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            <Box overflowX="auto">
              <ResourceHeatmap resources={piResources} sprints={piSprints} />
            </Box>
          </CardBody>
        </Card>
      )}

      {/* Allocation Distribution + Top Projects */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        {piResources && Object.keys(piResources).length > 0 && (() => {
          const resArr = Object.values(piResources);
          const total = resArr.length;
          const optimalCount = resArr.filter((r) => {
            const maxHrs = 488;
            const pct = maxHrs > 0 ? (r.total_hours / maxHrs) * 100 : 0;
            return pct >= 80 && pct <= 105;
          }).length;
          const optimalPct = total > 0 ? ((optimalCount / total) * 100).toFixed(0) : '0';

          return (
            <Card bg={cardBg}>
              <CardHeader pb={2}>
                <HStack>
                  <Icon as={BarChart3} boxSize={5} color="cyan.500" />
                  <Heading size="sm">Allocation Distribution</Heading>
                </HStack>
              </CardHeader>
              <CardBody pt={0}>
                <AllocationDistribution resources={piResources} />
                <Text fontSize="xs" color="gray.500" mt={2} textAlign="center">
                  {optimalPct}% of resources within optimal range (80-105%)
                </Text>
              </CardBody>
            </Card>
          );
        })()}
        {piProjects && Object.keys(piProjects).length > 0 && (
          <Card bg={cardBg}>
            <CardHeader pb={2}>
              <HStack>
                <Icon as={FolderOpen} boxSize={5} color="purple.500" />
                <Heading size="sm">Top Projects by Hours</Heading>
              </HStack>
            </CardHeader>
            <CardBody pt={0}>
              <TopProjectsChart projects={piProjects} />
            </CardBody>
          </Card>
        )}
      </SimpleGrid>

      {/* Financial Charts */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        {Object.keys(costByDiscipline).length > 0 && (
          <Card bg={cardBg}>
            <CardHeader pb={2}>
              <HStack>
                <Icon as={DollarSign} boxSize={5} color="green.500" />
                <Heading size="sm">Cost by Discipline</Heading>
              </HStack>
            </CardHeader>
            <CardBody pt={0}>
              <CostByDisciplineChart costByDiscipline={costByDiscipline} />
            </CardBody>
          </Card>
        )}
        {results.financial_summary?.cost_by_sprint && (
          <Card bg={cardBg}>
            <CardHeader pb={2}>
              <HStack>
                <Icon as={DollarSign} boxSize={5} color="green.500" />
                <Heading size="sm">Cost by Sprint</Heading>
              </HStack>
            </CardHeader>
            <CardBody pt={0}>
              <SprintCostChart costBySprint={results.financial_summary.cost_by_sprint} />
            </CardBody>
          </Card>
        )}
      </SimpleGrid>

      {/* Project Timeline */}
      {piProjects && piSprints && piSprints.length > 0 && Object.keys(piProjects).length > 0 && (
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <HStack>
              <Icon as={Clock} boxSize={5} color="purple.500" />
              <Heading size="sm">Project Timeline</Heading>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            <Box overflowX="auto">
              <ProjectTimeline projects={piProjects} sprints={piSprints} />
            </Box>
          </CardBody>
        </Card>
      )}

      {/* Financial Summary (text) */}
      {results.financial_summary && (
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <HStack>
              <Icon as={DollarSign} boxSize={5} color="green.500" />
              <Heading size="sm">Financial Summary</Heading>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
              <Box bg={subtleBg} p={4} borderRadius="md">
                <Text fontSize="xs" color="gray.500" textTransform="uppercase" mb={1}>Total Hours</Text>
                <Text fontSize="2xl" fontWeight="bold">
                  {results.financial_summary.total_hours.toLocaleString()}h
                </Text>
              </Box>
              <Box bg={subtleBg} p={4} borderRadius="md">
                <Text fontSize="xs" color="gray.500" textTransform="uppercase" mb={1}>Total Cost</Text>
                <Text fontSize="2xl" fontWeight="bold" color="green.500">
                  ${results.financial_summary.total_cost.toLocaleString()}
                </Text>
              </Box>
              <Box bg={subtleBg} p={4} borderRadius="md">
                <Text fontSize="xs" color="gray.500" textTransform="uppercase" mb={1}>Avg Cost/Hour</Text>
                <Text fontSize="2xl" fontWeight="bold">
                  ${(results.financial_summary.total_cost / results.financial_summary.total_hours).toFixed(0)}
                </Text>
              </Box>
            </SimpleGrid>
          </CardBody>
        </Card>
      )}

      {/* Timeline Summary */}
      {results.timeline && (
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <HStack>
              <Icon as={Clock} boxSize={5} color="blue.500" />
              <Heading size="sm">Timeline</Heading>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
              {results.timeline.start_date && (
                <Box bg={subtleBg} p={3} borderRadius="md">
                  <Text fontSize="xs" color="gray.500" textTransform="uppercase">Start Date</Text>
                  <Text fontWeight="semibold">{results.timeline.start_date}</Text>
                </Box>
              )}
              {results.timeline.end_date && (
                <Box bg={subtleBg} p={3} borderRadius="md">
                  <Text fontSize="xs" color="gray.500" textTransform="uppercase">End Date</Text>
                  <Text fontWeight="semibold">{results.timeline.end_date}</Text>
                </Box>
              )}
              {results.timeline.total_weeks && (
                <Box bg={subtleBg} p={3} borderRadius="md">
                  <Text fontSize="xs" color="gray.500" textTransform="uppercase">Duration</Text>
                  <Text fontWeight="semibold">{results.timeline.total_weeks} weeks</Text>
                </Box>
              )}
              {results.timeline.sprints && (
                <Box bg={subtleBg} p={3} borderRadius="md">
                  <Text fontSize="xs" color="gray.500" textTransform="uppercase">Sprints</Text>
                  <Text fontWeight="semibold">{results.timeline.sprints.length}</Text>
                </Box>
              )}
            </SimpleGrid>
          </CardBody>
        </Card>
      )}
    </VStack>
  );
}

// ─── Top Projects Chart ─────────────────────────────────────────

function TopProjectsChart({ projects }: { projects: Record<string, { total_hours: number; priority?: number; sprint_allocation?: Record<string, number> }> }) {
  const entries = Object.entries(projects)
    .map(([name, p]) => ({ name, hours: p.total_hours }))
    .sort((a, b) => b.hours - a.hours)
    .slice(0, 10);

  if (entries.length === 0) return <Text color="gray.500" fontSize="sm">No project data available.</Text>;

  const names = entries.map((e) => e.name);
  const hours = entries.map((e) => e.hours);

  return (
    <LazyPlot
      data={[
        {
          type: 'bar',
          orientation: 'h' as const,
          y: names.reverse(),
          x: hours.reverse(),
          marker: {
            color: CHART_PALETTE.slice(0, entries.length).concat(
              Array(Math.max(0, entries.length - CHART_PALETTE.length)).fill(CHART_PALETTE[0])
            ),
          },
          text: hours.map((h) => `${h.toFixed(0)}h`),
          textposition: 'outside' as const,
          hovertemplate: '%{y}: %{x:.0f} hours<extra></extra>',
        },
      ]}
      layout={plotlyLayout({
        xaxis: { title: { text: 'Hours' }, gridcolor: BORDER },
        yaxis: { automargin: true },
        height: 350,
        margin: { l: 140, r: 60, t: 20, b: 40 },
      })}
      config={PLOTLY_CONFIG}
      style={{ width: '100%' }}
    />
  );
}
