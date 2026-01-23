export interface User {
    id: number
    username: string
    first_name: string
    telegram_id: string
    is_google_connected: boolean
    invite_name?: string
    is_allowed: boolean
}

export interface Conversation {
    user_id: number
    user_name: string
    telegram_id: string
    last_message: string
    message_count: number
    last_activity: string
}

export interface Invite {
    id: number
    name: string
    phone?: string
    code: string
    is_used: boolean
    created_at: string
}

export interface Message {
    id: number
    sender: 'user' | 'bot'
    message_type: 'text' | 'photo' | 'document'
    content?: string
    file_name?: string
    created_at: string
}

export interface ConversationDetail {
    user: {
        name: string
        telegram_id: string
    }
    messages: Message[]
}
