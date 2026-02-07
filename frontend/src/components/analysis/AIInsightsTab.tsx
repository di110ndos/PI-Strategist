/**
 * AI Insights tab — generates and displays AI-powered analysis recommendations,
 * sprint rebalancing suggestions, and follow-up chat.
 */

import { useState, useRef, useCallback } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Badge,
  Icon,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Button,
  Spinner,
  List,
  ListItem,
  ListIcon,
  Tag,
  TagLabel,
  Wrap,
  WrapItem,
  Input,
  InputGroup,
  InputRightElement,
  IconButton,
  Divider,
} from '@chakra-ui/react';
import {
  Sparkles,
  Lightbulb,
  ArrowRight,
  ChevronRight,
  ArrowRightLeft,
  Send,
  MessageCircle,
} from 'lucide-react';
import { useAIInsights, useRebalancing, useAIChat } from '../../hooks/useAnalysis';
import type { AIInsightsResponse, AIRecommendation, ResourceData, RebalancingSuggestion, ChatMessage } from '../../types';

interface AIInsightsTabProps {
  results: {
    red_flags?: unknown[];
    capacity_plan?: Record<string, unknown>;
    pi_analysis?: {
      resources?: Record<string, ResourceData>;
      projects?: Record<string, unknown>;
      sprints?: string[];
      total_capacity?: number;
      total_allocated?: number;
      grand_total_hours?: number;
    };
  };
}

const PRIORITY_COLORS: Record<string, string> = { high: 'red', medium: 'orange', low: 'blue' };
const CATEGORY_COLORS: Record<string, string> = {
  capacity: 'teal', risk: 'red', cost: 'green', resource: 'purple', general: 'gray',
};

export default function AIInsightsTab({ results }: AIInsightsTabProps) {
  const cardBg = useColorModeValue('white', 'gray.800');
  const [insights, setInsights] = useState<AIInsightsResponse | null>(null);
  const mutation = useAIInsights();

  // ─── Recommendation Filters ─────────────────────────────────
  const [priorityFilters, setPriorityFilters] = useState<Set<string>>(new Set());
  const [categoryFilters, setCategoryFilters] = useState<Set<string>>(new Set());

  // ─── Rebalancing ────────────────────────────────────────────
  const [rebalancingSuggestions, setRebalancingSuggestions] = useState<RebalancingSuggestion[]>([]);
  const rebalancingMutation = useRebalancing();

  // ─── Chat ───────────────────────────────────────────────────
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const chatMutation = useAIChat();
  const chatEndRef = useRef<HTMLDivElement>(null);

  const handleGenerate = () => {
    mutation.mutate(
      {
        pi_analysis: (results.pi_analysis || {}) as Record<string, unknown>,
        capacity_plan: (results.capacity_plan as Record<string, unknown>) || null,
        red_flags: (results.red_flags as unknown[]) || null,
        insight_type: 'full',
      },
      {
        onSuccess: (data) => {
          setInsights(data);
          // Reset all sub-features
          setPriorityFilters(new Set());
          setCategoryFilters(new Set());
          setRebalancingSuggestions([]);
          setChatHistory([]);
        },
      }
    );
  };

  const handleRebalance = () => {
    rebalancingMutation.mutate(
      {
        pi_analysis: (results.pi_analysis || {}) as Record<string, unknown>,
        capacity_plan: (results.capacity_plan as Record<string, unknown>) || null,
        red_flags: null,
        insight_type: 'rebalancing',
      },
      {
        onSuccess: (data) => {
          setRebalancingSuggestions(data.rebalancing_suggestions || []);
        },
      }
    );
  };

  const handleChatSend = useCallback(() => {
    const question = chatInput.trim();
    if (!question || chatMutation.isPending) return;

    const userMsg: ChatMessage = { role: 'user', content: question };
    setChatHistory((prev) => [...prev, userMsg]);
    setChatInput('');

    chatMutation.mutate(
      {
        question,
        pi_analysis: (results.pi_analysis || {}) as Record<string, unknown>,
        capacity_plan: (results.capacity_plan as Record<string, unknown>) || null,
        previous_insights: insights,
        conversation_history: [...chatHistory, userMsg],
      },
      {
        onSuccess: (data) => {
          setChatHistory((prev) => [...prev, { role: 'assistant', content: data.answer }]);
          setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
        },
        onError: (err) => {
          setChatHistory((prev) => [
            ...prev,
            { role: 'assistant', content: `Sorry, I couldn't process that: ${err.message}` },
          ]);
        },
      }
    );
  }, [chatInput, chatMutation, chatHistory, insights, results]);

  // ─── Filtered Recommendations ───────────────────────────────
  const recs = insights?.recommendations ?? [];
  const filteredRecs = recs.filter((rec) => {
    if (priorityFilters.size > 0 && !priorityFilters.has(rec.priority)) return false;
    if (categoryFilters.size > 0 && !categoryFilters.has(rec.category)) return false;
    return true;
  });

  const toggleFilter = (set: Set<string>, value: string, setter: (s: Set<string>) => void) => {
    const next = new Set(set);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    setter(next);
  };

  // Derive unique categories from data
  const categories = [...new Set(recs.map((r) => r.category))];

  return (
    <VStack spacing={6} align="stretch">
      {/* ─── Main Insights Card ─────────────────────────────────── */}
      <Card bg={cardBg}>
        <CardHeader>
          <HStack justify="space-between" flexWrap="wrap">
            <HStack>
              <Icon as={Sparkles} boxSize={5} color="purple.500" />
              <Heading size="md">AI Insights</Heading>
            </HStack>
            {!insights && (
              <Button
                colorScheme="purple"
                size="sm"
                leftIcon={<Icon as={Sparkles} boxSize={4} />}
                onClick={handleGenerate}
                isLoading={mutation.isPending}
                loadingText="Analyzing..."
              >
                Generate Insights
              </Button>
            )}
          </HStack>
        </CardHeader>
        <CardBody pt={0}>
          {/* Loading state */}
          {mutation.isPending && (
            <VStack spacing={3} py={8}>
              <Spinner size="lg" color="purple.500" thickness="3px" />
              <Text color="gray.500">Claude is analyzing your PI data...</Text>
              <Text fontSize="sm" color="gray.400">This may take 10-15 seconds</Text>
            </VStack>
          )}

          {/* Error state */}
          {mutation.isError && !insights && (
            <Alert status="error" borderRadius="md">
              <AlertIcon />
              <Box>
                <AlertTitle>AI Analysis Failed</AlertTitle>
                <AlertDescription fontSize="sm">
                  {mutation.error?.message || 'Unknown error occurred.'}
                  {mutation.error?.message?.includes('API key') && (
                    <Text mt={1}>Configure your Anthropic API key in the .env file.</Text>
                  )}
                </AlertDescription>
              </Box>
            </Alert>
          )}

          {/* Empty state */}
          {!mutation.isPending && !mutation.isError && !insights && (
            <Text color="gray.500" fontSize="sm">
              Click &quot;Generate Insights&quot; to get AI-powered analysis, recommendations, and optimization opportunities.
            </Text>
          )}

          {/* Results */}
          {insights && (
            <VStack spacing={5} align="stretch">
              {/* Executive Summary */}
              {insights.executive_summary && (
                <Box>
                  <Text fontWeight="semibold" fontSize="sm" mb={2}>Executive Summary</Text>
                  <Box bg="purple.50" _dark={{ bg: 'purple.900' }} p={4} borderRadius="md" borderLeft="4px solid" borderLeftColor="purple.400">
                    <Text fontSize="sm" whiteSpace="pre-wrap">{insights.executive_summary}</Text>
                  </Box>
                </Box>
              )}

              {/* Recommendations with Filters */}
              {recs.length > 0 && (
                <Box>
                  <Text fontWeight="semibold" fontSize="sm" mb={2}>
                    Recommendations ({filteredRecs.length === recs.length
                      ? recs.length
                      : `${filteredRecs.length} of ${recs.length}`})
                  </Text>

                  {/* Priority Filters */}
                  <Wrap spacing={2} mb={2}>
                    {(['high', 'medium', 'low'] as const).map((p) => {
                      const count = recs.filter((r) => r.priority === p).length;
                      if (count === 0) return null;
                      const active = priorityFilters.has(p);
                      return (
                        <WrapItem key={p}>
                          <Tag
                            size="sm"
                            colorScheme={PRIORITY_COLORS[p]}
                            variant={active ? 'solid' : 'outline'}
                            cursor="pointer"
                            onClick={() => toggleFilter(priorityFilters, p, setPriorityFilters)}
                          >
                            <TagLabel>{p} ({count})</TagLabel>
                          </Tag>
                        </WrapItem>
                      );
                    })}
                  </Wrap>

                  {/* Category Filters */}
                  <Wrap spacing={2} mb={3}>
                    {categories.map((cat) => {
                      const count = recs.filter((r) => r.category === cat).length;
                      const active = categoryFilters.has(cat);
                      return (
                        <WrapItem key={cat}>
                          <Tag
                            size="sm"
                            colorScheme={CATEGORY_COLORS[cat] || 'gray'}
                            variant={active ? 'solid' : 'outline'}
                            cursor="pointer"
                            onClick={() => toggleFilter(categoryFilters, cat, setCategoryFilters)}
                          >
                            <TagLabel>{cat} ({count})</TagLabel>
                          </Tag>
                        </WrapItem>
                      );
                    })}
                  </Wrap>

                  <VStack spacing={3} align="stretch">
                    {filteredRecs.map((rec, i) => (
                      <RecommendationCard key={i} rec={rec} />
                    ))}
                    {filteredRecs.length === 0 && (
                      <Text fontSize="sm" color="gray.500" fontStyle="italic">
                        No recommendations match the selected filters.
                      </Text>
                    )}
                  </VStack>
                </Box>
              )}

              {/* Risk Assessment */}
              {insights.risk_assessment && (
                <Box>
                  <Text fontWeight="semibold" fontSize="sm" mb={2}>Risk Assessment</Text>
                  <Alert status="info" borderRadius="md" variant="left-accent">
                    <AlertIcon />
                    <Text fontSize="sm" whiteSpace="pre-wrap">{insights.risk_assessment}</Text>
                  </Alert>
                </Box>
              )}

              {/* Optimization Opportunities */}
              {insights.optimization_opportunities.length > 0 && (
                <Box>
                  <Text fontWeight="semibold" fontSize="sm" mb={2}>Optimization Opportunities</Text>
                  <List spacing={2}>
                    {insights.optimization_opportunities.map((opp, i) => (
                      <ListItem key={i} fontSize="sm">
                        <ListIcon as={Lightbulb} color="yellow.500" />
                        {opp}
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {/* Key Metrics Commentary */}
              {insights.key_metrics_commentary && (
                <Box>
                  <Text fontWeight="semibold" fontSize="sm" mb={2}>Key Metrics Commentary</Text>
                  <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.300' }} whiteSpace="pre-wrap">
                    {insights.key_metrics_commentary}
                  </Text>
                </Box>
              )}

              {/* Regenerate button */}
              <Box pt={2}>
                <Button
                  size="sm"
                  variant="outline"
                  colorScheme="purple"
                  leftIcon={<Icon as={Sparkles} boxSize={4} />}
                  onClick={handleGenerate}
                  isLoading={mutation.isPending}
                >
                  Regenerate
                </Button>
              </Box>
            </VStack>
          )}
        </CardBody>
      </Card>

      {/* ─── Sprint Rebalancing Card ──────────────────────────────── */}
      {insights && (
        <Card bg={cardBg}>
          <CardHeader>
            <HStack justify="space-between" flexWrap="wrap">
              <HStack>
                <Icon as={ArrowRightLeft} boxSize={5} color="blue.500" />
                <Heading size="md">Sprint Rebalancing</Heading>
              </HStack>
              <Button
                colorScheme="blue"
                size="sm"
                variant="outline"
                leftIcon={<Icon as={ArrowRightLeft} boxSize={4} />}
                onClick={handleRebalance}
                isLoading={rebalancingMutation.isPending}
                loadingText="Analyzing..."
              >
                Suggest Rebalancing
              </Button>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            {rebalancingMutation.isPending && (
              <VStack spacing={3} py={6}>
                <Spinner size="md" color="blue.500" thickness="3px" />
                <Text color="gray.500" fontSize="sm">Analyzing sprint balance...</Text>
              </VStack>
            )}

            {rebalancingMutation.isError && rebalancingSuggestions.length === 0 && (
              <Alert status="error" borderRadius="md" size="sm">
                <AlertIcon />
                <Text fontSize="sm">{rebalancingMutation.error?.message || 'Rebalancing analysis failed.'}</Text>
              </Alert>
            )}

            {!rebalancingMutation.isPending && rebalancingSuggestions.length === 0 && !rebalancingMutation.isError && (
              <Text color="gray.500" fontSize="sm">
                Click &quot;Suggest Rebalancing&quot; to get AI-powered sprint rebalancing recommendations.
              </Text>
            )}

            {rebalancingSuggestions.length > 0 && (
              <VStack spacing={3} align="stretch">
                {rebalancingSuggestions.map((suggestion, i) => (
                  <SuggestionCard key={i} suggestion={suggestion} />
                ))}
              </VStack>
            )}
          </CardBody>
        </Card>
      )}

      {/* ─── Follow-up Chat Card ──────────────────────────────────── */}
      {insights && (
        <Card bg={cardBg}>
          <CardHeader>
            <HStack>
              <Icon as={MessageCircle} boxSize={5} color="green.500" />
              <Heading size="md">Ask Follow-up Questions</Heading>
            </HStack>
          </CardHeader>
          <CardBody pt={0}>
            {/* Chat history */}
            {chatHistory.length > 0 && (
              <VStack spacing={3} align="stretch" mb={4} maxH="400px" overflowY="auto">
                {chatHistory.map((msg, i) => (
                  <ChatBubble key={i} message={msg} />
                ))}
                {chatMutation.isPending && (
                  <HStack spacing={2} alignSelf="flex-start">
                    <Spinner size="xs" color="gray.400" />
                    <Text fontSize="sm" color="gray.400">Thinking...</Text>
                  </HStack>
                )}
                <div ref={chatEndRef} />
              </VStack>
            )}

            {chatHistory.length > 0 && <Divider mb={3} />}

            {/* Chat input */}
            <InputGroup size="md">
              <Input
                placeholder="Ask a question about your PI analysis..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleChatSend();
                  }
                }}
                pr="3rem"
              />
              <InputRightElement>
                <IconButton
                  aria-label="Send message"
                  icon={<Icon as={Send} boxSize={4} />}
                  size="sm"
                  colorScheme="green"
                  variant="ghost"
                  onClick={handleChatSend}
                  isDisabled={!chatInput.trim() || chatMutation.isPending}
                />
              </InputRightElement>
            </InputGroup>

            {chatHistory.length === 0 && (
              <Text color="gray.500" fontSize="xs" mt={2}>
                Ask questions like &quot;What are the biggest risks to our delivery timeline?&quot; or &quot;Where can we reallocate budget to stay on track?&quot;
              </Text>
            )}
          </CardBody>
        </Card>
      )}
    </VStack>
  );
}

// ─── Recommendation Card ───────────────────────────────────────

function RecommendationCard({ rec }: { rec: AIRecommendation }) {
  const priorityColor = PRIORITY_COLORS[rec.priority] || 'gray';
  const categoryColor = CATEGORY_COLORS[rec.category] || 'gray';

  return (
    <Card variant="outline" size="sm">
      <CardBody>
        <VStack align="stretch" spacing={2}>
          <HStack justify="space-between" flexWrap="wrap">
            <HStack spacing={2}>
              <Badge colorScheme={priorityColor} textTransform="uppercase" fontSize="xs">
                {rec.priority}
              </Badge>
              <Badge colorScheme={categoryColor} fontSize="xs">
                {rec.category}
              </Badge>
            </HStack>
          </HStack>
          <Text fontWeight="semibold" fontSize="sm">{rec.title}</Text>
          <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.300' }}>{rec.description}</Text>

          {rec.action_items.length > 0 && (
            <List spacing={1}>
              {rec.action_items.map((item, i) => (
                <ListItem key={i} fontSize="xs" color="gray.600" _dark={{ color: 'gray.400' }}>
                  <ListIcon as={ChevronRight} color="gray.400" />
                  {item}
                </ListItem>
              ))}
            </List>
          )}

          {rec.impact && (
            <HStack spacing={1}>
              <Icon as={ArrowRight} boxSize={3} color="green.500" />
              <Text fontSize="xs" color="green.600" _dark={{ color: 'green.300' }} fontStyle="italic">
                {rec.impact}
              </Text>
            </HStack>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

// ─── Rebalancing Suggestion Card ──────────────────────────────

function SuggestionCard({ suggestion }: { suggestion: RebalancingSuggestion }) {
  const priorityColor = PRIORITY_COLORS[suggestion.priority] || 'gray';

  return (
    <Card variant="outline" size="sm">
      <CardBody>
        <VStack align="stretch" spacing={2}>
          <HStack>
            <Badge colorScheme={priorityColor} textTransform="uppercase" fontSize="xs">
              {suggestion.priority}
            </Badge>
          </HStack>
          <Text fontWeight="semibold" fontSize="sm">{suggestion.action}</Text>
          {suggestion.reason && (
            <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.300' }}>{suggestion.reason}</Text>
          )}
          {suggestion.impact && (
            <HStack spacing={1}>
              <Icon as={ArrowRight} boxSize={3} color="green.500" />
              <Text fontSize="xs" color="green.600" _dark={{ color: 'green.300' }} fontStyle="italic">
                {suggestion.impact}
              </Text>
            </HStack>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

// ─── Chat Bubble ──────────────────────────────────────────────

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const userBg = useColorModeValue('purple.100', 'purple.800');
  const assistantBg = useColorModeValue('gray.100', 'gray.700');

  return (
    <Box
      alignSelf={isUser ? 'flex-end' : 'flex-start'}
      maxW="85%"
      bg={isUser ? userBg : assistantBg}
      px={3}
      py={2}
      borderRadius="lg"
    >
      <Text fontSize="sm" whiteSpace="pre-wrap">{message.content}</Text>
    </Box>
  );
}
