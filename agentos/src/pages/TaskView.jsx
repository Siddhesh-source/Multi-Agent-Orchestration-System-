import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Copy, Check } from 'lucide-react'
import AgentCard from '../components/agents/AgentCard'
import { tasksApi } from '../lib/api'
import { useElapsedTime } from '../hooks/useElapsedTime'
import ErrorRow from '../components/shared/ErrorRow'

// ─── Mock ─────────────────────────────────────────────────────────────
function buildMock(id) {
    return {
        task_id: id,
        status: 'running',
        human_review_required: false,
        description: 'Compare pricing plans for AWS, GCP, and Azure.',
        startedAt: new Date(Date.now() - 47_000).toISOString(),
        final_output: null,
        agents: [
            { agent_name: 'Planner',    status: 'done',    input_text: 'Task description', output_text: '1. Research instances\n2. Fetch pricing\n3. Compare' },
            { agent_name: 'Research',   status: 'running', input_text: 'Fetch AWS/GCP/Azure pricing', output_text: null },
            { agent_name: 'Executor',   status: 'pending', input_text: null, output_text: null },
            { agent_name: 'Critic',     status: 'pending', input_text: null, output_text: null },
            { agent_name: 'Memory',     status: 'pending', input_text: null, output_text: null },
        ],
    }
}

// ─── Status config ────────────────────────────────────────────────────
const STATUS_CFG = {
    running: { color: '#00D9FF', label: 'Running' },
    done: { color: '#22C55E', label: 'Done' },
    failed: { color: '#EF4444', label: 'Failed' },
    pending: { color: '#6B7280', label: 'Pending' },
}

function StatusBadge({ status }) {
    const cfg = STATUS_CFG[status] ?? STATUS_CFG.pending
    return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontFamily: "'DM Mono', monospace", fontSize: '10px', letterSpacing: '0.05em', color: cfg.color, textTransform: 'uppercase' }}>
            <span style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: cfg.color, flexShrink: 0 }} />
            {cfg.label}
        </span>
    )
}

function ElapsedChip({ startedAt }) {
    const elapsed = useElapsedTime(startedAt)
    if (!elapsed) return null
    return <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.05em' }}>{elapsed}</span>
}

function CopyButton({ text }) {
    const [copied, setCopied] = useState(false)
    const handleCopy = () => {
        navigator.clipboard.writeText(text || '')
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }
    return (
        <button
            id="copy-output-btn"
            onClick={handleCopy}
            title="Copy output"
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', color: copied ? '#22C55E' : '#3A3A4A', transition: 'color 200ms ease', display: 'flex', alignItems: 'center' }}
            onMouseEnter={(e) => { if (!copied) e.currentTarget.style.color = '#6B7280' }}
            onMouseLeave={(e) => { if (!copied) e.currentTarget.style.color = '#3A3A4A' }}
        >
            {copied ? <Check size={14} /> : <Copy size={14} />}
        </button>
    )
}

function HumanReviewBanner({ taskId }) {
    const [rejected, setRejected] = useState(false)
    const [rejectNote, setRejectNote] = useState('')
    const queryClient = useQueryClient()
    const navigate = useNavigate()

    const approveMutation = useMutation({
        mutationFn: () => tasksApi.approve(taskId, 'approve', ''),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['task-status', taskId] }),
    })
    const rejectMutation = useMutation({
        mutationFn: (note) => tasksApi.reject(taskId, note),
        onSuccess: () => navigate('/'),
    })

    return (
        <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', borderLeft: '2px solid #00D9FF', backgroundColor: 'rgba(0,217,255,0.04)', padding: '12px 14px', margin: '2px 0' }}
        >
            <div style={{ flex: 1 }}>
                <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#E8E8F0', marginBottom: rejected ? '8px' : 0, lineHeight: 1.5 }}>
                    Critic flagged this output. Review before proceeding.
                </p>
                {rejected && (
                    <textarea value={rejectNote} onChange={(e) => setRejectNote(e.target.value)}
                        placeholder="Provide redirect instructions..." rows={2}
                        style={{ width: '100%', resize: 'none', backgroundColor: '#111118', border: '1px solid #1E1E2E', outline: 'none', padding: '8px', fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#E8E8F0', caretColor: '#00D9FF' }} />
                )}
            </div>
            <div style={{ display: 'flex', gap: '10px', flexShrink: 0, paddingTop: '1px' }}>
                {!rejected ? (
                    <>
                        <button id="approve-btn" onClick={() => approveMutation.mutate()}
                            style={{ backgroundColor: '#00D9FF', color: '#0A0A0F', border: 'none', borderRadius: '6px', padding: '6px 14px', cursor: 'pointer', fontFamily: "'DM Mono', monospace", fontSize: '10px', letterSpacing: '0.08em', textTransform: 'uppercase', transition: 'opacity 150ms ease' }}
                            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.85'}
                            onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}>
                            Approve
                        </button>
                        <button id="reject-btn" onClick={() => setRejected(true)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', fontFamily: "'DM Mono', monospace", fontSize: '10px', letterSpacing: '0.08em', textTransform: 'uppercase', color: '#EF4444', transition: 'opacity 150ms ease' }}
                            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
                            onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}>
                            Reject
                        </button>
                    </>
                ) : (
                    <button onClick={() => rejectMutation.mutate(rejectNote)} disabled={!rejectNote.trim()}
                        style={{ background: 'none', border: '1px solid #EF4444', borderRadius: '6px', padding: '6px 14px', cursor: 'pointer', fontFamily: "'DM Mono', monospace", fontSize: '10px', letterSpacing: '0.08em', textTransform: 'uppercase', color: '#EF4444', opacity: rejectNote.trim() ? 1 : 0.4, transition: 'opacity 150ms ease' }}>
                        Send
                    </button>
                )}
            </div>
        </motion.div>
    )
}

// ─── TaskView ─────────────────────────────────────────────────────────
export default function TaskView() {
    const { id } = useParams()

    const { data: task, isError, refetch } = useQuery({
        queryKey: ['task-status', id],
        queryFn: () => tasksApi.getById(id),
        refetchInterval: 2000,
        retry: false,
        placeholderData: buildMock(id),
    })

    const data = task ?? buildMock(id)
    const isDone = data.status === 'done' || data.status === 'failed'
    // Backend uses agent_name; mock uses name — normalise
    const agents = (data.agents ?? []).map((a) => ({
        ...a,
        name: a.agent_name ?? a.name,
        input: a.input_text ?? a.input,
        output: a.output_text ?? a.output,
    }))
    const criticIdx = agents.findIndex((a) => a.name === 'Critic') ?? 3
    const finalOutput = data.final_output ?? data.output

    return (
        <div style={{ display: 'flex', gap: '24px', minHeight: 0 }}>

            {/* ── LEFT: Agent Trace ──────────────────────────────────────── */}
            <div style={{ flex: '0 0 60%', minWidth: 0 }}>
                <span style={{ display: 'block', fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '12px' }}>
                    Agent Trace
                </span>

                {isError ? (
                    <ErrorRow onRetry={refetch} message="Failed to load task status." />
                ) : (
                    <div style={{ border: '1px solid #1E1E2E', backgroundColor: '#111118' }}>
                        {agents.map((agent, i) => {
                            const isLast = i === agents.length - 1
                            const showReview = data.human_review_required && i === criticIdx
                            return (
                                <div key={agent.name}>
                                    <AgentCard agent={agent} isLast={isLast && !showReview} />
                                    {showReview && <HumanReviewBanner taskId={id} />}
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>

            {/* ── RIGHT: Info + Output ───────────────────────────────────── */}
            <div style={{ flex: '0 0 40%', minWidth: 0, display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ border: '1px solid #1E1E2E', backgroundColor: '#111118' }}>
                    <div style={{ padding: '8px 14px', borderBottom: '1px solid #1E1E2E', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Task</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <ElapsedChip startedAt={data.startedAt} />
                            <StatusBadge status={data.status} />
                        </div>
                    </div>
                    <p style={{ padding: '12px 14px', fontFamily: "'DM Mono', monospace", fontSize: '13px', color: '#E8E8F0', lineHeight: 1.6, margin: 0 }}>
                        {data.description}
                    </p>
                </div>

                <AnimatePresence>
                    {isDone && finalOutput && (
                        <motion.div key="output" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}
                            style={{ border: '1px solid #1E1E2E', backgroundColor: '#111118', flex: 1, minHeight: 0 }}>
                            <div style={{ padding: '8px 14px', borderBottom: '1px solid #1E1E2E', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Output</span>
                                <CopyButton text={finalOutput} />
                            </div>
                            <div style={{ padding: '12px 14px', overflowY: 'auto', maxHeight: '60vh' }}>
                                <pre style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#E8E8F0', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.7 }}>
                                    {finalOutput}
                                </pre>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}
