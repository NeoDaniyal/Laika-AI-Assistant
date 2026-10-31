const API_BASE_URL= import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function apiFetch(path, options= {}){
    const token = sessionStorage.getItem("laika_access_token")

    const headers = new Headers(options.headers || {})

    if(token){
        headers.set("Authorization", `Bearer ${token}`)
    }

    if (options.body instanceof FormData) {
        headers.delete("Content-Type")
    }
    return fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers
    })
}
export {API_BASE_URL}