/**
 * Red Flags display tab component.
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
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Alert,
  AlertIcon,
  Code,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
} from '@chakra-ui/react';

interface RedFlag {
  flagged_term: string;
  category: string;
  severity: string;
  suggested_metric: string;
  negotiation_script: string;
  ac?: {
    text: string;
    story_id?: string;
    epic_id?: string;
  };
}

interface RedFlagsTabProps {
  redFlags: RedFlag[];
}

const severityColors: Record<string, string> = {
  critical: 'red',
  moderate: 'orange',
  low: 'blue',
};

const severityIcons: Record<string, string> = {
  critical: '🚨',
  moderate: '⚠️',
  low: '💡',
};

export default function RedFlagsTab({ redFlags }: RedFlagsTabProps) {
  if (!redFlags || redFlags.length === 0) {
    return (
      <Alert status="success" borderRadius="md">
        <AlertIcon />
        No red flags detected! Your acceptance criteria look well-defined.
      </Alert>
    );
  }

  // Group by severity
  const critical = redFlags.filter((rf) => rf.severity === 'critical');
  const moderate = redFlags.filter((rf) => rf.severity === 'moderate');
  const low = redFlags.filter((rf) => rf.severity === 'low');

  return (
    <VStack spacing={6} align="stretch">
      {/* Summary Stats */}
      <StatGroup>
        <Stat>
          <StatLabel>Total Issues</StatLabel>
          <StatNumber>{redFlags.length}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>🚨 Critical</StatLabel>
          <StatNumber color="red.500">{critical.length}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>⚠️ Moderate</StatLabel>
          <StatNumber color="orange.500">{moderate.length}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>💡 Low</StatLabel>
          <StatNumber color="blue.500">{low.length}</StatNumber>
        </Stat>
      </StatGroup>

      {/* Status Message */}
      {critical.length > 0 ? (
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          <Text>
            <strong>{critical.length} critical issue{critical.length !== 1 ? 's' : ''} found</strong>
            {' '}— These must be resolved before development begins.
          </Text>
        </Alert>
      ) : moderate.length > 0 ? (
        <Alert status="warning" borderRadius="md">
          <AlertIcon />
          <Text>
            <strong>{moderate.length} item{moderate.length !== 1 ? 's' : ''} need clarification</strong>
            {' '}— Address these before sprint planning.
          </Text>
        </Alert>
      ) : (
        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <Text>
            <strong>{low.length} minor suggestion{low.length !== 1 ? 's' : ''}</strong>
            {' '}— Consider clarifying during development.
          </Text>
        </Alert>
      )}

      {/* View Tabs */}
      <Tabs colorScheme="blue">
        <TabList>
          <Tab>By Severity</Tab>
          <Tab>All Items</Tab>
          <Tab>Table View</Tab>
        </TabList>

        <TabPanels>
          {/* By Severity View */}
          <TabPanel px={0}>
            <VStack spacing={4} align="stretch">
              {critical.length > 0 && (
                <SeveritySection
                  title="Critical"
                  description="Blocks acceptance — resolve before development"
                  flags={critical}
                  severity="critical"
                  defaultExpanded
                />
              )}
              {moderate.length > 0 && (
                <SeveritySection
                  title="Moderate"
                  description="Needs clarification before sprint planning"
                  flags={moderate}
                  severity="moderate"
                  defaultExpanded={critical.length === 0}
                />
              )}
              {low.length > 0 && (
                <SeveritySection
                  title="Low"
                  description="Nice to clarify during development"
                  flags={low}
                  severity="low"
                  defaultExpanded={critical.length === 0 && moderate.length === 0}
                />
              )}
            </VStack>
          </TabPanel>

          {/* All Items View */}
          <TabPanel px={0}>
            <VStack spacing={3} align="stretch">
              {redFlags.map((flag, idx) => (
                <RedFlagCard key={idx} flag={flag} showSeverity />
              ))}
            </VStack>
          </TabPanel>

          {/* Table View */}
          <TabPanel px={0}>
            <Box overflowX="auto">
              <Table size="sm">
                <Thead>
                  <Tr>
                    <Th>Severity</Th>
                    <Th>Term</Th>
                    <Th>Category</Th>
                    <Th>Found In</Th>
                    <Th>Suggested Replacement</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {redFlags.map((flag, idx) => (
                    <Tr key={idx}>
                      <Td>
                        <Badge colorScheme={severityColors[flag.severity]}>
                          {severityIcons[flag.severity]} {flag.severity}
                        </Badge>
                      </Td>
                      <Td>
                        <Code>{flag.flagged_term}</Code>
                      </Td>
                      <Td>{flag.category}</Td>
                      <Td>
                        <Text noOfLines={2} fontSize="sm">
                          {flag.ac?.text || 'N/A'}
                        </Text>
                      </Td>
                      <Td>
                        <Text fontSize="sm">{flag.suggested_metric}</Text>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </VStack>
  );
}

// Severity Section Component
function SeveritySection({
  title,
  description,
  flags,
  severity,
  defaultExpanded,
}: {
  title: string;
  description: string;
  flags: RedFlag[];
  severity: string;
  defaultExpanded?: boolean;
}) {
  return (
    <Accordion allowToggle defaultIndex={defaultExpanded ? [0] : []}>
      <AccordionItem border="none">
        <AccordionButton
          bg={useColorModeValue('gray.100', 'gray.700')}
          borderRadius="md"
          _hover={{ bg: useColorModeValue('gray.200', 'gray.600') }}
        >
          <Box flex="1" textAlign="left">
            <HStack>
              <Text fontSize="lg">{severityIcons[severity]}</Text>
              <Text fontWeight="bold">{title}</Text>
              <Badge colorScheme={severityColors[severity]}>{flags.length}</Badge>
              <Text fontSize="sm" color="gray.500">
                — {description}
              </Text>
            </HStack>
          </Box>
          <AccordionIcon />
        </AccordionButton>
        <AccordionPanel pb={4}>
          <VStack spacing={3} align="stretch" mt={2}>
            {flags.map((flag, idx) => (
              <RedFlagCard key={idx} flag={flag} />
            ))}
          </VStack>
        </AccordionPanel>
      </AccordionItem>
    </Accordion>
  );
}

// Red Flag Card Component
function RedFlagCard({ flag, showSeverity }: { flag: RedFlag; showSeverity?: boolean }) {
  const cardBg = useColorModeValue('gray.50', 'gray.700');

  return (
    <Card bg={cardBg} size="sm">
      <CardHeader pb={2}>
        <HStack justify="space-between" flexWrap="wrap">
          <HStack>
            {showSeverity && (
              <Badge colorScheme={severityColors[flag.severity]}>
                {severityIcons[flag.severity]} {flag.severity}
              </Badge>
            )}
            <Code fontWeight="bold">{flag.flagged_term}</Code>
          </HStack>
          <Text fontSize="sm" color="gray.500">
            {flag.category}
          </Text>
        </HStack>
      </CardHeader>
      <CardBody pt={0}>
        <VStack align="stretch" spacing={3}>
          {flag.ac?.text && (
            <Box>
              <Text fontSize="sm" color="gray.500">
                Found in:
              </Text>
              <Text fontSize="sm" noOfLines={2}>
                {flag.ac.text}
              </Text>
              {(flag.ac.story_id || flag.ac.epic_id) && (
                <HStack mt={1} spacing={2}>
                  {flag.ac.story_id && (
                    <Badge variant="outline" size="sm">
                      Story: {flag.ac.story_id}
                    </Badge>
                  )}
                  {flag.ac.epic_id && (
                    <Badge variant="outline" size="sm">
                      Epic: {flag.ac.epic_id}
                    </Badge>
                  )}
                </HStack>
              )}
            </Box>
          )}
          <Box>
            <Text fontSize="sm" fontWeight="medium" color="gray.500">
              Replace with:
            </Text>
            <Code p={2} display="block" colorScheme="green" fontSize="sm">
              {flag.suggested_metric}
            </Code>
          </Box>
          <Accordion allowToggle size="sm">
            <AccordionItem border="none">
              <AccordionButton px={0} _hover={{ bg: 'transparent' }}>
                <Text fontSize="sm" color="blue.400">
                  💬 How to discuss this
                </Text>
                <AccordionIcon ml={2} />
              </AccordionButton>
              <AccordionPanel px={0}>
                <Alert status="info" fontSize="sm">
                  <AlertIcon />
                  {flag.negotiation_script}
                </Alert>
              </AccordionPanel>
            </AccordionItem>
          </Accordion>
        </VStack>
      </CardBody>
    </Card>
  );
}
