const API_BASE = '/api'

function getToken() { return localStorage.getItem('token') }

async function apiRequest(endpoint: string, options: RequestInit = {}) {
    const token = getToken()
    const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(options.headers as Record<string, string>) }
    if (token) headers['Authorization'] = `Bearer ${token}`

    const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers })
    if (response.status === 401) { localStorage.removeItem('token'); window.location.href = '/login' }
    return response
}

export async function login(username: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    if (res.ok) {
        const data = await res.json()
        localStorage.setItem('token', data.access_token)
        return true
    }
    return false
}

export function logout() {
    localStorage.removeItem('token')
    window.location.href = '/login'
}

export function isAuthenticated() { return !!getToken() }

export async function getUsers() { return (await apiRequest('/users')).json() }
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function updateUser(id: number, data: any) { return (await apiRequest(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) })).json() }
export async function deleteUser(id: number) { return apiRequest(`/users/${id}`, { method: 'DELETE' }) }

export async function getInvites() { return (await apiRequest('/invites')).json() }
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function createInvite(data: any) { return (await apiRequest('/invites', { method: 'POST', body: JSON.stringify(data) })).json() }
export async function deleteInvite(id: number) { return apiRequest(`/invites/${id}`, { method: 'DELETE' }) }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function getLogs(params?: any) {
    const query = new URLSearchParams()
    if (params?.user_id) query.set('user_id', params.user_id.toString())
    if (params?.message_type) query.set('message_type', params.message_type)
    if (params?.page) query.set('page', params.page.toString())
    if (params?.limit) query.set('limit', params.limit.toString())
    return (await apiRequest(`/logs?${query}`)).json()
}

export function getMediaUrl(logId: number) {
    const token = getToken()
    return `${API_BASE}/logs/${logId}/media${token ? `?token=${token}` : ''}`
}

export async function getConversations() {
    return (await apiRequest('/logs/conversations')).json()
}

export async function getConversationMessages(userId: number, page = 1, limit = 50) {
    return (await apiRequest(`/logs/conversations/${userId}/messages?page=${page}&limit=${limit}`)).json()
}
