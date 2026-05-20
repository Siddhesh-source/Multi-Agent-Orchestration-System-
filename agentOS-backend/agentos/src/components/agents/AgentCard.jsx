import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronRight } from 'lucide-react'

// ─── Status config (shared with Dashboard) ────────────────────────────
const STATUS_CFG = {
    running: { color: '#00D9FF', label: 'Running' },
    done: { color: '#22C55E', label: 'Done' },
    failed: { color: '#EF4444', label: 'Failed' },
    pending: { color: '#6B7280', label: 'Pending' },
}

// ─── Typewriter hook ──────────────────────────────────────────────────
function useTypewriter(text, msPerChar = 8) {
    const [displayed, setDisplayed] = useState('')
    const rafRef = useRef(null)

    useEffect(() => {
        if (!text) { setDisplayed(''); return }
        setDisplayed('')
        let i = 0
        let last = performance.now()

        const tick = (now) => {
            const chars = Math.floor((now - last) / msPerChar)
            if (chars > 0) {
                i = Math.min(i + chars, text.length)
                setDisplayed(text.slice(0, i))
                last = now
            }
            if (i < text.length) rafRef.current = requestAnimationFrame(tick)
        }
        rafRef.current = requestAnimationFrame(tick)
        return () => cancelAnimationFrame(rafRef.current)
    }, [text, msPerChar])

    return displayed
}

// ─── 3-Dot running pulse ──────────────────────────────────────────────
function RunningPulse() {
    return (
        <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            {[0, 1, 2].map((i) => (
                <motion.span
                    key={i}
                    style={{
                        width: '4px',
                        height: '4px',
                        borderRadius: '50%',
                        backgroundColor: '#00D9FF',
                        display: 'inline-block',
                    }}
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{
                        duration: 1,
                        repeat: Infinity,
                        delay: i * 0.22,
                        ease: 'easeInOut',
                    }}
                />
            ))}
        </span>
    )
}

// ─── Status badge (plain, no bg) ──────────────────────────────────────
function AgentStatusBadge({ status }) {
    const cfg = STATUS_CFG[status] ?? STATUS_CFG.pending
    return (
        <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            fontFamily: "'DM Mono', monospace",
            fontSize: '10px',
            letterSpacing: '0.05em',
            color: cfg.color,
            textTransform: 'uppercase',
        }}>
            <span style={{
                width: '4px',
                height: '4px',
                borderRadius: '50%',
                backgroundColor: cfg.color,
                flexShrink: 0,
            }} />
            {cfg.label}
        </span>
    )
}

// ─── Collapsible section (Input / Output) ─────────────────────────────
function CollapsibleSection({ label, content, typewrite = false, defaultOpen = false }) {
    const [open, setOpen] = useState(defaultOpen)
    const text = useTypewriter(typewrite && open ? (content ?? '') : '', 8)
    const displayText = typewrite ? text : (content ?? '')

    return (
        <div style={{ borderTop: '1px solid #1E1E2E' }}>
            <button
                onClick={() => setOpen((v) => !v)}
                style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 12px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    textAlign: 'left',
                }}
            >
                {open
                    ? <ChevronDown size={10} color="#6B7280" />
                    : <ChevronRight size={10} color="#6B7280" />}
                <span style={{
                    fontFamily: "'DM Mono', monospace",
                    fontSize: '9px',
                    letterSpacing: '0.1em',
                    color: '#6B7280',
                    textTransform: 'uppercase',
                }}>
                    {label}
                </span>
            </button>

            <AnimatePresence initial={false}>
                {open && (
                    <motion.div
                        key="content"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.18, ease: 'easeInOut' }}
                        style={{ overflow: 'hidden' }}
                    >
                        <div style={{
                            margin: '0 12px 10px',
                            backgroundColor: '#0A0A0F',
                            padding: '10px',
                            maxHeight: '120px',
                            overflowY: 'auto',
                        }}>
                            <pre style={{
                                fontFamily: "'DM Mono', monospace",
                                fontSize: '12px',
                                color: '#E8E8F0',
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                                margin: 0,
                                lineHeight: 1.6,
                            }}>
                                {displayText || <span style={{ color: '#3A3A4A' }}>—</span>}
                            </pre>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

// ─── AgentCard ────────────────────────────────────────────────────────
export default function AgentCard({ agent, isLast }) {
    const isPending = agent.status === 'pending'
    const isRunning = agent.status === 'running'
    const isDone = agent.status === 'done' || agent.status === 'failed'

    return (
        <motion.div
            layout
            animate={{ opacity: isPending ? 0.35 : 1 }}
            transition={{ duration: 0.3 }}
            style={{
                borderBottom: isLast ? 'none' : '1px solid #1E1E2E',
                paddingTop: '10px',
            }}
        >
            {/* Header */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 12px 10px',
            }}>
                <span style={{
                    fontFamily: "'DM Mono', monospace",
                    fontSize: '11px',
                    letterSpacing: '0.08em',
                    color: '#6B7280',
                    textTransform: 'uppercase',
                }}>
                    {agent.name}
                </span>

                {isRunning
                    ? <RunningPulse />
                    : <AgentStatusBadge status={agent.status} />}
            </div>

            {/* Collapsible sections — only when done/failed */}
            {isDone && (
                <>
                    <CollapsibleSection
                        label="Input"
                        content={agent.input}
                        defaultOpen={false}
                    />
                    <CollapsibleSection
                        label="Output"
                        content={agent.output}
                        typewrite
                        defaultOpen
                    />
                </>
            )}

            {/* Running shimmer placeholder */}
            {isRunning && (
                <div style={{ padding: '0 12px 12px' }}>
                    {[1, 0.7, 0.5].map((w, i) => (
                        <motion.div
                            key={i}
                            animate={{ opacity: [0.15, 0.35, 0.15] }}
                            transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.2 }}
                            style={{
                                height: '8px',
                                borderRadius: '2px',
                                backgroundColor: '#1E1E2E',
                                width: `${w * 100}%`,
                                marginBottom: '6px',
                            }}
                        />
                    ))}
                </div>
            )}
        </motion.div>
    )
}
