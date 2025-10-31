import axios from 'axios';

export const api = axios.create({
  baseURL: '/',
  timeout: 30000,
});

export type ChatResponse = {
  response: string;
  conversation_id?: string;
  sources?: Record<string, [string, number]>;
};

export async function chat(message: string, documentId?: string, parishId?: string) {
  const { data } = await api.post<ChatResponse>('/agent/chat', { message, document_id: documentId, parish_id: parishId });
  return data;
}

export type UploadResult = {
  success: boolean;
  file_id?: string;
  filename?: string;
  parish_id?: string;
  document_type?: string;
  chunk_count?: number;
  s3_key?: string;
  processing_timestamp?: string;
  error?: string;
};

export async function uploadDocument(params: { file: File; parishId: string; documentType?: string; sermonDate?: string; metadata?: any; }) {
  const form = new FormData();
  form.append('file', params.file);
  form.append('parish_id', params.parishId);
  if (params.documentType) form.append('document_type', params.documentType);
  if (params.sermonDate) form.append('sermon_date', params.sermonDate);
  if (params.metadata) form.append('metadata', JSON.stringify(params.metadata));
  const { data } = await api.post<UploadResult>('/documents/upload', form);
  return data;
}

export async function getDocumentByDate(params: { startDate: string; endDate?: string; parishId?: string; documentType?: string; limit?: number; }) {
  const { data } = await api.get('/documents/by-date', {
    params: {
      start_date: params.startDate,
      end_date: params.endDate,
      parish_id: params.parishId,
      document_type: params.documentType,
      limit: params.limit ?? 100,
    }
  });
  return data as any;
}

export async function getDocumentsByParish(parishId: string, documentType?: string, limit: number = 1000) {
  const { data } = await api.get('/documents/parish', {
    params: { parish_id: parishId, document_type: documentType, limit }
  });
  return data as any;
}

export async function deleteDocument(fileId: string) {
  const { data } = await api.delete(`/documents/delete/${fileId}`);
  return data as any;
}

export async function getDocumentContent(fileIdOrEncoded: string) {
  const { data } = await api.get(`/documents/content/${fileIdOrEncoded}`);
  return data as any;
}

export async function getOpenSearchHealth() {
  const { data } = await api.get('/opensearch/health');
  return data as any;
}

export async function getOpenSearchStats() {
  const { data } = await api.get('/opensearch/stats');
  return data as any;
}

export async function refreshIndex() {
  const { data } = await api.post('/opensearch/refresh');
  return data as any;
}

