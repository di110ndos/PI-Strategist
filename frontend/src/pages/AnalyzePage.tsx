/**
 * PI Analysis Page - Upload Excel capacity planner for comprehensive analysis.
 */

import { useCallback, useState } from 'react';
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  SimpleGrid,
  Button,
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
  Card,
  CardBody,
  Alert,
  AlertIcon,
  Skeleton,
  SkeletonText,
  Icon,
  useColorModeValue,
  useToast,
} from '@chakra-ui/react';
import { ClipboardList, TrendingUp, Rocket, BarChart3, Sparkles } from 'lucide-react';

import FileUpload from '../components/common/FileUpload';
import CapacityTab from '../components/analysis/CapacityTab';
import SummaryTab from '../components/analysis/SummaryTab';
import AIInsightsTab from '../components/analysis/AIInsightsTab';
import DeploymentTab from '../components/analysis/DeploymentTab';
import PIDashboardTab from '../components/analysis/PIDashboardTab';
import { useFileUpload, useRunAnalysis, useSaveAnalysis } from '../hooks/useAnalysis';
import { useSettingsStore } from '../store/settingsStore';
import { useAnalysisStore } from '../store/analysisStore';
import type { AnalysisResponse } from '../types';

interface UploadedFileInfo {
  file_id: string;
  filename: string;
}

export default function AnalyzePage() {
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');

  // Stores
  const { defaultBuffer, defaultCDTarget } = useSettingsStore();
  const latestAnalysis = useAnalysisStore((s) => s.latestAnalysis);
  const setLatestAnalysis = useAnalysisStore((s) => s.setLatestAnalysis);
  const clearAnalysis = useAnalysisStore((s) => s.clearAnalysis);
  const [bufferPct, setBufferPct] = useState(defaultBuffer);
  const [cdTarget, setCdTarget] = useState(defaultCDTarget);

  // File state
  const [excelFile, setExcelFile] = useState<UploadedFileInfo | null>(null);

  // Analysis state — initialize from store so results survive navigation
  const [analysisResults, setAnalysisResults] = useState<AnalysisResponse | null>(latestAnalysis);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Mutations
  const uploadMutation = useFileUpload();
  const analysisMutation = useRunAnalysis();
  const saveMutation = useSaveAnalysis();

  const handleExcelUpload = (file: File) => {
    uploadMutation.mutate(
      { file, fileType: 'excel' },
      {
        onSuccess: (data) => {
          setExcelFile({ file_id: data.file_id, filename: data.filename });
          toast({
            title: 'Excel file uploaded',
            status: 'success',
            duration: 2000,
          });
        },
        onError: (error) => {
          toast({
            title: 'Upload failed',
            description: error.message,
            status: 'error',
            duration: 4000,
          });
        },
      }
    );
  };

  const handleAnalyze = () => {
    if (!excelFile) {
      toast({
        title: 'No file uploaded',
        description: 'Please upload an Excel capacity planner to analyze.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    setAnalysisError(null);
    analysisMutation.mutate(
      {
        ded_file_id: null,
        excel_file_id: excelFile.file_id,
        buffer_percentage: bufferPct / 100,
        cd_target_percentage: cdTarget / 100,
      },
      {
        onSuccess: (data) => {
          setAnalysisResults(data);
          setAnalysisError(null);
          setLatestAnalysis(data);
          toast({
            title: 'Analysis complete',
            status: 'success',
            duration: 3000,
          });
        },
        onError: (error) => {
          setAnalysisError(error.message);
        },
      }
    );
  };

  const handleSave = () => {
    if (!analysisResults) return;
    const now = new Date();
    const name = excelFile?.filename || 'Analysis';
    const year = String(now.getFullYear());
    const quarter = `Q${Math.ceil((now.getMonth() + 1) / 3)}`;

    saveMutation.mutate(
      { analysisId: analysisResults.analysis_id, metadata: { name, year, quarter } },
      {
        onSuccess: () => {
          toast({ title: 'Analysis saved for comparison', status: 'success', duration: 3000 });
        },
        onError: (error) => {
          toast({ title: 'Save failed', description: error.message, status: 'error', duration: 4000 });
        },
      }
    );
  };

  const handleReset = () => {
    setExcelFile(null);
    setAnalysisResults(null);
    setAnalysisError(null);
    clearAnalysis();
  };

  // Preserve scroll position when switching tabs (short panels would otherwise
  // shrink the page and snap scroll to top).
  const handleTabChange = useCallback(() => {
    const y = window.scrollY;
    requestAnimationFrame(() => window.scrollTo(0, y));
  }, []);

  const isAnalyzing = analysisMutation.isPending;
  const isUploading = uploadMutation.isPending;

  return (
    <Box px={{ base: 4, md: 6, lg: 8 }} py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            PI Analysis
          </Heading>
          <Text color="gray.500">
            Upload your Excel capacity planner for comprehensive analysis
            of capacity, deployment strategies, and PI metrics.
          </Text>
        </Box>

        {/* File Upload Section */}
        <Card bg={cardBg}>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Heading size="sm">Upload File</Heading>
              <FileUpload
                label="Excel Capacity Planner"
                accept={{
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
                  'application/vnd.ms-excel': ['.xls'],
                }}
                fileType="excel"
                uploadedFile={excelFile}
                isUploading={isUploading && !excelFile}
                onUpload={handleExcelUpload}
                onRemove={() => setExcelFile(null)}
              />
            </VStack>
          </CardBody>
        </Card>

        {/* Settings Section */}
        <Card bg={cardBg}>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Heading size="sm">Analysis Settings</Heading>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                <FormControl>
                  <FormLabel>
                    Buffer Percentage: {bufferPct}%
                  </FormLabel>
                  <Slider
                    value={bufferPct}
                    onChange={setBufferPct}
                    min={0}
                    max={50}
                    step={5}
                  >
                    <SliderTrack>
                      <SliderFilledTrack />
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    Reserve capacity for unexpected work (recommended: 20%)
                  </Text>
                </FormControl>
                <FormControl>
                  <FormLabel>
                    CD Target: {cdTarget}%
                  </FormLabel>
                  <Slider
                    value={cdTarget}
                    onChange={setCdTarget}
                    min={10}
                    max={50}
                    step={5}
                  >
                    <SliderTrack>
                      <SliderFilledTrack />
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    Target percentage for continuous delivery eligible tasks
                  </Text>
                </FormControl>
              </SimpleGrid>
            </VStack>
          </CardBody>
        </Card>

        {/* Analyze Button */}
        <HStack>
          <Button
            colorScheme="blue"
            size="lg"
            onClick={handleAnalyze}
            isLoading={isAnalyzing}
            loadingText="Analyzing..."
            isDisabled={!excelFile}
          >
            Analyze
          </Button>
          {(excelFile || analysisResults) && (
            <Button variant="outline" onClick={handleReset}>
              Reset
            </Button>
          )}
        </HStack>

        {/* Loading State — skeleton cards */}
        {isAnalyzing && (
          <Card bg={cardBg}>
            <CardBody>
              <VStack spacing={6} align="stretch">
                <Skeleton height="20px" width="200px" />
                <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
                  {[1, 2, 3, 4].map((i) => (
                    <Box key={i}>
                      <Skeleton height="12px" width="80px" mb={2} />
                      <Skeleton height="28px" width="60px" />
                    </Box>
                  ))}
                </SimpleGrid>
                <SkeletonText noOfLines={4} spacing="4" />
                <Skeleton height="200px" borderRadius="md" />
              </VStack>
            </CardBody>
          </Card>
        )}

        {/* Error Display */}
        {analysisError && !isAnalyzing && (
          <Alert status="error" borderRadius="md" alignItems="flex-start">
            <AlertIcon mt={1} />
            <Box flex="1">
              <Text fontWeight="bold" mb={2}>Analysis Failed</Text>
              <Box
                as="pre"
                fontSize="xs"
                whiteSpace="pre-wrap"
                wordBreak="break-word"
                bg="red.50"
                _dark={{ bg: 'red.900' }}
                p={3}
                borderRadius="md"
                maxH="400px"
                overflowY="auto"
              >
                {analysisError}
              </Box>
            </Box>
          </Alert>
        )}

        {/* Results */}
        {analysisResults && !isAnalyzing && (
          <Card bg={cardBg}>
            <CardBody>
              <HStack justify="flex-end" mb={4}>
                <Button
                  size="sm"
                  colorScheme="green"
                  variant="outline"
                  onClick={handleSave}
                  isLoading={saveMutation.isPending}
                  loadingText="Saving..."
                >
                  Save for Comparison
                </Button>
              </HStack>
              <Tabs colorScheme="blue" onChange={handleTabChange}>
                <TabList flexWrap="wrap">
                  <Tab>
                    <Icon as={ClipboardList} boxSize={4} mr={2} />
                    Summary
                  </Tab>
                  <Tab>
                    <Icon as={Sparkles} boxSize={4} mr={2} />
                    AI Insights
                  </Tab>
                  <Tab>
                    <Icon as={TrendingUp} boxSize={4} mr={2} />
                    Capacity
                    {analysisResults.summary.capacity.failing > 0 && (
                      <Badge ml={2} colorScheme="orange">
                        {analysisResults.summary.capacity.failing} issues
                      </Badge>
                    )}
                  </Tab>
                  <Tab>
                    <Icon as={Rocket} boxSize={4} mr={2} />
                    Deployment
                  </Tab>
                  <Tab>
                    <Icon as={BarChart3} boxSize={4} mr={2} />
                    PI Dashboard
                  </Tab>
                </TabList>

                <TabPanels>
                  {/* Summary Tab */}
                  <TabPanel>
                    <SummaryTab
                      results={analysisResults.results}
                      summary={analysisResults.summary}
                    />
                  </TabPanel>

                  {/* AI Insights Tab */}
                  <TabPanel>
                    <AIInsightsTab results={analysisResults.results} />
                  </TabPanel>

                  {/* Capacity Tab */}
                  <TabPanel>
                    <CapacityTab
                      capacityAnalysis={analysisResults.results.capacity_analysis as any[] || []}
                    />
                  </TabPanel>

                  {/* Deployment Tab */}
                  <TabPanel>
                    <DeploymentTab
                      deploymentClusters={analysisResults.results.deployment_clusters as any[] || []}
                    />
                  </TabPanel>

                  {/* PI Dashboard Tab */}
                  <TabPanel>
                    <PIDashboardTab
                      results={analysisResults.results}
                      summary={analysisResults.summary}
                    />
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Box>
  );
}
