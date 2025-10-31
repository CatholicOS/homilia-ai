import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import './DocumentDisplay.css';

const DocumentDisplay = () => {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (!fileId) {
          setError('No file ID provided');
          return;
        }
        
        const response = await apiService.getDocumentContent(fileId);
        
        if (response.success) {
          setDocument(response);
        } else {
          setError('Failed to load document');
        }
      } catch (err) {
        console.error('Error fetching document:', err);
        setError(err.message || 'Failed to load document');
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [fileId]);

  const handleBackToHome = () => {
    navigate('/');
  };

  const renderContent = () => {
    if (!document) return null;

    const { content, file_type, encoding } = document;

    // Handle different file types
    switch (file_type?.toLowerCase()) {
      case 'pdf':
        return (
          <div className="pdf-container">
            <p className="file-notice">
              PDF files are not directly viewable in the browser. 
              <br />
              <a href={`data:application/pdf;base64,${content}`} download={document.filename}>
                Download PDF
              </a>
            </p>
          </div>
        );
      
      case 'docx':
      case 'doc':
        return (
          <div className="doc-container">
            <p className="file-notice">
              Word documents are not directly viewable in the browser.
              <br />
              <a href={`data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,${content}`} download={document.filename}>
                Download Document
              </a>
            </p>
          </div>
        );
      
      case 'txt':
      case 'rtf':
      default:
        // For text files, display the content directly
        if (encoding === 'base64') {
          try {
            const decodedContent = atob(content);
            return (
              <div className="text-content">
                <pre>{decodedContent}</pre>
              </div>
            );
          } catch (err) {
            return (
              <div className="error-content">
                <p>Error decoding content: {err.message}</p>
              </div>
            );
          }
        } else {
          return (
            <div className="text-content">
              <pre>{content}</pre>
            </div>
          );
        }
    }
  };

  if (loading) {
    return (
      <div className="document-display">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading document...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-display">
        <div className="error-container">
          <h2>Error Loading Document</h2>
          <p>{error}</p>
          <button onClick={handleBackToHome} className="back-button">
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="document-display">
        <div className="error-container">
          <h2>Document Not Found</h2>
          <p>The requested document could not be found.</p>
          <button onClick={handleBackToHome} className="back-button">
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="document-display">
      <div className="document-header">
        <button onClick={handleBackToHome} className="back-button">
          ← Back to Home
        </button>
        <h1 className="document-title">{document.filename}</h1>
        <div className="document-meta">
          <span className="file-type">{document.file_type?.toUpperCase()}</span>
          <span className="content-type">{document.content_type}</span>
        </div>
      </div>
      
      <div className="document-content">
        {renderContent()}
      </div>
    </div>
  );
};

export default DocumentDisplay;
