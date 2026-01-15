'use client'

import { AnimatedSection, StaggerContainer, StaggerItem } from '../components/ui/AnimatedSection'
import { Shield, Lock, Database, Trash2, Server, Mail, ExternalLink } from 'lucide-react'

export default function Privacy() {
    return (
        <div className="pt-28 pb-16 2xl:pt-40 2xl:pb-24 px-6 transition-all duration-300">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <AnimatedSection className="text-center mb-16">
                    <div className="inline-flex p-4 bg-blue-50 dark:bg-blue-900/30 rounded-2xl mb-6">
                        <Shield size={40} className="text-blue-600 dark:text-blue-400" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-slate-900 dark:text-white mb-4">Privacy Policy</h1>
                    <p className="text-slate-600 dark:text-slate-400">Last Updated: January 5, 2026</p>
                </AnimatedSection>

                {/* Quick Summary Cards */}
                <StaggerContainer className="grid md:grid-cols-3 gap-4 mb-16">
                    <StaggerItem>
                        <div className="bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 rounded-xl p-6 text-center">
                            <Lock className="mx-auto text-green-600 dark:text-green-400 mb-3" size={24} />
                            <p className="font-semibold text-slate-900 dark:text-white text-sm">OAuth 2.0 Only</p>
                            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Your password is never stored</p>
                        </div>
                    </StaggerItem>
                    <StaggerItem>
                        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-xl p-6 text-center">
                            <Database className="mx-auto text-blue-600 dark:text-blue-400 mb-3" size={24} />
                            <p className="font-semibold text-slate-900 dark:text-white text-sm">Encrypted Storage</p>
                            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">AES-256 encryption at rest</p>
                        </div>
                    </StaggerItem>
                    <StaggerItem>
                        <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-100 dark:border-purple-800 rounded-xl p-6 text-center">
                            <Trash2 className="mx-auto text-purple-600 dark:text-purple-400 mb-3" size={24} />
                            <p className="font-semibold text-slate-900 dark:text-white text-sm">Easy Deletion</p>
                            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Revoke access anytime</p>
                        </div>
                    </StaggerItem>
                </StaggerContainer>

                {/* Main Content */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                    <div className="p-8 md:p-12 prose prose-slate dark:prose-invert max-w-none prose-headings:font-bold prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline">

                        <AnimatedSection>
                            <p className="text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                                EAS Academy ("we", "us", or "our") operates the <strong>EAS Academy Assistant</strong> (the "App").
                                This page informs you of our policies regarding the collection, use, and disclosure of personal data
                                when you use our App.
                            </p>
                        </AnimatedSection>

                        <AnimatedSection delay={0.1}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <span className="bg-slate-100 dark:bg-slate-700 w-8 h-8 rounded-lg flex items-center justify-center text-sm">1</span>
                                Information We Collect
                            </h2>

                            <h3 className="text-lg text-slate-800 dark:text-slate-200 mt-6 mb-3">Telegram Data</h3>
                            <ul className="space-y-2 text-slate-700 dark:text-slate-300">
                                <li><strong>Telegram User Information:</strong> Your Telegram User ID, Username, First Name, and Last Name.</li>
                                <li><strong>Chat Data:</strong> Messages you send to the bot are processed to generate AI responses.</li>
                            </ul>

                            <h3 className="text-lg text-slate-800 dark:text-slate-200 mt-6 mb-3">Google Workspace Data (If Connected)</h3>
                            <p className="text-slate-700 dark:text-slate-300">When you connect your Google account, we access data based on the permissions you grant:</p>
                            <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-6 mt-4 not-prose">
                                <ul className="space-y-3 text-sm">
                                    <li className="flex items-start gap-3">
                                        <Mail className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" size={18} />
                                        <div><strong className="text-slate-900 dark:text-white">Gmail:</strong> <span className="text-slate-700 dark:text-slate-300">Read, compose, and send emails on your behalf.</span></div>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <Server className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" size={18} />
                                        <div><strong className="text-slate-900 dark:text-white">Drive & Sheets:</strong> <span className="text-slate-700 dark:text-slate-300">List, search, read files and write data to spreadsheets.</span></div>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <Database className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" size={18} />
                                        <div><strong className="text-slate-900 dark:text-white">Calendar:</strong> <span className="text-slate-700 dark:text-slate-300">Read and manage calendar events.</span></div>
                                    </li>
                                </ul>
                            </div>
                        </AnimatedSection>

                        <AnimatedSection delay={0.2}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <span className="bg-slate-100 dark:bg-slate-700 w-8 h-8 rounded-lg flex items-center justify-center text-sm">2</span>
                                How We Use Your Data
                            </h2>
                            <ul className="space-y-2 text-slate-700 dark:text-slate-300">
                                <li>To provide and maintain the App's functionality.</li>
                                <li>To allow you to interact with your Google services via chat commands.</li>
                                <li>To provide AI-generated responses using Google Gemini API.</li>
                            </ul>
                        </AnimatedSection>

                        <AnimatedSection delay={0.3}>
                            <h2 id="limited-use" className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <span className="bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 w-8 h-8 rounded-lg flex items-center justify-center text-sm">3</span>
                                Google API Limited Use Policy
                            </h2>
                            <div className="bg-blue-50 dark:bg-blue-900/30 border-l-4 border-blue-500 p-6 my-6 not-prose rounded-r-xl">
                                <p className="text-slate-800 dark:text-slate-200 text-sm leading-relaxed">
                                    <strong>EAS Academy Assistant's use and transfer to any other app of information received from Google APIs
                                        will adhere to the{' '}
                                        <a
                                            href="https://developers.google.com/terms/api-services-user-data-policy#additional_requirements_for_specific_api_scopes"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
                                        >
                                            Google API Services User Data Policy <ExternalLink size={12} />
                                        </a>
                                        , including the Limited Use requirements.</strong>
                                </p>
                            </div>
                            <p className="text-slate-700 dark:text-slate-300">
                                We strictly limit the use of Google User Data to providing or improving user-facing features.
                                We do <strong>not</strong> use your data for:
                            </p>
                            <ul className="space-y-2 mt-4 text-slate-700 dark:text-slate-300">
                                <li>Advertisements or ad targeting</li>
                                <li>Training generalized AI/ML models</li>
                                <li>Selling to third parties</li>
                            </ul>
                        </AnimatedSection>

                        <AnimatedSection delay={0.4}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <span className="bg-slate-100 dark:bg-slate-700 w-8 h-8 rounded-lg flex items-center justify-center text-sm">4</span>
                                Data Retention & Deletion
                            </h2>
                            <p className="text-slate-700 dark:text-slate-300">
                                We retain your Google OAuth tokens only while your account is linked. You can disconnect at any time using the{' '}
                                <code className="bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded text-sm border border-slate-200 dark:border-slate-600 font-mono">/unlink_google</code>{' '}
                                command, which <strong>immediately and permanently</strong> deletes all stored tokens.
                            </p>
                        </AnimatedSection>

                        <AnimatedSection delay={0.5}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <span className="bg-slate-100 dark:bg-slate-700 w-8 h-8 rounded-lg flex items-center justify-center text-sm">5</span>
                                Contact Us
                            </h2>
                            <p className="text-slate-700 dark:text-slate-300">If you have any questions about this Privacy Policy:</p>
                            <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-6 mt-4 not-prose">
                                <p className="text-slate-900 dark:text-white font-medium">Email: <a href="mailto:terryong30@gmail.com" className="text-blue-600 dark:text-blue-400">terryong30@gmail.com</a></p>
                            </div>
                        </AnimatedSection>
                    </div>
                </div>
            </div>
        </div>
    )
}
