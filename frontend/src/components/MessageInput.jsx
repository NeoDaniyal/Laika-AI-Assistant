import { useEffect, useRef, useState } from "react";
import './MessageInput.css';

export default function MessageInput({ 
    onSendMessage, 
    onStopGeneration,
    loading, 
    onFileUpload, 
    uploadStatus, 
    attachedFiles = [], 
    onRemoveAttachment 
}) {
    const [input, setInput] = useState('');
    const fileInputRef = useRef(null);
    const textareaRef = useRef(null);

    useEffect(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
      }
    }, [input])
    
    const handleSubmit = (e) => {
        e.preventDefault();
        if ((!input.trim() && attachedFiles.length === 0) || loading) return;
        
        onSendMessage(input, attachedFiles);
        setInput('');
        if(textareaRef.current){
            textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e) =>{
        if(e.key === 'Enter' && !e.shiftKey){
            e.preventDefault();
            handleSubmit();
        }
    }
    const handleFileChange = (e) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        if (onFileUpload) {
            onFileUpload(files);
        }
        e.target.value = "";
    };

    return (
        <div className="message-input-container">
            {/* Multiple File Preview Pills & Status Bar */}
            {(attachedFiles.length > 0 || uploadStatus) && (
                <div className="upload-status-bar">
                    <div className="file-preview-list">
                        {attachedFiles.map((file, idx) => (
                            <div key={idx} className="file-preview-pill">
                                <span>📎 <strong>{file.name}</strong> ({file.chunks} chunks)</span>
                                <button 
                                    type="button" 
                                    className="remove-file-btn" 
                                    onClick={() => onRemoveAttachment(idx)}
                                    title="Remove file"
                                >
                                    ×
                                </button>
                            </div>
                        ))}
                    </div>
                    {uploadStatus && <span className="status-text">{uploadStatus}</span>}
                </div>
            )}

            <form onSubmit={handleSubmit} className="input-form">
                <input 
                    type="file"
                    ref={fileInputRef}
                    hidden
                    multiple
                    onChange={handleFileChange}
                    accept=".pdf,.txt,.docx,.csv,.png,.jpg,.jpeg"
                />
                
                <button 
                    type="button" 
                    className="upload-btn"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={loading}
                    title="Upload Documents or Photos"
                >
                    +
                </button>

                <textarea
                    ref={textareaRef}
                    className="message-input"
                    placeholder="Ask Laika..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={loading}
                    rows={1}
                />

                {loading ? (
                    <button 
                        type="button" 
                        className="stop-btn" 
                        onClick={onStopGeneration}
                        title="Stop generating"
                    >
                        ■ Stop
                    </button>
                ) : (
                    <button 
                        type="submit" 
                        className="send-btn" 
                        disabled={(!input.trim() && attachedFiles.length === 0) || loading}
                    >
                        Send
                    </button>
                )}
            </form>
        </div>
    );
}