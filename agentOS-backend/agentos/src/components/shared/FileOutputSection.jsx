import { useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, Download } from 'lucide-react'

function FileIcon({ filename }) {
  const ext = filename?.split('.').pop()?.toLowerCase() || ''
  const colors = { pdf: '#EF4444', pptx: '#F59E0B', docx: '#3B82F6', html: '#F97316' }
  return <FileText size={20} color={colors[ext] || '#6B7280'} />
}

export default function FileOutputSection({ files = [] }) {
  if (files.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{
          padding: '20px', background: 'rgba(255,255,255,0.02)',
          borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.1)', textAlign: 'center',
        }}
      >
        <FileText size={28} color="#3A3A4A" style={{ marginBottom: '8px' }} />
        <p style={{ margin: 0, fontSize: '12px', color: '#6B7280', fontFamily: "'DM Sans', sans-serif" }}>
          No files generated. PDF, PPTX, and DOCX outputs will appear here.
        </p>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', overflow: 'hidden' }}
    >
      <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Download size={16} color="#06B6D4" />
        <span style={{ fontSize: '12px', fontWeight: 600, color: '#fff', fontFamily: "'DM Sans', sans-serif" }}>Generated Files</span>
        <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(6,182,212,0.15)', color: '#06B6D4', fontFamily: "'DM Mono', monospace" }}>
          {files.length}
        </span>
      </div>
      <div style={{ padding: '8px' }}>
        {files.map((file, i) => (
          <motion.div
            key={file.filename}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            style={{ padding: '12px', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}
          >
            <FileIcon filename={file.filename} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                <span style={{ fontSize: '12px', fontWeight: 500, color: '#fff', fontFamily: "'DM Sans', sans-serif", overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {file.filename}
                </span>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.08)', color: '#9CA3AF', fontFamily: "'DM Mono', monospace" }}>
                  {file.filename?.split('.').pop()?.toUpperCase()}
                </span>
              </div>
              {file.file_size && (
                <span style={{ fontSize: '10px', color: '#6B7280', fontFamily: "'DM Mono', monospace" }}>
                  {(file.file_size / 1024).toFixed(1)} KB
                </span>
              )}
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => window.open(`http://localhost:8000/api/files/${file.filename}`, '_blank')}
              style={{
                padding: '8px 14px', borderRadius: '6px', border: 'none',
                background: 'linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)',
                color: '#fff', fontSize: '11px', fontWeight: 500, fontFamily: "'DM Sans', sans-serif",
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px',
              }}
            >
              <Download size={13} />
              Download
            </motion.button>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}
