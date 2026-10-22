import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ImageWithLightbox } from './ImageWithLightbox';
import './MessageList.css';

function CodeBlock({ language, code }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="code-block-container">
      <div className="code-block-header">
        <span className="code-language">{language || 'code'}</span>
        <button onClick={handleCopy} className="copy-btn" type="button">
          {copied ? '✓ Copied!' : '📋 Copy code'}
        </button>
      </div>
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={language || 'text'}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: '0 0 8px 8px',
          padding: '12px 16px',
          fontSize: '14px',
          lineHeight: '1.5',
          whiteSpace: 'pre',
          wordBreak: 'normal',
          overflowX: 'auto',
        }}
        codeTagProps={{
          style: {
            whiteSpace: 'pre',
            display: 'inline-block',
          },
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

export default function MessageList({ messages, loading }) {
  const bottomRef = useRef(null);
  const [copiedMsgIndex, setCopiedMsgIndex] = useState(null);
  const [activeSource, setActiveSource] = useState(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleCopyMessage = (content, index) => {
    navigator.clipboard.writeText(content);
    setCopiedMsgIndex(index);
    setTimeout(() => setCopiedMsgIndex(null), 2000);
  };

  return (
    <div className="message-list">
      {messages.map((msg, index) => {
        const isLast = index === messages.length - 1;
        const isThinking = isLast && msg.role === 'assistant' && !msg.content === '' && loading;

        return (
          <div key={index} className={`message-row ${msg.role}`}>
            <div className="avatar">
              {msg.role === 'user' ? '🧑🏻' : '🤖'}
            </div>

            <div className="message-wrapper">
              <div className="message-bubble">
                {isThinking ? (
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                ) : msg.role === 'assistant' ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      img({ node, ...props }) {
                        return <ImageWithLightbox src={props.src} alt={props.alt} />;
                      },
                      code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        const codeString = String(children).replace(/\n$/, '');

                        if (inline || (!match && !codeString.includes('\n'))) {
                          return (
                            <code className="inline-code" {...props}>
                              {children}
                            </code>
                          );
                        }

                        return <CodeBlock language={match ? match[1] : ''} code={codeString} />;
                      },
                      a({ node, ...props }) {
                        return <a {...props} target="_blank" rel="noopener noreferrer" className="markdown-link" />;
                      },
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
              {msg.role === 'assistant' && !isThinking && msg.content && (
                <div className="message-actions">
                  <button
                    className="full-copy-btn"
                    onClick={() => handleCopyMessage(msg.content, index)}
                    type="button"
                  >
                    {copiedMsgIndex === index ? '✓ Copied' : '📋 Copy'}
                  </button>

                  {msg.sources && msg.sources.length > 0 && (
                    <button
                      className="gemini-sources-btn"
                      onClick={() => setActiveSource(msg.sources[0])}
                      type="button"
                    >
                      <svg
                        className="gemini-sparkle-svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M12 2C12 7.52285 7.52285 12 2 12C7.52285 12 12 16.4771 12 22C12 16.4771 16.4771 12 22 12C16.4771 12 12 7.52285 12 2Z"
                          fill="url(#geminiGradient)"
                        />
                        <defs>
                          <linearGradient
                            id="geminiGradient"
                            x1="2"
                            y1="2"
                            x2="22"
                            y2="22"
                            gradientUnits="userSpaceOnUse"
                          >
                            <stop stopColor="#4285F4" />
                            <stop offset="0.5" stopColor="#9B72CB" />
                            <stop offset="1" stopColor="#D96570" />
                          </linearGradient>
                        </defs>
                      </svg>
                      <span>Sources</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* Gemini-Style Source Preview Modal */}
      {activeSource && (
        <div className="source-modal-overlay" onClick={() => setActiveSource(null)}>
          <div className="source-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="source-modal-header">
              <div className="source-modal-title-wrap">
                <span className="source-modal-icon">🌐</span>
                <h3>{activeSource.source}</h3>
              </div>
              <button className="source-modal-close" onClick={() => setActiveSource(null)} type="button">
                ✕
              </button>
            </div>
            <div className="source-modal-body">
              <p className="source-modal-desc">
                {activeSource.snippet || "Reference retrieved from secure RAG database or web search results."}
              </p>
              {activeSource.url && (
                <div className="source-modal-link-wrap">
                  <span className="source-modal-url-label">URL:</span>
                  <a href={activeSource.url} target="_blank" rel="noopener noreferrer" className="source-modal-link">
                    {activeSource.url}
                  </a>
                </div>
              )}
            </div>
            <div className="source-modal-footer">
              {activeSource.url && (
                <a href={activeSource.url} target="_blank" rel="noopener noreferrer" className="source-visit-btn">
                  Visit site ↗
                </a>
              )}
              <button className="source-close-btn" onClick={() => setActiveSource(null)} type="button">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}