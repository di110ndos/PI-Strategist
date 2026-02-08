/**
 * File upload API endpoints.
 */

import apiClient from '../client';
import type { UploadedFile } from '../../types';

export const filesApi = {
  /**
   * Upload a file (DED or Excel).
   */
  upload: async (file: File, fileType: 'ded' | 'excel'): Promise<UploadedFile> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<UploadedFile>(
      `/files/upload?file_type=${fileType}`,
      formData
    );
    return response.data;
  },

  /**
   * List all uploaded files.
   */
  list: async (): Promise<{ files: UploadedFile[] }> => {
    const response = await apiClient.get<{ files: UploadedFile[] }>('/files');
    return response.data;
  },

  /**
   * Delete an uploaded file.
   */
  delete: async (fileId: string): Promise<void> => {
    await apiClient.delete(`/files/${fileId}`);
  },
};

export default filesApi;
