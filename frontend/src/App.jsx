import { useState } from 'react'
import Upload from './pages/Upload'
import Dashboard from './pages/Dashboard'
import AuditLog from './pages/AuditLog'

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', minHeight: '100vh', background: '#fff' }}>
      <nav style={{
        height: 56, borderBottom: '1px solid #e5e7eb',
        display: 'flex', alignItems: 'center', padding: '0 24px', gap: 24
      }}>
        <div style={{ fontWeight: 700, fontSize: 15, color: '#111' }}>
          <span style={{ color: '#2563eb' }}>Breathe</span> ESG Ingest
        </div>
        <div style={{ display: 'flex', gap: 4, marginLeft: 8 }}>
          {[
            { key: 'dashboard', label: 'Review' },
            { key: 'upload', label: 'Upload' },
            { key: 'auditlog', label: 'Audit Log' },
          ].map(item => (
            <button key={item.key} onClick={() => setPage(item.key)} style={{
              padding: '6px 14px', borderRadius: 6, border: 'none',
              cursor: 'pointer', fontSize: 14, fontWeight: 500,
              background: page === item.key ? '#eff6ff' : 'transparent',
              color: page === item.key ? '#2563eb' : '#6b7280',
            }}>
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      {page === 'upload' && (
        <Upload onUploaded={() => { setRefreshKey(k => k + 1); setPage('dashboard') }} />
      )}
      {page === 'dashboard' && <Dashboard key={refreshKey} />}
      {page === 'auditlog' && <AuditLog />}
    </div>
  )
}
