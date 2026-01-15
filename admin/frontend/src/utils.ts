/**
 * Utility functions for the admin panel
 */

// Malaysian timezone (UTC+8)
const TIMEZONE = 'Asia/Kuala_Lumpur'

/**
 * Format a date string to Malaysian time
 */
export function formatDateTime(dateString: string | null | undefined): string {
    if (!dateString) return '—'
    return new Date(dateString).toLocaleString('en-MY', { timeZone: TIMEZONE })
}

/**
 * Format a date string to Malaysian date only
 */
export function formatDate(dateString: string | null | undefined): string {
    if (!dateString) return '—'
    return new Date(dateString).toLocaleDateString('en-MY', { timeZone: TIMEZONE })
}

/**
 * Format a date string to Malaysian time only
 */
export function formatTime(dateString: string | null | undefined): string {
    if (!dateString) return '—'
    return new Date(dateString).toLocaleTimeString('en-MY', {
        timeZone: TIMEZONE,
        hour: '2-digit',
        minute: '2-digit'
    })
}
