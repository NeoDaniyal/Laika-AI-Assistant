import { useState } from "react";
import MessageInput from "./MessageInput";
import MessageList from "./MessageList";
import './ChatArea.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const SUGGESTED_PROMPTS = [
    {
        icon: "🚀",
        title: "Latest Space News",
        prompt: "Search for the latest space exploration news"
    },
    {
        icon: "💡",
        title: "Brainstorm Ideas",
        prompt: "What are some creative project ideas using Python and AI?"
    },
    {
        icon: "🎨",
        title: "Generate Image",
        prompt: "Generate an image of a cybernetic wolf under a neon night sky"
    },
    {
        icon: "📊",
        title: "Analyze Data",
        prompt: "How do I perform technical analysis on stock data using Python?"
    },
]

export default function ChatArea({
    messages,
    loading,
    onSendMessage,
    onStopGeneration,
    onEditMessage,
    isSidebarOpen,
    onToggleSidebar
}) {
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState('');
    const [attachedFiles, setAttachedFiles] = useState([]);

    const handleFileUploads = async (fileList) => {
        const files = Array.from(fileList);
        if (files.length === 0) return;

        setUploading(true);
        setUploadStatus(`Uploading ${files.length} file(s)...`);

        const formData = new FormData();
        files.forEach((file) => {
            formData.append('files', file);
        });
        formData.append('user_id', 'default_user');

        try {
            const res = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || 'Failed to upload documents');
            }

            if (!Array.isArray(data.files)) {
                throw new Error("The server response does not contain a valid files array.");
            }

            setAttachedFiles((previous) => [
                ...previous,
                ...data.files.map((file) => ({
                    name: file.name,
                    url: file.url,
                    filename: file.filename,
                    type: file.type,
                    chunks: file.chunks || 0,
                    document_id: file.document_id || null,
                })),
            ]);

            setUploadStatus("📎 Successfully uploaded file(s).");

        } catch (error) {
            console.error('File Upload Error:', error);
            setUploadStatus(`❌ Error: ${error.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleSendWithAttachments = (text) => {
        onSendMessage(text, attachedFiles);
        setAttachedFiles([]);
        setUploadStatus('');
    };

    const handleRemoveFile = (indexToRemove) => {
        setAttachedFiles(prev => prev.filter((_, idx) => idx !== indexToRemove));
    };

    return (
        <div className="chat-area">
            <header className="chat-header">
                <div className="header-left">
                    <button className="sidebar-toggle-btn"
                        onClick={onToggleSidebar}
                        type="button"
                        title={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="9" y1="3" x2="9" y2="21"></line>
                        </svg>
                    </button>
                </div>
                <h3>Laika Chat Assistant</h3>
            </header>

            {messages.length === 0 ? (
                <div className="welcome-screen">
                    <div className="welcome-heading">
                        {/* Updated greeting with your correct name */}
                        <h1 className="neon-gradient-text">Hello, Monatasha Zara</h1>
                        <h2 className="welcome-subtext">What's on your mind today?</h2>
                    </div>
                    <div className="prompt-cards-grid">
                        {SUGGESTED_PROMPTS.map((item, idx) => (
                            <button
                                key={idx}
                                className="prompt-card"
                                onClick={() => handleSendWithAttachments(item.prompt)}
                                type="button"
                            >
                                <span className="prompt-card-icon">{item.icon}</span>
                                <div className="prompt-card-text">
                                    <span className="prompt-card-title">{item.title}</span>
                                    <span className="prompt-card-desc">{item.prompt}</span>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            ) : (
                <MessageList
                    messages={messages}
                    loading={loading}
                    onEditMessage={onEditMessage}
                />
            )}

            <MessageInput
                onSendMessage={handleSendWithAttachments}
                onStopGeneration={onStopGeneration}
                loading={loading || uploading}
                onFileUpload={handleFileUploads}
                uploadStatus={uploadStatus}
                attachedFiles={attachedFiles}
                onRemoveAttachment={handleRemoveFile}
            />
        </div>
    );
}