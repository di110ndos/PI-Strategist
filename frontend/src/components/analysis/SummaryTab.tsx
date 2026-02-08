/**
 * Summary tab component showing Executive Summary and overview.
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
  Icon,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Button,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Progress,
  Tag,
  TagLabel,
  Wrap,
  WrapItem,
} from '@chakra-ui/react';
import {
  TrendingUp,
  CheckCircle2,
  XCircle,
  BarChart3,
  Users,
  DollarSign,
  Clock,
  FolderOpen,
} from 'lucide-react';
import { ResourceAllocationBar } from '../charts';
import { exportSummaryPdf } from '../../utils/exportPdf';
import { exportSummaryCsv } from '../../utils/exportCsv';
import type { ResourceData, AnalysisSummary } from '../../types';

// ─── Constants ─────────────────────────────────────────────────

const PI_MAX = 488.0;

// ─── Helpers ───────────────────────────────────────────────────

function isMOProject(name: string): boolean {
  const lower = name.toLowerCase();
  return lower.includes('m&o') || lower.includes('maintenance') || lower.includes('maint');
}

interface MOBreakdown {
  mo: { hours: number; cost: number; projects: string[] };
  ddi: { hours: number; cost: number; projects: string[] };
}

function computeMOBreakdown(resources: Record<string, ResourceData>): MOBreakdown {
  const result: MOBreakdown = {
    mo: { hours: 0, cost: 0, projects: [] },
    ddi: { hours: 0, cost: 0, projects: [] },
  };
  const moProjects = new Set<string>();
  const ddiProjects = new Set<string>();

  for (const r of Object.values(resources)) {
    if (!r.project_hours) continue;
    const rate = r.rate || 0;
    for (const [projName, hours] of Object.entries(r.project_hours)) {
      if (isMOProject(projName)) {
        result.mo.hours += hours;
        result.mo.cost += hours * rate;
        moProjects.add(projName);
      } else {
        result.ddi.hours += hours;
        result.ddi.cost += hours * rate;
        ddiProjects.add(projName);
      }
    }
  }

  result.mo.projects = Array.from(moProjects);
  result.ddi.projects = Array.from(ddiProjects);
  return result;
}

interface DisciplineGroup {
  discipline: string;
  resources: Array<{
    name: string;
    total_hours: number;
    rate: number;
    cost: number;
    allocation_pct: number;
    status: 'over' | 'under' | 'optimal';
  }>;
  totalHours: number;
  totalCost: number;
  count: number;
}

function computeDisciplineGroups(resources: Record<string, ResourceData>): DisciplineGroup[] {
  const groups: Record<string, DisciplineGroup> = {};

  for (const [name, r] of Object.entries(resources)) {
    const disc = r.discipline || 'Unassigned';
    if (!groups[disc]) {
      groups[disc] = { discipline: disc, resources: [], totalHours: 0, totalCost: 0, count: 0 };
    }
    const rate = r.rate || 0;
    const cost = r.total_hours * rate;
    const maxHrs = r.max_hours || PI_MAX;
    const pct = maxHrs > 0 ? (r.total_hours / maxHrs) * 100 : 0;
    const status: 'over' | 'under' | 'optimal' =
      r.status || (pct > 105 ? 'over' : pct < 80 ? 'under' : 'optimal');

    groups[disc].resources.push({
      name: r.name || name,
      total_hours: r.total_hours,
      rate,
      cost,
      allocation_pct: pct,
      status,
    });
    groups[disc].totalHours += r.total_hours;
    groups[disc].totalCost += cost;
    groups[disc].count += 1;
  }

  return Object.values(groups).sort((a, b) => b.totalHours - a.totalHours);
}

function getStatusColor(status: 'over' | 'under' | 'optimal'): string {
  switch (status) {
    case 'over': return 'red';
    case 'under': return 'orange';
    case 'optimal': return 'green';
  }
}

function getStatusLabel(status: 'over' | 'under' | 'optimal'): string {
  switch (status) {
    case 'over': return 'Over-allocated';
    case 'under': return 'Under-allocated';
    case 'optimal': return 'Optimal';
  }
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value);
}

// ─── Props ─────────────────────────────────────────────────────

interface SummaryTabProps {
  results: {
    ded?: {
      filename: string;
      epics?: unknown[];
    };
    red_flags?: unknown[];
    capacity_plan?: Record<string, unknown>;
    capacity_analysis?: Array<{ status: string; utilization_percent: number }>;
    deployment_clusters?: unknown[];
    pi_analysis?: {
      resources?: Record<string, ResourceData>;
      projects?: Record<string, unknown>;
      sprints?: string[];
      total_capacity?: number;
      total_allocated?: number;
      grand_total_hours?: number;
    };
  };
  summary: {
    risk: { total: number; high: number; medium: number; low: number };
    capacity: { total_sprints: number; passing: number; failing: number; average_utilization?: number };
    deployment?: { total_clusters: number; cd_eligible_percentage: number };
  };
}

// ─── Main Component ────────────────────────────────────────────

export default function SummaryTab({ results, summary }: SummaryTabProps) {
  const cardBg = useColorModeValue('white', 'gray.800');
  const subtleBg = useColorModeValue('gray.50', 'gray.700');

  // Compute derived data
  const resources = (results.pi_analysis?.resources || {}) as Record<string, ResourceData>;
  const resourceCount = Object.keys(resources).length;
  const projectCount = results.pi_analysis?.projects
    ? Object.keys(results.pi_analysis.projects).length
    : 0;
  const sprintCount = results.pi_analysis?.sprints?.length || 0;

  const totalCapacity = results.pi_analysis?.total_capacity || resourceCount * PI_MAX;
  const totalAllocated = results.pi_analysis?.total_allocated ||
    Object.values(resources).reduce((sum, r) => sum + r.total_hours, 0);
  const utilizationPct = totalCapacity > 0 ? (totalAllocated / totalCapacity) * 100 : 0;

  const totalCost = Object.values(resources).reduce(
    (sum, r) => sum + r.total_hours * (r.rate || 0), 0
  );

  const avgAllocation = resourceCount > 0
    ? Object.values(resources).reduce((sum, r) => {
        const maxHrs = r.max_hours || PI_MAX;
        return sum + (maxHrs > 0 ? (r.total_hours / maxHrs) * 100 : 0);
      }, 0) / resourceCount
    : 0;

  const moBreakdown = computeMOBreakdown(resources);
  const hasMO = moBreakdown.mo.hours > 0;
  const disciplineGroups = computeDisciplineGroups(resources);

  // Health scores
  const capacityScore = summary.capacity.total_sprints > 0
    ? Math.round((summary.capacity.passing / summary.capacity.total_sprints) * 100)
    : 100;
  const overallScore = capacityScore;

  return (
    <VStack spacing={6} align="stretch">
      {/* ═══ Executive Summary ═══ */}
      {resourceCount > 0 && (
        <ExecutiveSummarySection
          cardBg={cardBg}
          subtleBg={subtleBg}
          resources={resources}
          resourceCount={resourceCount}
          projectCount={projectCount}
          totalCapacity={totalCapacity}
          totalAllocated={totalAllocated}
          utilizationPct={utilizationPct}
          totalCost={totalCost}
          avgAllocation={avgAllocation}
          overallScore={overallScore}
          moBreakdown={moBreakdown}
          hasMO={hasMO}
          disciplineGroups={disciplineGroups}
        />
      )}

      {/* ═══ Original Summary Content ═══ */}
      <Divider />

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
          label="Avg Utilization"
          value={`${formatNumber(avgAllocation)}%`}
          status={avgAllocation > 105 ? 'error' : avgAllocation < 80 ? 'warning' : 'success'}
          helpText="Across all resources"
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

      {/* Capacity Breakdown */}
      <Card bg={cardBg}>
          <CardHeader pb={2}>
            <HStack>
              <Icon as={TrendingUp} boxSize={4} color="blue.400" />
              <Heading size="sm">Capacity Analysis</Heading>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            <VStack align="stretch" spacing={3}>
              <HStack justify="space-between">
                <Text>Total Sprints</Text>
                <Badge>{summary.capacity.total_sprints}</Badge>
              </HStack>
              <Divider />
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <Icon as={CheckCircle2} boxSize={4} color="green.500" />
                  <Text fontSize="sm">Passing</Text>
                </HStack>
                <Text fontWeight="bold" color="green.500">{summary.capacity.passing}</Text>
              </HStack>
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <Icon as={XCircle} boxSize={4} color="red.500" />
                  <Text fontSize="sm">Overloaded</Text>
                </HStack>
                <Text fontWeight="bold" color={summary.capacity.failing > 0 ? 'red.500' : 'green.500'}>
                  {summary.capacity.failing}
                </Text>
              </HStack>
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <Icon as={BarChart3} boxSize={4} color="blue.400" />
                  <Text fontSize="sm">Capacity Score</Text>
                </HStack>
                <Text fontWeight="bold">{capacityScore}%</Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

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

      {/* Export Buttons */}
      <HStack spacing={3}>
        <Button
          size="sm"
          variant="outline"
          onClick={() => exportSummaryPdf(summary as AnalysisSummary)}
        >
          Export PDF
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => exportSummaryCsv(summary as AnalysisSummary)}
        >
          Export CSV
        </Button>
      </HStack>
    </VStack>
  );
}

// ─── Executive Summary Section ─────────────────────────────────

function ExecutiveSummarySection({
  cardBg,
  subtleBg,
  resources,
  resourceCount,
  projectCount,
  totalCapacity,
  totalAllocated,
  utilizationPct,
  totalCost,
  avgAllocation,
  overallScore,
  moBreakdown,
  hasMO,
  disciplineGroups,
}: {
  cardBg: string;
  subtleBg: string;
  resources: Record<string, ResourceData>;
  resourceCount: number;
  projectCount: number;
  totalCapacity: number;
  totalAllocated: number;
  utilizationPct: number;
  totalCost: number;
  avgAllocation: number;
  overallScore: number;
  moBreakdown: MOBreakdown;
  hasMO: boolean;
  disciplineGroups: DisciplineGroup[];
}) {
  return (
    <Card bg={cardBg}>
      <CardHeader>
        <HStack>
          <Icon as={BarChart3} boxSize={5} color="blue.500" />
          <Heading size="md">Executive Summary</Heading>
        </HStack>
      </CardHeader>
      <CardBody pt={0}>
        <VStack spacing={5} align="stretch">
          {/* Top Metrics Row */}
          <SimpleGrid columns={{ base: 2, sm: 3, md: 5 }} spacing={4}>
            <Stat>
              <StatLabel><HStack spacing={1}><Icon as={Clock} boxSize={3} /><Text>Team Capacity</Text></HStack></StatLabel>
              <StatNumber fontSize="xl">{formatNumber(totalCapacity)}h</StatNumber>
              <StatHelpText>{resourceCount} resources &times; PI</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel><HStack spacing={1}><Icon as={TrendingUp} boxSize={3} /><Text>Allocated Hours</Text></HStack></StatLabel>
              <StatNumber fontSize="xl">{formatNumber(totalAllocated)}h</StatNumber>
              <StatHelpText>{formatNumber(utilizationPct)}% utilization</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel><HStack spacing={1}><Icon as={DollarSign} boxSize={3} /><Text>Total Cost</Text></HStack></StatLabel>
              <StatNumber fontSize="xl">{formatCurrency(totalCost)}</StatNumber>
              <StatHelpText>Across all resources</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel><HStack spacing={1}><Icon as={Users} boxSize={3} /><Text>Resources</Text></HStack></StatLabel>
              <StatNumber fontSize="xl">{resourceCount}</StatNumber>
              <StatHelpText>Team members</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel><HStack spacing={1}><Icon as={FolderOpen} boxSize={3} /><Text>Projects</Text></HStack></StatLabel>
              <StatNumber fontSize="xl">{projectCount}</StatNumber>
              <StatHelpText>Active workstreams</StatHelpText>
            </Stat>
          </SimpleGrid>

          {/* Health Indicator */}
          <Alert
            status={utilizationPct > 105 ? 'error' : utilizationPct < 80 ? 'warning' : 'success'}
            borderRadius="md"
          >
            <AlertIcon />
            <Box>
              <AlertTitle>
                {utilizationPct > 105
                  ? 'Over-allocated'
                  : utilizationPct < 80
                    ? 'Under-utilized'
                    : 'Healthy Allocation'}
              </AlertTitle>
              <AlertDescription fontSize="sm">
                {utilizationPct > 105
                  ? `Team is allocated at ${formatNumber(utilizationPct)}% of capacity. Consider reducing scope or adding resources.`
                  : utilizationPct < 80
                    ? `Team is only at ${formatNumber(utilizationPct)}% utilization. There may be room for additional work.`
                    : `Team utilization at ${formatNumber(utilizationPct)}% is within the optimal range (80-105%).`}
              </AlertDescription>
            </Box>
          </Alert>

          {/* Resource Allocation Bar */}
          <Box>
            <Text fontWeight="semibold" fontSize="sm" mb={2}>Resource Allocation Distribution</Text>
            <ResourceAllocationBar resources={resources} />
          </Box>

          {/* Resource Summary Row */}
          <Box bg={subtleBg} p={4} borderRadius="md">
            <SimpleGrid columns={{ base: 2, sm: 3, md: 5 }} spacing={4}>
              <Box>
                <Text fontSize="xs" color="gray.500" textTransform="uppercase">Team Size</Text>
                <Text fontWeight="bold" fontSize="lg">{resourceCount}</Text>
              </Box>
              <Box>
                <Text fontSize="xs" color="gray.500" textTransform="uppercase">Total Hours</Text>
                <Text fontWeight="bold" fontSize="lg">{formatNumber(totalAllocated)}</Text>
              </Box>
              <Box>
                <Text fontSize="xs" color="gray.500" textTransform="uppercase">Total Cost</Text>
                <Text fontWeight="bold" fontSize="lg">{formatCurrency(totalCost)}</Text>
              </Box>
              <Box>
                <Text fontSize="xs" color="gray.500" textTransform="uppercase">Avg Allocation</Text>
                <Text fontWeight="bold" fontSize="lg">{formatNumber(avgAllocation)}%</Text>
              </Box>
              <Box>
                <Text fontSize="xs" color="gray.500" textTransform="uppercase">Health Score</Text>
                <Text
                  fontWeight="bold"
                  fontSize="lg"
                  color={overallScore >= 80 ? 'green.500' : overallScore >= 60 ? 'orange.500' : 'red.500'}
                >
                  {overallScore}/100
                </Text>
              </Box>
            </SimpleGrid>
          </Box>

          {/* M&O vs DD&I Breakdown */}
          {hasMO && (
            <>
              <Divider />
              <Text fontWeight="semibold" fontSize="sm">M&O vs DD&I Breakdown</Text>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <Card variant="outline" size="sm">
                  <CardBody>
                    <VStack align="stretch" spacing={2}>
                      <HStack justify="space-between">
                        <Badge colorScheme="blue">M&O / Maintenance</Badge>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm">Hours</Text>
                        <Text fontWeight="bold">{formatNumber(moBreakdown.mo.hours)}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm">Cost</Text>
                        <Text fontWeight="bold">{formatCurrency(moBreakdown.mo.cost)}</Text>
                      </HStack>
                      {moBreakdown.mo.projects.length > 0 && (
                        <Wrap spacing={1}>
                          {moBreakdown.mo.projects.map((p) => (
                            <WrapItem key={p}>
                              <Tag size="sm" variant="subtle" colorScheme="blue">
                                <TagLabel>{p}</TagLabel>
                              </Tag>
                            </WrapItem>
                          ))}
                        </Wrap>
                      )}
                    </VStack>
                  </CardBody>
                </Card>
                <Card variant="outline" size="sm">
                  <CardBody>
                    <VStack align="stretch" spacing={2}>
                      <HStack justify="space-between">
                        <Badge colorScheme="purple">DD&I / Development</Badge>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm">Hours</Text>
                        <Text fontWeight="bold">{formatNumber(moBreakdown.ddi.hours)}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm">Cost</Text>
                        <Text fontWeight="bold">{formatCurrency(moBreakdown.ddi.cost)}</Text>
                      </HStack>
                      {moBreakdown.ddi.projects.length > 0 && (
                        <Wrap spacing={1}>
                          {moBreakdown.ddi.projects.slice(0, 8).map((p) => (
                            <WrapItem key={p}>
                              <Tag size="sm" variant="subtle" colorScheme="purple">
                                <TagLabel>{p}</TagLabel>
                              </Tag>
                            </WrapItem>
                          ))}
                          {moBreakdown.ddi.projects.length > 8 && (
                            <WrapItem>
                              <Tag size="sm" variant="subtle">
                                <TagLabel>+{moBreakdown.ddi.projects.length - 8} more</TagLabel>
                              </Tag>
                            </WrapItem>
                          )}
                        </Wrap>
                      )}
                    </VStack>
                  </CardBody>
                </Card>
              </SimpleGrid>
            </>
          )}

          {/* Discipline Groups */}
          {disciplineGroups.length > 0 && (
            <>
              <Divider />
              <Text fontWeight="semibold" fontSize="sm">Resources by Discipline</Text>
              <Accordion allowMultiple>
                {disciplineGroups.map((group) => {
                  const overCount = group.resources.filter(r => r.status === 'over').length;
                  const underCount = group.resources.filter(r => r.status === 'under').length;
                  const optimalCount = group.resources.filter(r => r.status === 'optimal').length;

                  return (
                    <AccordionItem key={group.discipline}>
                      <AccordionButton>
                        <Box flex="1" textAlign="left">
                          <HStack spacing={3}>
                            <Text fontWeight="semibold">{group.discipline}</Text>
                            <Badge>{group.count}</Badge>
                            <Text fontSize="sm" color="gray.500">
                              {formatNumber(group.totalHours)}h &middot; {formatCurrency(group.totalCost)}
                            </Text>
                          </HStack>
                        </Box>
                        <HStack spacing={1} mr={2}>
                          {optimalCount > 0 && <Badge colorScheme="green" size="sm">{optimalCount}</Badge>}
                          {underCount > 0 && <Badge colorScheme="orange" size="sm">{underCount}</Badge>}
                          {overCount > 0 && <Badge colorScheme="red" size="sm">{overCount}</Badge>}
                        </HStack>
                        <AccordionIcon />
                      </AccordionButton>
                      <AccordionPanel pb={4}>
                        <VStack align="stretch" spacing={3}>
                          {group.resources
                            .sort((a, b) => b.total_hours - a.total_hours)
                            .map((r) => (
                              <Box key={r.name}>
                                <HStack justify="space-between" mb={1}>
                                  <HStack spacing={2}>
                                    <Text fontSize="sm" fontWeight="medium">{r.name}</Text>
                                    <Badge
                                      size="sm"
                                      colorScheme={getStatusColor(r.status)}
                                    >
                                      {getStatusLabel(r.status)}
                                    </Badge>
                                  </HStack>
                                  <Text fontSize="sm" color="gray.500">
                                    {formatNumber(r.total_hours)}h &middot; {formatCurrency(r.cost)}
                                  </Text>
                                </HStack>
                                <Progress
                                  value={Math.min(r.allocation_pct, 150)}
                                  max={150}
                                  size="sm"
                                  borderRadius="full"
                                  colorScheme={getStatusColor(r.status)}
                                />
                                <Text fontSize="xs" color="gray.500" mt={0.5}>
                                  {formatNumber(r.allocation_pct)}% of {PI_MAX}h capacity
                                </Text>
                              </Box>
                            ))}
                        </VStack>
                      </AccordionPanel>
                    </AccordionItem>
                  );
                })}
              </Accordion>
            </>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

// ─── Metric Card Component ─────────────────────────────────────

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
