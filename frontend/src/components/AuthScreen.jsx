import { useState } from "react"
import { API_BASE_URL } from "../api"
import "./AuthScreen.css"

export default function AuthScreen({onAuthenticated, onGuest}){
    const [mode, setMode] = useState("login")
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")
    const [notice, setNotice] = useState("")

    const handleSubmit = async (event)=>{
        event.preventDefault()
        setError("")
        setNotice("")
        setLoading(true)

        try {
            const endpoint = mode==="login"?"/auth/login":"/auth/registry";
            const response = await fetch(`${API_BASE_URL}${endpoint}`,
                {
                    method:"POST",
                    headers: {"Content-Type": "application/json"},
                    body : JSON.stringify({
                        email: email.trim(),
                        password
                    })
                },
            )
            const data = await response.json()

            if(!response.ok){
                throw new Error(data.detail || "Authentication failed.")
            }
            if(mode === "registry"){
                setMode("login")
                setPassword("")
                setNotice("Account created successfully. Please log in.")
                return
            }
            if(!data.access_token){
                throw new Error("The server did not return an access token.")
            }
            onAuthenticated(data.access_token)
        } catch (err) {
            setError(err.message || "something went wrong.")
        } finally{
            setLoading(false)
        }
    }

    return(
        <main className="auth-screen">
            <form onSubmit={handleSubmit} className="auth-card">
                <h1>Laika AI</h1>
                <p className="auth-subtitle">{mode === "login"?"Welcome back. Sign in to continue.":"Create your Laika account."}</p>
                <label htmlFor="auth-email">Email</label>
                <input type="email" id="auth-email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" autoComplete="email" required/>
                <label htmlFor="auth-password">Password</label>
                <input type="password" id="auth-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === "registry"?"At least 8 characters": "Enter your password"} autoComplete={mode === "login"?"current-password": "new-password"} minLength={mode === "registry"?8 : undefined} maxLength={128} required/>
                {error && (
                    <p className="auth-error" role="alert">
                        {error}
                    </p>
                )}
                {notice && (
                    <p className="auth-notice" role="status">
                        {notice}
                    </p>
                )}
                <button type="submit" disabled={loading}>
                    {loading ?"Please wait...":mode ==="login"?"Log In": "Created Account"}
                </button>
                <p className="auth-switch">{mode === "login"?"Don't have an account?":"Already have an account?"} <button type="button" className="auth-switch-button" onClick={() => {
                    setMode(mode === "login"?"registry":"login")
                    setError("")
                    setNotice("")
                }}>{mode == "login"?"Register": "Log In"}</button></p>
                {onGuest && (

                    <button className="guest-mode-btn" type="button" onClick={()=> onGuest(true)}
                    style={{background: 'transparent', border: '1px solid #414151', color: '#aaaab8', marginTop:'10px', width:'100%', padding: '10px', borderRadius: '8px', cursor: 'pointer'}}
                    >Continue as Guest</button>
                )} 
            </form>
        </main>
    )
}