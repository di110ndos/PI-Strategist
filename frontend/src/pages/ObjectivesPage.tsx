/**
 * PI Objectives Page — manage committed and stretch objectives for the PI.
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
  useColorModeValue,
  useToast,
} from '@chakra-ui/react';
import { Plus, Pencil, Trash2, X, Check } from 'lucide-react';

import {
  useObjectives,
  useCreateObjective,
  useUpdateObjective,
  useDeleteObjective,
} from '../hooks/useObjectives';
import type { PIObjective } from '../types';

const TYPE_COLORS: Record<string, string> = {
  committed: 'blue',
  stretch: 'purple',
};

const STATUS_COLORS: Record<string, string> = {
  planned: 'gray',
  in_progress: 'blue',
  completed: 'green',
  at_risk: 'red',
};

const STATUS_LABELS: Record<string, string> = {
  planned: 'Planned',
  in_progress: 'In Progress',
  completed: 'Completed',
  at_risk: 'At Risk',
};

interface ObjectiveFormData {
  name: string;
  description: string;
  objective_type: 'committed' | 'stretch';
  business_value: number;
  acceptance_criteria: string;
  status: 'planned' | 'in_progress' | 'completed' | 'at_risk';
}

const EMPTY_FORM: ObjectiveFormData = {
  name: '',
  description: '',
  objective_type: 'committed',
  business_value: 5,
  acceptance_criteria: '',
  status: 'planned',
};

export default function ObjectivesPage() {
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');

  // Queries & mutations
  const { data: objectives, isLoading, isError, error } = useObjectives();
  const createMutation = useCreateObjective();
  const updateMutation = useUpdateObjective();
  const deleteMutation = useDeleteObjective();

  // UI state
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<ObjectiveFormData>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<ObjectiveFormData>(EMPTY_FORM);

  const handleCreate = () => {
    if (!formData.name.trim()) {
      toast({ title: 'Name is required', status: 'warning', duration: 2000 });
      return;
    }

    createMutation.mutate(
      {
        name: formData.name,
        description: formData.description,
        objective_type: formData.objective_type,
        business_value: formData.business_value,
        acceptance_criteria: formData.acceptance_criteria,
      },
      {
        onSuccess: () => {
          toast({ title: 'Objective created', status: 'success', duration: 2000 });
          setFormData(EMPTY_FORM);
          setShowForm(false);
        },
        onError: (err) => {
          toast({ title: 'Failed to create objective', description: err.message, status: 'error', duration: 4000 });
        },
      }
    );
  };

  const handleStartEdit = (obj: PIObjective) => {
    setEditingId(obj.objective_id);
    setEditData({
      name: obj.name,
      description: obj.description,
      objective_type: obj.objective_type,
      business_value: obj.business_value,
      acceptance_criteria: obj.acceptance_criteria,
      status: obj.status,
    });
  };

  const handleSaveEdit = (id: string) => {
    if (!editData.name.trim()) {
      toast({ title: 'Name is required', status: 'warning', duration: 2000 });
      return;
    }

    updateMutation.mutate(
      {
        id,
        data: {
          name: editData.name,
          description: editData.description,
          objective_type: editData.objective_type,
          business_value: editData.business_value,
          acceptance_criteria: editData.acceptance_criteria,
          status: editData.status,
        },
      },
      {
        onSuccess: () => {
          toast({ title: 'Objective updated', status: 'success', duration: 2000 });
          setEditingId(null);
        },
        onError: (err) => {
          toast({ title: 'Failed to update objective', description: err.message, status: 'error', duration: 4000 });
        },
      }
    );
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast({ title: 'Objective deleted', status: 'success', duration: 2000 });
      },
      onError: (err) => {
        toast({ title: 'Failed to delete objective', description: err.message, status: 'error', duration: 4000 });
      },
    });
  };

  return (
    <Box px={{ base: 4, md: 6, lg: 8 }} py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            PI Objectives
          </Heading>
          <Text color="gray.500">
            Define and track committed and stretch objectives for your Program Increment.
          </Text>
        </Box>

        {/* Add Objective Button */}
        <Box>
          <Button
            leftIcon={showForm ? <X size={16} /> : <Plus size={16} />}
            colorScheme={showForm ? 'gray' : 'blue'}
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? 'Cancel' : 'Add Objective'}
          </Button>
        </Box>

        {/* Add Objective Form */}
        <Collapse in={showForm} animateOpacity>
          <Card bg={cardBg}>
            <CardBody>
              <VStack spacing={4} align="stretch">
                <Heading size="sm">New Objective</Heading>
                <FormControl isRequired>
                  <FormLabel>Name</FormLabel>
                  <Input
                    placeholder="Objective name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Description</FormLabel>
                  <Textarea
                    placeholder="Describe the objective..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </FormControl>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <FormControl>
                    <FormLabel>Type</FormLabel>
                    <Select
                      value={formData.objective_type}
                      onChange={(e) =>
                        setFormData({ ...formData, objective_type: e.target.value as 'committed' | 'stretch' })
                      }
                    >
                      <option value="committed">Committed</option>
                      <option value="stretch">Stretch</option>
                    </Select>
                  </FormControl>
                  <FormControl>
                    <FormLabel>Business Value: {formData.business_value}</FormLabel>
                    <Slider
                      value={formData.business_value}
                      onChange={(val) => setFormData({ ...formData, business_value: val })}
                      min={1}
                      max={10}
                      step={1}
                    >
                      <SliderTrack>
                        <SliderFilledTrack />
                      </SliderTrack>
                      <SliderThumb />
                    </Slider>
                  </FormControl>
                </SimpleGrid>
                <FormControl>
                  <FormLabel>Acceptance Criteria</FormLabel>
                  <Textarea
                    placeholder="Define acceptance criteria..."
                    value={formData.acceptance_criteria}
                    onChange={(e) => setFormData({ ...formData, acceptance_criteria: e.target.value })}
                  />
                </FormControl>
                <HStack>
                  <Button
                    colorScheme="blue"
                    onClick={handleCreate}
                    isLoading={createMutation.isPending}
                    loadingText="Creating..."
                  >
                    Create Objective
                  </Button>
                  <Button variant="outline" onClick={() => { setShowForm(false); setFormData(EMPTY_FORM); }}>
                    Cancel
                  </Button>
                </HStack>
              </VStack>
            </CardBody>
          </Card>
        </Collapse>

        {/* Loading State */}
        {isLoading && (
          <VStack spacing={4} align="stretch">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="120px" borderRadius="md" />
            ))}
          </VStack>
        )}

        {/* Error State */}
        {isError && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            Failed to load objectives: {(error as Error)?.message || 'Unknown error'}
          </Alert>
        )}

        {/* Empty State */}
        {!isLoading && !isError && objectives && objectives.length === 0 && (
          <Card bg={cardBg}>
            <CardBody textAlign="center" py={12}>
              <Text color="gray.500" fontSize="lg">
                No objectives yet. Add your first PI objective.
              </Text>
            </CardBody>
          </Card>
        )}

        {/* Objectives List */}
        {objectives && objectives.length > 0 && (
          <VStack spacing={4} align="stretch">
            {objectives.map((obj) => (
              <Card key={obj.objective_id} bg={cardBg}>
                <CardBody>
                  {editingId === obj.objective_id ? (
                    /* Inline Edit Mode */
                    <VStack spacing={4} align="stretch">
                      <FormControl isRequired>
                        <FormLabel>Name</FormLabel>
                        <Input
                          value={editData.name}
                          onChange={(e) => setEditData({ ...editData, name: e.target.value })}
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
                          <FormLabel>Type</FormLabel>
                          <Select
                            value={editData.objective_type}
                            onChange={(e) =>
                              setEditData({ ...editData, objective_type: e.target.value as 'committed' | 'stretch' })
                            }
                          >
                            <option value="committed">Committed</option>
                            <option value="stretch">Stretch</option>
                          </Select>
                        </FormControl>
                        <FormControl>
                          <FormLabel>Status</FormLabel>
                          <Select
                            value={editData.status}
                            onChange={(e) =>
                              setEditData({ ...editData, status: e.target.value as ObjectiveFormData['status'] })
                            }
                          >
                            <option value="planned">Planned</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                            <option value="at_risk">At Risk</option>
                          </Select>
                        </FormControl>
                        <FormControl>
                          <FormLabel>Business Value: {editData.business_value}</FormLabel>
                          <Slider
                            value={editData.business_value}
                            onChange={(val) => setEditData({ ...editData, business_value: val })}
                            min={1}
                            max={10}
                            step={1}
                          >
                            <SliderTrack>
                              <SliderFilledTrack />
                            </SliderTrack>
                            <SliderThumb />
                          </Slider>
                        </FormControl>
                      </SimpleGrid>
                      <FormControl>
                        <FormLabel>Acceptance Criteria</FormLabel>
                        <Textarea
                          value={editData.acceptance_criteria}
                          onChange={(e) => setEditData({ ...editData, acceptance_criteria: e.target.value })}
                        />
                      </FormControl>
                      <HStack>
                        <IconButton
                          aria-label="Save"
                          icon={<Check size={16} />}
                          colorScheme="green"
                          size="sm"
                          onClick={() => handleSaveEdit(obj.objective_id)}
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
                        <HStack spacing={2} flexWrap="wrap">
                          <Heading size="sm">{obj.name}</Heading>
                          <Badge colorScheme={TYPE_COLORS[obj.objective_type]}>
                            {obj.objective_type}
                          </Badge>
                          <Badge colorScheme={STATUS_COLORS[obj.status]}>
                            {STATUS_LABELS[obj.status] || obj.status}
                          </Badge>
                          <Badge colorScheme="teal" variant="solid" fontSize="xs">
                            BV: {obj.business_value}
                          </Badge>
                        </HStack>
                        <HStack spacing={1}>
                          <IconButton
                            aria-label="Edit"
                            icon={<Pencil size={14} />}
                            variant="outline"
                            size="sm"
                            onClick={() => handleStartEdit(obj)}
                          />
                          <IconButton
                            aria-label="Delete"
                            icon={<Trash2 size={14} />}
                            variant="outline"
                            colorScheme="red"
                            size="sm"
                            onClick={() => handleDelete(obj.objective_id)}
                            isLoading={deleteMutation.isPending}
                          />
                        </HStack>
                      </HStack>
                      {obj.description && (
                        <Text fontSize="sm" color="gray.500" mb={2}>
                          {obj.description}
                        </Text>
                      )}
                      {obj.acceptance_criteria && (
                        <Box>
                          <Text fontSize="xs" fontWeight="semibold" color="gray.400" mb={1}>
                            Acceptance Criteria
                          </Text>
                          <Text fontSize="sm" color="gray.500">
                            {obj.acceptance_criteria}
                          </Text>
                        </Box>
                      )}
                      {obj.linked_stories && obj.linked_stories.length > 0 && (
                        <HStack mt={2} spacing={1} flexWrap="wrap">
                          <Text fontSize="xs" color="gray.400">
                            Stories:
                          </Text>
                          {obj.linked_stories.map((story) => (
                            <Badge key={story} variant="subtle" size="sm" fontSize="xs">
                              {story}
                            </Badge>
                          ))}
                        </HStack>
                      )}
                    </Box>
                  )}
                </CardBody>
              </Card>
            ))}
          </VStack>
        )}
      </VStack>
    </Box>
  );
}
