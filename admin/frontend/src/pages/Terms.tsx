'use client'

import { Link } from 'react-router-dom'
import { AnimatedSection } from '../components/ui/AnimatedSection'
import { FileText, AlertTriangle, Scale, Trash2, Ban, Edit3 } from 'lucide-react'

export default function Terms() {
    return (
        <div className="pt-28 pb-16 2xl:pt-40 2xl:pb-24 px-6 transition-all duration-300">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <AnimatedSection className="text-center mb-16">
                    <div className="inline-flex p-4 bg-slate-100 dark:bg-slate-800 rounded-2xl mb-6">
                        <FileText size={40} className="text-slate-700 dark:text-slate-300" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-slate-900 dark:text-white mb-4">Terms of Service</h1>
                    <p className="text-slate-600 dark:text-slate-400">Last Updated: January 5, 2026</p>
                </AnimatedSection>

                {/* Main Content */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                    <div className="p-8 md:p-12 prose prose-slate dark:prose-invert max-w-none prose-headings:font-bold prose-a:text-blue-600 dark:prose-a:text-blue-400">

                        <AnimatedSection>
                            <p className="text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                                Please read these Terms of Service ("Terms") carefully before using the EAS Academy Assistant
                                (the "Service") operated by EAS Academy ("us", "we", or "our").
                            </p>
                            <p className="text-slate-700 dark:text-slate-300">
                                By accessing or using the Service, you agree to be bound by these Terms. If you disagree with any
                                part of the terms, you may not access the Service.
                            </p>
                        </AnimatedSection>

                        <AnimatedSection delay={0.1}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <span className="bg-slate-100 dark:bg-slate-700 w-8 h-8 rounded-lg flex items-center justify-center text-sm">1</span>
                                Description of Service
                            </h2>
                            <p className="text-slate-700 dark:text-slate-300">
                                EAS Academy Assistant is an AI-powered assistant integrated with the Telegram messaging platform.
                                It allows users to interact with Google services (Gmail, Drive, Sheets, Calendar) through natural
                                language commands powered by Google Gemini.
                            </p>
                        </AnimatedSection>

                        <AnimatedSection delay={0.2}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <span className="bg-slate-100 dark:bg-slate-700 w-8 h-8 rounded-lg flex items-center justify-center text-sm">2</span>
                                Use of Google Services
                            </h2>
                            <p className="text-slate-700 dark:text-slate-300">
                                To use certain features, you must link your Google account. By doing so, you grant us permission to
                                access your Google data as described in our <Link to="/privacy" className="hover:underline">Privacy Policy</Link>.
                            </p>
                            <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-6 mt-4 not-prose">
                                <p className="font-semibold text-slate-900 dark:text-white mb-3">You acknowledge that:</p>
                                <ul className="space-y-2 text-sm text-slate-700 dark:text-slate-300">
                                    <li className="flex items-start gap-2">
                                        <span className="text-green-600 dark:text-green-400 mt-0.5">✓</span>
                                        You are responsible for activities that occur under your account.
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <span className="text-green-600 dark:text-green-400 mt-0.5">✓</span>
                                        You can revoke access at any time using <code className="bg-white dark:bg-slate-800 px-1.5 py-0.5 rounded border dark:border-slate-600 text-xs">/unlink_google</code>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <span className="text-green-600 dark:text-green-400 mt-0.5">✓</span>
                                        We comply with the Google API Services User Data Policy.
                                    </li>
                                </ul>
                            </div>
                        </AnimatedSection>

                        <AnimatedSection delay={0.3}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <Ban className="text-red-500 dark:text-red-400" size={20} />
                                Prohibited Uses
                            </h2>
                            <p className="text-slate-700 dark:text-slate-300">You agree <strong>not</strong> to use the Service:</p>
                            <ul className="space-y-2 mt-4 text-slate-700 dark:text-slate-300">
                                <li>In any way that violates applicable law.</li>
                                <li>To transmit unsolicited advertising or spam.</li>
                                <li>To impersonate any person or entity.</li>
                                <li>To engage in conduct that restricts others' use of the Service.</li>
                            </ul>
                        </AnimatedSection>

                        <AnimatedSection delay={0.4}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <Scale className="text-slate-600 dark:text-slate-400" size={20} />
                                Limitation of Liability
                            </h2>
                            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800 rounded-xl p-6 not-prose">
                                <div className="flex items-start gap-3">
                                    <AlertTriangle className="text-amber-600 dark:text-amber-400 shrink-0" size={20} />
                                    <p className="text-slate-800 dark:text-slate-200 text-sm leading-relaxed">
                                        In no event shall EAS Academy be liable for any indirect, incidental, special, consequential
                                        or punitive damages, including loss of profits, data, use, goodwill, or other intangible losses,
                                        resulting from your access to or use of the Service.
                                    </p>
                                </div>
                            </div>
                        </AnimatedSection>

                        <AnimatedSection delay={0.5}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <Trash2 className="text-slate-600 dark:text-slate-400" size={20} />
                                Termination
                            </h2>
                            <p className="text-slate-700 dark:text-slate-300">
                                We may terminate or suspend access to our Service immediately, without prior notice, for any reason
                                whatsoever, including without limitation if you breach these Terms.
                            </p>
                        </AnimatedSection>

                        <AnimatedSection delay={0.6}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <Edit3 className="text-slate-600 dark:text-slate-400" size={20} />
                                Changes to Terms
                            </h2>
                            <p className="text-slate-700 dark:text-slate-300">
                                We reserve the right to modify these Terms at any time. Continued use of the Service after changes
                                constitutes acceptance of the new Terms.
                            </p>
                        </AnimatedSection>

                        <AnimatedSection delay={0.7}>
                            <h2 className="text-2xl text-slate-900 dark:text-white mt-12 mb-4 flex items-center gap-3">
                                <span className="bg-slate-100 dark:bg-slate-700 w-8 h-8 rounded-lg flex items-center justify-center text-sm">7</span>
                                Contact
                            </h2>
                            <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-6 not-prose">
                                <p className="text-slate-900 dark:text-white">Questions about these Terms? Email us at <a href="mailto:terryong30@gmail.com" className="text-blue-600 dark:text-blue-400 hover:underline">terryong30@gmail.com</a></p>
                            </div>
                        </AnimatedSection>
                    </div>
                </div>
            </div>
        </div>
    )
}
