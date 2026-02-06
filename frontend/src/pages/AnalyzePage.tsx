/**
 * Full Analysis Page - Upload files and run comprehensive analysis.
 */

import { useState } from 'react';
import {
  Box,
  Container,
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
  Spinner,
  useColorModeValue,
  useToast,
} from '@chakra-ui/react';

import FileUpload from '../components/common/FileUpload';
import RedFlagsTab from '../components/analysis/RedFlagsTab';
import CapacityTab from '../components/analysis/CapacityTab';
import SummaryTab from '../components/analysis/SummaryTab';
import { useFileUpload, useRunAnalysis } from '../hooks/useAnalysis';
import { useSettingsStore } from '../store/settingsStore';
import type { AnalysisResponse } from '../types';

interface UploadedFileInfo {
  file_id: string;
  filename: string;
}

export default function AnalyzePage() {
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');

  // Settings
  const { defaultBuffer, defaultCDTarget } = useSettingsStore();
  const [bufferPct, setBufferPct] = useState(defaultBuffer);
  const [cdTarget, setCdTarget] = useState(defaultCDTarget);

  // File state
  const [dedFile, setDedFile] = useState<UploadedFileInfo | null>(null);
  const [excelFile, setExcelFile] = useState<UploadedFileInfo | null>(null);

  // Analysis state
  const [analysisResults, setAnalysisResults] = useState<AnalysisResponse | null>(null);

  // Mutations
  const uploadMutation = useFileUpload();
  const analysisMutation = useRunAnalysis();

  const handleDedUpload = (file: File) => {
    uploadMutation.mutate(
      { file, fileType: 'ded' },
      {
        onSuccess: (data) => {
          setDedFile({ file_id: data.file_id, filename: data.filename });
          toast({
            title: 'DED file uploaded',
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
    if (!dedFile && !excelFile) {
      toast({
        title: 'No files uploaded',
        description: 'Please upload at least one file to analyze.',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    analysisMutation.mutate(
      {
        ded_file_id: dedFile?.file_id || null,
        excel_file_id: excelFile?.file_id || null,
        buffer_percentage: bufferPct / 100,
        cd_target_percentage: cdTarget / 100,
      },
      {
        onSuccess: (data) => {
          setAnalysisResults(data);
          toast({
            title: 'Analysis complete',
            status: 'success',
            duration: 3000,
          });
        },
        onError: (error) => {
          toast({
            title: 'Analysis failed',
            description: error.message,
            status: 'error',
            duration: 4000,
          });
        },
      }
    );
  };

  const handleReset = () => {
    setDedFile(null);
    setExcelFile(null);
    setAnalysisResults(null);
  };

  const isAnalyzing = analysisMutation.isPending;
  const isUploading = uploadMutation.isPending;

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Full DED Analysis
          </Heading>
          <Text color="gray.500">
            Upload your DED document and Excel capacity planner for comprehensive analysis
            of risks, capacity, and deployment strategies.
          </Text>
        </Box>

        {/* File Upload Section */}
        <Card bg={cardBg}>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Heading size="sm">Upload Files</Heading>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
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
                  isUploading={isUploading && !dedFile}
                  onUpload={handleDedUpload}
                  onRemove={() => setDedFile(null)}
                />
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
              </SimpleGrid>
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
            isDisabled={!dedFile && !excelFile}
          >
            Analyze
          </Button>
          {(dedFile || excelFile || analysisResults) && (
            <Button variant="outline" onClick={handleReset}>
              Reset
            </Button>
          )}
        </HStack>

        {/* Loading State */}
        {isAnalyzing && (
          <Box textAlign="center" py={8}>
            <Spinner size="xl" color="blue.500" />
            <Text mt={4} color="gray.500">
              Running analysis... This may take a moment.
            </Text>
          </Box>
        )}

        {/* Results */}
        {analysisResults && !isAnalyzing && (
          <Card bg={cardBg}>
            <CardBody>
              <Tabs colorScheme="blue">
                <TabList flexWrap="wrap">
                  <Tab>
                    📋 Summary
                  </Tab>
                  <Tab>
                    🚩 Red Flags
                    {analysisResults.summary.risk.total > 0 && (
                      <Badge ml={2} colorScheme="red">
                        {analysisResults.summary.risk.total}
                      </Badge>
                    )}
                  </Tab>
                  <Tab>
                    📈 Capacity
                    {analysisResults.summary.capacity.failing > 0 && (
                      <Badge ml={2} colorScheme="orange">
                        {analysisResults.summary.capacity.failing} issues
                      </Badge>
                    )}
                  </Tab>
                  <Tab>🚀 Deployment</Tab>
                  <Tab>📊 PI Dashboard</Tab>
                </TabList>

                <TabPanels>
                  {/* Summary Tab */}
                  <TabPanel>
                    <SummaryTab
                      results={analysisResults.results}
                      summary={analysisResults.summary}
                    />
                  </TabPanel>

                  {/* Red Flags Tab */}
                  <TabPanel>
                    <RedFlagsTab
                      redFlags={analysisResults.results.red_flags as any[] || []}
                    />
                  </TabPanel>

                  {/* Capacity Tab */}
                  <TabPanel>
                    <CapacityTab
                      capacityAnalysis={analysisResults.results.capacity_analysis as any[] || []}
                    />
                  </TabPanel>

                  {/* Deployment Tab */}
                  <TabPanel>
                    <Alert status="info">
                      <AlertIcon />
                      Deployment analysis view coming soon.
                    </Alert>
                  </TabPanel>

                  {/* PI Dashboard Tab */}
                  <TabPanel>
                    <Alert status="info">
                      <AlertIcon />
                      PI Dashboard view coming soon.
                    </Alert>
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Container>
  );
}
