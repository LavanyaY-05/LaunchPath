'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, FileText, X, Loader2, Sparkles, AlertCircle } from 'lucide-react';

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  sources?: string[];
  followUps?: string[];
}

interface UploadedFile {
  filename: string;
  extractedText: string;
}

interface ChatTabProps {
  initialPrompt?: string;
  onClearInitialPrompt?: () => void;
}

export default function ChatTab({ initialPrompt, onClearInitialPrompt }: ChatTabProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const [uploadStatus, setUploadStatus] = useState<'idle' | 'extracting' | 'processing' | 'ready' | 'error'>('idle');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [selectedFileIndex, setSelectedFileIndex] = useState<number>(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const selectedFile = uploadedFiles[selectedFileIndex];

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    if (initialPrompt) {
      setInput(initialPrompt);
      if (onClearInitialPrompt) onClearInitialPrompt();
    }
  }, [initialPrompt, onClearInitialPrompt]);

  const promptChips = [
    'How do I get my first 3 freelance clients?',
    'What are the eligibility rules for Startup India Seed Fund?',
    'Review my pitch deck structure and highlight key missing slides.',
    'Compare starting a freelance design agency vs building an EdTech tool.'
  ];

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: query
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          uploaded_files: uploadedFiles.map((file) => ({ filename: file.filename, extracted_text: file.extractedText }))
        })
      });

      if (!response.ok) {
        throw new Error(`Server error ${response.status}`);
      }

      const data = await response.json();
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: data.answer || "I don't have relevant information on that right now.",
        sources: data.sources || [],
        followUps: data.follow_ups || []
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error: any) {
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: error?.message || 'Unable to process your request at the moment.',
        sources: [],
        followUps: []
      };
      setMessages((prev) => [...prev, aiMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (file.size > 3 * 1024 * 1024) {
      setUploadError('File size exceeds 3MB limit.');
      setUploadStatus('error');
      return;
    }

    setUploadStatus('extracting');
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadStatus('processing');
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload file.');
      }

      const data = await response.json();
      setUploadedFiles((prev) => {
        const next = [...prev, { filename: data.filename, extractedText: data.extracted_text }];
        setSelectedFileIndex(next.length - 1);
        return next;
      });
      setUploadStatus('ready');
    } catch (error: any) {
      setUploadError(error?.message || 'File upload failed.');
      setUploadStatus('error');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      handleFileUpload(event.dataTransfer.files[0]);
    }
  };

  return (
    <div className="chat-layout">
      <div className="chat-section">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="chat-welcome">
              <Sparkles size={40} style={{ color: 'var(--accent-blue)', marginBottom: '0.5rem' }} />
              <h2>Welcome to LaunchPath</h2>
              <p>Your AI advisor for early-stage freelancing, startup schemes, and small business growth.</p>
              <div className="prompt-chips-container">
                {promptChips.map((chip, idx) => (
                  <button key={idx} className="prompt-chip" onClick={() => handleSend(chip)}>
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`message-row ${msg.sender}`}>
                <div className="message-bubble">
                  <p style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</p>
                  {msg.sender === 'ai' && msg.sources && msg.sources.length > 0 && (
                    <div className="sources-row">
                      <span className="sources-label">Sources:</span>
                      {msg.sources.map((src, index) => (
                        <span key={index} className="source-badge">{src}</span>
                      ))}
                    </div>
                  )}
                  {msg.sender === 'ai' && msg.followUps && msg.followUps.length > 0 && (
                    <div className="followups-container">
                      <span className="followups-title">Suggested Follow-ups:</span>
                      {msg.followUps.map((chip, index) => (
                        <button key={index} className="followup-chip" onClick={() => handleSend(chip)}>
                          → {chip}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="message-row ai">
              <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Loader2 className="animate-spin" size={18} style={{ color: 'var(--accent-blue)' }} />
                <span style={{ color: 'var(--text-secondary)' }}>LaunchPath is analyzing domain guidance...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form
          className="chat-input-area"
          onSubmit={(event) => {
            event.preventDefault();
            handleSend();
          }}
        >
          <input
            type="text"
            className="chat-input"
            placeholder={selectedFile ? `Ask a question about ${selectedFile.filename}...` : 'Ask LaunchPath about schemes, freelancing, roadmap, investors...'}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            disabled={loading}
          />
          <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
            <Send size={16} />
            <span>Send</span>
          </button>
        </form>
      </div>

      <div className="upload-section">
        <div className="upload-header">
          <Upload size={20} style={{ color: 'var(--accent-blue)' }} />
          <span>Document Review Panel</span>
        </div>

        {uploadedFiles.length > 0 ? (
          <div className="file-list-panel">
            <div className="upload-summary">
              <div>
                <strong>{uploadedFiles.length} document{uploadedFiles.length > 1 ? 's' : ''} uploaded</strong>
                <p style={{ margin: '0.25rem 0 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  Select one file to focus the next review or summary request.
                </p>
              </div>
            </div>
            {uploadedFiles.map((file, idx) => (
              <div
                key={`${file.filename}-${idx}`}
                className={`file-card ${selectedFileIndex === idx ? 'selected-file' : ''}`}
                onClick={() => setSelectedFileIndex(idx)}
                style={{ cursor: 'pointer' }}
              >
                <div className="file-info">
                  <FileText size={20} style={{ color: selectedFileIndex === idx ? 'var(--accent-emerald)' : 'var(--text-secondary)' }} />
                  <div>
                    <strong style={{ display: 'block', fontSize: '0.85rem' }}>{file.filename}</strong>
                    <span style={{ fontSize: '0.75rem', color: selectedFileIndex === idx ? 'var(--accent-emerald)' : 'var(--text-secondary)' }}>
                      {selectedFileIndex === idx ? 'Selected' : 'Click to select'}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  className="remove-file-btn"
                  onClick={(event) => {
                    event.stopPropagation();
                    setUploadedFiles((prev) => {
                      const next = prev.filter((_, index) => index !== idx);
                      if (next.length === 0) {
                        setSelectedFileIndex(0);
                      } else if (selectedFileIndex >= next.length) {
                        setSelectedFileIndex(next.length - 1);
                      }
                      return next;
                    });
                  }}
                  title="Remove document"
                >
                  <X size={18} />
                </button>
              </div>
            ))}
            <button type="button" className="upload-add-more-btn" onClick={() => fileInputRef.current?.click()} style={{ marginTop: '1rem' }}>
              + Upload another file
            </button>
          </div>
        ) : (
          <div
            className={`dropzone ${uploadStatus === 'extracting' || uploadStatus === 'processing' ? 'active' : ''}`}
            onDragOver={(event) => event.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".pdf,.docx,.txt"
              onChange={(event) => {
                if (event.target.files && event.target.files[0]) {
                  handleFileUpload(event.target.files[0]);
                }
              }}
            />
            {uploadStatus === 'idle' && (
              <>
                <Upload className="dropzone-icon" size={32} />
                <p className="dropzone-text">Upload Pitch Deck or Portfolio</p>
                <span className="dropzone-hint">PDF, DOCX, TXT (Max 3MB)</span>
              </>
            )}
            {uploadStatus === 'extracting' && (
              <>
                <Loader2 className="animate-spin dropzone-icon" size={32} />
                <p className="dropzone-text">Extracting text...</p>
              </>
            )}
            {uploadStatus === 'processing' && (
              <>
                <Loader2 className="animate-spin dropzone-icon" size={32} />
                <p className="dropzone-text">Processing document structure...</p>
              </>
            )}
            {uploadStatus === 'error' && (
              <>
                <AlertCircle className="dropzone-icon" size={32} style={{ color: '#ef4444' }} />
                <p className="dropzone-text" style={{ color: '#ef4444' }}>{uploadError || 'Upload failed'}</p>
                <span className="dropzone-hint">Click to try again</span>
              </>
            )}
          </div>
        )}
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
          💡 <strong>Pro Tip:</strong> Uploading your pitch deck or portfolio text attaches it to your next message. Ask <em>"Review my pitch deck"</em> to evaluate against standard investor expectations.
        </div>
      </div>
    </div>
  );
}
