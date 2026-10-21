import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import './Sidebar.css';

export default function Sidebar({
  chats = [],
  currentChatId,
  onSelectChat,
  onNewChat,
  onRenameChat,
  onDeleteChat
}) {
  const [localChats, setLocalChats] = useState(chats);
  const [editingId, setEditingId] = useState(null);
  const [titleInput, setTitleInput] = useState('');
  const [openMenuId, setOpenMenuId] = useState(null);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });

  const sidebarRef = useRef(null);
  const popupRef = useRef(null);

  useEffect(() => {
    setLocalChats(chats);
  }, [chats]);
  
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        sidebarRef.current?.contains(e.target) ||
        popupRef.current?.contains(e.target)
      ) {
        return;
      }
      setOpenMenuId(null);
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggleMenu = (e, chatId) => {
    e.stopPropagation();

    if (openMenuId === chatId) {
      setOpenMenuId(null);
      return;
    }

    const rect = e.currentTarget.getBoundingClientRect();
    const menuWidth = 160;
    const menuHeight = 100;
    const gap = 5;

    let left = rect.right - menuWidth;
    let top = rect.bottom + gap;

    left = Math.max(8, Math.min(left, window.innerWidth - menuWidth - 8));

    if (top + menuHeight > window.innerHeight - 8) {
      top = rect.top - menuHeight - gap;
    }

    setMenuPosition({ top, left });
    setOpenMenuId(chatId);
  };

  const handleStartRename = (e, chatId, currentTitle) => {
    e.stopPropagation();
    setOpenMenuId(null);
    setEditingId(chatId);
    setTitleInput(currentTitle || 'New Conversation');
  };

  const handleInputChange = (e, chatId) => {
    const val = e.target.value;
    setTitleInput(val);

    setLocalChats((prev)=>
    prev.map((c) => ((c._id || c.id) === chatId ? { ...c, title: val}: c)))
  }

  const handleSaveRename = (chatId) => {
    if (titleInput.trim() && onRenameChat) {
      onRenameChat(chatId, titleInput.trim());
    }
    setEditingId(null);
  };

  const handleKeyDown = (e, chatId) => {
    if (e.key === 'Enter') {
      handleSaveRename(chatId);
    } else if (e.key === 'Escape') {
      setEditingId(null);
    }
  };

  const handleDelete = (e, chatId) => {
    e.stopPropagation();
    setOpenMenuId(null);
    if (onDeleteChat) {
      onDeleteChat(chatId);
    }
  };

  return (
    <div className="sidebar" ref={sidebarRef}>
      <button className="new-chat-btn" onClick={onNewChat}>
        + New Chat
      </button>

      <div className="chat-history-list">
        <p className="history-title">Recent Chats</p>

        {localChats.map((chat) => {
          const chatId = chat._id || chat.id;
          const isActive = chatId === currentChatId;

          return (
            <div
              key={chatId}
              className={`history-item ${isActive ? 'active' : ''}`}
              onClick={() => {
                setOpenMenuId(null);
                onSelectChat(chatId);
              }}
            >
              {editingId === chatId ? (
                <input
                  type="text"
                  className="rename-input animate-fade-in"
                  value={titleInput}
                  onChange={(e) => setTitleInput(e.target.value)}
                  onBlur={() => handleSaveRename(chatId)}
                  onKeyDown={(e) => handleKeyDown(e, chatId)}
                  autoFocus
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="chat-title">
                  {chat.title || 'New Conversation'}
                </span>
              )}

              {/* Three-dot menu trigger button */}
              <div className="menu-container">
                <button
                  className="menu-trigger-btn"
                  onClick={(e) => handleToggleMenu(e, chatId)}
                  title="Options"
                >
                  ⋮
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Portal for Popup Menu to escape container overflow clipping */}
      {openMenuId &&
        createPortal(
          <div
            ref={popupRef}
            className="chat-popup-menu animate-scale-in"
            style={{
              position: 'fixed',
              top: `${menuPosition.top}px`,
              left: `${menuPosition.left}px`,
              zIndex: 999999,
            }}
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => e.stopPropagation()}
          >
            {(() => {
              const chat = chats.find(
                (item) => (item._id || item.id) === openMenuId
              );
              if (!chat) return null;
              return (
                <>
                  <button
                    className="menu-item"
                    onClick={(e) => handleStartRename(e, openMenuId, chat.title)}
                  >
                    ✏️ Rename
                  </button>
                  <button
                    className="menu-item delete"
                    onClick={(e) => handleDelete(e, openMenuId)}
                  >
                    🗑️ Delete
                  </button>
                </>
              );
            })()}
          </div>,
          document.body
        )}
    </div>
  );
}