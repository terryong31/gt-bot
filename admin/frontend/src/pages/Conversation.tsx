import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getConversationMessages, getMediaUrl } from '../api'
import { formatTime } from '../utils'
import { ArrowLeft, Clock, Paperclip } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'

const MESSAGES_PER_PAGE = 10

export default function Conversation() {
    const { userId } = useParams<{ userId: string }>()
    const navigate = useNavigate()
    const [data, setData] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [visibleCount, setVisibleCount] = useState(MESSAGES_PER_PAGE)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        loadMessages()
    }, [userId])

    const loadMessages = async () => {
        if (!userId) return
        setLoading(true)
        const result = await getConversationMessages(parseInt(userId))
        setData(result)
        setLoading(false)
        setVisibleCount(MESSAGES_PER_PAGE)
    }

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        if (!loading && data) {
            scrollToBottom()
        }
    }, [loading, data])

    const showMore = () => {
        setVisibleCount(prev => prev + MESSAGES_PER_PAGE)
    }

    if (loading) return <div className="text-center text-slate-500 dark:text-slate-400 py-12">Loading conversation...</div>
    if (!data) return <div className="text-center text-slate-500 dark:text-slate-400 py-12">Error loading conversation</div>

    // Get visible messages
    const allMessages = data.messages || []
    const totalMessages = allMessages.length
    const hiddenCount = Math.max(0, totalMessages - visibleCount)
    const visibleMessages = allMessages.slice(hiddenCount)

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4 bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <Button variant="ghost" size="sm" onClick={() => navigate('/logs')} className="shrink-0 gap-2">
                    <ArrowLeft size={16} /> Back
                </Button>
                <div className="w-px h-8 bg-slate-200 dark:bg-slate-700" />
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-lg shrink-0">
                        {data.user.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <h2 className="font-bold text-slate-900 dark:text-white">{data.user.name}</h2>
                        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                            <span className="font-mono">{data.user.telegram_id}</span>
                            <span>•</span>
                            <span>{totalMessages} messages</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Messages Area */}
            <div className="bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 min-h-[500px] flex flex-col">
                {hiddenCount > 0 && (
                    <div className="text-center pb-6">
                        <Button variant="secondary" size="sm" onClick={showMore} className="text-xs">
                            Load older messages ({hiddenCount} remaining)
                        </Button>
                    </div>
                )}

                <div className="space-y-6 flex-1">
                    {visibleMessages.map((msg: any, idx: number) => {
                        const isUser = msg.sender === 'user'
                        return (
                            <div key={`${msg.id}-${idx}`} className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
                                <div className={cn(
                                    "flex flex-col max-w-[75%]",
                                    isUser ? "items-end" : "items-start"
                                )}>
                                    <div className={cn(
                                        "rounded-2xl px-5 py-3 shadow-sm text-sm leading-relaxed",
                                        isUser
                                            ? "bg-blue-600 text-white rounded-br-none"
                                            : "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-bl-none"
                                    )}>
                                        {msg.message_type === 'text' ? (
                                            <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                                        ) : msg.message_type === 'photo' ? (
                                            <div className="space-y-2">
                                                <a
                                                    href={getMediaUrl(msg.id)}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="block"
                                                    title="View Full Size"
                                                >
                                                    <img
                                                        src={getMediaUrl(msg.id)}
                                                        alt="Photo"
                                                        className="rounded-lg max-w-sm max-h-64 object-cover hover:brightness-95 transition-all bg-black/5"
                                                    />
                                                </a>
                                                {msg.content && <p className="whitespace-pre-wrap break-words mt-1">{msg.content}</p>}
                                            </div>
                                        ) : (
                                            <a
                                                href={getMediaUrl(msg.id)}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className={cn(
                                                    "flex items-center gap-2 underline decoration-current underline-offset-2",
                                                    isUser ? "text-white/90 hover:text-white" : "text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                                                )}
                                            >
                                                <Paperclip size={14} />
                                                <span>{msg.file_name || `${msg.message_type?.toUpperCase() || 'FILE'}`}</span>
                                            </a>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-1 mt-1.5 text-[10px] text-slate-400 dark:text-slate-500 font-medium px-1">
                                        <Clock size={10} />
                                        {formatTime(msg.created_at)}
                                    </div>
                                </div>
                            </div>
                        )
                    })}

                    {totalMessages === 0 && (
                        <div className="flex-1 flex flex-col items-center justify-center text-slate-400 dark:text-slate-500">
                            <Clock size={48} className="mb-4 opacity-20" />
                            <p>No messages in this conversation yet</p>
                        </div>
                    )}
                </div>
                <div ref={messagesEndRef} />
            </div>
        </div>
    )
}
