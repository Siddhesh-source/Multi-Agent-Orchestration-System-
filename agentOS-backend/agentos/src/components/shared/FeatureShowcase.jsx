import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Brain, Zap, Shield, Cpu, FileText, GitBranch, 
  Layers, Sparkles, Target, Activity, Database,
  Code, FileOutput, Globe, Clock, Users
} from 'lucide-react'

// USP Cards data
const USP_FEATURES = [
  {
    id: 'cognitive-router',
    icon: Brain,
    title: 'Cognitive Router',
    description: 'LLM-as-judge that estimates epistemic gap and intelligently routes tasks',
    badge: 'USP #1',
    color: '#00D9FF',
  },
  {
    id: 'dag-planner',
    icon: GitBranch,
    title: 'DAG Planner',
    description: 'Dependency-aware task planning with parallel execution',
    badge: 'USP #6',
    color: '#A855F7',
  },
  {
    id: 'adversarial-critic',
    icon: Users,
    title: 'Society of Critics',
    description: 'Multi-agent debate: Skeptic vs Devil\'s Advocate vs Synthesis',
    badge: 'USP #5',
    color: '#F59E0B',
  },
  {
    id: '3-tier-memory',
    icon: Database,
    title: '3-Tier Memory',
    description: 'Episodic + Semantic + Procedural memory with forgetting curves',
    badge: 'USP #2',
    color: '#22C55E',
  },
  {
    id: 'metacognition',
    icon: Sparkles,
    title: 'Metacognition',
    description: 'Self-calibrating agents that learn from failures',
    badge: 'USP #3',
    color: '#EC4899',
  },
  {
    id: 'uncertainty',
    icon: Target,
    title: 'Uncertainty Quant',
    description: 'Confidence scores via ensemble sampling',
    badge: 'USP #7',
    color: '#EF4444',
  },
  {
    id: 'file-output',
    icon: FileOutput,
    title: 'Real File Output',
    description: 'PDF, PPTX, DOCX generation - actual files, not just text',
    badge: 'NEW',
    color: '#06B6D4',
  },
  {
    id: 'code-sandbox',
    icon: Code,
    title: 'Code Execution',
    description: 'Runs code in sandbox, self-heals on errors',
    badge: 'NEW',
    color: '#84CC16',
  },
  {
    id: 'github-deploy',
    icon: Globe,
    title: 'GitHub Deploy',
    description: 'Push code to real GitHub repositories',
    badge: 'NEW',
    color: '#F97316',
  },
]

export default function FeatureShowcase() {
  const [expanded, setExpanded] = useState(false)
  const [hoveredId, setHoveredId] = useState(null)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      style={{
        background: 'linear-gradient(135deg, rgba(20, 20, 35, 0.8) 0%, rgba(10, 10, 20, 0.9) 100%)',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        overflow: 'hidden',
        marginBottom: '24px',
      }}
    >
      {/* Header */}
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          borderBottom: expanded ? '1px solid rgba(255,255,255,0.05)' : 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '32px', height: '32px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #00D9FF 0%, #A855F7 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Zap size={18} color="white" />
          </div>
          <div>
            <h3 style={{ 
              margin: 0, fontSize: '14px', fontWeight: 600, color: '#fff',
              fontFamily: "'DM Sans', sans-serif",
            }}>
              AgentOS Capabilities
            </h3>
            <p style={{ 
              margin: 0, fontSize: '11px', color: '#6B7280',
              fontFamily: "'DM Mono', monospace",
            }}>
              {expanded ? 'Click to collapse' : `${USP_FEATURES.length} advanced features`}
            </p>
          </div>
        </div>
        <motion.div
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M5 7.5L10 12.5L15 7.5" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </motion.div>
      </div>

      {/* Features Grid */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div style={{
              padding: '16px',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '12px',
            }}>
              {USP_FEATURES.map((feature, index) => (
                <motion.div
                  key={feature.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                  onMouseEnter={() => setHoveredId(feature.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  style={{
                    padding: '14px',
                    borderRadius: '12px',
                    background: hoveredId === feature.id 
                      ? `linear-gradient(135deg, ${feature.color}15 0%, ${feature.color}08 100%)`
                      : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${hoveredId === feature.id ? feature.color + '40' : 'rgba(255,255,255,0.05)'}`,
                    transition: 'all 0.2s ease',
                    cursor: 'default',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                    <div style={{
                      width: '36px', height: '36px',
                      borderRadius: '10px',
                      background: `${feature.color}20`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0,
                    }}>
                      <feature.icon size={18} color={feature.color} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <h4 style={{ 
                          margin: 0, fontSize: '13px', fontWeight: 600, color: '#fff',
                          fontFamily: "'DM Sans', sans-serif",
                        }}>
                          {feature.title}
                        </h4>
                        <span style={{
                          fontSize: '9px', fontFamily: "'DM Mono', monospace",
                          padding: '2px 6px', borderRadius: '4px',
                          background: `${feature.color}20`, color: feature.color,
                        }}>
                          {feature.badge}
                        </span>
                      </div>
                      <p style={{ 
                        margin: 0, fontSize: '11px', color: '#9CA3AF',
                        fontFamily: "'DM Sans', sans-serif", lineHeight: 1.4,
                      }}>
                        {feature.description}
                      </p>
                    </div>
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
