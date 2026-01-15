import React from 'react';
import { cn } from '../../lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
}

export function Button({
    className,
    variant = 'primary',
    size = 'md',
    ...props
}: ButtonProps) {
    const variants = {
        primary: 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm border border-transparent dark:bg-blue-600 dark:hover:bg-blue-500',
        secondary: 'bg-white text-slate-900 border border-slate-200 hover:bg-slate-50 shadow-sm dark:bg-slate-800 dark:text-white dark:border-slate-600 dark:hover:bg-slate-700',
        outline: 'bg-transparent border border-slate-200 text-slate-900 hover:bg-slate-50 dark:border-slate-600 dark:text-white dark:hover:bg-slate-800',
        ghost: 'bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white',
    };

    const sizes = {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 py-2 text-sm',
        lg: 'h-12 px-8 text-base',
    };

    return (
        <button
            className={cn(
                'inline-flex items-center justify-center rounded-lg font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]',
                variants[variant],
                sizes[size],
                className
            )}
            {...props}
        />
    );
}
