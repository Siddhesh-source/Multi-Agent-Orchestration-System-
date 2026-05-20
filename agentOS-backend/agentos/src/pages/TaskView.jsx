import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Copy, Check, Brain, GitBranch, Users, Target, Database, Sparkles, Search, FileText, Code, Bug, TestTube, Edit3, FileOutput, AlertTriangle, Zap, ChevronDown, ChevronRight } from 'lucide-react'
import AgentCard from '../components/agents/AgentCard'
import { tasksApi } from '../lib/api'
import { useElapsedTime } from '../hooks/useElapsedTime'
import ErrorRow from '../components/shared/ErrorRow'

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

// ─── Enhanced Agent Icons & Colors ────────────────────────────────────
const AGENT_CONFIG = {
    // Planning & Routing
    DAGPlanner:      { icon: GitBranch,  color: '#A855F7', category: 'Planning',   desc: 'Creates dependency-aware task DAG' },
    CognitiveRouter: { icon: Brain,      color: '#00D9FF', category: 'Routing',   desc: 'Estimates epistemic gap for research routing' },
    Router:          { icon: Zap,        color: '#F59E0B', category: 'Dispatch',   desc: 'Dispatches to specialist agents' },
    
    // Research & Content
    Research:        { icon: Search,     color: '#8B5CF6', category: 'Research',   desc: 'Web search & knowledge retrieval' },
    Writer:          { icon: FileText,   color: '#22C55E', category: 'Content',    desc: 'Writes articles, papers, reports' },
    Editor:          { icon: Edit3,      color: '#14B8A6', category: 'Content',    desc: 'Grammar, clarity, style editing' },
    Summarizer:      { icon: FileText,   color: '#06B6D4', category: 'Content',    desc: 'TL;DR & key point extraction' },
    
    // Code agents
    Coder:           { icon: Code,       color: '#84CC16', category: 'Code',       desc: 'Full file generation' },
    Debugger:        { icon: Bug,        color: '#EF4444', category: 'Code',       desc: 'Error analysis & fixing' },
    Tester:          { icon: TestTube,   color: '#10B981', category: 'Code',       desc: 'Unit test generation' },
    CodeReview:      { icon: Code,       color: '#F97316', category: 'Code',       desc: 'Security & quality audit' },
    
    // Quality & Memory
    AdversarialCritic:{ icon: Users,     color: '#F59E0B', category: 'Review',     desc: 'Multi-agent debate: Skeptic vs Devil\'s Advocate vs Synthesis' },
    Uncertainty:     { icon: Target,     color: '#EF4444', category: 'Quality',    desc: 'Confidence scoring via ensemble sampling' },
    TrieMemory:      { icon: Database,   color: '#22C55E', category: 'Memory',     desc: '3-tier: Episodic + Semantic + Procedural' },
    Metacognition:   { icon: Sparkles,   color: '#EC4899', category: 'Learning',   desc: 'Self-reflection & prompt adjustment' },
    
    // Legacy agents (for backward compat)
    Planner:         { icon: GitBranch,  color: '#A855F7', category: 'Legacy',     desc: 'Legacy planner' },
    Executor:        { icon: Zap,        color: '#F59E0B', category: 'Legacy',     desc: 'Legacy executor' },
    Critic:          { icon: Users,      color: '#F59E0B', category: 'Legacy',     desc: 'Legacy critic' },
    Memory:          { icon: Database,   color: '#22C55E', category: 'Legacy',     desc: 'Legacy memory' },
}

// ─── Status config ────────────────────────────────────────────────────
const STATUS_CFG = {
    running: { color: '#00D9FF', label: 'Running' },
    done: { color: '#22C55E', label: 'Done' },
    failed: { color: '#EF4444', label: 'Failed' },
    pending: { color: '#6B7280', label: 'Pending' },
    skipped: { color: '#6B7280', label: 'Skipped' },
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

// ─── Confidence Score Display ─────────────────────────────────────────
function ConfidenceBadge({ score }) {
    if (score === null || score === undefined) return null
    
    const pct = Math.round(score * 100)
    let color = '#22C55E' // green - high confidence
    if (pct < 50) color = '#EF4444' // red - low confidence
    else if (pct < 75) color = '#F59E0B' // amber - medium
    
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', padding: '6px 10px', backgroundColor: `${color}15`, borderRadius: '6px', border: `1px solid ${color}30` }}>
            <Target size={12} color={color} />
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color, letterSpacing: '0.05em' }}>
                Confidence: {pct}%
            </span>
        </div>
    )
}

// ─── Metacognition Feedback Display ──────────────────────────────────
function MetacognitionFeedback({ feedback }) {
    if (!feedback) return null
    
    return (
        <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ marginTop: '8px', padding: '8px 10px', backgroundColor: '#EC489915', borderRadius: '6px', border: '1px solid #EC489930' }}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <Sparkles size={12} color="#EC4899" />
                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '9px', color: '#EC4899', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                    Metacognition
                </span>
            </div>
            <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#9CA3AF', margin: 0, lineHeight: 1.5 }}>
                {feedback}
            </p>
        </motion.div>
    )
}

// ─── Adversarial Critic Debate Display ────────────────────────────────
function DebateDisplay({ debate }) {
    if (!debate || !debate.length) return null
    
    return (
        <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                <Users size={12} color="#F59E0B" />
                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '9px', color: '#F59E0B', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                    Society of Critics
                </span>
            </div>
            {debate.map((turn, i) => {
                const roleColors = {
                    Skeptic: '#EF4444',
                    'Devil\'s Advocate': '#8B5CF6',
                    Synthesis: '#22C55E',
                }
                const roleColor = roleColors[turn.role] || '#6B7280'
                
                return (
                    <div key={i} style={{ padding: '6px 8px', backgroundColor: '#0A0A0F', borderRadius: '4px', borderLeft: `2px solid ${roleColor}` }}>
                        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '9px', color: roleColor, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                            {turn.role}
                        </span>
                        <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#9CA3AF', margin: '4px 0 0 0', lineHeight: 1.4 }}>
                            {turn.text?.slice(0, 200)}{turn.text?.length > 200 ? '…' : ''}
                        </p>
                    </div>
                )
            })}
        </div>
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
    })

    // Build mock for loading state only (not for display)
    const buildMock = (taskId) => ({
        task_id: taskId,
        status: 'running',
        human_review_required: false,
        description: 'Loading task...',
        startedAt: new Date().toISOString(),
        final_output: null,
        confidence_score: null,
        metacognition_feedback: null,
        debate: [],
        agents: [],
    })

    const data = task || buildMock(id)
    const isDone = data.status === 'done' || data.status === 'failed'
    const isRunning = data.status === 'running'
    
    // Normalize agents - handle both enhanced and legacy formats
    const agents = (data.agents ?? []).map((a) => ({
        ...a,
        name: a.agent_name ?? a.name ?? 'Unknown',
        input: a.input_text ?? a.input ?? '',
        output: a.output_text ?? a.output ?? '',
        status: a.status ?? 'pending',
        metadata: a.metadata ?? {},
    }))

    // Find special agents for enhanced display
    const criticAgent = agents.find((a) => 
        ['AdversarialCritic', 'Critic'].includes(a.name)
    )
    const uncertaintyAgent = agents.find((a) => a.name === 'Uncertainty')
    const metacogAgent = agents.find((a) => a.name === 'Metacognition')
    
    const finalOutput = data.final_output ?? data.output

    // Render enhanced agent cards with custom rendering for special agents
    const renderAgentCard = (agent, index, isLast) => {
        const config = AGENT_CONFIG[agent.name] || { icon: Zap, color: '#6B7280', category: 'Unknown', desc: '' }
        
        return (
            <div key={agent.name + index}>
                <EnhancedAgentCard 
                    agent={agent} 
                    config={config}
                    isLast={isLast} 
                />
                {/* Show debate for AdversarialCritic */}
                {agent.name === 'AdversarialCritic' && agent.output && (
                    <DebateDisplay debate={agent.metadata?.debate || parseDebate(agent.output)} />
                )}
                {/* Show confidence for Uncertainty agent */}
                {agent.name === 'Uncertainty' && (
                    <ConfidenceBadge score={agent.metadata?.confidence ?? agent.output?.match(/[\d.]+/)?.[0]} />
                )}
            </div>
        )
    }

    return (
        <div style={{ display: 'flex', gap: '24px', minHeight: 0 }}>

            {/* ── LEFT: Agent Trace ──────────────────────────────────────── */}
            <div style={{ flex: '0 0 60%', minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <span style={{ display: 'block', fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                        Agent Trace
                    </span>
                    {agents.length > 0 && (
                        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '9px', color: '#4B5563' }}>
                            {agents.filter(a => a.status === 'done').length}/{agents.length} complete
                        </span>
                    )}
                </div>

                {isError ? (
                    <ErrorRow onRetry={refetch} message="Failed to load task status." />
                ) : (
                    <div style={{ border: '1px solid #1E1E2E', backgroundColor: '#111118' }}>
                        {agents.length > 0 ? (
                            agents.map((agent, i) => {
                                const isLast = i === agents.length - 1
                                return renderAgentCard(agent, i, isLast)
                            })
                        ) : isRunning ? (
                            // Show skeleton for running task with no agents yet
                            <div style={{ padding: '20px' }}>
                                <SkeletonAgentTrace />
                            </div>
                        ) : (
                            <div style={{ padding: '20px', textAlign: 'center' }}>
                                <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#6B7280' }}>
                                    No agents executed yet
                                </p>
                            </div>
                        )}
                        
                        {/* Human review banner if needed */}
                        {data.human_review_required && (
                            <HumanReviewBanner taskId={id} />
                        )}
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

                {/* Confidence Score (from Uncertainty agent) */}
                {isDone && data.confidence_score !== null && data.confidence_score !== undefined && (
                    <ConfidenceBadge score={data.confidence_score} />
                )}

                {/* Metacognition Feedback */}
                {isDone && data.metacognition_feedback && (
                    <MetacognitionFeedback feedback={data.metacognition_feedback} />
                )}

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

// ─── Helper: Parse debate transcript ─────────────────────────────────
function parseDebate(output) {
    if (!output) return []
    try {
        // Try to parse as JSON
        const parsed = JSON.parse(output)
        if (Array.isArray(parsed)) return parsed
    } catch {
        // Try to parse as text with role markers
        const lines = output.split('\n')
        const debate = []
        let currentRole = null
        let currentText = []
        
        for (const line of lines) {
            const roleMatch = line.match(/^(Skeptic|Devil's Advocate|Synthesis):?/i)
            if (roleMatch) {
                if (currentRole && currentText.length) {
                    debate.push({ role: currentRole, text: currentText.join('\n') })
                }
                currentRole = roleMatch[1]
                currentText = [line.replace(/^[^:]+:?\s*/, '')]
            } else if (currentRole) {
                currentText.push(line)
            }
        }
        
        if (currentRole && currentText.length) {
            debate.push({ role: currentRole, text: currentText.join('\n') })
        }
        
        return debate
    }
    return []
}

// ─── Skeleton Agent Trace ─────────────────────────────────────────────
function SkeletonAgentTrace() {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '8px 0' }}>
            {['DAGPlanner', 'CognitiveRouter', 'Research', 'Router'].map((name, i) => (
                <div key={name} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 12px' }}>
                    <motion.div
                        animate={{ opacity: [0.2, 0.5, 0.2] }}
                        transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1 }}
                        style={{
                            width: '8px', height: '8px', borderRadius: '50%',
                            backgroundColor: i === 0 ? '#A855F7' : i === 1 ? '#00D9FF' : '#6B7280'
                        }}
                    />
                    <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#6B7280', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                        {name}
                    </span>
                </div>
            ))}
        </div>
    )
}

// ─── Enhanced Agent Card with Icon & Category ─────────────────────────
function EnhancedAgentCard({ agent, config, isLast }) {
    const isPending = agent.status === 'pending'
    const isRunning = agent.status === 'running'
    const isDone = agent.status === 'done' || agent.status === 'failed'
    const IconComponent = config.icon

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
            {/* Header with icon and category */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 12px 8px',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                        width: '22px', height: '22px', borderRadius: '6px',
                        backgroundColor: `${config.color}18`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                        <IconComponent size={12} color={config.color} />
                    </div>
                    <div>
                        <span style={{
                            fontFamily: "'DM Mono', monospace",
                            fontSize: '11px',
                            letterSpacing: '0.08em',
                            color: '#E8E8F0',
                            textTransform: 'uppercase',
                        }}>
                            {agent.name}
                        </span>
                        <span style={{
                            fontFamily: "'DM Mono', monospace",
                            fontSize: '8px',
                            letterSpacing: '0.05em',
                            color: '#6B7280',
                            marginLeft: '8px',
                            textTransform: 'uppercase',
                        }}>
                            {config.category}
                        </span>
                    </div>
                </div>

                {isRunning ? (
                    <RunningPulse />
                ) : (
                    <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        fontFamily: "'DM Mono', monospace",
                        fontSize: '10px',
                        letterSpacing: '0.05em',
                        color: isDone ? '#22C55E' : '#6B7280',
                        textTransform: 'uppercase',
                    }}>
                        <span style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: isDone ? '#22C55E' : '#6B7280' }} />
                        {isDone ? 'Done' : 'Pending'}
                    </span>
                )}
            </div>

            {/* Description */}
            <div style={{ padding: '0 12px 8px', paddingLeft: '42px' }}>
                <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', margin: 0, lineHeight: 1.4 }}>
                    {config.desc}
                </p>
            </div>

            {/* Collapsible Input/Output */}
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

            {/* Running shimmer */}
            {isRunning && (
                <div style={{ padding: '0 12px 12px', paddingLeft: '42px' }}>
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

// ─── Collapsible Section (reused from AgentCard) ─────────────────────
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

// ─── 3-Dot running pulse (reused) ─────────────────────────────────────
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
