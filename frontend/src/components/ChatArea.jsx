import { useState } from "react";
import MessageInput from "./MessageInput";
import MessageList from "./MessageList";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function ChatArea({
    messages,
    loading,
    onSendMessage
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
        // If your backend currently expects 'file' (singular), append them appropriately
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

            console.log("Upload response:", data);

            // SAFELY handle response whether backend returns 'files' array or single 'chunks_created'
            let newFilesInfo = [];
            if (data.files && Array.isArray(data.files)) {
                newFilesInfo = data.files.map(f => ({
                    name: f.name,
                    chunks: f.chunks || 0
                }));
            } else {
                // Fallback for single file backend response
                files.forEach(file => {
                    newFilesInfo.push({
                        name: file.name,
                        chunks: data.chunks_created || 0
                    });
                });
            }

            setAttachedFiles(prev => [...prev, ...newFilesInfo]);
            setUploadStatus(`📎 Successfully uploaded file(s).`);

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
                <h3>Laika Chat Assistant</h3>
            </header>

            <MessageList
                messages={messages}
                loading={loading}
            />

            <MessageInput
                onSendMessage={handleSendWithAttachments}
                loading={loading || uploading}
                onFileUpload={handleFileUploads}
                uploadStatus={uploadStatus}
                attachedFiles={attachedFiles}
                onRemoveAttachment={handleRemoveFile}
            />
        </div>
    );
}