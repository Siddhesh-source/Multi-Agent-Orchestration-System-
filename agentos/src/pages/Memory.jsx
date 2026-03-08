import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ExternalLink, Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { memoryApi, tasksApi } from '../lib/api'
import { useDebounce } from '../hooks/useDebounce'
import { useRelativeTime } from '../hooks/useRelativeTime'
import { SkeletonRow } from '../components/shared/Skeleton'
import ErrorRow from '../components/shared/ErrorRow'

// ─── Mock memory entries ──────────────────────────────────────────────
const MOCK_MEMORY = [
    {
        id: 'mem_001',
        task_id: 'task_001',
        task_description: 'Research the latest advances in transformer architecture efficiency',
        chunk: 'Key finding: Flash Attention v2 reduces memory complexity from O(n²) to O(n). Multi-query attention (MQA) and grouped-query attention (GQA) are now standard in production LLMs for reducing KV cache size by 8–32×.',
        score: 0.94,
        timestamp: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
    },
    {
        id: 'mem_002',
        task_id: 'task_002',
        task_description: 'Research transformer architecture efficiency',
        chunk: 'Speculative decoding reduces inference latency by 2–3× using a small draft model to propose token sequences that a larger model verifies in parallel.',
        score: 0.81,
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    },
    {
        id: 'mem_003',
        task_id: 'task_003',
        task_description: 'Write a Python script to batch-resize images in a folder',
        chunk: "Pillow's Image.save() accepts a quality parameter for JPEG/WebP output. Use os.walk() for recursive directory traversal.",
        score: 0.76,
        timestamp: new Date(Date.now() - 1000 * 60 * 13).toISOString(),
    },
    {
        id: 'mem_004',
        task_id: 'task_004',
        task_description: 'Compare pricing plans for AWS, GCP, and Azure',
        chunk: 'AWS c5.9xlarge on-demand: $1.53/hr. GCP n2-standard-32: $1.37/hr. Azure Standard_D32s_v5: $1.54/hr.',
        score: 0.89,
        timestamp: new Date(Date.now() - 1000 * 60 * 122).toISOString(),
    },
    {
        id: 'mem_005',
        task_id: 'task_005',
        task_description: 'Draft a product requirements document for a real-time markdown editor',
        chunk: 'CRDTs are preferred over OT for P2P sync. Yjs and Automerge are the leading CRDT libraries for text.',
        score: 0.65,
        timestamp: new Date(Date.now() - 1000 * 60 * 300).toISOString(),
    },
]

// ─── Task Detail Modal ────────────────────────────────────────────────
function TaskDetailModal({ taskId, onClose }) {
    const navigate = useNavigate()
    
    console.log('TaskDetailModal opened with taskId:', taskId)
    
    const { data: task, isLoading, isError } = useQuery({
        queryKey: ['task-detail', taskId],
        queryFn: () => tasksApi.getById(taskId),
        enabled: !!taskId,
        retry: false,
    })

    console.log('Task data:', task, 'Loading:', isLoading, 'Error:', isError)

    const statusConfig = {
        running: { icon: Loader2, color: '#00D9FF', label: 'Running' },
        done: { icon: CheckCircle2, color: '#22C55E', label: 'Completed' },
        failed: { icon: XCircle, color: '#EF4444', label: 'Failed' },
        pending: { icon: Clock, color: '#6B7280', label: 'Pending' },
    }

    const status = task?.status || 'pending'
    const StatusIcon = statusConfig[status]?.icon || Clock
    const statusColor = statusConfig[status]?.color || '#6B7280'
    const statusLabel = statusConfig[status]?.label || 'Unknown'

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
                position: 'fixed',
                inset: 0,
                backgroundColor: 'rgba(0,0,0,0.85)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                padding: '20px',
            }}
        >
            <motion.div
                initial={{ scale: 0.95, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.95, y: 20 }}
                onClick={(e) => e.stopPropagation()}
                style={{
                    backgroundColor: '#111118',
                    border: '1px solid #1E1E2E',
                    maxWidth: '900px',
                    width: '100%',
                    maxHeight: '85vh',
                    display: 'flex',
                    flexDirection: 'column',
                    boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
                }}
            >
                {/* Header */}
                <div style={{ padding: '16px 20px', borderBottom: '1px solid #1E1E2E', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <StatusIcon size={16} color={statusColor} style={{ flexShrink: 0 }} />
                        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: statusColor, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                            {statusLabel}
                        </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <button
                            onClick={() => navigate(`/task/${taskId}`)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', color: '#6B7280', display: 'flex', alignItems: 'center', gap: '6px', transition: 'color 150ms' }}
                            onMouseEnter={(e) => e.currentTarget.style.color = '#00D9FF'}
                            onMouseLeave={(e) => e.currentTarget.style.color = '#6B7280'}
                        >
                            <ExternalLink size={14} />
                            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', letterSpacing: '0.05em' }}>Open Full View</span>
                        </button>
                        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', color: '#6B7280', transition: 'color 150ms' }}
                            onMouseEnter={(e) => e.currentTarget.style.color = '#E8E8F0'}
                            onMouseLeave={(e) => e.currentTarget.style.color = '#6B7280'}>
                            <X size={18} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
                    {isLoading ? (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px 0' }}>
                            <Loader2 size={24} color="#00D9FF" style={{ animation: 'spin 1s linear infinite' }} />
                        </div>
                    ) : isError ? (
                        <div style={{ textAlign: 'center', padding: '40px 0' }}>
                            <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#EF4444', marginBottom: '12px' }}>
                                Task not found or failed to load
                            </p>
                            <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#6B7280' }}>
                                This task may have been deleted or the ID is invalid.
                            </p>
                        </div>
                    ) : task ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            {/* Task Description */}
                            <div>
                                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
                                    Task Description
                                </span>
                                <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '13px', color: '#E8E8F0', lineHeight: 1.7, margin: 0 }}>
                                    {task.description || 'No description available'}
                                </p>
                            </div>

                            {/* Agent Execution */}
                            {task.agents && task.agents.length > 0 && (
                                <div>
                                    <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase', display: 'block', marginBottom: '12px' }}>
                                        Agent Execution
                                    </span>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                        {task.agents.map((agent) => {
                                            const agentStatus = agent.status || 'pending'
                                            const AgentIcon = statusConfig[agentStatus]?.icon || Clock
                                            const agentColor = statusConfig[agentStatus]?.color || '#6B7280'
                                            
                                            return (
                                                <div key={agent.agent_name} style={{ border: '1px solid #1E1E2E', backgroundColor: '#0A0A0F', padding: '12px' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: agent.output_text ? '8px' : 0 }}>
                                                        <AgentIcon size={12} color={agentColor} />
                                                        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#E8E8F0', fontWeight: 500 }}>
                                                            {agent.agent_name}
                                                        </span>
                                                        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '9px', color: agentColor, marginLeft: 'auto' }}>
                                                            {agentStatus}
                                                        </span>
                                                    </div>
                                                    {agent.output_text && (
                                                        <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#9CA3AF', lineHeight: 1.6, margin: 0, paddingLeft: '20px' }}>
                                                            {agent.output_text}
                                                        </p>
                                                    )}
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            )}

                            {/* Final Output */}
                            {task.final_output && (
                                <div>
                                    <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
                                        Final Output
                                    </span>
                                    <div style={{ border: '1px solid #1E1E2E', backgroundColor: '#0A0A0F', padding: '14px' }}>
                                        <pre style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#E8E8F0', lineHeight: 1.7, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                                            {task.final_output}
                                        </pre>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#6B7280', textAlign: 'center', padding: '40px 0' }}>
                            Task not found
                        </p>
                    )}
                </div>
            </motion.div>
        </motion.div>
    )
}

// ─── Memory row ───────────────────────────────────────────────────────
function MemoryRow({ entry, index, onTaskClick }) {
    const ago = useRelativeTime(entry.timestamp)
    const [hovered, setHovered] = useState(false)
    const taskDesc = entry.task_description ?? ''
    const truncatedTask = taskDesc.length > 55 ? taskDesc.slice(0, 55) + '…' : taskDesc

    const handleClick = () => {
        console.log('Memory row clicked:', entry.task_id)
        if (entry.task_id) {
            onTaskClick(entry.task_id)
        } else {
            console.warn('No task_id found for entry:', entry)
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04, duration: 0.18 }}
            id={`memory-row-${entry.id}`}
            role="button"
            tabIndex={0}
            onClick={handleClick}
            onKeyDown={(e) => e.key === 'Enter' && handleClick()}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            style={{
                borderBottom: '1px solid #1E1E2E',
                padding: '12px 0',
                cursor: 'pointer',
                backgroundColor: hovered ? 'rgba(0,217,255,0.03)' : 'transparent',
                transition: 'background-color 120ms ease',
            }}
        >
            {/* Top row: task source + timestamp */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: hovered ? '#00D9FF' : '#E8E8F0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, minWidth: 0, marginRight: '12px', transition: 'color 120ms' }}>
                    {truncatedTask}
                </span>
                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', flexShrink: 0 }}>
                    {ago}
                </span>
            </div>

            {/* Body: memory chunk, 3-line clamp */}
            <p style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: '11px',
                color: '#9CA3AF',
                lineHeight: 1.6,
                margin: '0 0 8px 0',
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
            }}>
                {entry.chunk}
            </p>

            {/* Relevance score bar */}
            <div style={{ height: '2px', backgroundColor: '#1E1E2E', width: '100%' }}>
                <div style={{ height: '2px', width: `${Math.round(entry.score * 100)}%`, backgroundColor: '#00D9FF', transition: 'width 400ms ease' }} />
            </div>
        </motion.div>
    )
}

// ─── Memory page ──────────────────────────────────────────────────────
export default function Memory() {
    const [search, setSearch] = useState('')
    const [selectedTaskId, setSelectedTaskId] = useState(null)
    const debouncedQ = useDebounce(search, 300)

    console.log('Memory component - selectedTaskId:', selectedTaskId)

    const { data, isLoading, isError, refetch } = useQuery({
        queryKey: ['memory', debouncedQ],
        queryFn: () => debouncedQ ? memoryApi.search(debouncedQ) : memoryApi.getAll(),
        retry: 1,
        staleTime: 5000,
    })

    const entries = data ?? []
    const filtered = debouncedQ
        ? entries.filter((e) =>
            e.content?.toLowerCase().includes(debouncedQ.toLowerCase()) ||
            e.chunk?.toLowerCase().includes(debouncedQ.toLowerCase()) ||
            e.taskDescription?.toLowerCase().includes(debouncedQ.toLowerCase()) ||
            e.task_description?.toLowerCase().includes(debouncedQ.toLowerCase())
        )
        : entries

    const handleTaskClick = (taskId) => {
        console.log('handleTaskClick called with:', taskId)
        setSelectedTaskId(taskId)
    }

    console.log('Rendering Memory with', filtered.length, 'entries')

    return (
        <>
            <div style={{ maxWidth: '800px' }}>

                {/* ── Header ───────────────────────────────────────────────── */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                        Memory
                    </span>
                    <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280' }}>
                        {filtered.length} {filtered.length === 1 ? 'entry' : 'entries'}
                    </span>
                </div>

                {/* ── Search bar ───────────────────────────────────────────── */}
                <div style={{ border: '1px solid #1E1E2E', backgroundColor: '#111118', marginBottom: '24px' }}>
                    <input
                        id="memory-search"
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search memory..."
                        style={{
                            width: '100%',
                            backgroundColor: 'transparent',
                            border: 'none',
                            outline: 'none',
                            padding: '10px 14px',
                            fontFamily: "'DM Mono', monospace",
                            fontSize: '12px',
                            color: '#E8E8F0',
                            caretColor: '#00D9FF',
                        }}
                    />
                </div>

                {/* ── Results ──────────────────────────────────────────────── */}
                {isLoading ? (
                    [0, 1, 2, 3].map((i) => <SkeletonRow key={i} />)
                ) : filtered.length > 0 ? (
                    filtered.map((entry, i) => (
                        <MemoryRow 
                            key={entry.id} 
                            entry={entry} 
                            index={i} 
                            onTaskClick={handleTaskClick}
                        />
                    ))
                ) : isError ? (
                    <ErrorRow onRetry={refetch} />
                ) : (
                    <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#6B7280', textAlign: 'center', padding: '40px 0' }}>
                        Nothing found.
                    </p>
                )}
            </div>

            {/* ── Task Detail Modal ────────────────────────────────────── */}
            <AnimatePresence>
                {selectedTaskId && (
                    <TaskDetailModal 
                        taskId={selectedTaskId} 
                        onClose={() => setSelectedTaskId(null)} 
                    />
                )}
            </AnimatePresence>
        </>
    )
}
