import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getConversations } from '../api'
import { formatDateTime } from '../utils'
import { MessageSquare } from 'lucide-react'

export default function Logs() {
    const [conversations, setConversations] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const navigate = useNavigate()

    useEffect(() => { loadConversations() }, [])

    const loadConversations = async () => {
        setLoading(true)
        const data = await getConversations()
        setConversations(data)
        setLoading(false)
    }

    if (loading) return <div className="text-center text-slate-500 dark:text-slate-400 py-12">Loading conversations...</div>

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Conversations</h2>
                <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">
                    {conversations.length} active {conversations.length === 1 ? 'conversation' : 'conversations'}
                </p>
            </div>

            {conversations.length === 0 ? (
                <div className="text-center py-20 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="mx-auto bg-slate-100 dark:bg-slate-700 w-16 h-16 rounded-full flex items-center justify-center mb-4">
                        <MessageSquare className="text-slate-400 dark:text-slate-500" size={32} />
                    </div>
                    <p className="text-lg text-slate-900 dark:text-white font-medium">No conversations yet</p>
                    <p className="text-slate-600 dark:text-slate-400 text-sm">Conversations will appear here once users start chatting</p>
                </div>
            ) : (
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 font-medium">
                                <tr>
                                    <th className="px-6 py-4">User</th>
                                    <th className="px-6 py-4">Last Message</th>
                                    <th className="px-6 py-4 text-center">Messages</th>
                                    <th className="px-6 py-4 text-right">Last Activity</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                                {conversations.map(conv => (
                                    <tr
                                        key={conv.user_id}
                                        onClick={() => navigate(`/logs/conversation/${conv.user_id}`)}
                                        className="hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors"
                                    >
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 font-bold shrink-0">
                                                    {(conv.user_name || '?').charAt(0).toUpperCase()}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-slate-900 dark:text-white">{conv.user_name}</div>
                                                    <div className="text-xs text-slate-500 dark:text-slate-400 font-mono">{conv.telegram_id}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-slate-600 dark:text-slate-400 max-w-md truncate">
                                                {conv.last_message || '—'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                                                {conv.message_count}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right text-slate-500 dark:text-slate-400 whitespace-nowrap">
                                            {conv.last_activity ? formatDateTime(conv.last_activity) : '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
