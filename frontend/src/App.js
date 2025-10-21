import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [error, setError] = useState(null);

  const handleDocumentUploaded = (document) => {
    setSelectedDocument(document);
    setError(null);
  };

  const handleError = (errorMessage) => {
    setError(errorMessage);
  };

  const clearError = () => {
    setError(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Homilia AI</h1>
        <p>Upload documents and chat with AI assistant</p>
      </header>
      
      <main className="App-main">
        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={clearError} className="close-error">×</button>
          </div>
        )}
        
        <div className="app-content">
          <div className="upload-section">
            <DocumentUpload 
              onDocumentUploaded={handleDocumentUploaded}
              onError={handleError}
            />
          </div>
          
          <div className="chat-section">
            <ChatInterface 
              selectedDocument={selectedDocument}
              onError={handleError}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
