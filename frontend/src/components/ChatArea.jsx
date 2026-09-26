import MessageInput from "./MessageInput";
import MessageList from "./MessageList";

export default function ChatArea({ messages, loading, onSendMessage }){
    return (
        <div className="chat-area">
            <header className="chat-header">
                <h3>Laika Chat Assistent</h3>
            </header>
            <MessageList messages={messages} loading={loading}/>
            <MessageInput onSendMessage={onSendMessage} loading={loading}/>
        </div>
    )
}