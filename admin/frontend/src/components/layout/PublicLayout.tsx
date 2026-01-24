import { useState, useEffect } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { Moon, Sun, Menu, X } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export default function PublicLayout() {
    const { theme, toggleTheme } = useTheme();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);
    const location = useLocation();
    const isLanding = location.pathname === '/';
    const showDarkText = isScrolled || !isLanding;

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <div className="min-h-screen flex flex-col font-sans transition-colors">
            {/* Header - Fixed styling with dynamic background */}
            <header className="fixed w-full top-0 z-50 transition-all duration-300 bg-white/30 dark:bg-slate-900/30 backdrop-blur-[40px] saturate-150 border-b border-white/20 dark:border-white/10 shadow-sm">
                <div className="max-w-6xl 2xl:max-w-7xl mx-auto px-5 sm:px-6 h-[72px] 2xl:h-24 flex justify-between items-center transition-all duration-300">
                    <Link to="/" className="flex items-center gap-2 2xl:gap-3 group shrink-0">
                        <img
                            src="/logo.png"
                            alt="GT-Bot"
                            className="h-9 w-auto 2xl:h-12 rounded-lg transition-all duration-300"
                        />
                        <span className={`font-bold tracking-tight text-base sm:text-base 2xl:text-xl transition-colors ${showDarkText ? 'text-slate-900 dark:text-white' : 'text-white drop-shadow-md'}`}>GT-Bot</span>
                    </Link>

                    {/* Desktop Nav */}
                    <nav className="hidden md:flex items-center gap-6 2xl:gap-10">
                        <Link to="/privacy" className={`text-sm 2xl:text-lg font-medium transition-colors ${showDarkText ? 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white' : 'text-white/80 hover:text-white'}`}>Privacy</Link>
                        <Link to="/terms" className={`text-sm 2xl:text-lg font-medium transition-colors ${showDarkText ? 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white' : 'text-white/80 hover:text-white'}`}>Terms</Link>
                        <button
                            onClick={toggleTheme}
                            className={`p-2 rounded-lg transition-colors 2xl:scale-125 ${showDarkText ? 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white' : 'text-white/70 hover:text-white'}`}
                            aria-label="Toggle theme"
                        >
                            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
                        </button>
                    </nav>

                    {/* Mobile Nav Controls */}
                    <div className="flex items-center gap-2 md:hidden">
                        <button
                            onClick={toggleTheme}
                            className={`p-2.5 rounded-lg transition-colors ${showDarkText ? 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white' : 'text-white/80 hover:text-white'}`}
                            aria-label="Toggle theme"
                        >
                            {theme === 'light' ? <Moon size={22} /> : <Sun size={22} />}
                        </button>
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className={`p-2.5 rounded-lg transition-colors ${showDarkText ? 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700' : 'text-white/80 hover:text-white'}`}
                            aria-label="Toggle menu"
                        >
                            {mobileMenuOpen ? <X size={28} /> : <Menu size={28} />}
                        </button>
                    </div>
                </div>

                {/* Mobile Menu */}
                {mobileMenuOpen && (
                    <div className="md:hidden border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3">
                        <nav className="flex flex-col gap-1">
                            <Link
                                to="/privacy"
                                onClick={() => setMobileMenuOpen(false)}
                                className="px-3 py-2 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 text-sm font-medium transition-colors"
                            >
                                Privacy
                            </Link>
                            <Link
                                to="/terms"
                                onClick={() => setMobileMenuOpen(false)}
                                className="px-3 py-2 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 text-sm font-medium transition-colors"
                            >
                                Terms
                            </Link>
                        </nav>
                    </div>
                )}
            </header>

            {/* Main Content */}
            <main className="flex-grow">
                <Outlet />
            </main>

            {/* Footer */}
            <footer className="bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 py-10 2xl:py-16 transition-all duration-300">
                <div className="max-w-6xl 2xl:max-w-7xl mx-auto px-5 sm:px-6">
                    <div className="flex flex-col md:flex-row justify-between items-start gap-8">
                        {/* Company Info */}
                        <div className="max-w-xs 2xl:max-w-md">
                            <div className="flex items-center gap-2 mb-3 2xl:mb-5">
                                <img src="/logo.png" alt="GT-Bot" className="h-7 w-auto 2xl:h-10 rounded-lg" />
                                <span className="font-bold text-slate-900 dark:text-white text-sm 2xl:text-lg">GT-Bot</span>
                            </div>
                            <p className="text-slate-600 dark:text-slate-400 text-xs 2xl:text-base leading-relaxed">
                                Connect your Google Workspace with Telegram securely. AI-powered productivity for professional teams.
                            </p>
                        </div>

                        {/* Links - Side by side on mobile */}
                        <div className="flex gap-16 sm:gap-12 2xl:gap-20">
                            <div>
                                <h4 className="font-semibold text-slate-900 dark:text-white mb-3 2xl:mb-6 text-xs 2xl:text-base uppercase tracking-wider">Product</h4>
                                <ul className="space-y-2 2xl:space-y-4 text-sm 2xl:text-lg text-slate-600 dark:text-slate-400">
                                    <li><Link to="/" className="hover:text-slate-900 dark:hover:text-white">Features</Link></li>
                                </ul>
                            </div>
                            <div>
                                <h4 className="font-semibold text-slate-900 dark:text-white mb-3 2xl:mb-6 text-xs 2xl:text-base uppercase tracking-wider">Legal</h4>
                                <ul className="space-y-2 2xl:space-y-4 text-sm 2xl:text-lg text-slate-600 dark:text-slate-400">
                                    <li><Link to="/privacy" className="hover:text-slate-900 dark:hover:text-white">Privacy Policy</Link></li>
                                    <li><Link to="/terms" className="hover:text-slate-900 dark:hover:text-white">Terms of Service</Link></li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 pt-6 2xl:mt-12 2xl:pt-8 border-t border-slate-100 dark:border-slate-700 flex flex-col md:flex-row justify-between items-center gap-4 text-xs 2xl:text-base text-slate-500 dark:text-slate-500">
                        <p>© 2026 GT-Bot. All rights reserved.</p>
                        <p className="max-w-md 2xl:max-w-lg text-center md:text-right">
                            Google and the Google logo are registered trademarks of Google LLC.
                            This application is not endorsed by or affiliated with Google LLC.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
}
