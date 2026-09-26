import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import './App.css';

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

  const handleNewChat = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/chats', { method: 'POST' });
      const data = await res.json();
      setCurrentChatId(data.chat_id);
      setMessages([]);
      await fetchChats();
    } catch (err) {
      console.error('Failed to create new chat session:', err);
    }
  };

  const handleSendMessage = async (userMessage) => {
    let activeChatId = currentChatId;

    // Create session if user starts typing without selecting/creating one
    if (!activeChatId) {
      try {
        const res = await fetch('http://127.0.0.1:8000/chats', { method: 'POST' });
        const data = await res.json();
        activeChatId = data.chat_id;
        setCurrentChatId(activeChatId);
      } catch (err) {
        console.error('Error starting session:', err);
        return;
      }
    }

    const updatedMessages = [
      ...messages,
      { role: 'user', content: userMessage },
    ];

    setMessages([
      ...updatedMessages,
      { role: 'assistant', content: '' }
    ]);
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: activeChatId,
          messages: updatedMessages
        }),
      });

      if (!response.ok) throw new Error('Network Error');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      // Turn off full-screen/block loading state as streaming begins
      setLoading(false);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        // Decode incoming raw text token directly
        const tokenChunk = decoder.decode(value, { stream: true });

        setMessages((prev) => {
          const newMessages = [...prev];
          const lastIndex = newMessages.length - 1;
          newMessages[lastIndex] = {
            ...newMessages[lastIndex],
            content: newMessages[lastIndex].content + tokenChunk,
          };
          return newMessages;
        });
      }

      // Reload sidebar to reflect updated titles
      fetchChats();
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

  return (
    <div className="app-container">
      <Sidebar
        chats={chats}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
      />
      <ChatArea
        messages={messages}
        loading={loading}
        onSendMessage={handleSendMessage}
      />
    </div>
  );
}