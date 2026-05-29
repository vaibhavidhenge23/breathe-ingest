import { useState, useEffect } from 'react'

export default function AuditLog() {
const [logs, setLogs] = useState([])
const [loading, setLoading] = useState(true)

useEffect(() => {
    fetch('/api/analyst/audit-log/')
    .then(r => r.json())
    .then(data => { setLogs(data); setLoading(false) })
    .catch(() => setLoading(false))
  }, [])

  const ACTION_STYLE = {
    approve: { bg: '#f0fdf4', color: '#15803d' },
    flag:    { bg: '#fef2f2', color: '#dc2626' },
    upload:  { bg: '#eff6ff', color: '#2563eb' },
    edit:    { bg: '#fefce8', color: '#854d0e' },
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{ fontSize: 20, fontWeight: 600, marginBottom: 4 }}>Audit Log</h1>
      <p style={{ color: '#888', fontSize: 13, marginBottom: 24 }}>
        Every approve, flag, and upload action — full trail for auditors.
      </p>

      {loading ? (
        <div style={{ color: '#9ca3af' }}>Loading...</div>
      ) : logs.length === 0 ? (
        <div style={{ color: '#9ca3af' }}>No actions yet.</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
              {['Time', 'User', 'Action', 'Detail'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '6px 10px', color: '#6b7280', fontSize: 11, textTransform: 'uppercase', fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.map(l => {
              const s = ACTION_STYLE[l.action] || ACTION_STYLE.edit
              return (
                <tr key={l.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '8px 10px', color: '#6b7280', whiteSpace: 'nowrap' }}>
                    {new Date(l.timestamp).toLocaleString()}
                  </td>
                  <td style={{ padding: '8px 10px', fontWeight: 500 }}>{l.user}</td>
                  <td style={{ padding: '8px 10px' }}>
                    <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 99, background: s.bg, color: s.color }}>
                      {l.action}
                    </span>
                  </td>
                  <td style={{ padding: '8px 10px', color: '#374151' }}>{l.detail || '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
