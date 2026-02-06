/**
 * File upload component with drag-and-drop support.
 */

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Text,
  VStack,
  useColorModeValue,
  Spinner,
  Badge,
  HStack,
  IconButton,
} from '@chakra-ui/react';

interface FileUploadProps {
  label: string;
  accept: Record<string, string[]>;
  fileType: 'ded' | 'excel';
  uploadedFile?: { filename: string; file_id: string } | null;
  isUploading?: boolean;
  onUpload: (file: File) => void;
  onRemove?: () => void;
}

export default function FileUpload({
  label,
  accept,
  fileType,
  uploadedFile,
  isUploading,
  onUpload,
  onRemove,
}: FileUploadProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0]);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple: false,
    disabled: isUploading,
  });

  const borderColor = useColorModeValue('gray.300', 'gray.600');
  const activeBorderColor = useColorModeValue('blue.400', 'blue.300');
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const activeBgColor = useColorModeValue('blue.50', 'gray.600');

  if (uploadedFile) {
    return (
      <Box
        p={4}
        borderWidth={2}
        borderRadius="lg"
        borderColor="green.400"
        bg={useColorModeValue('green.50', 'gray.700')}
      >
        <HStack justify="space-between">
          <VStack align="start" spacing={1}>
            <Badge colorScheme="green">Uploaded</Badge>
            <Text fontWeight="medium" fontSize="sm" noOfLines={1}>
              {uploadedFile.filename}
            </Text>
          </VStack>
          {onRemove && (
            <IconButton
              aria-label="Remove file"
              icon={<Text>×</Text>}
              size="sm"
              variant="ghost"
              colorScheme="red"
              onClick={onRemove}
            />
          )}
        </HStack>
      </Box>
    );
  }

  return (
    <Box
      {...getRootProps()}
      p={6}
      borderWidth={2}
      borderStyle="dashed"
      borderRadius="lg"
      borderColor={isDragActive ? activeBorderColor : borderColor}
      bg={isDragActive ? activeBgColor : bgColor}
      cursor={isUploading ? 'wait' : 'pointer'}
      transition="all 0.2s"
      _hover={{
        borderColor: activeBorderColor,
        bg: activeBgColor,
      }}
    >
      <input {...getInputProps()} />
      <VStack spacing={2}>
        {isUploading ? (
          <>
            <Spinner size="lg" color="blue.400" />
            <Text color="gray.500">Uploading...</Text>
          </>
        ) : (
          <>
            <Text fontSize="2xl">
              {fileType === 'ded' ? '📄' : '📊'}
            </Text>
            <Text fontWeight="medium">{label}</Text>
            <Text fontSize="sm" color="gray.500">
              {isDragActive
                ? 'Drop the file here'
                : 'Drag & drop or click to select'}
            </Text>
            <Text fontSize="xs" color="gray.400">
              {fileType === 'ded'
                ? 'Supports: .docx, .md, .txt, .pdf'
                : 'Supports: .xlsx, .xls'}
            </Text>
          </>
        )}
      </VStack>
    </Box>
  );
}
