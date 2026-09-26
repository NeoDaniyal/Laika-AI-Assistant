export default function Sidebar({ chats, currentChatId, onSelectChat,  onNewChat}){
    return(
        <div className="sidebar">
            <button className="new-chat-btn" onClick={onNewChat}>
                + New Chat
            </button>
            <div className="chat-history-list">
                <p className="history-title">Recent Chats</p>
                {chats.map((chat)=>(
                    <div
                        key={chat.id}
                        className={`history-item ${chat.id === currentChatId ? 'active': ''}`}
                        onClick={()=> onSelectChat(chat.id)}>
                            {chat.title}
                    </div>
                ))}
                <div className="history-item active">Current Conversation</div>
            </div>
        </div>

    )
}