import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, isAuthenticated } from '../api'
import { Button } from '../components/ui/Button'
import { Lock } from 'lucide-react'

export default function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated()) {
            navigate('/users', { replace: true })
        }
    }, [navigate])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        const success = await login(username, password)
        if (success) navigate('/users')
        else setError('Invalid credentials')
        setLoading(false)
    }

    return (
        <div className="flex flex-col items-center justify-center py-20 px-6">
            <div className="w-full max-w-sm bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-8">
                <div className="text-center mb-8">
                    <div className="inline-flex p-3 bg-slate-50 dark:bg-slate-700 rounded-full mb-4">
                        <Lock className="text-slate-400 dark:text-slate-500" size={24} />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Admin Sign In</h1>
                    <p className="text-slate-600 dark:text-slate-400 text-sm mt-2">Enter your credentials to access the dashboard</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-900 dark:text-white shadow-sm placeholder-slate-400
                            focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                            placeholder="admin"
                            required
                            autoFocus
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-900 dark:text-white shadow-sm placeholder-slate-400
                            focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                            required
                        />
                    </div>

                    {error && (
                        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 text-red-600 dark:text-red-400 text-xs font-medium text-center">
                            {error}
                        </div>
                    )}

                    <Button
                        type="submit"
                        className="w-full mt-2"
                        disabled={loading}
                    >
                        {loading ? 'Signing in...' : 'Sign In'}
                    </Button>
                </form>
            </div>
        </div>
    )
}
