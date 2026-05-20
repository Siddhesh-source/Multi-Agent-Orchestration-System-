import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain, GitBranch, Users, Database, Sparkles,
  Target, FileOutput, Code2, Globe, ChevronDown,
  Zap, Send, Clock, CheckCircle, XCircle, Loader
} from 'lucide-react'
import { tasksApi } from '../lib/api'
import useTaskStore from '../store/useTaskStore'
import { useRelativeTime } from '../hooks/useRelativeTime'
import { SkeletonRow } from '../components/shared/Skeleton'
import ErrorRow from '../components/shared/ErrorRow'

// ─── USP Feature data ────────────────────────────────────────────────
const FEATURES = [
  { icon: Brain,      color: '#00D9FF', label: 'Cognitive Router',   badge: 'USP #1', desc: 'LLM-as-judge estimates epistemic gap, replaces brittle keyword matching' },
  { icon: GitBranch,  color: '#A855F7', label: 'DAG Planner',        badge: 'USP #6', desc: 'Dependency-aware task graph runs independent subtasks in parallel' },
  { icon: Users,      color: '#F59E0B', label: 'Society of Critics',  badge: 'USP #5', desc: 'Skeptic vs Devil\'s Advocate vs Synthesis — multi-agent constitutional review' },
  { icon: Database,   color: '#22C55E', label: '3-Tier Memory',       badge: 'USP #2', desc: 'Episodic + Semantic + Procedural memory with Ebbinghaus forgetting curves' },
  { icon: Sparkles,   color: '#EC4899', label: 'Metacognition',       badge: 'USP #3', desc: 'Agents learn from failures and auto-adjust their own system prompts' },
  { icon: Target,     color: '#EF4444', label: 'Uncertainty Quant',   badge: 'USP #7', desc: 'Ensemble sampling gives confidence scores — quantifies hallucination risk' },
  { icon: FileOutput, color: '#06B6D4', label: 'Real File Output',    badge: 'NEW',    desc: 'PDF, PPTX, DOCX — actual downloadable files, not just text' },
  { icon: Code2,      color: '#84CC16', label: 'Code Execution',      badge: 'NEW',    desc: 'Runs code in sandbox, self-heals errors up to 3 retries automatically' },
  { icon: Globe,      color: '#F97316', label: 'GitHub Deploy',       badge: 'NEW',    desc: 'Creates real GitHub repositories and pushes generated code' },
]

// ─── Quick prompt templates ───────────────────────────────────────────
const TEMPLATES = [
  { label: 'Research Paper', prompt: 'Write a research paper on quantum computing applications in finance with citations and export as PDF' },
  { label: 'Python App',     prompt: 'Build a working Python web scraper for HackerNews top stories and run it to show results' },
  { label: 'Data Analysis',  prompt: 'Analyze the trend of AI adoption in enterprises, create charts and a slide deck' },
  { label: 'GitHub Repo',    prompt: 'Create a FastAPI REST API with authentication, tests, and deploy to a GitHub repository' },
]

// ─── Status config ────────────────────────────────────────────────────
const STATUS = {
  running: { color: '#00D9FF', label: 'Running',  Icon: Loader },
  done:    { color: '#22C55E', label: 'Done',     Icon: CheckCircle },
  failed:  { color: '#EF4444', label: 'Failed',   Icon: XCircle },
  pending: { color: '#6B7280', label: 'Pending',  Icon: Clock },
}

// ─── Feature Showcase ─────────────────────────────────────────────────
function FeatureShowcase() {
  const [open, setOpen] = useState(false)
  const [hovered, setHovered] = useState(null)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      style={{
        background: 'linear-gradient(135deg, rgba(0,217,255,0.04) 0%, rgba(168,85,247,0.04) 100%)',
        borderRadius: '14px',
        border: '1px solid rgba(0,217,255,0.15)',
        overflow: 'hidden',
        marginBottom: '28px',
      }}
    >
      {/* Header row */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', padding: '14px 18px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'none', border: 'none', cursor: 'pointer',
          borderBottom: open ? '1px solid rgba(255,255,255,0.05)' : 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px', height: '28px', borderRadius: '8px',
            background: 'linear-gradient(135deg, #00D9FF, #A855F7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Zap size={15} color="#fff" />
          </div>
          <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: '13px', fontWeight: 600, color: '#E8E8F0' }}>
            AgentOS — 9 Active Capabilities
          </span>
          <span style={{
            fontSize: '9px', fontFamily: "'DM Mono', monospace", letterSpacing: '0.05em',
            padding: '2px 7px', borderRadius: '4px',
            background: 'rgba(0,217,255,0.12)', color: '#00D9FF',
          }}>
            {FEATURES.filter(f => f.badge === 'NEW').length} NEW
          </span>
        </div>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={16} color="#6B7280" />
        </motion.div>
      </button>

      {/* Grid */}
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="grid"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{
              padding: '16px',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
              gap: '10px',
            }}>
              {FEATURES.map((f, i) => (
                <motion.div
                  key={f.label}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  onMouseEnter={() => setHovered(f.label)}
                  onMouseLeave={() => setHovered(null)}
                  style={{
                    padding: '12px',
                    borderRadius: '10px',
                    background: hovered === f.label ? `${f.color}12` : 'rgba(255,255,255,0.025)',
                    border: `1px solid ${hovered === f.label ? f.color + '35' : 'rgba(255,255,255,0.05)'}`,
                    transition: 'all 0.18s ease',
                    display: 'flex', gap: '12px', alignItems: 'flex-start',
                  }}
                >
                  <div style={{
                    width: '34px', height: '34px', borderRadius: '9px',
                    background: `${f.color}18`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}>
                    <f.icon size={17} color={f.color} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#E8E8F0', fontFamily: "'DM Sans', sans-serif" }}>
                        {f.label}
                      </span>
                      <span style={{
                        fontSize: '9px', fontFamily: "'DM Mono', monospace",
                        padding: '1px 5px', borderRadius: '3px',
                        background: `${f.color}20`, color: f.color,
                      }}>
                        {f.badge}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '10px', color: '#6B7280', fontFamily: "'DM Sans', sans-serif", lineHeight: 1.45 }}>
                      {f.desc}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ─── Quick templates ──────────────────────────────────────────────────
function TemplateChips({ onSelect }) {
  return (
    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
      {TEMPLATES.map(t => (
        <button
          key={t.label}
          onClick={() => onSelect(t.prompt)}
          style={{
            padding: '5px 10px', borderRadius: '6px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            color: '#9CA3AF', fontSize: '11px',
            fontFamily: "'DM Mono', monospace",
            cursor: 'pointer', transition: 'all 0.15s ease',
            letterSpacing: '0.02em',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.borderColor = '#00D9FF50'
            e.currentTarget.style.color = '#00D9FF'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
            e.currentTarget.style.color = '#9CA3AF'
          }}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}

// ─── Status badge ─────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const cfg = STATUS[status] ?? STATUS.pending
  const isRunning = status === 'running'
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontFamily: "'DM Mono', monospace", fontSize: '10px', color: cfg.color, textTransform: 'uppercase', letterSpacing: '0.05em', flexShrink: 0 }}>
      {isRunning
        ? <motion.span animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 1.2, repeat: Infinity }} style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: cfg.color, display: 'inline-block' }} />
        : <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: cfg.color, display: 'inline-block' }} />
      }
      {cfg.label}
    </span>
  )
}

// ─── Toggle ───────────────────────────────────────────────────────────
function Toggle({ checked, onChange }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
    >
      <div style={{
        width: '28px', height: '16px', borderRadius: '99px',
        backgroundColor: checked ? '#00D9FF' : '#1E1E2E',
        border: '1px solid', borderColor: checked ? '#00D9FF' : '#3A3A4A',
        position: 'relative', transition: 'all 200ms ease', flexShrink: 0,
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

// ─── Task row ─────────────────────────────────────────────────────────
function TaskRow({ task, index }) {
  const navigate = useNavigate()
  const ago = useRelativeTime(task.created_at)
  const [hovered, setHovered] = useState(false)
  const truncated = (task.description ?? '').length > 72 ? task.description.slice(0, 72) + '…' : task.description

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.2 }}
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/task/${task.id}`)}
      onKeyDown={e => e.key === 'Enter' && navigate(`/task/${task.id}`)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: '16px',
        padding: '11px 10px',
        borderRadius: '8px',
        marginBottom: '2px',
        cursor: 'pointer',
        backgroundColor: hovered ? 'rgba(255,255,255,0.03)' : 'transparent',
        border: '1px solid',
        borderColor: hovered ? 'rgba(255,255,255,0.06)' : 'transparent',
        transition: 'all 0.15s ease',
      }}
    >
      <span style={{ flex: 1, fontFamily: "'DM Mono', monospace", fontSize: '12px', color: hovered ? '#E8E8F0' : '#9CA3AF', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', minWidth: 0, transition: 'color 0.15s ease' }}>
        {truncated}
      </span>
      <StatusBadge status={task.status} />
      <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#4B5563', flexShrink: 0 }}>{ago}</span>
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
    refetchInterval: 3000,
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

  const handleKeyDown = e => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit()
  }

  return (
    <div style={{ maxWidth: '820px' }}>

      {/* ── Feature Showcase ─────────────────────────────────────── */}
      <FeatureShowcase />

      {/* ── Task Input ───────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        style={{ marginBottom: '28px' }}
      >
        <TemplateChips onSelect={p => setInput(p)} />

        <div style={{
          border: '1px solid #1E1E2E',
          borderRadius: '10px',
          backgroundColor: '#0D0D16',
          overflow: 'hidden',
          transition: 'border-color 0.2s ease',
        }}
          onFocusCapture={e => e.currentTarget.style.borderColor = '#00D9FF40'}
          onBlurCapture={e => e.currentTarget.style.borderColor = '#1E1E2E'}
        >
          <textarea
            id="task-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your task… e.g. 'Write a research paper on LLM agents and export as PDF'"
            rows={4}
            style={{
              width: '100%', resize: 'none', backgroundColor: 'transparent',
              border: 'none', outline: 'none', padding: '14px 16px',
              fontFamily: "'DM Mono', monospace", fontSize: '13px',
              color: '#E8E8F0', lineHeight: 1.6, caretColor: '#00D9FF',
              boxSizing: 'border-box',
            }}
          />
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderTop: '1px solid #1E1E2E' }}>
            <Toggle checked={humanReview} onChange={setHumanReview} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#3A3A4A' }}>⌘ + Enter</span>
              <motion.button
                id="run-task-btn"
                whileHover={{ scale: isSubmitting || !input.trim() ? 1 : 1.03 }}
                whileTap={{ scale: isSubmitting || !input.trim() ? 1 : 0.97 }}
                onClick={handleSubmit}
                disabled={isSubmitting || !input.trim()}
                style={{
                  backgroundColor: isSubmitting || !input.trim() ? '#1A1A28' : '#00D9FF',
                  color: isSubmitting || !input.trim() ? '#3A3A4A' : '#0A0A0F',
                  border: 'none', borderRadius: '7px', padding: '8px 18px',
                  fontFamily: "'DM Mono', monospace", fontSize: '11px', fontWeight: 600,
                  letterSpacing: '0.08em', textTransform: 'uppercase',
                  cursor: isSubmitting || !input.trim() ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', gap: '7px',
                  transition: 'background-color 0.2s ease, color 0.2s ease',
                }}
              >
                {isSubmitting
                  ? <><motion.div animate={{ rotate: 360 }} transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }} style={{ width: '12px', height: '12px', border: '2px solid rgba(0,0,0,0.2)', borderTopColor: '#0A0A0F', borderRadius: '50%' }} />Running…</>
                  : <><Send size={12} />Run Task</>
                }
              </motion.button>
            </div>
          </div>
        </div>

        <AnimatePresence>
          {submitError && (
            <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#EF4444', marginTop: '8px', marginBottom: 0 }}>
              {submitError}
            </motion.p>
          )}
        </AnimatePresence>
      </motion.div>

      {/* ── Recent Tasks ─────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#6B7280', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            Recent Tasks
          </span>
          {displayTasks.length > 0 && (
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#4B5563' }}>
              {displayTasks.length} total
            </span>
          )}
        </div>

        {isLoading
          ? [0, 1, 2].map(i => <SkeletonRow key={i} />)
          : isError
            ? <ErrorRow onRetry={refetch} />
            : displayTasks.length > 0
              ? displayTasks.map((task, i) => <TaskRow key={task.id} task={task} index={i} />)
              : (
                <div style={{ textAlign: 'center', padding: '48px 0' }}>
                  <Zap size={28} color="#1E1E2E" style={{ marginBottom: '12px' }} />
                  <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#3A3A4A', margin: 0 }}>
                    No tasks yet — run your first task above
                  </p>
                </div>
              )
        }
      </motion.div>
    </div>
  )
}
