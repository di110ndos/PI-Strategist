/**
 * What-If Scenario Planning page.
 */

import { useState, useMemo } from 'react';
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
  Input,
  Textarea,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  FormControl,
  FormLabel,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatGroup,
  Alert,
  AlertIcon,
  Progress,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Checkbox,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Icon,
  useDisclosure,
  useColorModeValue,
  useToast,
  Divider,
} from '@chakra-ui/react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAnalysisStore } from '../store/analysisStore';
import { LazyPlot } from '../components/charts';
import { plotlyLayout, PLOTLY_CONFIG, CHART_PALETTE, TEXT_MUTED } from '../components/charts/plotlyDefaults';

// Types
interface Resource {
  name: string;
  discipline: string;
  total_hours: number;
  rate: number;
}

interface Project {
  name: string;
  total_hours: number;
  cost: number;
  resource_hours: Record<string, number>;
}

interface PIAnalysis {
  total_capacity: number;
  total_allocated: number;
  resources: Record<string, Resource>;
  projects: Record<string, Project>;
}

interface Scenario {
  id: string;
  name: string;
  description: string;
  resource_adjustments: Record<string, number>;
  removed_projects: string[];
  removed_resources: string[];
  added_resources: Array<{ name: string; hours: number; rate: number }>;
}

interface ScenarioImpact {
  modified_capacity: number;
  modified_allocated: number;
  modified_cost: number;
  utilization_delta: number;
  cost_delta: number;
}

function buildPIAnalysisFromStore(results: Record<string, unknown>): PIAnalysis | null {
  const piAnalysis = results?.pi_analysis as Record<string, unknown> | undefined;
  if (!piAnalysis) return null;

  const rawResources = (piAnalysis.resources || {}) as Record<string, Record<string, unknown>>;

  const resources: Record<string, Resource> = {};
  for (const [key, r] of Object.entries(rawResources)) {
    resources[key] = {
      name: (r.name as string) || key,
      discipline: (r.discipline as string) || '',
      total_hours: (r.total_hours as number) || 0,
      rate: (r.rate as number) || 0,
    };
  }

  // Build projects with computed costs
  const rawProjects = (piAnalysis.projects || {}) as Record<string, Record<string, unknown>>;
  const projects: Record<string, Project> = {};
  for (const [key, p] of Object.entries(rawProjects)) {
    const resourceHours = (p.resource_hours || {}) as Record<string, number>;
    let cost = 0;
    for (const [resName, hours] of Object.entries(resourceHours)) {
      const rate = resources[resName]?.rate || 0;
      cost += hours * rate;
    }
    projects[key] = {
      name: (p.name as string) || key,
      total_hours: (p.total_hours as number) || 0,
      cost,
      resource_hours: resourceHours,
    };
  }

  return {
    total_capacity: (piAnalysis.total_capacity as number) || 0,
    total_allocated: (piAnalysis.total_allocated as number) || (piAnalysis.grand_total_hours as number) || 0,
    resources,
    projects,
  };
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

function calculateScenarioImpact(scenario: Scenario, baseAnalysis: PIAnalysis): ScenarioImpact {
  let modifiedCapacity = baseAnalysis.total_capacity;
  let modifiedAllocated = baseAnalysis.total_allocated;

  const baseCost = Object.values(baseAnalysis.resources).reduce(
    (sum, r) => sum + r.total_hours * r.rate,
    0
  );

  let modifiedCost = baseCost;

  // Apply resource adjustments
  for (const [resourceName, hoursDelta] of Object.entries(scenario.resource_adjustments)) {
    const resource = baseAnalysis.resources[resourceName];
    if (resource) {
      modifiedAllocated += hoursDelta;
      modifiedCost += hoursDelta * resource.rate;
    }
  }

  // Apply removed projects
  for (const projectName of scenario.removed_projects) {
    const project = baseAnalysis.projects[projectName];
    if (project) {
      modifiedAllocated -= project.total_hours;
      modifiedCost -= project.cost;
    }
  }

  // Apply removed resources
  for (const resourceName of scenario.removed_resources) {
    const resource = baseAnalysis.resources[resourceName];
    if (resource) {
      modifiedAllocated -= resource.total_hours;
      modifiedCost -= resource.total_hours * resource.rate;
    }
  }

  // Apply added resources
  for (const added of scenario.added_resources) {
    modifiedAllocated += added.hours;
    modifiedCost += added.hours * added.rate;
  }

  const baseUtilization = baseAnalysis.total_capacity > 0
    ? (baseAnalysis.total_allocated / baseAnalysis.total_capacity) * 100
    : 0;
  const modifiedUtilization = modifiedCapacity > 0
    ? (modifiedAllocated / modifiedCapacity) * 100
    : 0;

  return {
    modified_capacity: modifiedCapacity,
    modified_allocated: modifiedAllocated,
    modified_cost: modifiedCost,
    utilization_delta: modifiedUtilization - baseUtilization,
    cost_delta: modifiedCost - baseCost,
  };
}

export default function ScenariosPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  const deleteModal = useDisclosure();

  const latestAnalysis = useAnalysisStore((s) => s.latestAnalysis);
  const baseAnalysis = useMemo(
    () => (latestAnalysis ? buildPIAnalysisFromStore(latestAnalysis.results) : null),
    [latestAnalysis]
  );
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const [scenarioToDelete, setScenarioToDelete] = useState<string | null>(null);

  const baseCost = useMemo(() => {
    if (!baseAnalysis) return 0;
    return Object.values(baseAnalysis.resources).reduce(
      (sum, r) => sum + r.total_hours * r.rate,
      0
    );
  }, [baseAnalysis]);

  const baseUtilization = useMemo(() => {
    if (!baseAnalysis || baseAnalysis.total_capacity === 0) return 0;
    return (baseAnalysis.total_allocated / baseAnalysis.total_capacity) * 100;
  }, [baseAnalysis]);

  const createScenario = (name?: string, template?: Partial<Scenario>) => {
    const newScenario: Scenario = {
      id: generateId(),
      name: name || `Scenario ${scenarios.length + 1}`,
      description: '',
      resource_adjustments: {},
      removed_projects: [],
      removed_resources: [],
      added_resources: [],
      ...template,
    };
    setScenarios([...scenarios, newScenario]);
    setActiveTabIndex(scenarios.length);
    toast({ title: `Created "${newScenario.name}"`, status: 'success', duration: 2000 });
  };

  const updateScenario = (id: string, updates: Partial<Scenario>) => {
    setScenarios(scenarios.map(s => s.id === id ? { ...s, ...updates } : s));
  };

  const deleteScenario = (id: string) => {
    setScenarios(scenarios.filter(s => s.id !== id));
    setActiveTabIndex(0);
    toast({ title: 'Scenario deleted', status: 'info', duration: 2000 });
    deleteModal.onClose();
  };

  const handleDeleteClick = (id: string) => {
    setScenarioToDelete(id);
    deleteModal.onOpen();
  };

  if (!baseAnalysis) {
    return (
      <Box px={{ base: 4, md: 6, lg: 8 }} py={8}>
        <Alert status="warning" borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">No PI analysis data available.</Text>
            <Text>
              Please go to the Analysis page and upload your capacity planner Excel file first.
              The scenario planner uses that data as the baseline for simulations.
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
            What-If Scenario Planning
          </Heading>
          <Text color="gray.500">
            Simulate changes to your PI plan and compare different scenarios.
          </Text>
        </Box>

        {/* Baseline Metrics */}
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Text fontWeight="bold">Baseline Metrics</Text>
          </CardHeader>
          <CardBody pt={0}>
            <StatGroup>
              <Stat>
                <StatLabel>Total Capacity</StatLabel>
                <StatNumber>{baseAnalysis.total_capacity.toLocaleString()}h</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Total Allocated</StatLabel>
                <StatNumber>{baseAnalysis.total_allocated.toLocaleString()}h</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Utilization</StatLabel>
                <StatNumber>{baseUtilization.toFixed(1)}%</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Total Cost</StatLabel>
                <StatNumber>${baseCost.toLocaleString()}</StatNumber>
              </Stat>
            </StatGroup>
          </CardBody>
        </Card>

        {/* Quick Start Templates */}
        <Card bg={cardBg}>
          <CardHeader pb={2}>
            <Text fontWeight="bold">Quick Start Templates</Text>
          </CardHeader>
          <CardBody pt={0}>
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
              <Button
                variant="outline"
                onClick={() => createScenario()}
                leftIcon={<Text>+</Text>}
              >
                New Scenario
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  const adjustments: Record<string, number> = {};
                  Object.entries(baseAnalysis.resources).forEach(([name, resource]) => {
                    adjustments[name] = -resource.total_hours * 0.1;
                  });
                  createScenario('Reduced Capacity', { resource_adjustments: adjustments });
                }}
              >
                Reduce 10% Capacity
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  createScenario('Added Contractor', {
                    added_resources: [{ name: 'Contractor', hours: 160, rate: 150 }],
                  });
                }}
              >
                Add Contractor
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  const adjustments: Record<string, number> = {};
                  Object.entries(baseAnalysis.resources).forEach(([name, resource]) => {
                    adjustments[name] = resource.total_hours * 0.2;
                  });
                  createScenario('Aggressive Timeline', { resource_adjustments: adjustments });
                }}
              >
                Aggressive Timeline
              </Button>
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* Scenarios */}
        {scenarios.length > 0 ? (
          <Card bg={cardBg}>
            <CardBody>
              <Tabs
                index={activeTabIndex}
                onChange={setActiveTabIndex}
                colorScheme="blue"
              >
                <TabList flexWrap="wrap">
                  {scenarios.map((scenario) => (
                    <Tab key={scenario.id}>{scenario.name}</Tab>
                  ))}
                  <Tab>Compare All</Tab>
                </TabList>

                <TabPanels>
                  {scenarios.map((scenario) => (
                    <TabPanel key={scenario.id}>
                      <ScenarioEditor
                        scenario={scenario}
                        baseAnalysis={baseAnalysis}
                        baseCost={baseCost}
                        onUpdate={(updates) => updateScenario(scenario.id, updates)}
                        onDelete={() => handleDeleteClick(scenario.id)}
                      />
                    </TabPanel>
                  ))}
                  <TabPanel>
                    <ScenarioComparison
                      scenarios={scenarios}
                      baseAnalysis={baseAnalysis}
                      baseCost={baseCost}
                    />
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </CardBody>
          </Card>
        ) : (
          <Alert status="info" borderRadius="md">
            <AlertIcon />
            No scenarios created yet. Use the templates above to create a new scenario.
          </Alert>
        )}
      </VStack>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={deleteModal.isOpen} onClose={deleteModal.onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Delete Scenario</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            Are you sure you want to delete this scenario? This action cannot be undone.
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={deleteModal.onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="red"
              onClick={() => scenarioToDelete && deleteScenario(scenarioToDelete)}
            >
              Delete
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}

// Scenario Editor Component
interface ScenarioEditorProps {
  scenario: Scenario;
  baseAnalysis: PIAnalysis;
  baseCost: number;
  onUpdate: (updates: Partial<Scenario>) => void;
  onDelete: () => void;
}

function ScenarioEditor({ scenario, baseAnalysis, baseCost, onUpdate, onDelete }: ScenarioEditorProps) {
  const cardBg = useColorModeValue('gray.50', 'gray.700');
  const impact = calculateScenarioImpact(scenario, baseAnalysis);
  const modifiedUtilization = impact.modified_capacity > 0
    ? (impact.modified_allocated / impact.modified_capacity) * 100
    : 0;

  const getStatusColor = () => {
    if (modifiedUtilization > 100) return 'red';
    if (modifiedUtilization > 90) return 'yellow';
    if (modifiedUtilization < 60) return 'blue';
    return 'green';
  };

  return (
    <VStack spacing={6} align="stretch">
      {/* Scenario Header */}
      <HStack justify="space-between">
        <Box flex={1}>
          <FormControl>
            <FormLabel>Scenario Name</FormLabel>
            <Input
              value={scenario.name}
              onChange={(e) => onUpdate({ name: e.target.value })}
            />
          </FormControl>
        </Box>
        <Button colorScheme="red" variant="outline" onClick={onDelete}>
          Delete
        </Button>
      </HStack>

      <FormControl>
        <FormLabel>Description</FormLabel>
        <Textarea
          value={scenario.description}
          onChange={(e) => onUpdate({ description: e.target.value })}
          placeholder="Describe the purpose of this scenario..."
          rows={2}
        />
      </FormControl>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
        {/* Left Column - Modifications */}
        <VStack spacing={4} align="stretch">
          <Text fontWeight="bold" fontSize="lg">Modifications</Text>

          {/* Resource Adjustments */}
          <Accordion allowMultiple>
            <AccordionItem>
              <AccordionButton>
                <Box flex={1} textAlign="left">
                  <Text fontWeight="medium">Adjust Resource Hours</Text>
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel>
                <VStack spacing={3} align="stretch">
                  {Object.entries(baseAnalysis.resources).map(([name, resource]) => {
                    const adjustment = scenario.resource_adjustments[name] || 0;
                    const maxAdjust = resource.total_hours * 0.5;

                    return (
                      <Box key={name} p={3} bg={cardBg} borderRadius="md">
                        <HStack justify="space-between" mb={2}>
                          <Text fontWeight="medium">{name}</Text>
                          <Badge colorScheme={adjustment > 0 ? 'green' : adjustment < 0 ? 'red' : 'gray'}>
                            {adjustment > 0 ? '+' : ''}{adjustment.toFixed(0)}h
                          </Badge>
                        </HStack>
                        <Text fontSize="xs" color="gray.500" mb={2}>
                          Base: {resource.total_hours}h @ ${resource.rate}/hr
                        </Text>
                        <Slider
                          value={adjustment}
                          onChange={(val) => onUpdate({
                            resource_adjustments: { ...scenario.resource_adjustments, [name]: val },
                          })}
                          min={-maxAdjust}
                          max={maxAdjust}
                          step={8}
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                      </Box>
                    );
                  })}
                </VStack>
              </AccordionPanel>
            </AccordionItem>

            <AccordionItem>
              <AccordionButton>
                <Box flex={1} textAlign="left">
                  <Text fontWeight="medium">Remove Projects</Text>
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel>
                <VStack spacing={3} align="stretch">
                  {Object.keys(baseAnalysis.projects).length === 0 ? (
                    <Text fontSize="sm" color="gray.500">
                      No project data available. Ensure your capacity planner has project allocations.
                    </Text>
                  ) : (
                    Object.entries(baseAnalysis.projects)
                      .sort((a, b) => b[1].total_hours - a[1].total_hours)
                      .map(([name, project]) => {
                        const isRemoved = scenario.removed_projects.includes(name);
                        return (
                          <Box key={name} p={3} bg={cardBg} borderRadius="md" opacity={isRemoved ? 0.6 : 1}>
                            <Checkbox
                              isChecked={isRemoved}
                              onChange={(e) => {
                                const updated = e.target.checked
                                  ? [...scenario.removed_projects, name]
                                  : scenario.removed_projects.filter(p => p !== name);
                                onUpdate({ removed_projects: updated });
                              }}
                              colorScheme="red"
                            >
                              <Text fontWeight="medium" as="span" textDecoration={isRemoved ? 'line-through' : 'none'}>
                                {project.name}
                              </Text>
                            </Checkbox>
                            <HStack mt={1} ml={6} spacing={4}>
                              <Text fontSize="xs" color="gray.500">
                                {project.total_hours.toLocaleString()}h
                              </Text>
                              <Text fontSize="xs" color="gray.500">
                                ${project.cost.toLocaleString()}
                              </Text>
                            </HStack>
                          </Box>
                        );
                      })
                  )}
                </VStack>
              </AccordionPanel>
            </AccordionItem>

          </Accordion>
        </VStack>

        {/* Right Column - Impact */}
        <VStack spacing={4} align="stretch">
          <Text fontWeight="bold" fontSize="lg">Live Impact Preview</Text>

          {/* Status */}
          <Alert status={getStatusColor() === 'green' ? 'success' : getStatusColor() === 'yellow' ? 'warning' : 'error'} borderRadius="md">
            <AlertIcon />
            <Text>
              {modifiedUtilization > 100
                ? `Over-allocated (${modifiedUtilization.toFixed(1)}%)`
                : modifiedUtilization > 90
                ? `High utilization (${modifiedUtilization.toFixed(1)}%)`
                : modifiedUtilization < 60
                ? `Low utilization (${modifiedUtilization.toFixed(1)}%)`
                : `Healthy (${modifiedUtilization.toFixed(1)}%)`}
            </Text>
          </Alert>

          {/* Utilization Impact Gauge */}
          <UtilizationImpactGauge
            baselineUtilization={baseAnalysis.total_capacity > 0
              ? (baseAnalysis.total_allocated / baseAnalysis.total_capacity) * 100
              : 0}
            scenarioUtilization={modifiedUtilization}
          />

          {/* Metrics */}
          <SimpleGrid columns={3} spacing={4}>
            <Stat>
              <StatLabel>Hours</StatLabel>
              <StatNumber fontSize="lg">{impact.modified_allocated.toLocaleString()}h</StatNumber>
              <StatHelpText color={impact.modified_allocated > baseAnalysis.total_allocated ? 'green.500' : 'red.500'}>
                {impact.modified_allocated - baseAnalysis.total_allocated > 0 ? '+' : ''}
                {(impact.modified_allocated - baseAnalysis.total_allocated).toLocaleString()}h
              </StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Utilization</StatLabel>
              <StatNumber fontSize="lg">{modifiedUtilization.toFixed(1)}%</StatNumber>
              <StatHelpText color={impact.utilization_delta > 0 ? 'orange.500' : 'green.500'}>
                {impact.utilization_delta > 0 ? '+' : ''}{impact.utilization_delta.toFixed(1)}%
              </StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Cost</StatLabel>
              <StatNumber fontSize="lg">${impact.modified_cost.toLocaleString()}</StatNumber>
              <StatHelpText color={impact.cost_delta > 0 ? 'red.500' : 'green.500'}>
                {impact.cost_delta > 0 ? '+' : ''}${impact.cost_delta.toLocaleString()}
              </StatHelpText>
            </Stat>
          </SimpleGrid>

          {/* Before vs After */}
          <Divider />
          <SimpleGrid columns={2} spacing={4}>
            <Box p={3} bg={cardBg} borderRadius="md">
              <Text fontWeight="bold" mb={2}>Baseline</Text>
              <Text fontSize="sm">Hours: {baseAnalysis.total_allocated.toLocaleString()}h</Text>
              <Text fontSize="sm">Util: {((baseAnalysis.total_allocated / baseAnalysis.total_capacity) * 100).toFixed(1)}%</Text>
              <Text fontSize="sm">Cost: ${baseCost.toLocaleString()}</Text>
            </Box>
            <Box p={3} bg={cardBg} borderRadius="md">
              <Text fontWeight="bold" mb={2}>Scenario</Text>
              <Text fontSize="sm">Hours: {impact.modified_allocated.toLocaleString()}h</Text>
              <Text fontSize="sm">Util: {modifiedUtilization.toFixed(1)}%</Text>
              <Text fontSize="sm">Cost: ${impact.modified_cost.toLocaleString()}</Text>
            </Box>
          </SimpleGrid>
        </VStack>
      </SimpleGrid>
    </VStack>
  );
}

// Scenario Comparison Component
interface ScenarioComparisonProps {
  scenarios: Scenario[];
  baseAnalysis: PIAnalysis;
  baseCost: number;
}

function ScenarioComparison({ scenarios, baseAnalysis, baseCost }: ScenarioComparisonProps) {
  const cardBg = useColorModeValue('gray.50', 'gray.700');
  const baseUtilization = baseAnalysis.total_capacity > 0
    ? (baseAnalysis.total_allocated / baseAnalysis.total_capacity) * 100
    : 0;

  if (scenarios.length === 0) {
    return (
      <Alert status="info" borderRadius="md">
        <AlertIcon />
        Create scenarios to compare them here.
      </Alert>
    );
  }

  const scenarioImpacts = scenarios.map(s => ({
    scenario: s,
    impact: calculateScenarioImpact(s, baseAnalysis),
  }));

  return (
    <VStack spacing={6} align="stretch">
      <Text fontWeight="bold" fontSize="lg">Scenario Comparison</Text>

      {/* Multi-Scenario Comparison Chart */}
      {scenarios.length >= 2 && (
        <Box>
          <LazyPlot
            data={[
              // Baseline trace
              {
                type: 'bar',
                name: 'Baseline',
                x: ['Hours', 'Cost ($)', 'Utilization (%)'],
                y: [baseAnalysis.total_allocated, baseCost, baseUtilization],
                marker: { color: TEXT_MUTED },
                text: [
                  `${baseAnalysis.total_allocated.toLocaleString()}h`,
                  `$${baseCost.toLocaleString()}`,
                  `${baseUtilization.toFixed(1)}%`,
                ],
                textposition: 'outside',
              },
              // One trace per scenario
              ...scenarioImpacts.map(({ scenario, impact }, idx) => {
                const util = impact.modified_capacity > 0
                  ? (impact.modified_allocated / impact.modified_capacity) * 100
                  : 0;
                return {
                  type: 'bar' as const,
                  name: scenario.name,
                  x: ['Hours', 'Cost ($)', 'Utilization (%)'],
                  y: [impact.modified_allocated, impact.modified_cost, util],
                  marker: { color: CHART_PALETTE[idx % CHART_PALETTE.length] },
                  text: [
                    `${impact.modified_allocated.toLocaleString()}h`,
                    `$${impact.modified_cost.toLocaleString()}`,
                    `${util.toFixed(1)}%`,
                  ],
                  textposition: 'outside' as const,
                };
              }),
            ]}
            layout={plotlyLayout({
              barmode: 'group',
              height: 320,
              yaxis: { title: { text: 'Value' }, gridcolor: '#2a2a30', zerolinecolor: '#35353d' },
              xaxis: { gridcolor: '#2a2a30', zerolinecolor: '#35353d' },
              legend: { orientation: 'h', y: 1.18, x: 0.5, xanchor: 'center', bgcolor: 'rgba(0,0,0,0)', bordercolor: '#2a2a30', font: { color: TEXT_MUTED } },
              margin: { l: 60, r: 40, t: 60, b: 40 },
            })}
            config={PLOTLY_CONFIG}
            style={{ width: '100%', height: '320px' }}
          />
        </Box>
      )}

      <Box overflowX="auto">
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Scenario</Th>
            <Th isNumeric>Allocated</Th>
            <Th isNumeric>Utilization</Th>
            <Th isNumeric>Cost</Th>
            <Th isNumeric>Cost Delta</Th>
            <Th>Status</Th>
          </Tr>
        </Thead>
        <Tbody>
          <Tr bg={cardBg}>
            <Td fontWeight="bold">Baseline</Td>
            <Td isNumeric>{baseAnalysis.total_allocated.toLocaleString()}h</Td>
            <Td isNumeric>{baseUtilization.toFixed(1)}%</Td>
            <Td isNumeric>${baseCost.toLocaleString()}</Td>
            <Td isNumeric>-</Td>
            <Td>
              <Badge colorScheme={baseUtilization <= 100 ? 'green' : 'red'}>
                {baseUtilization <= 100 ? 'OK' : 'Over'}
              </Badge>
            </Td>
          </Tr>
          {scenarioImpacts.map(({ scenario, impact }) => {
            const util = impact.modified_capacity > 0
              ? (impact.modified_allocated / impact.modified_capacity) * 100
              : 0;
            return (
              <Tr key={scenario.id}>
                <Td>{scenario.name}</Td>
                <Td isNumeric>{impact.modified_allocated.toLocaleString()}h</Td>
                <Td isNumeric>{util.toFixed(1)}%</Td>
                <Td isNumeric>${impact.modified_cost.toLocaleString()}</Td>
                <Td isNumeric color={impact.cost_delta > 0 ? 'red.500' : 'green.500'}>
                  {impact.cost_delta > 0 ? '+' : ''}${impact.cost_delta.toLocaleString()}
                </Td>
                <Td>
                  <Badge colorScheme={util <= 100 ? 'green' : util <= 110 ? 'yellow' : 'red'}>
                    {util <= 100 ? 'OK' : 'Over'}
                  </Badge>
                </Td>
              </Tr>
            );
          })}
        </Tbody>
      </Table>
      </Box>

      {/* Utilization Bars */}
      <Box>
        <Text fontWeight="bold" mb={4}>Utilization Comparison</Text>
        <VStack spacing={3} align="stretch">
          {scenarioImpacts.map(({ scenario, impact }) => {
            const util = impact.modified_capacity > 0
              ? (impact.modified_allocated / impact.modified_capacity) * 100
              : 0;
            return (
              <Box key={scenario.id}>
                <HStack justify="space-between" mb={1}>
                  <Text fontSize="sm">{scenario.name}</Text>
                  <Text fontSize="sm" fontWeight="bold">{util.toFixed(0)}%</Text>
                </HStack>
                <Progress
                  value={Math.min(util, 100)}
                  colorScheme={util <= 80 ? 'green' : util <= 100 ? 'yellow' : 'red'}
                  borderRadius="full"
                  size="lg"
                />
              </Box>
            );
          })}
        </VStack>
      </Box>

      {/* Recommendation */}
      <Divider />
      <Box>
        <Text fontWeight="bold" mb={2}>Recommendation</Text>
        {(() => {
          const validScenarios = scenarioImpacts.filter(({ impact }) => {
            const util = impact.modified_capacity > 0
              ? (impact.modified_allocated / impact.modified_capacity) * 100
              : 0;
            return util <= 100;
          });

          if (validScenarios.length === 0) {
            return (
              <Alert status="warning" borderRadius="md">
                <AlertIcon />
                All scenarios result in over-allocation. Consider reducing scope or adding resources.
              </Alert>
            );
          }

          const best = validScenarios.reduce((prev, curr) => {
            const prevUtil = prev.impact.modified_allocated / prev.impact.modified_capacity;
            const currUtil = curr.impact.modified_allocated / curr.impact.modified_capacity;
            return currUtil > prevUtil ? curr : prev;
          });

          const bestUtil = (best.impact.modified_allocated / best.impact.modified_capacity) * 100;

          return (
            <Alert status="success" borderRadius="md">
              <AlertIcon />
              <Text>
                <strong>{best.scenario.name}</strong> provides the best balance with{' '}
                {bestUtil.toFixed(1)}% utilization and a cost impact of{' '}
                {best.impact.cost_delta > 0 ? '+' : ''}${best.impact.cost_delta.toLocaleString()}
              </Text>
            </Alert>
          );
        })()}
      </Box>
    </VStack>
  );
}

// ─── Utilization Impact Gauge ───────────────────────────────────

interface UtilizationImpactGaugeProps {
  baselineUtilization: number;
  scenarioUtilization: number;
}

function UtilizationImpactGauge({ baselineUtilization, scenarioUtilization }: UtilizationImpactGaugeProps) {
  const delta = scenarioUtilization - baselineUtilization;
  const isUp = delta >= 0;

  // Optimal range is 80-100%. Determine if moving toward or away from it.
  const baseDistFromOptimal = baselineUtilization < 80
    ? 80 - baselineUtilization
    : baselineUtilization > 100
    ? baselineUtilization - 100
    : 0;
  const scenarioDistFromOptimal = scenarioUtilization < 80
    ? 80 - scenarioUtilization
    : scenarioUtilization > 100
    ? scenarioUtilization - 100
    : 0;
  const movingTowardOptimal = scenarioDistFromOptimal < baseDistFromOptimal;
  const inOptimal = scenarioUtilization >= 80 && scenarioUtilization <= 100;

  const badgeColor = inOptimal
    ? 'green'
    : movingTowardOptimal
    ? 'green'
    : 'red';

  const label = inOptimal
    ? 'In Optimal Range'
    : movingTowardOptimal
    ? 'Toward Optimal'
    : 'Away from Optimal';

  return (
    <HStack spacing={3} p={3} borderWidth="1px" borderRadius="md" borderColor="gray.600">
      <Badge colorScheme={badgeColor} fontSize="sm" px={2} py={1}>
        {scenarioUtilization.toFixed(1)}%
      </Badge>
      <Icon
        as={isUp ? TrendingUp : TrendingDown}
        boxSize={4}
        color={movingTowardOptimal || inOptimal ? 'green.400' : 'red.400'}
      />
      <Text fontSize="sm" color={movingTowardOptimal || inOptimal ? 'green.400' : 'red.400'}>
        {label} (80-100%)
      </Text>
      {Math.abs(delta) > 0.05 && (
        <Text fontSize="xs" color="gray.500">
          {isUp ? '+' : ''}{delta.toFixed(1)}% from baseline
        </Text>
      )}
    </HStack>
  );
}
