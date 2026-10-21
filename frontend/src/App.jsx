import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import './App.css';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
export default function App() {
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/chats');
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
      const res = await fetch(`http://127.0.0.1:8000/chats/${chatId}`);
      const data = await res.json();
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleNewChat = () => {
    setCurrentChatId(null);
    setMessages([]);
  };
  const handleSendMessage = async (userMessage) => {
    const updatedMessages = [
      ...messages,
      { role: 'user', content: userMessage },
    ];

    // Append user message + empty assistant placeholder message
    setMessages([
      ...updatedMessages,
      { role: 'assistant', content: '', sources: [] }
    ]);
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: currentChatId,
          user_id: 'default_user',
          messages: updatedMessages
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      setLoading(false);

      let assistantText = '';
      let assistantSources = [];
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split('\n\n');

        // Keep incomplete block in buffer
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
                const newChatId = parsedData.chat_id;
                setCurrentChatId(newChatId);
              }
              catch (e) {
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

      // Refresh sidebar titles after streaming finishes
      await fetchChats();
    } catch (err) {
      console.error('Streaming error:', err);
      setMessages([
        ...updatedMessages,
        { role: 'assistant', content: 'Error: Streaming failed.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRenameChat = async (chatId, newTitle) => {
    try {
      const res = await fetch(`${API_BASE_URL}/chats/${chatId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ title: newTitle })
      })

      if (res.ok) {
        fetchChats();
      }
    } catch (error) {
      console.error("Failed to renaming chat: ", error);
    }
  }

  const handleDeleteChat = async (chatId) => {
    if (!window.confirm("Are you sure you want to delete this chat? This action cannot be undone.")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/chats/${chatId}`, {
        method: "DELETE"
      });

      if (res.ok) {
        if (currentChatId === chatId) {
          handleNewChat();
        }
        fetchChats();
      }
    } catch (error) {
      console.error("Failed to delete chat: ", error);
    }
  }
  return (
    <div className="app-container">
      <Sidebar
        chats={chats}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onRenameChat={handleRenameChat}
        onDeleteChat={handleDeleteChat}
      />
      <ChatArea
        messages={messages}
        loading={loading}
        onSendMessage={handleSendMessage}
      />
    </div>
  );
}