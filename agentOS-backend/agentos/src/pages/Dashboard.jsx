import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { tasksApi } from '../lib/api'
import useTaskStore from '../store/useTaskStore'
import { useRelativeTime } from '../hooks/useRelativeTime'
import { SkeletonRow } from '../components/shared/Skeleton'
import ErrorRow from '../components/shared/ErrorRow'

// ─── Mock data ────────────────────────────────────────────────────────
const MOCK_TASKS = [
    {
        id: 'task_001',
        description: 'Research the latest advances in transformer architecture efficiency and summarize key findings',
        status: 'done',
        created_at: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
    },
    {
        id: 'task_002',
        description: 'Write a Python script to batch-resize images in a folder and output as WebP',
        status: 'running',
        created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    },
    {
        id: 'task_003',
        description: 'Compare pricing plans for AWS, GCP, and Azure for a 10-node compute cluster',
        status: 'failed',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    },
    {
        id: 'task_004',
        description: 'Draft a product requirements document for a real-time collaborative markdown editor',
        status: 'pending',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
    },
]

// ─── Status config ────────────────────────────────────────────────────
const STATUS = {
    running: { color: '#00D9FF', label: 'Running' },
    done: { color: '#22C55E', label: 'Done' },
    failed: { color: '#EF4444', label: 'Failed' },
    pending: { color: '#6B7280', label: 'Pending' },
}

// ─── Toggle ───────────────────────────────────────────────────────────
function Toggle({ checked, onChange }) {
    return (
        <button
            id="human-review-toggle"
            role="switch"
            aria-checked={checked}
            onClick={() => onChange(!checked)}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
        >
            <div style={{
                width: '28px', height: '16px', borderRadius: '99px',
                backgroundColor: checked ? '#00D9FF' : '#1E1E2E',
                border: '1px solid', borderColor: checked ? '#00D9FF' : '#3A3A4A',
                position: 'relative', transition: 'background-color 200ms ease, border-color 200ms ease', flexShrink: 0,
            }}>
                <motion.div
                    animate={{ x: checked ? 13 : 1 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                    style={{ position: 'absolute', top: '2px', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: checked ? '#0A0A0F' : '#6B7280' }}
                />
            </div>
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.05em', userSelect: 'none' }}>
                Human Review
            </span>
        </button>
    )
}

// ─── Status badge ─────────────────────────────────────────────────────
function StatusBadge({ status }) {
    const cfg = STATUS[status] ?? STATUS.pending
    return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontFamily: "'DM Mono', monospace", fontSize: '10px', letterSpacing: '0.05em', color: cfg.color, textTransform: 'uppercase', flexShrink: 0 }}>
            <span style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: cfg.color, flexShrink: 0 }} />
            {cfg.label}
        </span>
    )
}

// ─── Task row ─────────────────────────────────────────────────────────
function TaskRow({ task, index }) {
    const navigate = useNavigate()
    const ago = useRelativeTime(task.created_at)
    const [hovered, setHovered] = useState(false)
    const truncated = (task.description ?? '').length > 60 ? task.description.slice(0, 60) + '…' : task.description

    return (
        <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04, duration: 0.2 }}
            id={`task-row-${task.id}`}
            role="button"
            tabIndex={0}
            onClick={() => navigate(`/task/${task.id}`)}
            onKeyDown={(e) => e.key === 'Enter' && navigate(`/task/${task.id}`)}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            style={{
                display: 'flex', alignItems: 'center', gap: '16px',
                padding: '10px 0', borderBottom: '1px solid #1E1E2E',
                cursor: 'pointer', backgroundColor: hovered ? 'rgba(255,255,255,0.02)' : 'transparent',
                transition: 'background-color 120ms ease',
            }}
        >
            <span style={{ flex: 1, fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#E8E8F0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', minWidth: 0 }}>
                {truncated}
            </span>
            <StatusBadge status={task.status} />
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', flexShrink: 0, letterSpacing: '0.03em' }}>{ago}</span>
        </motion.div>
    )
}

// ─── Dashboard ────────────────────────────────────────────────────────
export default function Dashboard() {
    const navigate = useNavigate()
    const [input, setInput] = useState('')
    const [humanReview, setHumanReview] = useState(false)
    const [submitError, setSubmitError] = useState(null)
    const { isSubmitting, setSubmitting, setActiveTaskId } = useTaskStore()

    const { data: tasks, isLoading, isError, refetch } = useQuery({
        queryKey: ['tasks'],
        queryFn: tasksApi.getAll,
        retry: 1,
        refetchInterval: 3000, // Refresh every 3 seconds
        staleTime: 2000,
    })
    const displayTasks = tasks ?? []

    const handleSubmit = useCallback(async () => {
        const prompt = input.trim()
        if (!prompt || isSubmitting) return
        setSubmitError(null)
        setSubmitting(true)
        try {
            const res = await tasksApi.create({ description: prompt, human_review: humanReview })
            const taskId = res?.id ?? res?.task_id
            setActiveTaskId(taskId)
            navigate(`/task/${taskId}`)
        } catch (err) {
            setSubmitError(err.message || 'Failed to submit task.')
        } finally {
            setSubmitting(false)
        }
    }, [input, humanReview, isSubmitting, navigate, setSubmitting, setActiveTaskId])

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit()
    }

    return (
        <div style={{ maxWidth: '800px' }}>

            {/* ── Section 1: Task Input ─────────────────────────────────── */}
            <div style={{ border: '1px solid #1E1E2E', backgroundColor: '#111118', marginBottom: '32px' }}>
                <textarea
                    id="task-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Describe your task..."
                    rows={4}
                    style={{
                        width: '100%', resize: 'none', backgroundColor: 'transparent',
                        border: 'none', outline: 'none', padding: '14px 16px',
                        fontFamily: "'DM Mono', monospace", fontSize: '13px',
                        color: '#E8E8F0', lineHeight: 1.6, caretColor: '#00D9FF',
                    }}
                />

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', borderTop: '1px solid #1E1E2E' }}>
                    <Toggle checked={humanReview} onChange={setHumanReview} />
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#3A3A4A' }}>⌘ + Enter to run</span>
                        <button
                            id="run-task-btn"
                            onClick={handleSubmit}
                            disabled={isSubmitting || !input.trim()}
                            style={{
                                backgroundColor: isSubmitting || !input.trim() ? '#1E1E2E' : '#00D9FF',
                                color: isSubmitting || !input.trim() ? '#3A3A4A' : '#0A0A0F',
                                border: 'none', borderRadius: '6px', padding: '8px 20px',
                                fontFamily: "'DM Mono', monospace", fontSize: '11px', fontWeight: 500,
                                letterSpacing: '0.08em', textTransform: 'uppercase',
                                cursor: isSubmitting || !input.trim() ? 'not-allowed' : 'pointer',
                                transition: 'opacity 150ms ease, background-color 150ms ease',
                            }}
                            onMouseEnter={(e) => { if (!isSubmitting && input.trim()) e.currentTarget.style.opacity = '0.85' }}
                            onMouseLeave={(e) => { e.currentTarget.style.opacity = '1' }}
                        >
                            {isSubmitting ? 'Running…' : 'Run Task'}
                        </button>
                    </div>
                </div>
            </div>

            <AnimatePresence>
                {submitError && (
                    <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                        style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#EF4444', marginBottom: '12px', marginTop: '-24px' }}>
                        {submitError}
                    </motion.p>
                )}
            </AnimatePresence>

            {/* ── Section 2: Recent Tasks ───────────────────────────────── */}
            <div>
                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
                    Recent
                </span>

                {isLoading ? (
                    [0, 1, 2].map((i) => <SkeletonRow key={i} />)
                ) : displayTasks.length > 0 ? (
                    displayTasks.map((task, i) => <TaskRow key={task.id} task={task} index={i} />)
                ) : isError ? (
                    <ErrorRow onRetry={refetch} />
                ) : (
                    <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#6B7280', textAlign: 'center', padding: '32px 0' }}>
                        No tasks yet.
                    </p>
                )}
            </div>
        </div>
    )
}
