/**
 * Risk Register Page — manage risks with heat map visualization.
 */

import { useState } from 'react';
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Input,
  Textarea,
  Select,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  FormControl,
  FormLabel,
  Card,
  CardBody,
  Badge,
  IconButton,
  Collapse,
  SimpleGrid,
  Skeleton,
  Alert,
  AlertIcon,
  Tag,
  TagLabel,
  Wrap,
  WrapItem,
  useColorModeValue,
  useToast,
} from '@chakra-ui/react';
import { Plus, Pencil, Trash2, X, Check, ChevronDown, ChevronUp } from 'lucide-react';

import {
  useRisks,
  useCreateRisk,
  useUpdateRisk,
  useDeleteRisk,
} from '../hooks/useRisks';
import KPICard from '../components/common/KPICard';
import { RiskHeatMap } from '../components/charts';
import { AlertTriangle, Shield, TrendingUp, BarChart3 } from 'lucide-react';
import type { Risk } from '../types';

const CATEGORY_COLORS: Record<string, string> = {
  technical: 'purple',
  resource: 'blue',
  schedule: 'orange',
  scope: 'teal',
  external: 'pink',
  general: 'gray',
};

const STATUS_COLORS: Record<string, string> = {
  open: 'red',
  mitigating: 'orange',
  mitigated: 'green',
  accepted: 'blue',
  closed: 'gray',
};

const STATUS_LABELS: Record<string, string> = {
  open: 'Open',
  mitigating: 'Mitigating',
  mitigated: 'Mitigated',
  accepted: 'Accepted',
  closed: 'Closed',
};

const ALL_STATUSES = ['open', 'mitigating', 'mitigated', 'accepted', 'closed'];

interface RiskFormData {
  title: string;
  description: string;
  category: Risk['category'];
  probability: number;
  impact: number;
  owner: string;
  mitigation_plan: string;
  status: Risk['status'];
}

const EMPTY_FORM: RiskFormData = {
  title: '',
  description: '',
  category: 'general',
  probability: 3,
  impact: 3,
  owner: '',
  mitigation_plan: '',
  status: 'open',
};

function getRiskScoreColorHex(score: number): string {
  if (score < 7) return 'green.400';
  if (score < 13) return 'yellow.400';
  if (score < 19) return 'orange.400';
  return 'red.400';
}

export default function RiskRegisterPage() {
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');

  // Filter state
  const [statusFilter, setStatusFilter] = useState<Set<string>>(new Set());

  // Queries & mutations
  const { data: risks, isLoading, isError, error } = useRisks();
  const createMutation = useCreateRisk();
  const updateMutation = useUpdateRisk();
  const deleteMutation = useDeleteRisk();

  // UI state
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<RiskFormData>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<RiskFormData>(EMPTY_FORM);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Filter logic
  const filteredRisks = risks
    ? statusFilter.size === 0
      ? risks
      : risks.filter((r) => statusFilter.has(r.status))
    : [];

  const toggleFilter = (value: string) => {
    setStatusFilter((prev) => {
      const next = new Set(prev);
      if (next.has(value)) {
        next.delete(value);
      } else {
        next.add(value);
      }
      return next;
    });
  };

  // Summary calculations
  const totalRisks = risks?.length || 0;
  const openRisks = risks?.filter((r) => r.status === 'open').length || 0;
  const avgScore =
    totalRisks > 0
      ? (risks!.reduce((sum, r) => sum + r.risk_score, 0) / totalRisks)
      : 0;
  const highestRisk = risks && risks.length > 0
    ? risks.reduce((max, r) => (r.risk_score > max.risk_score ? r : max), risks[0])
    : null;

  const handleCreate = () => {
    if (!formData.title.trim()) {
      toast({ title: 'Title is required', status: 'warning', duration: 2000 });
      return;
    }

    createMutation.mutate(
      {
        title: formData.title,
        description: formData.description,
        category: formData.category,
        probability: formData.probability,
        impact: formData.impact,
        owner: formData.owner,
        mitigation_plan: formData.mitigation_plan,
      },
      {
        onSuccess: () => {
          toast({ title: 'Risk created', status: 'success', duration: 2000 });
          setFormData(EMPTY_FORM);
          setShowForm(false);
        },
        onError: (err) => {
          toast({ title: 'Failed to create risk', description: err.message, status: 'error', duration: 4000 });
        },
      }
    );
  };

  const handleStartEdit = (risk: Risk) => {
    setEditingId(risk.risk_id);
    setEditData({
      title: risk.title,
      description: risk.description,
      category: risk.category,
      probability: risk.probability,
      impact: risk.impact,
      owner: risk.owner,
      mitigation_plan: risk.mitigation_plan,
      status: risk.status,
    });
  };

  const handleSaveEdit = (id: string) => {
    if (!editData.title.trim()) {
      toast({ title: 'Title is required', status: 'warning', duration: 2000 });
      return;
    }

    updateMutation.mutate(
      {
        id,
        data: {
          title: editData.title,
          description: editData.description,
          category: editData.category,
          probability: editData.probability,
          impact: editData.impact,
          owner: editData.owner,
          mitigation_plan: editData.mitigation_plan,
          status: editData.status,
        },
      },
      {
        onSuccess: () => {
          toast({ title: 'Risk updated', status: 'success', duration: 2000 });
          setEditingId(null);
        },
        onError: (err) => {
          toast({ title: 'Failed to update risk', description: err.message, status: 'error', duration: 4000 });
        },
      }
    );
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast({ title: 'Risk deleted', status: 'success', duration: 2000 });
      },
      onError: (err) => {
        toast({ title: 'Failed to delete risk', description: err.message, status: 'error', duration: 4000 });
      },
    });
  };

  return (
    <Box px={{ base: 4, md: 6, lg: 8 }} py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Risk Register
          </Heading>
          <Text color="gray.500">
            Identify, assess, and track risks across your Program Increment with a visual heat map.
          </Text>
        </Box>

        {/* Loading State */}
        {isLoading && (
          <VStack spacing={4} align="stretch">
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              <Skeleton height="200px" borderRadius="md" />
              <Skeleton height="200px" borderRadius="md" />
            </SimpleGrid>
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="100px" borderRadius="md" />
            ))}
          </VStack>
        )}

        {/* Error State */}
        {isError && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            Failed to load risks: {(error as Error)?.message || 'Unknown error'}
          </Alert>
        )}

        {/* Risk Summary Section */}
        {!isLoading && !isError && risks && (
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
            {/* KPI Cards */}
            <SimpleGrid columns={{ base: 2, md: 2 }} spacing={4}>
              <KPICard
                label="Total Risks"
                value={totalRisks}
                status="info"
                icon={BarChart3}
                helpText="Total number of registered risks"
              />
              <KPICard
                label="Open Risks"
                value={openRisks}
                status={openRisks > 0 ? 'error' : 'success'}
                icon={AlertTriangle}
                helpText="Risks that are currently open"
              />
              <KPICard
                label="Avg Risk Score"
                value={avgScore.toFixed(1)}
                status={avgScore >= 13 ? 'error' : avgScore >= 7 ? 'warning' : 'success'}
                icon={TrendingUp}
                helpText="Average probability x impact across all risks"
              />
              <KPICard
                label="Highest Risk"
                value={highestRisk ? highestRisk.risk_score : 'N/A'}
                status={
                  highestRisk
                    ? highestRisk.risk_score >= 19
                      ? 'error'
                      : highestRisk.risk_score >= 13
                        ? 'warning'
                        : 'success'
                    : 'info'
                }
                icon={Shield}
                helpText={highestRisk ? highestRisk.title : 'No risks registered'}
              />
            </SimpleGrid>

            {/* Risk Heat Map */}
            <Card bg={cardBg}>
              <CardBody>
                <Heading size="sm" mb={2}>Risk Heat Map</Heading>
                <RiskHeatMap risks={risks} />
              </CardBody>
            </Card>
          </SimpleGrid>
        )}

        {/* Add Risk Button */}
        {!isLoading && !isError && (
          <Box>
            <Button
              leftIcon={showForm ? <X size={16} /> : <Plus size={16} />}
              colorScheme={showForm ? 'gray' : 'blue'}
              onClick={() => setShowForm(!showForm)}
            >
              {showForm ? 'Cancel' : 'Add Risk'}
            </Button>
          </Box>
        )}

        {/* Add Risk Form */}
        <Collapse in={showForm} animateOpacity>
          <Card bg={cardBg}>
            <CardBody>
              <VStack spacing={4} align="stretch">
                <Heading size="sm">New Risk</Heading>
                <FormControl isRequired>
                  <FormLabel>Title</FormLabel>
                  <Input
                    placeholder="Risk title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Description</FormLabel>
                  <Textarea
                    placeholder="Describe the risk..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </FormControl>
                <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                  <FormControl>
                    <FormLabel>Category</FormLabel>
                    <Select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value as Risk['category'] })}
                    >
                      <option value="technical">Technical</option>
                      <option value="resource">Resource</option>
                      <option value="schedule">Schedule</option>
                      <option value="scope">Scope</option>
                      <option value="external">External</option>
                      <option value="general">General</option>
                    </Select>
                  </FormControl>
                  <FormControl>
                    <FormLabel>Probability: {formData.probability}</FormLabel>
                    <Slider
                      value={formData.probability}
                      onChange={(val) => setFormData({ ...formData, probability: val })}
                      min={1}
                      max={5}
                      step={1}
                    >
                      <SliderTrack>
                        <SliderFilledTrack />
                      </SliderTrack>
                      <SliderThumb />
                    </Slider>
                  </FormControl>
                  <FormControl>
                    <FormLabel>Impact: {formData.impact}</FormLabel>
                    <Slider
                      value={formData.impact}
                      onChange={(val) => setFormData({ ...formData, impact: val })}
                      min={1}
                      max={5}
                      step={1}
                    >
                      <SliderTrack>
                        <SliderFilledTrack />
                      </SliderTrack>
                      <SliderThumb />
                    </Slider>
                  </FormControl>
                </SimpleGrid>
                <Box>
                  <Text fontSize="sm" fontWeight="semibold">
                    Risk Score:{' '}
                    <Text as="span" color={getRiskScoreColorHex(formData.probability * formData.impact)} fontSize="lg">
                      {formData.probability * formData.impact}
                    </Text>
                  </Text>
                </Box>
                <FormControl>
                  <FormLabel>Owner</FormLabel>
                  <Input
                    placeholder="Risk owner"
                    value={formData.owner}
                    onChange={(e) => setFormData({ ...formData, owner: e.target.value })}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Mitigation Plan</FormLabel>
                  <Textarea
                    placeholder="Describe mitigation strategy..."
                    value={formData.mitigation_plan}
                    onChange={(e) => setFormData({ ...formData, mitigation_plan: e.target.value })}
                  />
                </FormControl>
                <HStack>
                  <Button
                    colorScheme="blue"
                    onClick={handleCreate}
                    isLoading={createMutation.isPending}
                    loadingText="Creating..."
                  >
                    Create Risk
                  </Button>
                  <Button variant="outline" onClick={() => { setShowForm(false); setFormData(EMPTY_FORM); }}>
                    Cancel
                  </Button>
                </HStack>
              </VStack>
            </CardBody>
          </Card>
        </Collapse>

        {/* Status Filter */}
        {!isLoading && !isError && risks && risks.length > 0 && (
          <Box>
            <Text fontSize="sm" fontWeight="semibold" mb={2}>
              Filter by Status
            </Text>
            <Wrap spacing={2}>
              {ALL_STATUSES.map((s) => {
                const count = risks.filter((r) => r.status === s).length;
                const isActive = statusFilter.has(s);
                return (
                  <WrapItem key={s}>
                    <Tag
                      size="md"
                      cursor="pointer"
                      colorScheme={isActive ? STATUS_COLORS[s] : 'gray'}
                      variant={isActive ? 'solid' : 'outline'}
                      onClick={() => toggleFilter(s)}
                    >
                      <TagLabel>
                        {STATUS_LABELS[s]} ({count})
                      </TagLabel>
                    </Tag>
                  </WrapItem>
                );
              })}
            </Wrap>
          </Box>
        )}

        {/* Empty State */}
        {!isLoading && !isError && risks && risks.length === 0 && (
          <Card bg={cardBg}>
            <CardBody textAlign="center" py={12}>
              <Text color="gray.500" fontSize="lg">
                No risks registered yet. Add your first risk to get started.
              </Text>
            </CardBody>
          </Card>
        )}

        {/* Risk List */}
        {!isLoading && filteredRisks.length > 0 && (
          <VStack spacing={4} align="stretch">
            <Heading size="sm">
              Risks ({filteredRisks.length === (risks?.length || 0)
                ? filteredRisks.length
                : `${filteredRisks.length} of ${risks?.length || 0}`})
            </Heading>
            {filteredRisks.map((risk) => (
              <Card key={risk.risk_id} bg={cardBg}>
                <CardBody>
                  {editingId === risk.risk_id ? (
                    /* Inline Edit Mode */
                    <VStack spacing={4} align="stretch">
                      <FormControl isRequired>
                        <FormLabel>Title</FormLabel>
                        <Input
                          value={editData.title}
                          onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                        />
                      </FormControl>
                      <FormControl>
                        <FormLabel>Description</FormLabel>
                        <Textarea
                          value={editData.description}
                          onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                        />
                      </FormControl>
                      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                        <FormControl>
                          <FormLabel>Category</FormLabel>
                          <Select
                            value={editData.category}
                            onChange={(e) =>
                              setEditData({ ...editData, category: e.target.value as Risk['category'] })
                            }
                          >
                            <option value="technical">Technical</option>
                            <option value="resource">Resource</option>
                            <option value="schedule">Schedule</option>
                            <option value="scope">Scope</option>
                            <option value="external">External</option>
                            <option value="general">General</option>
                          </Select>
                        </FormControl>
                        <FormControl>
                          <FormLabel>Status</FormLabel>
                          <Select
                            value={editData.status}
                            onChange={(e) =>
                              setEditData({ ...editData, status: e.target.value as Risk['status'] })
                            }
                          >
                            <option value="open">Open</option>
                            <option value="mitigating">Mitigating</option>
                            <option value="mitigated">Mitigated</option>
                            <option value="accepted">Accepted</option>
                            <option value="closed">Closed</option>
                          </Select>
                        </FormControl>
                        <FormControl>
                          <FormLabel>Owner</FormLabel>
                          <Input
                            value={editData.owner}
                            onChange={(e) => setEditData({ ...editData, owner: e.target.value })}
                          />
                        </FormControl>
                      </SimpleGrid>
                      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                        <FormControl>
                          <FormLabel>Probability: {editData.probability}</FormLabel>
                          <Slider
                            value={editData.probability}
                            onChange={(val) => setEditData({ ...editData, probability: val })}
                            min={1}
                            max={5}
                            step={1}
                          >
                            <SliderTrack>
                              <SliderFilledTrack />
                            </SliderTrack>
                            <SliderThumb />
                          </Slider>
                        </FormControl>
                        <FormControl>
                          <FormLabel>Impact: {editData.impact}</FormLabel>
                          <Slider
                            value={editData.impact}
                            onChange={(val) => setEditData({ ...editData, impact: val })}
                            min={1}
                            max={5}
                            step={1}
                          >
                            <SliderTrack>
                              <SliderFilledTrack />
                            </SliderTrack>
                            <SliderThumb />
                          </Slider>
                        </FormControl>
                      </SimpleGrid>
                      <Box>
                        <Text fontSize="sm" fontWeight="semibold">
                          Risk Score:{' '}
                          <Text as="span" color={getRiskScoreColorHex(editData.probability * editData.impact)} fontSize="lg">
                            {editData.probability * editData.impact}
                          </Text>
                        </Text>
                      </Box>
                      <FormControl>
                        <FormLabel>Mitigation Plan</FormLabel>
                        <Textarea
                          value={editData.mitigation_plan}
                          onChange={(e) => setEditData({ ...editData, mitigation_plan: e.target.value })}
                        />
                      </FormControl>
                      <HStack>
                        <IconButton
                          aria-label="Save"
                          icon={<Check size={16} />}
                          colorScheme="green"
                          size="sm"
                          onClick={() => handleSaveEdit(risk.risk_id)}
                          isLoading={updateMutation.isPending}
                        />
                        <IconButton
                          aria-label="Cancel"
                          icon={<X size={16} />}
                          variant="outline"
                          size="sm"
                          onClick={() => setEditingId(null)}
                        />
                      </HStack>
                    </VStack>
                  ) : (
                    /* Display Mode */
                    <Box>
                      <HStack justify="space-between" mb={2} flexWrap="wrap">
                        <HStack spacing={2} flexWrap="wrap" align="center">
                          {/* Risk score as large colored number */}
                          <Text
                            fontSize="2xl"
                            fontWeight="bold"
                            color={getRiskScoreColorHex(risk.risk_score)}
                            lineHeight="1"
                            mr={1}
                          >
                            {risk.risk_score}
                          </Text>
                          <Heading size="sm">{risk.title}</Heading>
                          <Badge colorScheme={CATEGORY_COLORS[risk.category]}>
                            {risk.category}
                          </Badge>
                          <Badge colorScheme={STATUS_COLORS[risk.status]}>
                            {STATUS_LABELS[risk.status] || risk.status}
                          </Badge>
                        </HStack>
                        <HStack spacing={1}>
                          <IconButton
                            aria-label={expandedId === risk.risk_id ? 'Collapse' : 'Expand'}
                            icon={expandedId === risk.risk_id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setExpandedId(expandedId === risk.risk_id ? null : risk.risk_id)
                            }
                          />
                          <IconButton
                            aria-label="Edit"
                            icon={<Pencil size={14} />}
                            variant="outline"
                            size="sm"
                            onClick={() => handleStartEdit(risk)}
                          />
                          <IconButton
                            aria-label="Delete"
                            icon={<Trash2 size={14} />}
                            variant="outline"
                            colorScheme="red"
                            size="sm"
                            onClick={() => handleDelete(risk.risk_id)}
                            isLoading={deleteMutation.isPending}
                          />
                        </HStack>
                      </HStack>
                      <HStack spacing={4} fontSize="xs" color="gray.500" mb={1}>
                        <Text>P: {risk.probability} | I: {risk.impact}</Text>
                        {risk.owner && <Text>Owner: {risk.owner}</Text>}
                      </HStack>
                      <Collapse in={expandedId === risk.risk_id} animateOpacity>
                        <VStack align="stretch" spacing={2} mt={3} pt={3} borderTopWidth="1px" borderColor="gray.600">
                          {risk.description && (
                            <Box>
                              <Text fontSize="xs" fontWeight="semibold" color="gray.400" mb={1}>
                                Description
                              </Text>
                              <Text fontSize="sm" color="gray.500">
                                {risk.description}
                              </Text>
                            </Box>
                          )}
                          {risk.mitigation_plan && (
                            <Box>
                              <Text fontSize="xs" fontWeight="semibold" color="gray.400" mb={1}>
                                Mitigation Plan
                              </Text>
                              <Text fontSize="sm" color="gray.500">
                                {risk.mitigation_plan}
                              </Text>
                            </Box>
                          )}
                        </VStack>
                      </Collapse>
                    </Box>
                  )}
                </CardBody>
              </Card>
            ))}
          </VStack>
        )}

        {/* No results for filter */}
        {!isLoading && !isError && risks && risks.length > 0 && filteredRisks.length === 0 && (
          <Card bg={cardBg}>
            <CardBody textAlign="center" py={8}>
              <Text color="gray.500">
                No risks match the selected filters.
              </Text>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Box>
  );
}
