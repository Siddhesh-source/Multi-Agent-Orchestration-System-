import { useState, useEffect } from 'react'

function format(date) {
    const diff = Math.floor((Date.now() - new Date(date).getTime()) / 1000)
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

export function useRelativeTime(date) {
    const [label, setLabel] = useState(() => format(date))
    useEffect(() => {
        const id = setInterval(() => setLabel(format(date)), 30_000)
        return () => clearInterval(id)
    }, [date])
    return label
}
