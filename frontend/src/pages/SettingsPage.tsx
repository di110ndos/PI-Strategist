/**
 * Settings Page - Configure application defaults.
 */

import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Button,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  FormControl,
  FormLabel,
  Input,
  InputGroup,
  InputRightElement,
  Divider,
  Badge,
  useColorModeValue,
  useToast,
} from '@chakra-ui/react';
import { useState } from 'react';
import { useSettingsStore } from '../store/settingsStore';

export default function SettingsPage() {
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');

  const {
    defaultBuffer,
    defaultCDTarget,
    apiKey,
    setDefaultBuffer,
    setDefaultCDTarget,
    setApiKey,
  } = useSettingsStore();

  const [showApiKey, setShowApiKey] = useState(false);
  const [localApiKey, setLocalApiKey] = useState(apiKey || '');

  const handleSaveApiKey = () => {
    setApiKey(localApiKey || null);
    toast({
      title: 'API key saved',
      status: 'success',
      duration: 2000,
    });
  };

  const handleResetDefaults = () => {
    setDefaultBuffer(20);
    setDefaultCDTarget(30);
    toast({
      title: 'Settings reset to defaults',
      status: 'info',
      duration: 2000,
    });
  };

  return (
    <Container maxW="container.lg" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Settings
          </Heading>
          <Text color="gray.500">
            Configure default analysis parameters and API settings.
          </Text>
        </Box>

        {/* Analysis Defaults */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Analysis Defaults</Heading>
          </CardHeader>
          <CardBody pt={0}>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
              <FormControl>
                <FormLabel>
                  Default Buffer Percentage: {defaultBuffer}%
                </FormLabel>
                <Slider
                  value={defaultBuffer}
                  onChange={setDefaultBuffer}
                  min={0}
                  max={50}
                  step={5}
                  colorScheme="blue"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
                <Text fontSize="xs" color="gray.500" mt={1}>
                  Reserve capacity for unexpected work and meetings.
                  Recommended: 20%
                </Text>
              </FormControl>

              <FormControl>
                <FormLabel>
                  Default CD Target: {defaultCDTarget}%
                </FormLabel>
                <Slider
                  value={defaultCDTarget}
                  onChange={setDefaultCDTarget}
                  min={10}
                  max={50}
                  step={5}
                  colorScheme="blue"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
                <Text fontSize="xs" color="gray.500" mt={1}>
                  Target percentage for continuous delivery eligible tasks.
                  Recommended: 30%
                </Text>
              </FormControl>
            </SimpleGrid>

            <HStack mt={6}>
              <Button variant="outline" onClick={handleResetDefaults}>
                Reset to Defaults
              </Button>
            </HStack>
          </CardBody>
        </Card>

        {/* API Settings */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">AI Integration</Heading>
          </CardHeader>
          <CardBody pt={0}>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Anthropic API Key</FormLabel>
                <InputGroup>
                  <Input
                    type={showApiKey ? 'text' : 'password'}
                    value={localApiKey}
                    onChange={(e) => setLocalApiKey(e.target.value)}
                    placeholder="sk-ant-..."
                  />
                  <InputRightElement width="4.5rem">
                    <Button
                      h="1.75rem"
                      size="sm"
                      onClick={() => setShowApiKey(!showApiKey)}
                    >
                      {showApiKey ? 'Hide' : 'Show'}
                    </Button>
                  </InputRightElement>
                </InputGroup>
                <Text fontSize="xs" color="gray.500" mt={1}>
                  Required for AI-powered recommendations. Get your key from{' '}
                  <Text as="span" color="blue.400">
                    console.anthropic.com
                  </Text>
                </Text>
              </FormControl>

              <Button colorScheme="blue" onClick={handleSaveApiKey} alignSelf="start">
                Save API Key
              </Button>

              {apiKey && (
                <Badge colorScheme="green" alignSelf="start">
                  API Key Configured
                </Badge>
              )}
            </VStack>
          </CardBody>
        </Card>

        {/* Current Configuration */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Current Configuration</Heading>
          </CardHeader>
          <CardBody pt={0}>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              <Box>
                <Text fontSize="sm" color="gray.500">
                  Buffer Percentage
                </Text>
                <Text fontWeight="medium">{defaultBuffer}%</Text>
              </Box>
              <Box>
                <Text fontSize="sm" color="gray.500">
                  CD Target
                </Text>
                <Text fontWeight="medium">{defaultCDTarget}%</Text>
              </Box>
              <Box>
                <Text fontSize="sm" color="gray.500">
                  API Key Status
                </Text>
                <Badge colorScheme={apiKey ? 'green' : 'gray'}>
                  {apiKey ? 'Configured' : 'Not Set'}
                </Badge>
              </Box>
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* About Section */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">About PI Strategist</Heading>
          </CardHeader>
          <CardBody pt={0}>
            <VStack align="stretch" spacing={4}>
              <Text>
                PI Strategist helps agile teams analyze their PI planning documents
                for potential risks, capacity issues, and deployment strategies.
              </Text>

              <Divider />

              <Box>
                <Text fontWeight="medium" mb={2}>
                  Supported File Formats
                </Text>
                <SimpleGrid columns={2} spacing={2}>
                  <Box>
                    <Text fontSize="sm" color="gray.500">
                      DED Documents
                    </Text>
                    <HStack spacing={2} mt={1}>
                      <Badge>.docx</Badge>
                      <Badge>.md</Badge>
                      <Badge>.txt</Badge>
                      <Badge>.pdf</Badge>
                    </HStack>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.500">
                      Capacity Planners
                    </Text>
                    <HStack spacing={2} mt={1}>
                      <Badge>.xlsx</Badge>
                      <Badge>.xls</Badge>
                    </HStack>
                  </Box>
                </SimpleGrid>
              </Box>

              <Divider />

              <Box>
                <Text fontWeight="medium" mb={2}>
                  Version
                </Text>
                <Badge>1.0.0 (React)</Badge>
              </Box>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
}
