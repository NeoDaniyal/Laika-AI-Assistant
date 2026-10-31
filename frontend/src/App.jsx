import { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import AuthScreen from "./components/AuthScreen";
import { apiFetch, API_BASE_URL } from "./api";
import './App.css';

export default function App() {
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isGuest, setIsGuest] = useState(false);
  
  const [token, setToken] = useState(
    () => sessionStorage.getItem("laika_access_token")
  );
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  const abortControllerRef = useRef(null);

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setLoading(false);
    }
  };

  // Verify session on token change
  useEffect(() => {
    let cancelled = false;

    async function verifySession() {
      if (!token) {
        setCurrentUser(null);
        setAuthLoading(false);
        return;
      }

      setAuthLoading(true);

      try {
        const response = await fetch(
          `${API_BASE_URL}/auth/me`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error("Session expired or invalid.");
        }

        const user = await response.json();

        if (!cancelled) {
          setCurrentUser(user);
        }
      } catch {
        sessionStorage.removeItem("laika_access_token");

        if (!cancelled) {
          setToken(null);
          setCurrentUser(null);
        }
      } finally {
        if (!cancelled) {
          setAuthLoading(false);
        }
      }
    }

    verifySession();

    return () => {
      cancelled = true;
    };
  }, [token]);

  // Load chats only when user is authenticated
  useEffect(() => {
    if (currentUser) {
      fetchChats();
    } else {
      setChats([]);
      setCurrentChatId(null);
      setMessages([]);
    }
  }, [currentUser]);

  const handleAuthenticated = (accessToken) => {
    sessionStorage.setItem("laika_access_token", accessToken);
    setIsGuest(false); // Clear guest flag upon successful login
    setAuthLoading(true);
    setToken(accessToken);
  };

  const handleLogout = () => {

    if(isGuest){
      setIsGuest(false)
      setMessages([])
      return;
    }
    sessionStorage.removeItem("laika_access_token");

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setToken(null);
    setCurrentUser(null);
    setIsGuest(false);
    setChats([]);
    setCurrentChatId(null);
    setMessages([]);
    setLoading(false);
  };

  const parseLegacyMessageSources = (msg) => {
    if (msg.content && (msg.content.includes('SOURCES_JSON:') || msg.content.includes('__SOURCES_JSON__'))) {
      const delimiter = msg.content.includes('SOURCES_JSON:') ? 'SOURCES_JSON:' : '__SOURCES_JSON__:';
      const parts = msg.content.split(delimiter);
      const cleanContent = parts[0].trim();

      let parsedSources = msg.sources || [];
      if (parts[1]) {
        try {
          parsedSources = JSON.parse(parts[1].trim());
        } catch (err) {
          console.error("Failed to parse legacy sources json.", err);
        }
      }
      return {
        ...msg,
        content: cleanContent,
        sources: parsedSources
      };
    }
    return msg;
  };

  const fetchChats = async () => {
    if(isGuest) return;
    try {
      const res = await apiFetch("/chats");
      if (res.status === 401) {
        handleLogout();
        return;
      }
      if (!res.ok) throw new Error('Failed to fetch chats');
      const data = await res.json();
      setChats(data);
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  const handleSelectChat = async (chatId) => {
    if (loading) return;
    setCurrentChatId(chatId);
    try {
      const res = await apiFetch(`/chats/${chatId}`);
      if (res.status === 401) {
        handleLogout();
        return;
      }
      const data = await res.json();
      const cleanMessages = (data.messages || []).map(parseLegacyMessageSources);
      setMessages(cleanMessages);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleNewChat = () => {
    setCurrentChatId(null);
    setMessages([]);
  };

  const handleSendMessage = async (userMessage, attachments = []) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const imageAttachments = attachments
      .filter((file) => file.type === "image" && file.url)
      .map((file) => ({
        url: file.url,
        name: file.name
      }));

    const documentIds = attachments
      .filter((file) => file.type === "document" && file.document_id)
      .map((file) => file.document_id);

    const updatedMessages = [
      ...messages,
      { 
        role: 'user', 
        content: userMessage, 
        images: imageAttachments.length > 0 ? imageAttachments : undefined,
        document_ids: documentIds.length > 0 ? documentIds : undefined 
      },
    ];

    setMessages([
      ...updatedMessages,
      { role: 'assistant', content: '', sources: [] }
    ]);
    setLoading(true);

    try {
      const response = await apiFetch("/chat/stream", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: currentChatId,
          messages: updatedMessages
        }),
        signal: controller.signal,
      });

      if (response.status === 401 && !isGuest) {
        handleLogout();
        return;
      }
      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let assistantText = '';
      let assistantSources = [];
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split('\n\n');

        buffer = blocks.pop();

        for (const block of blocks) {
          if (!block.trim()) continue;

          const eventMatch = block.match(/^event:\s*(.+)$/m);
          const dataMatch = block.match(/^data:\s*(.+)$/m);

          if (eventMatch && dataMatch) {
            const eventType = eventMatch[1].trim();
            const rawData = dataMatch[1].trim();
            if (eventType === 'chat_id') {
              try {
                const parsedData = JSON.parse(rawData);
                setCurrentChatId(parsedData.chat_id);
              } catch (e) {
                console.error('Error parsing chat_id SSE event:', e);
              }
            }
            else if (eventType === 'token') {
              try {
                const parsed = JSON.parse(rawData);
                assistantText += parsed.content || '';

                let finalContent = assistantText;
                let extractedSources = assistantSources;

                if (assistantText.includes('__SOURCES_JSON__:')) {
                  const parts = assistantText.split('__SOURCES_JSON__:');
                  finalContent = parts[0].trim();
                  try {
                    extractedSources = JSON.parse(parts[1].trim());
                  } catch (err) {
                    console.error('Failed to parse embedded sources json', err);
                  }
                }

                setMessages((prev) => {
                  const newMsgs = [...prev];
                  const lastIdx = newMsgs.length - 1;
                  newMsgs[lastIdx] = {
                    ...newMsgs[lastIdx],
                    content: finalContent,
                    sources: extractedSources,
                  };
                  return newMsgs;
                });
              } catch (e) {
                console.error('Error parsing token SSE event:', e);
              }
            }
            else if (eventType === 'sources') {
              try {
                assistantSources = JSON.parse(rawData);
                setMessages((prev) => {
                  const newMsgs = [...prev];
                  const lastIdx = newMsgs.length - 1;
                  newMsgs[lastIdx] = {
                    ...newMsgs[lastIdx],
                    sources: assistantSources,
                  };
                  return newMsgs;
                });
              } catch (e) {
                console.error('Error parsing sources SSE event:', e);
              }
            }
          }
        }
      }

      if (!isGuest) {
        await fetchChats();
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Generation stopped by user.');
      } else {
        console.error('Streaming error:', err);
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleEditMessage = (index, newContent) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);

    const truncatedHistory = messages.slice(0, index);
    const existingDocumentIds = messages[index]?.document_ids || [];

    const updatedMessages = [
      ...truncatedHistory,
      { role: 'user', content: newContent, document_ids: existingDocumentIds.length > 0 ? existingDocumentIds : undefined }
    ];
    setMessages(updatedMessages);

    setTimeout(() => {
      handleSendMessageWithHistory(newContent, truncatedHistory, existingDocumentIds);
    }, 10);
  };

  const handleSendMessageWithHistory = async (userMessage, currentHistory, documentIds = []) => {
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const updatedMessages = [
      ...currentHistory,
      { role: 'user', content: userMessage, document_ids: documentIds.length > 0 ? documentIds : undefined },
    ];

    setMessages([
      ...updatedMessages,
      { role: 'assistant', content: '', sources: [] }
    ]);
    setLoading(true);

    try {
      const response = await apiFetch("/chat/stream", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: currentChatId,
          messages: updatedMessages
        }),
        signal: controller.signal,
      });

      if (response.status === 401 && !isGuest) {
        handleLogout();
        return;
      }
      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let assistantText = '';
      let assistantSource = [];
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split('\n\n');
        buffer = blocks.pop();

        for (const block of blocks) {
          if (!block.trim()) continue;

          const eventMatch = block.match(/^event:\s*(.+)$/m);
          const dataMatch = block.match(/^data:\s*(.+)$/m);

          if (eventMatch && dataMatch) {
            const eventType = eventMatch[1].trim();
            const rawData = dataMatch[1].trim();
            if (eventType === 'chat_id') {
              try {
                const parsedData = JSON.parse(rawData);
                setCurrentChatId(parsedData.chat_id);
              } catch (e) {
                console.error("Error parsing chat_id SSE event: ", e);
              }
            }
            else if (eventType === 'token') {
              try {
                const parsed = JSON.parse(rawData);
                assistantText += parsed.content || '';

                let finalContent = assistantText;
                let extractedSources = assistantSource;

                if (assistantText.includes('__SOURCES_JSON__:')) {
                  const parts = assistantText.split('__SOURCES_JSON__:');
                  finalContent = parts[0].trim();
                  try {
                    extractedSources = JSON.parse(parts[1].trim());
                  } catch (err) {
                    console.error('Failed to parse embedded sources json', err);
                  }
                }
                setMessages((prev) => {
                  const newMsgs = [...prev];
                  const lastIdx = newMsgs.length - 1;
                  newMsgs[lastIdx] = {
                    ...newMsgs[lastIdx],
                    content: finalContent,
                    sources: extractedSources,
                  };
                  return newMsgs;
                });
              } catch (err) {
                console.error('Error parsing token SSE event:', err);
              }
            }
            else if (eventType === 'sources') {
              try {
                assistantSource = JSON.parse(rawData);
                setMessages((prev) => {
                  const newMsgs = [...prev];
                  const lastIdx = newMsgs.length - 1;
                  newMsgs[lastIdx] = {
                    ...newMsgs[lastIdx],
                    sources: assistantSource,
                  };
                  return newMsgs;
                });
              } catch (e) {
                console.error('Error parsing sources SSE event:', e);
              }
            }
          }
        }
      }

      if (!isGuest) {
        await fetchChats();
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Generation stopped by the user.');
      } else {
        console.error('Streaming error:', err);
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleRenameChat = async (chatId, newTitle) => {
    try {
      const res = await apiFetch(`/chats/${chatId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle })
      });

      if (res.status === 401) {
        handleLogout();
        return;
      }
      if (res.ok) {
        fetchChats();
      }
    } catch (error) {
      console.error("Failed to rename chat: ", error);
    }
  };

  const handleDeleteChat = async (chatId) => {
    if (!window.confirm("Are you sure you want to delete this chat? This action cannot be undone.")) return;
    try {
      const res = await apiFetch(`/chats/${chatId}`, {
        method: "DELETE"
      });

      if (res.status === 401) {
        handleLogout();
        return;
      }
      if (res.ok) {
        if (currentChatId === chatId) {
          handleNewChat();
        }
        fetchChats();
      }
    } catch (error) {
      console.error("Failed to delete chat: ", error);
    }
  };

  if (authLoading) {
    return (
      <div className="auth-loading" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: '#101014', color: 'white' }}>
        Loading Laika...
      </div>
    );
  }

  if (!currentUser && !isGuest) {
    return (
      <AuthScreen 
        onAuthenticated={handleAuthenticated} 
        onGuest={() => setIsGuest(true)} 
      />
    );
  }

  return (
    <div className="app-container">
      <div className={`sidebar-container ${isSidebarOpen ? 'open' : 'closed'}`}>
        <Sidebar
          chats={isGuest ? [] : chats}
          currentChatId={currentChatId}
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
          onRenameChat={handleRenameChat}
          onDeleteChat={handleDeleteChat}
        />
      </div>
      <ChatArea
        messages={messages}
        loading={loading}
        onSendMessage={handleSendMessage}
        onStopGeneration={handleStopGeneration}
        onEditMessage={handleEditMessage}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        onLogout={handleLogout}
      />
    </div>
  );
}