import { useState } from "react";

export default function MessageInput({onSendMessage, loading}){
    const [input, setInput] = useState('')

    const handleSubmit = (e) => {
        e.preventDefault()
        if(!input.trim() || loading) return
        onSendMessage(input)
        setInput('')
    }
    return (
        <form onSubmit={handleSubmit} className="input-form">
            <input type="text"
            placeholder="Send a massage..."
            value={input}
            onChange={(e) =>setInput(e.target.value)}
            disabled={loading}
            />
            <button type="submit" disabled={!input.trim() || loading}>Send</button>
        </form>
    )
}
