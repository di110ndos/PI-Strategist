/**
 * DED Page - Upload DED for red-flag analysis, or paste text for quick check.
 */

import { useState } from 'react';
import {
  Box,
  Heading,
  Text,
  Textarea,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  VStack,
  HStack,
  Badge,
  Card,
  CardBody,
  CardHeader,
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
  Code,
  Spinner,
  useColorModeValue,
  useToast,
} from '@chakra-ui/react';
import { Upload, Type } from 'lucide-react';
import FileUpload from '../components/common/FileUpload';
import RedFlagsTab from '../components/analysis/RedFlagsTab';
import { useQuickCheck } from '../hooks/useQuickCheck';
import { useFileUpload, useRunAnalysis } from '../hooks/useAnalysis';
import type { QuickCheckResponse, RedFlagItem, AnalysisResponse } from '../types';

// Sample text for demo
const SAMPLE_TEXT = `The system shall be fast and user-friendly.
The application must handle all requests efficiently.
Users should be able to login quickly.
The API will respond in a timely manner.
System uptime shall be 99.9%.
Response time must be under 200ms.
The solution should be scalable and secure.`;

// Severity colors
const severityColors: Record<string, string> = {
  critical: 'red',
  moderate: 'orange',
  low: 'blue',
};

interface UploadedFileInfo {
  file_id: string;
  filename: string;
}

export default function QuickCheckPage() {
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');

  // Upload DED mode state
  const [dedFile, setDedFile] = useState<UploadedFileInfo | null>(null);
  const [dedResults, setDedResults] = useState<AnalysisResponse | null>(null);
  const uploadMutation = useFileUpload();
  const analysisMutation = useRunAnalysis();

  // Paste Text mode state
  const [text, setText] = useState('');
  const [textResults, setTextResults] = useState<QuickCheckResponse | null>(null);
  const { mutate: analyzeText, isPending: isTextPending } = useQuickCheck();

  const handleDedUpload = (file: File) => {
    uploadMutation.mutate(
      { file, fileType: 'ded' },
      {
        onSuccess: (data) => {
          setDedFile({ file_id: data.file_id, filename: data.filename });
          toast({ title: 'DED file uploaded', status: 'success', duration: 2000 });
        },
        onError: (error) => {
          toast({ title: 'Upload failed', description: error.message, status: 'error', duration: 4000 });
        },
      }
    );
  };

  const handleDedAnalyze = () => {
    if (!dedFile) return;
    analysisMutation.mutate(
      {
        ded_file_id: dedFile.file_id,
        excel_file_id: null,
        buffer_percentage: 0.2,
        cd_target_percentage: 0.3,
      },
      {
        onSuccess: (data) => {
          setDedResults(data);
          toast({ title: 'DED analysis complete', status: 'success', duration: 3000 });
        },
        onError: (error) => {
          toast({ title: 'Analysis failed', description: error.message, status: 'error', duration: 4000 });
        },
      }
    );
  };

  const handleTextAnalyze = () => {
    if (!text.trim()) return;
    analyzeText(
      { text },
      {
        onSuccess: (data) => setTextResults(data),
        onError: (error) => console.error('Analysis failed:', error),
      }
    );
  };

  const handleLoadSample = () => setText(SAMPLE_TEXT);

  const isDedAnalyzing = analysisMutation.isPending;
  const isDedUploading = uploadMutation.isPending;

  return (
    <Box px={{ base: 4, md: 6, lg: 8 }} py={8}>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>DED Analysis</Heading>
          <Text color="gray.500">
            Upload a DED document to scan for red flags, or paste text for a quick check.
          </Text>
        </Box>

        <Tabs colorScheme="blue" variant="enclosed">
          <TabList flexWrap="wrap">
            <Tab><Box as={Upload} size={16} mr={2} /> Upload DED</Tab>
            <Tab><Box as={Type} size={16} mr={2} /> Paste Text</Tab>
          </TabList>

          <TabPanels>
            {/* Upload DED Tab */}
            <TabPanel px={0}>
              <VStack spacing={6} align="stretch">
                <Card bg={cardBg}>
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <FileUpload
                        label="DED Document"
                        accept={{
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
                          'text/markdown': ['.md'],
                          'text/plain': ['.txt'],
                          'application/pdf': ['.pdf'],
                        }}
                        fileType="ded"
                        uploadedFile={dedFile}
                        isUploading={isDedUploading}
                        onUpload={handleDedUpload}
                        onRemove={() => { setDedFile(null); setDedResults(null); }}
                      />
                      <Button
                        colorScheme="blue"
                        onClick={handleDedAnalyze}
                        isLoading={isDedAnalyzing}
                        loadingText="Analyzing..."
                        isDisabled={!dedFile}
                      >
                        Analyze DED
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>

                {isDedAnalyzing && (
                  <Box textAlign="center" py={8}>
                    <Spinner size="xl" color="blue.500" />
                    <Text mt={4} color="gray.500">Analyzing DED document...</Text>
                  </Box>
                )}

                {dedResults && !isDedAnalyzing && (
                  <Card bg={cardBg}>
                    <CardBody>
                      <RedFlagsTab redFlags={dedResults.results.red_flags as any[] || []} />
                    </CardBody>
                  </Card>
                )}
              </VStack>
            </TabPanel>

            {/* Paste Text Tab */}
            <TabPanel px={0}>
              <VStack spacing={6} align="stretch">
                <Card bg={cardBg}>
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <Textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Paste your acceptance criteria here..."
                        minH="200px"
                        fontFamily="mono"
                        fontSize="sm"
                      />
                      <HStack>
                        <Button
                          colorScheme="blue"
                          onClick={handleTextAnalyze}
                          isLoading={isTextPending}
                          loadingText="Analyzing..."
                          isDisabled={!text.trim()}
                        >
                          Analyze
                        </Button>
                        <Button variant="outline" onClick={handleLoadSample}>
                          Load Sample
                        </Button>
                        {text && (
                          <Button variant="ghost" onClick={() => setText('')}>
                            Clear
                          </Button>
                        )}
                      </HStack>
                    </VStack>
                  </CardBody>
                </Card>

                {isTextPending && (
                  <Box textAlign="center" py={8}>
                    <Spinner size="xl" color="blue.500" />
                    <Text mt={4} color="gray.500">Analyzing text...</Text>
                  </Box>
                )}

                {textResults && !isTextPending && (
                  <TextResults results={textResults} cardBg={cardBg} />
                )}
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
}

// Text quick-check results (original functionality)
function TextResults({ results, cardBg }: { results: QuickCheckResponse; cardBg: string }) {
  return (
    <VStack spacing={6} align="stretch">
      <StatGroup>
        <Stat>
          <StatLabel>Red Flags</StatLabel>
          <StatNumber color="red.500">{results.summary.red_flags.total}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Critical</StatLabel>
          <StatNumber color="red.600">{results.summary.red_flags.critical}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Obligations</StatLabel>
          <StatNumber color="purple.500">{results.summary.obligations.total}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>SLA Metrics</StatLabel>
          <StatNumber color="green.500">{results.summary.sla.total}</StatNumber>
        </Stat>
      </StatGroup>

      <Tabs colorScheme="blue" bg={cardBg} borderRadius="lg" p={4}>
        <TabList flexWrap="wrap">
          <Tab>
            Red Flags <Badge ml={2} colorScheme="red">{results.summary.red_flags.total}</Badge>
          </Tab>
          <Tab>
            Obligations <Badge ml={2} colorScheme="purple">{results.summary.obligations.total}</Badge>
          </Tab>
          <Tab>
            SLA/SLO <Badge ml={2} colorScheme="green">{results.summary.sla.total}</Badge>
          </Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            {results.red_flags.length === 0 ? (
              <Alert status="success"><AlertIcon />No red flags detected!</Alert>
            ) : (
              <Accordion allowMultiple>
                {results.red_flags.map((lineFlags, idx) => (
                  <AccordionItem key={idx}>
                    <AccordionButton>
                      <Box flex="1" textAlign="left">
                        <HStack>
                          <Text fontWeight="medium" noOfLines={1}>Line {lineFlags.line_number}</Text>
                          {lineFlags.flags.map((flag, i) => (
                            <Badge key={i} colorScheme={severityColors[flag.severity]}>{flag.term}</Badge>
                          ))}
                        </HStack>
                      </Box>
                      <AccordionIcon />
                    </AccordionButton>
                    <AccordionPanel>
                      <VStack align="stretch" spacing={4}>
                        <Code p={2} display="block" whiteSpace="pre-wrap">{lineFlags.line}</Code>
                        {lineFlags.flags.map((flag, i) => (
                          <RedFlagCard key={i} flag={flag} />
                        ))}
                      </VStack>
                    </AccordionPanel>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </TabPanel>

          <TabPanel>
            {results.obligations.total === 0 ? (
              <Alert status="info"><AlertIcon />No obligation statements found.</Alert>
            ) : (
              <VStack align="stretch" spacing={4}>
                <HStack spacing={4}>
                  <Badge colorScheme="red">Binding: {results.obligations.binding_count}</Badge>
                  <Badge colorScheme="orange">Commitment: {results.obligations.commitment_count}</Badge>
                  <Badge colorScheme="gray">Negative: {results.obligations.negative_count}</Badge>
                </HStack>
                {results.obligations.obligations.map((ob, idx) => (
                  <Card key={idx} size="sm">
                    <CardBody>
                      <HStack justify="space-between" mb={2}>
                        <Badge>{ob.obligation_type}</Badge>
                        <Code>{ob.keyword}</Code>
                      </HStack>
                      <Text>{ob.text}</Text>
                    </CardBody>
                  </Card>
                ))}
              </VStack>
            )}
          </TabPanel>

          <TabPanel>
            {results.sla.total === 0 ? (
              <Alert status="info"><AlertIcon />No SLA/SLO metrics found.</Alert>
            ) : (
              <VStack align="stretch" spacing={4}>
                <HStack spacing={4}>
                  <Badge colorScheme="green">Valid: {results.sla.valid_count}</Badge>
                  <Badge colorScheme="red">Invalid: {results.sla.invalid_count}</Badge>
                </HStack>
                {results.sla.findings.map((finding, idx) => (
                  <Card key={idx} size="sm">
                    <CardBody>
                      <HStack justify="space-between" mb={2}>
                        <Badge colorScheme={finding.is_valid ? 'green' : 'red'}>{finding.metric_type}</Badge>
                        {finding.value && <Code>{finding.value}</Code>}
                      </HStack>
                      <Text>{finding.text}</Text>
                      {finding.issues.length > 0 && (
                        <Alert status="warning" mt={2} size="sm">
                          <AlertIcon />{finding.issues.join(', ')}
                        </Alert>
                      )}
                    </CardBody>
                  </Card>
                ))}
              </VStack>
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </VStack>
  );
}

function RedFlagCard({ flag }: { flag: RedFlagItem }) {
  const cardBg = useColorModeValue('gray.50', 'gray.700');

  return (
    <Card bg={cardBg} size="sm">
      <CardHeader pb={2}>
        <HStack justify="space-between">
          <HStack>
            <Badge colorScheme={severityColors[flag.severity]} fontSize="sm">
              {flag.severity.toUpperCase()}
            </Badge>
            <Code fontWeight="bold">{flag.term}</Code>
          </HStack>
          <Text fontSize="sm" color="gray.500">{flag.category}</Text>
        </HStack>
      </CardHeader>
      <CardBody pt={0}>
        <VStack align="stretch" spacing={3}>
          <Box>
            <Text fontSize="sm" fontWeight="medium" color="gray.500">Suggested Replacement:</Text>
            <Code p={2} display="block" colorScheme="green">{flag.suggested_metric}</Code>
          </Box>
          <Box>
            <Text fontSize="sm" fontWeight="medium" color="gray.500">How to Discuss:</Text>
            <Text fontSize="sm" fontStyle="italic">{flag.negotiation_script}</Text>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
}
