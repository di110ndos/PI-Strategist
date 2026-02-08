/**
 * Compare saved analyses page.
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Button,
  Select,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatGroup,
  Alert,
  AlertIcon,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Spinner,
  Icon,
  useColorModeValue,
} from '@chakra-ui/react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useSavedAnalyses, useSavedAnalysis } from '../hooks/useAnalysis';
import { LazyPlot } from '../components/charts';
import { plotlyLayout, PLOTLY_CONFIG, BLUE, TEXT_MUTED } from '../components/charts/plotlyDefaults';
import type { AnalysisResponse } from '../types';

// ─── Types ──────────────────────────────────────────────────────

/** Shape returned by the list endpoint (metadata only). */
interface SavedAnalysisListItem {
  id: string;
  name: string;
  year: string;
  quarter: string;
  saved_at: string;
  source_file?: string;
}

interface ResourceEntry {
  total_hours: number;
  rate?: number;
  name?: string;
  discipline?: string;
}

interface ProjectEntry {
  total_hours: number;
  name?: string;
}

// ─── Helpers ────────────────────────────────────────────────────

function getAnalysisLabel(analysis: SavedAnalysisListItem): string {
  const { year, quarter, name } = analysis;
  let label = year && quarter ? `${year} ${quarter}` : name || 'Unnamed';
  if (year && quarter && name) label += ` - ${name}`;
  return label;
}

function extractPIAnalysis(full: AnalysisResponse) {
  const pi = (full.results as any)?.pi_analysis || {};
  const resources: Record<string, ResourceEntry> = pi.resources || {};
  const projects: Record<string, ProjectEntry> = pi.projects || {};
  const totalCapacity: number = pi.total_capacity || 0;
  const totalAllocated: number = pi.total_allocated ||
    Object.values(resources).reduce((sum, r) => sum + (r.total_hours || 0), 0);
  const totalCost = Object.values(resources).reduce(
    (sum, r) => sum + (r.total_hours || 0) * (r.rate || 0), 0
  );
  const resourceCount = Object.keys(resources).length;
  const projectCount = Object.keys(projects).length;
  const utilization = totalCapacity > 0 ? (totalAllocated / totalCapacity) * 100 : 0;

  return { resources, projects, totalCapacity, totalAllocated, totalCost, resourceCount, projectCount, utilization };
}

// ─── Main Component ─────────────────────────────────────────────

export default function ComparePage() {
  const navigate = useNavigate();
  const cardBg = useColorModeValue('white', 'gray.800');

  const { data, isLoading } = useSavedAnalyses();
  const analyses: SavedAnalysisListItem[] = (data as any)?.analyses || [];
  const [selectedA, setSelectedA] = useState<string>('');
  const [selectedB, setSelectedB] = useState<string>('');

  // Fetch full analysis data for each selection
  const { data: fullA, isLoading: loadingA } = useSavedAnalysis(selectedA || undefined);
  const { data: fullB, isLoading: loadingB } = useSavedAnalysis(selectedB || undefined);

  const listItemA = analyses.find((a) => a.id === selectedA);
  const listItemB = analyses.find((a) => a.id === selectedB);

  // Set defaults when analyses load
  useEffect(() => {
    if (analyses.length >= 2 && !selectedA && !selectedB) {
      setSelectedA(analyses[1]?.id || '');
      setSelectedB(analyses[0]?.id || '');
    }
  }, [analyses, selectedA, selectedB]);

  if (isLoading) {
    return (
      <Box px={{ base: 4, md: 6, lg: 8 }} py={8}>
        <Text>Loading saved analyses...</Text>
      </Box>
    );
  }

  if (analyses.length < 2) {
    return (
      <Box px={{ base: 4, md: 6, lg: 8 }} py={8}>
        <Alert status="warning" borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">Need at least 2 saved analyses to compare.</Text>
            <Text>
              Currently have {analyses.length} saved analysis(es).
              Go to the Analysis page, run an analysis, and save it to enable comparison.
            </Text>
            <Button mt={4} colorScheme="blue" onClick={() => navigate('/analyze')}>
              Go to Analysis Page
            </Button>
          </Box>
        </Alert>
      </Box>
    );
  }

  return (
    <Box px={{ base: 4, md: 6, lg: 8 }} py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Compare Saved Analyses
          </Heading>
          <Text color="gray.500">
            Select two saved analyses to compare capacity, utilization, and cost changes.
          </Text>
        </Box>

        {/* Selection */}
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
          <Card bg={cardBg}>
            <CardHeader pb={2}>
              <Text fontWeight="bold">Baseline (Earlier)</Text>
            </CardHeader>
            <CardBody pt={0}>
              <Select
                value={selectedA}
                onChange={(e) => setSelectedA(e.target.value)}
                placeholder="Select analysis..."
              >
                {analyses.map((a) => (
                  <option key={a.id} value={a.id}>
                    {getAnalysisLabel(a)}
                  </option>
                ))}
              </Select>
              {listItemA && (
                <Box mt={4}>
                  <Text fontSize="sm" color="gray.500">
                    Saved: {listItemA.saved_at?.slice(0, 10) || 'Unknown'}
                  </Text>
                  <Text fontSize="sm" color="gray.500">
                    Source: {listItemA.source_file || 'Unknown'}
                  </Text>
                </Box>
              )}
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardHeader pb={2}>
              <Text fontWeight="bold">Current (Later)</Text>
            </CardHeader>
            <CardBody pt={0}>
              <Select
                value={selectedB}
                onChange={(e) => setSelectedB(e.target.value)}
                placeholder="Select analysis..."
              >
                {analyses.map((a) => (
                  <option key={a.id} value={a.id}>
                    {getAnalysisLabel(a)}
                  </option>
                ))}
              </Select>
              {listItemB && (
                <Box mt={4}>
                  <Text fontSize="sm" color="gray.500">
                    Saved: {listItemB.saved_at?.slice(0, 10) || 'Unknown'}
                  </Text>
                  <Text fontSize="sm" color="gray.500">
                    Source: {listItemB.source_file || 'Unknown'}
                  </Text>
                </Box>
              )}
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Comparison */}
        {selectedA === selectedB && selectedA !== '' ? (
          <Alert status="warning" borderRadius="md">
            <AlertIcon />
            Please select two different analyses to compare.
          </Alert>
        ) : (loadingA || loadingB) ? (
          <VStack py={8}>
            <Spinner size="lg" color="blue.500" />
            <Text color="gray.500">Loading analysis data...</Text>
          </VStack>
        ) : fullA && fullB && listItemA && listItemB ? (
          <ComparisonView
            fullA={fullA}
            fullB={fullB}
            labelA={getAnalysisLabel(listItemA)}
            labelB={getAnalysisLabel(listItemB)}
            cardBg={cardBg}
          />
        ) : null}
      </VStack>
    </Box>
  );
}

// ─── Comparison View ────────────────────────────────────────────

interface ComparisonViewProps {
  fullA: AnalysisResponse;
  fullB: AnalysisResponse;
  labelA: string;
  labelB: string;
  cardBg: string;
}

function ComparisonView({ fullA, fullB, labelA, labelB, cardBg }: ComparisonViewProps) {
  const piA = extractPIAnalysis(fullA);
  const piB = extractPIAnalysis(fullB);

  const deltaHours = piB.totalAllocated - piA.totalAllocated;
  const deltaUtil = piB.utilization - piA.utilization;
  const deltaCost = piB.totalCost - piA.totalCost;
  const deltaResources = piB.resourceCount - piA.resourceCount;

  // Determine trend arrow logic per metric:
  // Hours: more hours = neutral (not inherently good/bad), show gray
  // Utilization: moving toward 80-100% is good, moving away is bad
  // Cost: lower cost is good (green down), higher cost is bad (red up)
  const hoursIsUp = deltaHours >= 0;
  const utilIsUp = deltaUtil >= 0;
  const costIsUp = deltaCost >= 0;

  // Utilization improvement: closer to 80-100% optimal range
  const baseOptimalDist = Math.abs(piA.utilization - 90);
  const currOptimalDist = Math.abs(piB.utilization - 90);
  const utilImproved = currOptimalDist < baseOptimalDist;

  return (
    <VStack spacing={6} align="stretch">
      {/* Key Metrics */}
      <Card bg={cardBg}>
        <CardHeader pb={2}>
          <Text fontWeight="bold" fontSize="lg">Key Metrics</Text>
        </CardHeader>
        <CardBody pt={0}>
          <StatGroup>
            <Stat>
              <StatLabel>Allocated Hours</StatLabel>
              <StatNumber>{piB.totalAllocated.toLocaleString()}h</StatNumber>
              <StatHelpText color={deltaHours >= 0 ? 'green.500' : 'red.500'}>
                <HStack spacing={1} display="inline-flex" alignItems="center">
                  <Icon
                    as={hoursIsUp ? TrendingUp : TrendingDown}
                    boxSize={3.5}
                    color={deltaHours >= 0 ? 'green.500' : 'red.500'}
                  />
                  <Text as="span">{deltaHours >= 0 ? '+' : ''}{deltaHours.toLocaleString()}h</Text>
                </HStack>
              </StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Utilization</StatLabel>
              <StatNumber>{piB.utilization.toFixed(1)}%</StatNumber>
              <StatHelpText color={utilImproved ? 'green.500' : 'orange.500'}>
                <HStack spacing={1} display="inline-flex" alignItems="center">
                  <Icon
                    as={utilIsUp ? TrendingUp : TrendingDown}
                    boxSize={3.5}
                    color={utilImproved ? 'green.500' : 'orange.500'}
                  />
                  <Text as="span">{deltaUtil >= 0 ? '+' : ''}{deltaUtil.toFixed(1)}%</Text>
                </HStack>
              </StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Total Cost</StatLabel>
              <StatNumber>${piB.totalCost.toLocaleString()}</StatNumber>
              <StatHelpText color={costIsUp ? 'red.500' : 'green.500'}>
                <HStack spacing={1} display="inline-flex" alignItems="center">
                  <Icon
                    as={costIsUp ? TrendingUp : TrendingDown}
                    boxSize={3.5}
                    color={costIsUp ? 'red.500' : 'green.500'}
                  />
                  <Text as="span">{deltaCost >= 0 ? '+' : ''}${deltaCost.toLocaleString()}</Text>
                </HStack>
              </StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Resources</StatLabel>
              <StatNumber>{piB.resourceCount}</StatNumber>
              {deltaResources !== 0 && (
                <StatHelpText>
                  <HStack spacing={1} display="inline-flex" alignItems="center">
                    <Icon
                      as={deltaResources > 0 ? TrendingUp : TrendingDown}
                      boxSize={3.5}
                    />
                    <Text as="span">{deltaResources > 0 ? '+' : ''}{deltaResources}</Text>
                  </HStack>
                </StatHelpText>
              )}
            </Stat>
          </StatGroup>
        </CardBody>
      </Card>

      {/* Delta Visualization Chart */}
      {(piA.totalAllocated > 0 || piB.totalAllocated > 0) && (
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Text fontWeight="bold" fontSize="lg">Baseline vs Current</Text>
          </CardHeader>
          <CardBody pt={0}>
            <LazyPlot
              data={[
                {
                  type: 'bar',
                  name: labelA,
                  x: ['Total Hours', 'Total Cost ($)', 'Utilization (%)'],
                  y: [piA.totalAllocated, piA.totalCost, piA.utilization],
                  marker: { color: TEXT_MUTED },
                  text: [
                    `${piA.totalAllocated.toLocaleString()}h`,
                    `$${piA.totalCost.toLocaleString()}`,
                    `${piA.utilization.toFixed(1)}%`,
                  ],
                  textposition: 'outside',
                },
                {
                  type: 'bar',
                  name: labelB,
                  x: ['Total Hours', 'Total Cost ($)', 'Utilization (%)'],
                  y: [piB.totalAllocated, piB.totalCost, piB.utilization],
                  marker: { color: BLUE },
                  text: [
                    `${piB.totalAllocated.toLocaleString()}h`,
                    `$${piB.totalCost.toLocaleString()}`,
                    `${piB.utilization.toFixed(1)}%`,
                  ],
                  textposition: 'outside',
                },
              ]}
              layout={plotlyLayout({
                barmode: 'group',
                height: 300,
                yaxis: { title: { text: 'Value' }, gridcolor: '#2a2a30', zerolinecolor: '#35353d' },
                xaxis: { gridcolor: '#2a2a30', zerolinecolor: '#35353d' },
                legend: { orientation: 'h', y: 1.15, x: 0.5, xanchor: 'center', bgcolor: 'rgba(0,0,0,0)', bordercolor: '#2a2a30', font: { color: TEXT_MUTED } },
                margin: { l: 60, r: 40, t: 50, b: 40 },
              })}
              config={PLOTLY_CONFIG}
              style={{ width: '100%', height: '300px' }}
            />
          </CardBody>
        </Card>
      )}

      {/* Side-by-Side */}
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Text fontWeight="bold">{labelA}</Text>
          </CardHeader>
          <CardBody pt={0}>
            <VStack align="stretch" spacing={2}>
              <HStack justify="space-between">
                <Text fontSize="sm">Allocated</Text>
                <Text fontWeight="medium">{piA.totalAllocated.toLocaleString()}h</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Capacity</Text>
                <Text fontWeight="medium">{piA.totalCapacity.toLocaleString()}h</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Utilization</Text>
                <Text fontWeight="medium">{piA.utilization.toFixed(1)}%</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Cost</Text>
                <Text fontWeight="medium">${piA.totalCost.toLocaleString()}</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Resources</Text>
                <Text fontWeight="medium">{piA.resourceCount}</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Projects</Text>
                <Text fontWeight="medium">{piA.projectCount}</Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Text fontWeight="bold">{labelB}</Text>
          </CardHeader>
          <CardBody pt={0}>
            <VStack align="stretch" spacing={2}>
              <HStack justify="space-between">
                <Text fontSize="sm">Allocated</Text>
                <Text fontWeight="medium">{piB.totalAllocated.toLocaleString()}h</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Capacity</Text>
                <Text fontWeight="medium">{piB.totalCapacity.toLocaleString()}h</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Utilization</Text>
                <Text fontWeight="medium">{piB.utilization.toFixed(1)}%</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Cost</Text>
                <Text fontWeight="medium">${piB.totalCost.toLocaleString()}</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Resources</Text>
                <Text fontWeight="medium">{piB.resourceCount}</Text>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="sm">Projects</Text>
                <Text fontWeight="medium">{piB.projectCount}</Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Resource Changes */}
      <ResourceChanges
        resourcesA={piA.resources}
        resourcesB={piB.resources}
        cardBg={cardBg}
      />

      {/* Project Changes */}
      <ProjectChanges
        projectsA={piA.projects}
        projectsB={piB.projects}
        cardBg={cardBg}
      />

      {/* Assessment */}
      <Card bg={cardBg}>
        <CardHeader pb={2}>
          <Text fontWeight="bold" fontSize="lg">Assessment</Text>
        </CardHeader>
        <CardBody pt={0}>
          {(() => {
            if (deltaHours > 0 && deltaUtil <= 10) {
              return (
                <Alert status="success" borderRadius="md">
                  <AlertIcon />
                  Increased allocation by {deltaHours.toLocaleString()}h while maintaining healthy utilization ({piB.utilization.toFixed(1)}%)
                </Alert>
              );
            } else if (deltaHours < 0 && deltaCost < 0) {
              return (
                <Alert status="info" borderRadius="md">
                  <AlertIcon />
                  Reduced scope by {Math.abs(deltaHours).toLocaleString()}h, saving ${Math.abs(deltaCost).toLocaleString()}
                </Alert>
              );
            } else if (piB.utilization > 100) {
              return (
                <Alert status="error" borderRadius="md">
                  <AlertIcon />
                  Over-allocated at {piB.utilization.toFixed(1)}% - consider reducing scope or adding resources
                </Alert>
              );
            } else if (deltaCost > 0 && deltaHours <= 0) {
              return (
                <Alert status="warning" borderRadius="md">
                  <AlertIcon />
                  Cost increased by ${deltaCost.toLocaleString()} without adding hours - check rate changes
                </Alert>
              );
            } else {
              return (
                <Alert status="info" borderRadius="md">
                  <AlertIcon />
                  Hours: {deltaHours >= 0 ? '+' : ''}{deltaHours.toLocaleString()}h |
                  Utilization: {deltaUtil >= 0 ? '+' : ''}{deltaUtil.toFixed(1)}% |
                  Cost: {deltaCost >= 0 ? '+' : ''}${deltaCost.toLocaleString()}
                </Alert>
              );
            }
          })()}
        </CardBody>
      </Card>
    </VStack>
  );
}

// ─── Resource Changes ───────────────────────────────────────────

function ResourceChanges({
  resourcesA,
  resourcesB,
  cardBg,
}: {
  resourcesA: Record<string, ResourceEntry>;
  resourcesB: Record<string, ResourceEntry>;
  cardBg: string;
}) {
  const addedBg = useColorModeValue('green.50', 'green.900');
  const removedBg = useColorModeValue('red.50', 'red.900');
  const allNames = new Set([...Object.keys(resourcesA), ...Object.keys(resourcesB)]);

  const added: Array<{ name: string; hours: number; rate: number }> = [];
  const removed: Array<{ name: string; hours: number; rate: number }> = [];
  const changed: Array<{ name: string; hoursA: number; hoursB: number; delta: number }> = [];

  allNames.forEach(name => {
    const inA = name in resourcesA;
    const inB = name in resourcesB;

    if (inA && !inB) {
      removed.push({ name, hours: resourcesA[name].total_hours || 0, rate: resourcesA[name].rate || 0 });
    } else if (inB && !inA) {
      added.push({ name, hours: resourcesB[name].total_hours || 0, rate: resourcesB[name].rate || 0 });
    } else {
      const hoursA = resourcesA[name].total_hours || 0;
      const hoursB = resourcesB[name].total_hours || 0;
      if (Math.abs(hoursA - hoursB) > 0.1) {
        changed.push({ name, hoursA, hoursB, delta: hoursB - hoursA });
      }
    }
  });

  if (added.length === 0 && removed.length === 0 && changed.length === 0) {
    return (
      <Card bg={cardBg}>
        <CardHeader pb={2}>
          <Text fontWeight="bold" fontSize="lg">Resource Changes</Text>
        </CardHeader>
        <CardBody pt={0}>
          <Alert status="info" borderRadius="md">
            <AlertIcon />
            No resource changes detected between analyses.
          </Alert>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card bg={cardBg}>
      <CardHeader pb={2}>
        <Text fontWeight="bold" fontSize="lg">Resource Changes</Text>
      </CardHeader>
      <CardBody pt={0}>
        <Accordion allowMultiple>
          {added.length > 0 && (
            <AccordionItem>
              <AccordionButton>
                <Box flex={1} textAlign="left">
                  <Badge colorScheme="green" mr={2}>+</Badge>
                  Added Resources ({added.length})
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel>
                <VStack align="stretch" spacing={2}>
                  {added.map((r, i) => (
                    <HStack key={`${r.name}-${i}`} justify="space-between" p={2} bg={addedBg} borderRadius="md">
                      <Text fontWeight="medium">{r.name}</Text>
                      <Text>{r.hours.toLocaleString()}h @ ${r.rate}/hr = ${(r.hours * r.rate).toLocaleString()}</Text>
                    </HStack>
                  ))}
                </VStack>
              </AccordionPanel>
            </AccordionItem>
          )}

          {removed.length > 0 && (
            <AccordionItem>
              <AccordionButton>
                <Box flex={1} textAlign="left">
                  <Badge colorScheme="red" mr={2}>-</Badge>
                  Removed Resources ({removed.length})
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel>
                <VStack align="stretch" spacing={2}>
                  {removed.map((r, i) => (
                    <HStack key={`${r.name}-${i}`} justify="space-between" p={2} bg={removedBg} borderRadius="md">
                      <Text fontWeight="medium">{r.name}</Text>
                      <Text>{r.hours.toLocaleString()}h @ ${r.rate}/hr = ${(r.hours * r.rate).toLocaleString()}</Text>
                    </HStack>
                  ))}
                </VStack>
              </AccordionPanel>
            </AccordionItem>
          )}

          {changed.length > 0 && (
            <AccordionItem>
              <AccordionButton>
                <Box flex={1} textAlign="left">
                  <Badge colorScheme="blue" mr={2}>~</Badge>
                  Changed Resources ({changed.length})
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel>
                <Box overflowX="auto">
                <Table size="sm" variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Resource</Th>
                      <Th isNumeric>Before</Th>
                      <Th isNumeric>After</Th>
                      <Th isNumeric>Change</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {changed.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)).map((r, i) => (
                      <Tr key={`${r.name}-${i}`}>
                        <Td>{r.name}</Td>
                        <Td isNumeric>{r.hoursA.toLocaleString()}h</Td>
                        <Td isNumeric>{r.hoursB.toLocaleString()}h</Td>
                        <Td isNumeric color={r.delta > 0 ? 'green.500' : 'red.500'}>
                          {r.delta > 0 ? '+' : ''}{r.delta.toLocaleString()}h
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                </Box>
              </AccordionPanel>
            </AccordionItem>
          )}
        </Accordion>
      </CardBody>
    </Card>
  );
}

// ─── Project Changes ────────────────────────────────────────────

function ProjectChanges({
  projectsA,
  projectsB,
  cardBg,
}: {
  projectsA: Record<string, ProjectEntry>;
  projectsB: Record<string, ProjectEntry>;
  cardBg: string;
}) {
  const addedBg = useColorModeValue('green.50', 'green.900');
  const removedBg = useColorModeValue('red.50', 'red.900');
  const allNames = new Set([...Object.keys(projectsA), ...Object.keys(projectsB)]);

  const added: Array<{ name: string; hours: number }> = [];
  const removed: Array<{ name: string; hours: number }> = [];
  const changed: Array<{ name: string; hoursA: number; hoursB: number; delta: number }> = [];

  allNames.forEach(name => {
    const inA = name in projectsA;
    const inB = name in projectsB;

    if (inA && !inB) {
      removed.push({ name, hours: projectsA[name].total_hours || 0 });
    } else if (inB && !inA) {
      added.push({ name, hours: projectsB[name].total_hours || 0 });
    } else {
      const hoursA = projectsA[name].total_hours || 0;
      const hoursB = projectsB[name].total_hours || 0;
      if (Math.abs(hoursA - hoursB) > 0.1) {
        changed.push({ name, hoursA, hoursB, delta: hoursB - hoursA });
      }
    }
  });

  if (added.length === 0 && removed.length === 0 && changed.length === 0) {
    return (
      <Card bg={cardBg}>
        <CardHeader pb={2}>
          <Text fontWeight="bold" fontSize="lg">Project Changes</Text>
        </CardHeader>
        <CardBody pt={0}>
          <Alert status="info" borderRadius="md">
            <AlertIcon />
            No project changes detected between analyses.
          </Alert>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card bg={cardBg}>
      <CardHeader pb={2}>
        <Text fontWeight="bold" fontSize="lg">Project Changes</Text>
      </CardHeader>
      <CardBody pt={0}>
        <Accordion allowMultiple>
          {added.length > 0 && (
            <AccordionItem>
              <AccordionButton>
                <Box flex={1} textAlign="left">
                  <Badge colorScheme="green" mr={2}>+</Badge>
                  Added Projects ({added.length})
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel>
                <VStack align="stretch" spacing={2}>
                  {added.map((p, i) => (
                    <HStack key={`${p.name}-${i}`} justify="space-between" p={2} bg={addedBg} borderRadius="md">
                      <Text fontWeight="medium" noOfLines={1}>{p.name}</Text>
                      <Text>{p.hours.toLocaleString()}h</Text>
                    </HStack>
                  ))}
                </VStack>
              </AccordionPanel>
            </AccordionItem>
          )}

          {removed.length > 0 && (
            <AccordionItem>
              <AccordionButton>
                <Box flex={1} textAlign="left">
                  <Badge colorScheme="red" mr={2}>-</Badge>
                  Removed Projects ({removed.length})
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel>
                <VStack align="stretch" spacing={2}>
                  {removed.map((p, i) => (
                    <HStack key={`${p.name}-${i}`} justify="space-between" p={2} bg={removedBg} borderRadius="md">
                      <Text fontWeight="medium" noOfLines={1}>{p.name}</Text>
                      <Text>{p.hours.toLocaleString()}h</Text>
                    </HStack>
                  ))}
                </VStack>
              </AccordionPanel>
            </AccordionItem>
          )}

          {changed.length > 0 && (
            <AccordionItem>
              <AccordionButton>
                <Box flex={1} textAlign="left">
                  <Badge colorScheme="blue" mr={2}>~</Badge>
                  Changed Projects ({changed.length})
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel>
                <Box overflowX="auto">
                <Table size="sm" variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Project</Th>
                      <Th isNumeric>Before</Th>
                      <Th isNumeric>After</Th>
                      <Th isNumeric>Change</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {changed.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)).slice(0, 20).map((p, i) => (
                      <Tr key={`${p.name}-${i}`}>
                        <Td noOfLines={1} maxW="200px">{p.name}</Td>
                        <Td isNumeric>{p.hoursA.toLocaleString()}h</Td>
                        <Td isNumeric>{p.hoursB.toLocaleString()}h</Td>
                        <Td isNumeric color={p.delta > 0 ? 'green.500' : 'red.500'}>
                          {p.delta > 0 ? '+' : ''}{p.delta.toLocaleString()}h
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                </Box>
                {changed.length > 20 && (
                  <Text fontSize="sm" color="gray.500" mt={2}>
                    ...and {changed.length - 20} more projects with changes
                  </Text>
                )}
              </AccordionPanel>
            </AccordionItem>
          )}
        </Accordion>
      </CardBody>
    </Card>
  );
}
