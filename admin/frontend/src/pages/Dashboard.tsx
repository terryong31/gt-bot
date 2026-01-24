import { useState } from 'react'
import { Outlet, NavLink, Navigate } from 'react-router-dom'
import { isAuthenticated, logout } from '../api'
import { cn } from '../lib/utils'
import { FileText, Menu, Ticket, Users, X, LogOut, Moon, Sun } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function Dashboard() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)
    const { theme, toggleTheme } = useTheme()

    if (!isAuthenticated()) return <Navigate to="/login" replace />

    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen)

    const navItems = [
        { to: "/users", icon: <Users size={20} />, label: "Users" },
        { to: "/invites", icon: <Ticket size={20} />, label: "Invites" },
        { to: "/logs", icon: <FileText size={20} />, label: "Logs" },
    ]

    return (
        <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-900 font-sans transition-colors">
            {/* Mobile Header */}
            <div className="fixed top-0 left-0 right-0 z-20 h-16 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-4 md:hidden">
                <div className="flex items-center gap-3">
                    <img src="/logo.png" alt="GT-Bot" className="h-8 w-auto rounded-lg" />
                    <span className="font-bold text-slate-900 dark:text-white">Admin</span>
                </div>
                <button
                    onClick={toggleSidebar}
                    className="p-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
                >
                    {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>

            {/* Sidebar Backdrop (Mobile) */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 z-20 bg-slate-900/50 backdrop-blur-sm md:hidden"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <div className={cn(
                "fixed inset-y-0 left-0 z-30 w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transform transition-transform duration-300 ease-in-out md:static md:translate-x-0 flex flex-col",
                isSidebarOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-100 dark:border-slate-700">
                    <img src="/company-logo.jpg" alt="EAS Academy" className="h-8 w-auto rounded-lg" />
                    <span className="font-bold text-slate-900 dark:text-white tracking-tight">GT-Bot Admin</span>
                </div>

                <div className="p-4">
                    <p className="px-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">
                        Menu
                    </p>
                    <nav className="space-y-1">
                        {navItems.map((item) => (
                            <NavLink
                                key={item.to}
                                to={item.to}
                                onClick={() => setIsSidebarOpen(false)}
                                className={({ isActive }) => cn(
                                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                                    isActive
                                        ? "bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white"
                                        : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 hover:text-slate-900 dark:hover:text-white"
                                )}
                            >
                                {item.icon}
                                {item.label}
                            </NavLink>
                        ))}
                    </nav>
                </div>

                <div className="mt-auto p-4 border-t border-slate-100 dark:border-slate-700 space-y-2">
                    {/* Theme Toggle */}
                    <button
                        onClick={toggleTheme}
                        className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 hover:text-slate-900 dark:hover:text-white transition-colors"
                    >
                        {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
                        {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
                    </button>

                    <button
                        onClick={logout}
                        className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    >
                        <LogOut size={20} />
                        Sign Out
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto pt-16 md:pt-0">
                <main className="max-w-7xl mx-auto px-6 py-8">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
