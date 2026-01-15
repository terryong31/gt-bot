import { useState, useEffect } from 'react'
import { getInvites, createInvite, deleteInvite } from '../api'
import { formatDate } from '../utils'
import { Button } from '../components/ui/Button'
import { Check, Copy, Ticket, Plus, Trash2, X } from 'lucide-react'
import { cn } from '../lib/utils'

export default function Invites() {
    const [invites, setInvites] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [showModal, setShowModal] = useState(false)
    const [name, setName] = useState('')
    const [phone, setPhone] = useState('')
    const [copied, setCopied] = useState<string | null>(null)

    useEffect(() => { loadInvites() }, [])

    const loadInvites = async () => {
        setInvites(await getInvites())
        setLoading(false)
    }

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault()
        const invite = await createInvite({ name, phone: phone || undefined })
        setInvites([invite, ...invites])
        setShowModal(false)
        setName('')
        setPhone('')
    }

    const removeInvite = async (invite: any) => {
        if (!confirm(`Delete invite for ${invite.name}?`)) return
        await deleteInvite(invite.id)
        setInvites(invites.filter(i => i.id !== invite.id))
    }

    const copyCode = (code: string) => {
        navigator.clipboard.writeText(code)
        setCopied(code)
        setTimeout(() => setCopied(null), 2000)
    }

    if (loading) return <div className="text-center text-slate-500 dark:text-slate-400 py-12">Loading invites...</div>

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Invite Codes</h2>
                    <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">Create and manage user invitations ({invites.length} total)</p>
                </div>
                <Button onClick={() => setShowModal(true)} className="gap-2">
                    <Plus size={16} /> New Invite Bi
                </Button>
            </div>

            {invites.length === 0 ? (
                <div className="text-center py-20 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="mx-auto bg-slate-100 dark:bg-slate-700 w-16 h-16 rounded-full flex items-center justify-center mb-4">
                        <Ticket className="text-slate-400 dark:text-slate-500" size={32} />
                    </div>
                    <p className="text-lg text-slate-900 dark:text-white font-medium">No invite codes yet</p>
                    <p className="text-slate-600 dark:text-slate-400 text-sm mb-6">Create an invite to allow users to register</p>
                    <Button onClick={() => setShowModal(true)}>
                        Create First Invite
                    </Button>
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {invites.map(invite => (
                        <div key={invite.id} className="group bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm hover:shadow-md transition-all relative overflow-hidden">
                            {invite.is_used && (
                                <div className="absolute top-0 right-0 bg-slate-100 dark:bg-slate-700 px-3 py-1 rounded-bl-xl text-xs font-semibold text-slate-500 dark:text-slate-400">
                                    Used
                                </div>
                            )}

                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="font-bold text-slate-900 dark:text-white">{invite.name}</h3>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{invite.phone || 'No phone'}</p>
                                </div>
                                <div className={cn(
                                    "w-10 h-10 rounded-full flex items-center justify-center shrink-0",
                                    invite.is_used ? "bg-slate-100 dark:bg-slate-700 text-slate-400" : "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
                                )}>
                                    <Ticket size={18} />
                                </div>
                            </div>

                            <div className="flex items-center gap-2 mb-4">
                                <code className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 font-mono text-sm text-slate-700 dark:text-slate-300 font-semibold truncate">
                                    {invite.code}
                                </code>
                                <button
                                    onClick={() => copyCode(invite.code)}
                                    className="p-2 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors border border-transparent hover:border-blue-100 dark:hover:border-blue-800"
                                    title="Copy Code"
                                >
                                    {copied === invite.code ? <Check size={16} /> : <Copy size={16} />}
                                </button>
                            </div>

                            <div className="flex items-center justify-between text-xs text-slate-400 dark:text-slate-500 pt-4 border-t border-slate-50 dark:border-slate-700">
                                <span>Created {formatDate(invite.created_at)}</span>
                                {!invite.is_used && (
                                    <button
                                        onClick={() => removeInvite(invite)}
                                        className="text-red-400 hover:text-red-600 dark:hover:text-red-400 transition-colors flex items-center gap-1"
                                    >
                                        <Trash2 size={12} /> Delete
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={() => setShowModal(false)} />
                    <div className="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md p-6 border border-slate-100 dark:border-slate-700">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Create New Invite</h3>
                            <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={handleCreate} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. John Doe"
                                    value={name}
                                    onChange={e => setName(e.target.value)}
                                    className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-900 dark:text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                    required
                                    autoFocus
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Phone (optional)</label>
                                <input
                                    type="text"
                                    placeholder="e.g. +1234567890"
                                    value={phone}
                                    onChange={e => setPhone(e.target.value)}
                                    className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-900 dark:text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <Button type="button" variant="outline" className="flex-1" onClick={() => setShowModal(false)}>
                                    Cancel
                                </Button>
                                <Button type="submit" className="flex-1">
                                    Create Invite
                                </Button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
