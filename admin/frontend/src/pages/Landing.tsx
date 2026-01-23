'use client'

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
    ArrowRight,
    Calendar,
    CheckCircle2,
    FileText,
    Lock,
    Mail,
    MessageSquare,
    Shield,
    Sparkles,
    Table2,
    Video,
    Zap,
    BarChart3
} from 'lucide-react'
import { AnimatedSection, StaggerContainer, StaggerItem } from '../components/ui/AnimatedSection'

// Feature tabs data with unique chat examples
const features = [
    {
        id: 'gmail',
        icon: <Mail size={20} />,
        title: 'Gmail',
        headline: 'Your Inbox, Conversational',
        description: 'Search emails, summarize threads, draft replies, and send messages - all through natural chat. No more digging through folders.',
        capabilities: ['Search specific emails instantly', 'Summarize long threads', 'Draft and send replies', 'Get smart notifications'],
        chatExample: {
            user: 'Find emails from John about the Q4 report',
            bot: 'Found 3 emails from John regarding Q4 report. The latest one (Dec 15) contains the final draft attachment. Would you like me to summarize it?'
        }
    },
    {
        id: 'calendar',
        icon: <Calendar size={20} />,
        title: 'Calendar',
        headline: 'Schedule Without Switching Apps',
        description: 'Check your agenda, schedule meetings, set reminders, and get daily briefings. Your calendar becomes a conversation.',
        capabilities: ['View today\'s schedule', 'Create new events', 'Schedule Google Meet calls', 'Get smart reminders'],
        chatExample: {
            user: 'What meetings do I have tomorrow?',
            bot: 'Tomorrow you have 3 meetings: Team standup at 9am, Client call with ABC Corp at 2pm, and Sprint review at 4pm.'
        }
    },
    {
        id: 'drive',
        icon: <FileText size={20} />,
        title: 'Drive',
        headline: 'Find Files Instantly',
        description: 'Search across your entire Drive with natural language. Find that document from last month without remembering the exact name.',
        capabilities: ['Natural language search', 'Quick file previews', 'Share files securely', 'Access recent documents'],
        chatExample: {
            user: 'Find the marketing proposal from last week',
            bot: 'Found "Marketing Proposal 2026.pdf" modified 5 days ago. It\'s in your Marketing folder. Would you like me to share it with someone?'
        }
    },
    {
        id: 'sheets',
        icon: <Table2 size={20} />,
        title: 'Sheets',
        headline: 'Data Entry Made Simple',
        description: 'Log expenses, track tasks, append rows to spreadsheets using simple commands. Perfect for on-the-go data management.',
        capabilities: ['Append data to sheets', 'Read spreadsheet data', 'Quick expense logging', 'Automate data entry'],
        chatExample: {
            user: 'Add expense: Lunch meeting RM85',
            bot: 'Added to your Expenses sheet: "Lunch meeting" - RM85.00 on Jan 9, 2026. Your monthly total is now RM2,340.'
        }
    },
    {
        id: 'charts',
        icon: <BarChart3 size={20} />,
        title: 'Charts',
        headline: 'Generate Reports Instantly',
        description: 'Create visual charts and graphs from your spreadsheet data with a simple request. Perfect for quick insights and presentations.',
        capabilities: ['Generate bar, line & pie charts', 'Pull data from any Sheet', 'Export as images', 'Sales & analytics reports'],
        chatExample: {
            user: 'Show me a sales report chart from Q4 data',
            bot: 'Generated a bar chart from your Q4 Sales spreadsheet showing monthly revenue. Total: RM245,000. Would you like me to add a trend line?'
        }
    },
    {
        id: 'meet',
        icon: <Video size={20} />,
        title: 'Meet',
        headline: 'Video Calls in Seconds',
        description: 'Create instant Google Meet links or schedule meetings with participants. Perfect for quick team huddles or client calls.',
        capabilities: ['Create instant Meet links', 'Schedule meetings with invites', 'Add participants automatically', 'Sync with Calendar'],
        chatExample: {
            user: 'Create a meeting with Sarah for tomorrow at 3pm',
            bot: 'Created: "Meeting with Sarah" tomorrow at 3pm. Google Meet link generated and calendar invite sent to sarah@company.com.'
        }
    }
]

const steps = [
    {
        number: '01',
        title: 'Connect Your Account',
        description: 'Securely link your Google Workspace with OAuth 2.0. Your password is never stored.'
    },
    {
        number: '02',
        title: 'Chat Naturally',
        description: 'Just message the bot like you would a colleague. Ask questions, give commands, get things done.'
    },
    {
        number: '03',
        title: 'Stay Productive',
        description: 'Access emails, calendar, files, and more without leaving Telegram. Work smarter, not harder.'
    }
]

export default function Landing() {
    const [activeFeature, setActiveFeature] = useState('gmail')
    const currentFeature = features.find(f => f.id === activeFeature) || features[0]

    return (
        <div className="overflow-hidden">
            {/* Hero Section - starts at top, padding for fixed header */}
            <section className="relative min-h-screen pt-20 2xl:pt-32 flex items-center justify-center px-6 py-8 overflow-hidden">
                {/* Animated gradient wave background */}
                <div className="animated-gradient-bg absolute inset-0 z-0">
                    {/* Animated waves at bottom */}
                    <div className="wave"></div>
                    <div className="wave"></div>
                    <div className="wave"></div>
                </div>

                <div className="max-w-4xl 2xl:max-w-6xl mx-auto text-center relative py-12 z-10 transition-all duration-300">
                    {/* Badge - Gemini gradient */}
                    <AnimatedSection delay={0.1}>
                        <div className="inline-flex items-center gap-2 px-3 py-1.5 2xl:px-5 2xl:py-2.5 rounded-full bg-white/20 backdrop-blur-sm border border-white/30 shadow-sm mb-5 transition-all duration-300">
                            <Sparkles size={14} className="gemini-star 2xl:w-5 2xl:h-5" />
                            <span className="text-xs font-medium text-white 2xl:text-base">Powered by <span className="gemini-gradient font-semibold">Google Gemini</span></span>
                        </div>
                    </AnimatedSection>

                    {/* Headline - good size, less margin */}
                    <AnimatedSection delay={0.2}>
                        <h1 className="text-4xl md:text-5xl lg:text-6xl 2xl:text-8xl font-bold text-white tracking-tight leading-[1.1] 2xl:leading-tight mb-4 drop-shadow-lg transition-all duration-300">
                            Your Google Workspace.
                            <br />
                            <span className="bg-gradient-to-r from-cyan-300 via-blue-300 to-purple-300 bg-clip-text text-transparent">
                                One Chat Away.
                            </span>
                        </h1>
                    </AnimatedSection>

                    {/* Subheadline - slightly smaller */}
                    <AnimatedSection delay={0.3}>
                        <p className="text-base md:text-lg 2xl:text-2xl text-white/90 max-w-xl 2xl:max-w-3xl mx-auto mb-12 leading-relaxed drop-shadow transition-all duration-300">
                            Manage emails, calendar, files and more through natural Telegram conversations.
                            Enterprise-grade security. Zero learning curve.
                        </p>
                    </AnimatedSection>

                    {/* CTAs - Sparkle button + underlined link */}
                    <AnimatedSection delay={0.4}>
                        <div className="flex flex-col items-center justify-center gap-6 2xl:gap-8 2xl:scale-125 2xl:mt-4 origin-top transition-all duration-300">
                            <a href="https://t.me/eas_academy_testing_n8n_bot" target="_blank" rel="noopener noreferrer" className="transform scale-125 pb-4">
                                <button className="sparkle-button">
                                    <div className="sparkle-inner !text-lg !px-8">
                                        <div className="sparkle-svgs">
                                            <svg viewBox="0 0 256 256" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg" className="svg-l">
                                                <path d="M240 128a15.79 15.79 0 0 1-10.5 15l-63.44 23.07L143 229.5a16 16 0 0 1-30 0l-23.06-63.44L26.5 143a16 16 0 0 1 0-30l63.44-23.06L113 26.5a16 16 0 0 1 30 0l23.07 63.44L229.5 113a15.79 15.79 0 0 1 10.5 15" fill="currentColor"></path>
                                            </svg>
                                            <svg viewBox="0 0 256 256" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg" className="svg-s">
                                                <path d="M240 128a15.79 15.79 0 0 1-10.5 15l-63.44 23.07L143 229.5a16 16 0 0 1-30 0l-23.06-63.44L26.5 143a16 16 0 0 1 0-30l63.44-23.06L113 26.5a16 16 0 0 1 30 0l23.07 63.44L229.5 113a15.79 15.79 0 0 1 10.5 15" fill="currentColor"></path>
                                            </svg>
                                        </div>
                                        Start Free
                                    </div>
                                </button>
                            </a>
                            <a
                                href="#features"
                                onClick={(e) => {
                                    e.preventDefault();
                                    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                                }}
                                className="text-white/80 hover:text-white underline underline-offset-4 text-sm font-medium transition-colors cursor-pointer pb-8"
                            >
                                See How It Works
                            </a>
                        </div>
                    </AnimatedSection>

                    {/* Trust indicators */}
                    <AnimatedSection delay={0.5} viewportMargin="-20px">
                        <div className="flex flex-wrap justify-center gap-x-5 gap-y-2 mt-6 2xl:mt-10 text-xs 2xl:text-base text-white/80 transition-all duration-300">
                            <span className="flex items-center gap-1.5"><CheckCircle2 size={12} className="text-white" /> OAuth 2.0 Secured</span>
                            <span className="flex items-center gap-1.5"><CheckCircle2 size={12} className="text-white" /> No Password Stored</span>
                            <span className="flex items-center gap-1.5"><CheckCircle2 size={12} className="text-white" /> GDPR Compliant</span>
                        </div>
                    </AnimatedSection>
                </div>
            </section>

            {/* Features Section with Interactive Tabs */}
            <section id="features" className="py-14 px-6 2xl:py-24 bg-white dark:bg-slate-800 transition-all duration-300">
                <div className="max-w-6xl 2xl:max-w-7xl mx-auto">
                    <AnimatedSection className="text-center mb-10 2xl:mb-16">
                        <h2 className="text-2xl md:text-3xl 2xl:text-5xl font-bold text-slate-900 dark:text-white mb-2 2xl:mb-4">
                            Everything You Need, One Place
                        </h2>
                        <p className="text-base 2xl:text-2xl text-slate-700 dark:text-slate-300 max-w-2xl 2xl:max-w-4xl mx-auto">
                            Seamlessly connect with your entire Google Workspace through intuitive chat commands.
                        </p>
                    </AnimatedSection>

                    {/* Feature Tabs */}
                    <div className="bg-slate-50 dark:bg-slate-900 rounded-2xl p-2 border border-slate-200 dark:border-slate-700">
                        {/* Tab Headers */}
                        <div className="flex flex-wrap justify-center gap-1 mb-3">
                            {features.map((feature) => (
                                <button
                                    key={feature.id}
                                    onClick={() => setActiveFeature(feature.id)}
                                    className={`relative flex items-center gap-1.5 px-3 py-2 2xl:px-5 2xl:py-3 rounded-lg text-xs 2xl:text-base font-medium transition-all duration-300 ${activeFeature === feature.id
                                        ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-md'
                                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white/50 dark:hover:bg-slate-800/50'
                                        }`}
                                >
                                    {feature.icon}
                                    {feature.title}
                                </button>
                            ))}
                        </div>

                        {/* Tab Content */}
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={currentFeature.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.3 }}
                                className="bg-white dark:bg-slate-800 rounded-xl p-5 md:p-8 shadow-sm"
                            >
                                <div className="grid md:grid-cols-2 gap-8 items-center">
                                    <div>
                                        <div className="inline-flex items-center gap-2 px-2 py-1 2xl:px-3 2xl:py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs 2xl:text-sm font-medium mb-2">
                                            {currentFeature.icon}
                                            {currentFeature.title} Integration
                                        </div>
                                        <h3 className="text-xl 2xl:text-3xl font-bold text-slate-900 dark:text-white mb-2 2xl:mb-4">
                                            {currentFeature.headline}
                                        </h3>
                                        <p className="text-sm 2xl:text-xl text-slate-700 dark:text-slate-300 mb-4 2xl:mb-8 leading-relaxed 2xl:leading-relaxed">
                                            {currentFeature.description}
                                        </p>
                                        <ul className="space-y-1.5 2xl:space-y-3">
                                            {currentFeature.capabilities.map((cap, i) => (
                                                <motion.li
                                                    key={i}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: i * 0.1 }}
                                                    className="flex items-center gap-2 text-sm 2xl:text-lg text-slate-700 dark:text-slate-300"
                                                >
                                                    <CheckCircle2 size={14} className="text-green-600 shrink-0" />
                                                    {cap}
                                                </motion.li>
                                            ))}
                                        </ul>
                                    </div>

                                    {/* Feature Visual - DYNAMIC CHAT */}
                                    <div className="relative">
                                        <div className="bg-gradient-to-br from-slate-100 to-slate-50 dark:from-slate-700 dark:to-slate-800 rounded-xl p-5 border border-slate-200 dark:border-slate-600">
                                            <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-4 border border-slate-100 dark:border-slate-700">
                                                <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-100 dark:border-slate-700">
                                                    <div className="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
                                                        <MessageSquare size={12} className="text-blue-600 dark:text-blue-400" />
                                                    </div>
                                                    <div>
                                                        <p className="font-semibold text-slate-900 dark:text-white text-xs">EAS Assistant</p>
                                                        <p className="text-[10px] text-slate-500 dark:text-slate-400">Powered by Gemini</p>
                                                    </div>
                                                </div>
                                                <div className="space-y-2">
                                                    <div className="bg-blue-600 text-white rounded-lg rounded-br-sm px-3 py-2 text-xs ml-auto max-w-[85%]">
                                                        {currentFeature.chatExample.user}
                                                    </div>
                                                    <div className="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-lg rounded-bl-sm px-3 py-2 text-xs max-w-[90%]">
                                                        {currentFeature.chatExample.bot}
                                                        {/* Show chart image for Charts tab */}
                                                        {currentFeature.id === 'charts' && (
                                                            <img
                                                                src="/sales-chart.png"
                                                                alt="Q4 Sales Chart"
                                                                className="mt-2 rounded-lg w-full max-w-[200px]"
                                                            />
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        </AnimatePresence>
                    </div>
                </div>
            </section>

            {/* How It Works - More compact */}
            <section className="py-14 px-6 2xl:py-24 bg-slate-50 dark:bg-slate-900 transition-all duration-300">
                <div className="max-w-6xl 2xl:max-w-7xl mx-auto">
                    <AnimatedSection className="text-center mb-10 2xl:mb-16">
                        <h2 className="text-2xl md:text-3xl 2xl:text-5xl font-bold text-slate-900 dark:text-white mb-2 2xl:mb-4">
                            Get Started in Minutes
                        </h2>
                        <p className="text-base 2xl:text-2xl text-slate-700 dark:text-slate-300">
                            Three simple steps to transform your productivity.
                        </p>
                    </AnimatedSection>

                    <StaggerContainer className="grid md:grid-cols-3 gap-5">
                        {steps.map((step, i) => (
                            <StaggerItem key={i}>
                                <div className="bg-white dark:bg-slate-800 rounded-xl p-5 2xl:p-8 border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow h-full">
                                    <div className="text-3xl 2xl:text-5xl font-bold text-blue-600 dark:text-blue-400 mb-2 2xl:mb-4">{step.number}</div>
                                    <h3 className="text-base 2xl:text-2xl font-bold text-slate-900 dark:text-white mb-1 2xl:mb-2">{step.title}</h3>
                                    <p className="text-sm 2xl:text-lg text-slate-700 dark:text-slate-300 leading-relaxed">{step.description}</p>
                                </div>
                            </StaggerItem>
                        ))}
                    </StaggerContainer>
                </div>
            </section>

            {/* Security & Compliance - More compact */}
            <section id="security" className="py-14 px-6 2xl:py-24 bg-white dark:bg-slate-800 transition-all duration-300">
                <div className="max-w-5xl 2xl:max-w-7xl mx-auto">
                    <AnimatedSection className="text-center mb-10 2xl:mb-16">
                        <div className="inline-flex p-2.5 2xl:p-4 bg-green-50 dark:bg-green-900/30 rounded-xl mb-3">
                            <Shield size={28} className="text-green-600 dark:text-green-400 2xl:w-10 2xl:h-10" />
                        </div>
                        <h2 className="text-2xl md:text-3xl 2xl:text-5xl font-bold text-slate-900 dark:text-white mb-2 2xl:mb-4">
                            Enterprise-Grade Security
                        </h2>
                        <p className="text-base 2xl:text-2xl text-slate-700 dark:text-slate-300 max-w-2xl 2xl:max-w-4xl mx-auto">
                            Built with security-first architecture. Your data stays yours.
                        </p>
                    </AnimatedSection>

                    <StaggerContainer className="grid md:grid-cols-2 gap-4">
                        <StaggerItem>
                            <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-5 2xl:p-8 border border-slate-100 dark:border-slate-700 h-full">
                                <Lock className="text-blue-600 dark:text-blue-400 mb-2 2xl:mb-4 2xl:w-8 2xl:h-8" size={22} />
                                <h3 className="text-base 2xl:text-xl font-bold text-slate-900 dark:text-white mb-1 2xl:mb-2">OAuth 2.0 Authentication</h3>
                                <p className="text-sm 2xl:text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                                    Industry-standard authentication. We never see or store your Google password.
                                </p>
                            </div>
                        </StaggerItem>
                        <StaggerItem>
                            <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-5 2xl:p-8 border border-slate-100 dark:border-slate-700 h-full">
                                <Shield className="text-blue-600 dark:text-blue-400 mb-2 2xl:mb-4 2xl:w-8 2xl:h-8" size={22} />
                                <h3 className="text-base 2xl:text-xl font-bold text-slate-900 dark:text-white mb-1 2xl:mb-2">AES-256 Encryption</h3>
                                <p className="text-sm 2xl:text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                                    All stored tokens are encrypted at rest using military-grade AES-256 encryption.
                                </p>
                            </div>
                        </StaggerItem>
                        <StaggerItem>
                            <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-5 2xl:p-8 border border-slate-100 dark:border-slate-700 h-full">
                                <Zap className="text-blue-600 dark:text-blue-400 mb-2 2xl:mb-4 2xl:w-8 2xl:h-8" size={22} />
                                <h3 className="text-base 2xl:text-xl font-bold text-slate-900 dark:text-white mb-1 2xl:mb-2">Minimal Scope Access</h3>
                                <p className="text-sm 2xl:text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                                    We only request permissions absolutely necessary for each feature you use.
                                </p>
                            </div>
                        </StaggerItem>
                        <StaggerItem>
                            <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-5 2xl:p-8 border border-slate-100 dark:border-slate-700 h-full">
                                <CheckCircle2 className="text-blue-600 dark:text-blue-400 mb-2 2xl:mb-4 2xl:w-8 2xl:h-8" size={22} />
                                <h3 className="text-base 2xl:text-xl font-bold text-slate-900 dark:text-white mb-1 2xl:mb-2">Easy Revocation</h3>
                                <p className="text-sm 2xl:text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                                    Disconnect anytime with a single command. All tokens are immediately deleted.
                                </p>
                            </div>
                        </StaggerItem>
                    </StaggerContainer>

                    {/* Google Compliance Notice */}
                    <AnimatedSection className="mt-6">
                        <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-800 rounded-xl p-5 text-center">
                            <p className="text-blue-800 dark:text-blue-300 text-xs leading-relaxed max-w-3xl mx-auto">
                                <strong>Google API Services Compliance:</strong> GT-Bot's use and transfer of information received from
                                Google APIs adheres to the{' '}
                                <a
                                    href="https://developers.google.com/terms/api-services-user-data-policy"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="underline hover:text-blue-900 dark:hover:text-blue-200"
                                >
                                    Google API Services User Data Policy
                                </a>
                                , including the Limited Use requirements.
                            </p>
                        </div>
                    </AnimatedSection>
                </div>
            </section>

            {/* Final CTA - More compact */}
            <section className="py-14 px-6 2xl:py-24 relative overflow-hidden transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900" />
                <div className="absolute inset-0 opacity-30">
                    <div className="absolute top-1/2 left-1/4 w-64 h-64 bg-blue-500 rounded-full blur-3xl" />
                    <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-cyan-500 rounded-full blur-3xl" />
                </div>

                <div className="max-w-4xl 2xl:max-w-6xl mx-auto text-center relative py-12 z-10">
                    <AnimatedSection>
                        <h2 className="text-2xl md:text-3xl 2xl:text-5xl font-bold text-white mb-3 2xl:mb-6">
                            Ready to Work Smarter?
                        </h2>
                        <p className="text-base 2xl:text-2xl text-slate-300 mb-6 2xl:mb-10 max-w-2xl 2xl:max-w-4xl mx-auto">
                            Join professionals who've transformed their productivity with AI-powered
                            Google Workspace integration.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-3 2xl:gap-5 justify-center">
                            <a href="https://t.me/eas_academy_testing_n8n_bot" target="_blank" rel="noopener noreferrer">
                                <button className="inline-flex items-center justify-center gap-2 px-6 py-3 2xl:px-8 2xl:py-4 bg-white text-slate-900 rounded-lg font-semibold text-sm 2xl:text-lg hover:bg-slate-100 transition-colors shadow-lg">
                                    Get Started Free <ArrowRight size={16} className="2xl:w-5 2xl:h-5" />
                                </button>
                            </a>
                            <Link to="/privacy">
                                <button className="inline-flex items-center justify-center px-6 py-3 2xl:px-8 2xl:py-4 text-white border border-white/20 rounded-lg font-semibold text-sm 2xl:text-lg hover:bg-white/10 transition-colors">
                                    Privacy Policy
                                </button>
                            </Link>
                        </div>
                    </AnimatedSection>
                </div>
            </section>
        </div>
    )
}
