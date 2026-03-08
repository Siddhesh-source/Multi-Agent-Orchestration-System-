import { useState, useEffect } from 'react'

/**
 * Returns a live-counting elapsed-time string ("0s", "1m 04s", "1h 02m").
 * Ticks every second.
 */
export function useElapsedTime(startedAt) {
    const getElapsed = () => {
        if (!startedAt) return null
        const secs = Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000)
        if (secs < 60) return `${secs}s`
        if (secs < 3600) return `${Math.floor(secs / 60)}m ${String(secs % 60).padStart(2, '0')}s`
        const h = Math.floor(secs / 3600)
        const m = Math.floor((secs % 3600) / 60)
        return `${h}h ${String(m).padStart(2, '0')}m`
    }

    const [elapsed, setElapsed] = useState(getElapsed)

    useEffect(() => {
        if (!startedAt) return
        const id = setInterval(() => setElapsed(getElapsed()), 1000)
        return () => clearInterval(id)
    }, [startedAt])

    return elapsed
}
