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
  const [activeSource, setActiveSource] = useState(null)

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
        const isThinking = isLast && msg.role === 'assistant' && msg.content === '' && loading;

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
                        return (
                          <ImageWithLightbox
                            src={props.src}
                            alt={props.alt}
                          />
                        );
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

                        return (
                          <CodeBlock
                            language={match ? match[1] : ''}
                            code={codeString}
                          />
                        );
                      },
                      a({ node, ...props }) {
                        return (
                          <a
                            {...props}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="markdown-link"
                          />
                        );
                      },
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>

              {/* RAG Source Citations Footer */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources-footer">
                  <span className="sources-label">Sources:</span>
                  <div className="sources-chips">
                    {msg.sources.map((src, sIdx) => {
                      <button
                        key={sIdx}
                        type='button'
                        className="source-chip"
                        onClick={() => setActiveSource(src)}
                        title='Click to view source details'
                      >
                        🌐 <span>{src.sources}</span>
                      </button>
                    })}
                  </div>
                </div>
              )}

              {/* Gemini-Style Copy Response Action Bar */}
              {msg.role === 'assistant' && !isThinking && msg.content && (
                <div className="message-actions">
                  <button
                    className="full-copy-btn"
                    onClick={() => handleCopyMessage(msg.content, index)}
                    type="button"
                  >
                    {copiedMsgIndex === index ? '✓ Copied response' : '📋 Copy'}
                  </button>
                </div>
              )}
            </div>
          </div>
        );
      })}
      {activeSource && (
        <div className="source-model-overlay" onClick={() => setActiveSource(null)}>
          <div className="source-model-card" onClick={(e) => e.stopPropagation()}>
            <div className="source-model-header">
              <span className="source-modal-icon">🌐</span>
              <h3>{activeSource.sources}</h3>
            </div>
            <button className="source-model-close"
              onClick={() => setActiveSource(null)}
              type='button'>
              ✕
            </button>
          </div>
          <div className="source-modal-body">
            <p className="source-modal-desc">
              {activeSource.snippet || "Reference retrieved from secure RAG daabase or web search results."}
            </p>
            {activeSource.url && (
              <div className="source-modal-link-wrap">
                <span className="source-model-url-label">URL:</span>
                <a href={activeSource.url} target='_blank' rel='noopener noreferrer' className='source-modal-link'>
                  {activeSource.url}
                </a>
              </div>

            )}
            <div className="source-modal-footer">
              {activeSource.url && (
                <a href={activeSource.url} target='_blank' rel='noopener noreferrer' className="source-visit-btn">
                  Visit site ↗
                </a>
              )}
              <button className='source-close-btn' onClick={() => setActiveSource(null)} type='button'>Close</button>
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}