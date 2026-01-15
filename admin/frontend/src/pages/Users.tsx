import { useState, useEffect } from 'react'
import { getUsers, updateUser, deleteUser } from '../api'
import { User as UserIcon, Trash2, ShieldCheck, ShieldAlert } from 'lucide-react'
import { cn } from '../lib/utils'

export default function Users() {
    const [users, setUsers] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => { loadUsers() }, [])

    const loadUsers = async () => {
        setUsers(await getUsers())
        setLoading(false)
    }

    const toggleUser = async (user: any) => {
        await updateUser(user.id, { is_allowed: !user.is_allowed })
        setUsers(users.map(u => u.id === user.id ? { ...u, is_allowed: !u.is_allowed } : u))
    }

    const removeUser = async (user: any) => {
        if (!confirm(`Delete ${user.first_name || user.username}?`)) return
        await deleteUser(user.id)
        setUsers(users.filter(u => u.id !== user.id))
    }

    if (loading) return <div className="text-center text-slate-500 dark:text-slate-400 py-12">Loading users...</div>

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Users</h2>
                    <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">Manage registered bot users ({users.length} total)</p>
                </div>
            </div>

            {users.length === 0 ? (
                <div className="text-center py-20 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="mx-auto bg-slate-100 dark:bg-slate-700 w-16 h-16 rounded-full flex items-center justify-center mb-4">
                        <UserIcon className="text-slate-400 dark:text-slate-500" size={32} />
                    </div>
                    <p className="text-lg text-slate-900 dark:text-white font-medium">No users yet</p>
                    <p className="text-slate-600 dark:text-slate-400 text-sm">Create an invite code to get started</p>
                </div>
            ) : (
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 font-medium">
                                <tr>
                                    <th className="px-6 py-4">User</th>
                                    <th className="px-6 py-4">Telegram ID</th>
                                    <th className="px-6 py-4">Google Connected</th>
                                    <th className="px-6 py-4">Access</th>
                                    <th className="px-6 py-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                                {users.map(user => (
                                    <tr key={user.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center text-slate-600 dark:text-slate-300 font-bold shrink-0">
                                                    {(user.first_name || user.username || '?')[0].toUpperCase()}
                                                </div>
                                                <div>
                                                    <p className="font-medium text-slate-900 dark:text-white">{user.first_name || user.username}</p>
                                                    {user.invite_name && <p className="text-xs text-slate-500 dark:text-slate-400">via {user.invite_name}</p>}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 font-mono text-slate-600 dark:text-slate-400 text-xs">{user.telegram_id}</td>
                                        <td className="px-6 py-4">
                                            <div className={cn(
                                                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
                                                user.is_google_connected
                                                    ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800"
                                                    : "bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-600"
                                            )}>
                                                <div className={cn("w-1.5 h-1.5 rounded-full", user.is_google_connected ? "bg-blue-600 dark:bg-blue-400" : "bg-slate-400")} />
                                                {user.is_google_connected ? 'Connected' : 'Not Linked'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => toggleUser(user)}
                                                className={cn(
                                                    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                                                    user.is_allowed
                                                        ? "bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800 hover:bg-green-100 dark:hover:bg-green-900/50"
                                                        : "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800 hover:bg-red-100 dark:hover:bg-red-900/50"
                                                )}
                                            >
                                                {user.is_allowed ? <ShieldCheck size={14} /> : <ShieldAlert size={14} />}
                                                {user.is_allowed ? 'Allowed' : 'Blocked'}
                                            </button>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => removeUser(user)}
                                                className="text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                                                title="Delete User"
                                            >
                                                <Trash2 size={16} />
                                            </button>
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
