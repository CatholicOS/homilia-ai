const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  async uploadDocument(file, parishId = 'default', documentType = 'document', useTextract = false) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('parish_id', parishId);
    formData.append('document_type', documentType);
    formData.append('use_textract', useTextract.toString());

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async chatWithAgent(message, documentId = null) {
    const response = await fetch(`${API_BASE_URL}/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        document_id: documentId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getDocumentInfo(fileId) {
    const response = await fetch(`${API_BASE_URL}/documents/info/${fileId}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch document info: ${response.statusText}`);
    }

    return response.json();
  }

  async getDocumentsByDate(startDate, endDate = null, parishId = null, documentType = null) {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (parishId) params.append('parish_id', parishId);
    if (documentType) params.append('document_type', documentType);

    const response = await fetch(`${API_BASE_URL}/documents/by-date?${params}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch documents by date: ${response.statusText}`);
    }

    return response.json();
  }

  async deleteDocument(documentId) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete document: ${response.statusText}`);
    }

    return response.json();
  }

  async searchDocuments(query) {
    const response = await fetch(`${API_BASE_URL}/documents/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Failed to search documents: ${response.statusText}`);
    }

    return response.json();
  }

  async getAgentInfo() {
    const response = await fetch(`${API_BASE_URL}/agent/info`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get agent info: ${response.statusText}`);
    }

    return response.json();
  }

  async getSupportedFormats() {
    const response = await fetch(`${API_BASE_URL}/documents/supported-formats`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get supported formats: ${response.statusText}`);
    }

    return response.json();
  }

  async getDocumentContent(fileId) {
    const response = await fetch(`${API_BASE_URL}/documents/content/${fileId}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get document content: ${response.statusText}`);
    }

    return response.json();
  }
}

export default new ApiService();
