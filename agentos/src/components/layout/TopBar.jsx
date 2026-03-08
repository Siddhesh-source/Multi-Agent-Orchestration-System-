import { motion } from 'framer-motion'
import { useLocation } from 'react-router-dom'
import useTaskStore from '../../store/useTaskStore'

// ─── Derive page title from path ──────────────────────────────────────
function getTitle(pathname) {
    if (pathname === '/') return 'dashboard'
    if (pathname === '/memory') return 'memory'
    if (pathname === '/settings') return 'settings'
    const m = pathname.match(/^\/task\/(.+)$/)
    if (m) return `task / ${m[1]}`
    return pathname.replace(/^\//, '') || 'dashboard'
}

// ─── Live Pulse Dot ───────────────────────────────────────────────────
function LiveDot({ isLive }) {
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ position: 'relative', width: '7px', height: '7px' }}>
                <div
                    style={{
                        position: 'absolute',
                        inset: 0,
                        borderRadius: '50%',
                        backgroundColor: isLive ? '#22C55E' : '#3A3A4A',
                        transition: 'background-color 300ms ease',
                    }}
                />
                {isLive && (
                    <motion.div
                        style={{
                            position: 'absolute',
                            inset: 0,
                            borderRadius: '50%',
                            backgroundColor: '#22C55E',
                        }}
                        animate={{ scale: [1, 2.2], opacity: [0.6, 0] }}
                        transition={{ duration: 1.4, repeat: Infinity, ease: 'easeOut' }}
                    />
                )}
            </div>
            <span
                style={{
                    fontFamily: "'DM Mono', monospace",
                    fontSize: '10px',
                    letterSpacing: '0.1em',
                    color: isLive ? '#22C55E' : '#3A3A4A',
                    transition: 'color 300ms ease',
                }}
            >
                {isLive ? 'LIVE' : 'IDLE'}
            </span>
        </div>
    )
}

// ─── TopBar ───────────────────────────────────────────────────────────
export default function TopBar() {
    const { pathname } = useLocation()
    const isSubmitting = useTaskStore((s) => s.isSubmitting)
    const activeTask = useTaskStore((s) => s.activeTask)
    const isLive = isSubmitting || activeTask?.status === 'running'

    return (
        <header
            style={{
                height: '44px',
                flexShrink: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid #1E1E2E',
                paddingLeft: '24px',
                paddingRight: '24px',
                backgroundColor: '#0A0A0F',
            }}
        >
            <span
                style={{
                    fontFamily: "'DM Mono', monospace",
                    fontSize: '13px',
                    color: '#E8E8F0',
                    letterSpacing: '0.03em',
                }}
            >
                {getTitle(pathname)}
            </span>
            <LiveDot isLive={isLive} />
        </header>
    )
}
