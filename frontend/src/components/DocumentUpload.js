import React, { useState, useRef } from 'react';
import './DocumentUpload.css';

const DocumentUpload = ({ onDocumentUploaded, onError }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [sermonDate, setSermonDate] = useState('');
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file) => {
    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];

    if (!allowedTypes.includes(file.type)) {
      onError('Please upload a PDF, DOC, DOCX, or TXT file.');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      onError('File size must be less than 10MB.');
      return;
    }

    setIsUploading(true);

    try {
      const apiService = await import('../services/api');
      const formattedDate = sermonDate ? sermonDate : null;
      const result = await apiService.default.uploadDocument(file, 'default', 'document', formattedDate);
      onDocumentUploaded(result);
    } catch (error) {
      onError(`Upload failed: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="document-upload">
      <h2>Upload Document</h2>
      
      <div className="sermon-date-input">
        <label htmlFor="sermon-date">Sermon Date (Optional):</label>
        <input
          id="sermon-date"
          type="date"
          value={sermonDate}
          onChange={(e) => setSermonDate(e.target.value)}
          disabled={isUploading}
        />
      </div>

      <div
        className={`upload-area ${dragActive ? 'drag-active' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={openFileDialog}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileInput}
          accept=".pdf,.doc,.docx,.txt"
          style={{ display: 'none' }}
        />
        
        {isUploading ? (
          <div className="upload-content">
            <div className="spinner"></div>
            <p>Uploading document...</p>
          </div>
        ) : (
          <div className="upload-content">
            <div className="upload-icon">📄</div>
            <p className="upload-text">
              {dragActive 
                ? 'Drop your document here' 
                : 'Click to upload or drag and drop your document'
              }
            </p>
            <p className="upload-hint">
              Supports PDF, DOC, DOCX, and TXT files (max 10MB)
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentUpload;
