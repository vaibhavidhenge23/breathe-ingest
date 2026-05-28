import { useState, useEffect } from 'react'
import { getRecords, getSummary, approveRecord, bulkApprove, getRecordDetail } from '../api'

const STATUS_STYLE = {
  pending:  { bg: '#fefce8', color: '#854d0e', label: 'Pending' },
  flagged:  { bg: '#fef2f2', color: '#dc2626', label: 'Flagged' },
  approved: { bg: '#f0fdf4', color: '#15803d', label: 'Approved' },
}

const SCOPE_COLOR = { 1: '#dc2626', 2: '#2563eb', 3: '#7c3aed' }

export default function Dashboard() {
  const [records, setRecords] = useState([])
  const [summary, setSummary] = useState(null)
  const [filter, setFilter] = useState('pending')
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const [recs, sum] = await Promise.all([
      getRecords({ status: filter }),
      getSummary()
    ])
    setRecords(recs)
    setSummary(sum)
    setLoading(false)
  }

  useEffect(() => { load() }, [filter])

  async function handleApprove(id) {
    await approveRecord(id)
    load()
  }

  async function handleBulkApprove() {
    if (!confirm('Approve all pending records?')) return
    await bulkApprove()
    load()
  }

  async function handleRowClick(id) {
    const d = await getRecordDetail(id)
    setDetail(d)
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 56px)' }}>

      {/* Sidebar */}
      <div style={{ width: 220, borderRight: '1px solid #e5e7eb', padding: 20, background: '#fafafa', flexShrink: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 16 }}>Overview</div>
        {summary && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <SummaryItem label="Total" value={summary.total} color="#374151" />
            <SummaryItem label="Pending" value={summary.pending} color="#854d0e" />
            <SummaryItem label="Flagged" value={summary.flagged} color="#dc2626" />
            <SummaryItem label="Approved" value={summary.approved} color="#15803d" />
            <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: 10, marginTop: 4 }}>
              <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 2 }}>Approved CO₂e</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#374151' }}>
                {summary.approved_kgco2e.toLocaleString()} kg
              </div>
            </div>
          </div>
        )}

        <div style={{ marginTop: 24 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 10 }}>Filter</div>
          {['pending', 'flagged', 'approved'].map(s => (
            <button key={s} onClick={() => setFilter(s)} style={{
              display: 'block', width: '100%', textAlign: 'left',
              padding: '6px 10px', borderRadius: 6, marginBottom: 4,
              border: 'none', cursor: 'pointer', fontSize: 13,
              background: filter === s ? '#eff6ff' : 'transparent',
              color: filter === s ? '#2563eb' : '#374151',
              fontWeight: filter === s ? 600 : 400
            }}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>

        {filter === 'pending' && (
          <button onClick={handleBulkApprove} style={{
            marginTop: 16, width: '100%', padding: '8px 0',
            background: '#2563eb', color: '#fff', border: 'none',
            borderRadius: 6, cursor: 'pointer', fontSize: 13, fontWeight: 600
          }}>
            Approve all pending
          </button>
        )}
      </div>

      {/* Main table */}
      <div style={{ flex: 1, overflow: 'auto', padding: '20px 24px' }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
          {filter.charAt(0).toUpperCase() + filter.slice(1)} Records
          {!loading && <span style={{ fontSize: 13, fontWeight: 400, color: '#9ca3af', marginLeft: 8 }}>({records.length})</span>}
        </h2>

        {loading ? (
          <div style={{ color: '#9ca3af', fontSize: 14 }}>Loading...</div>
        ) : records.length === 0 ? (
          <div style={{ color: '#9ca3af', fontSize: 14 }}>No records.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                {['Scope', 'Category', 'Date', 'Qty', 'kgCO₂e', 'Location', 'Source', 'Status', ''].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '6px 10px', color: '#6b7280', fontWeight: 600, fontSize: 11, textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {records.map(r => (
                <tr key={r.id}
                  onClick={() => handleRowClick(r.id)}
                  style={{
                    borderBottom: '1px solid #f3f4f6',
                    cursor: 'pointer',
                    background: r.status === 'flagged' ? '#fff7f7' : 'transparent',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = '#f9fafb'}
                  onMouseLeave={e => e.currentTarget.style.background = r.status === 'flagged' ? '#fff7f7' : 'transparent'}
                >
                  <td style={{ padding: '8px 10px' }}>
                    <span style={{ fontSize: 11, fontWeight: 600, color: SCOPE_COLOR[r.scope] }}>S{r.scope}</span>
                  </td>
                  <td style={{ padding: '8px 10px', textTransform: 'capitalize' }}>{r.category}</td>
                  <td style={{ padding: '8px 10px', color: '#6b7280' }}>{r.activity_date || '—'}</td>
                  <td style={{ padding: '8px 10px' }}>{r.quantity_original} {r.unit_original}</td>
                  <td style={{ padding: '8px 10px', fontWeight: 500 }}>
                    {r.kgco2e ? parseFloat(r.kgco2e).toFixed(1) : '—'}
                  </td>
                  <td style={{ padding: '8px 10px', color: '#6b7280', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.location || '—'}</td>
                  <td style={{ padding: '8px 10px' }}>
                    <span style={{ fontSize: 11, color: '#9ca3af', textTransform: 'uppercase' }}>{r.source}</span>
                  </td>
                  <td style={{ padding: '8px 10px' }}>
                    <StatusBadge status={r.status} />
                  </td>
                  <td style={{ padding: '8px 10px' }} onClick={e => e.stopPropagation()}>
                    {r.status !== 'approved' && (
                      <button onClick={() => handleApprove(r.id)} style={{
                        padding: '3px 10px', fontSize: 12, borderRadius: 5,
                        border: '1px solid #d1d5db', cursor: 'pointer',
                        background: '#fff', color: '#374151', fontWeight: 500
                      }}>
                        Approve
                      </button>
                    )}
                    {r.status === 'approved' && (
                      <span style={{ fontSize: 11, color: '#9ca3af' }}>🔒 Locked</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Detail panel */}
      {detail && (
        <div style={{
          width: 320, borderLeft: '1px solid #e5e7eb', padding: 20,
          background: '#fff', overflow: 'auto', flexShrink: 0
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Record Detail</div>
            <button onClick={() => setDetail(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 18, color: '#9ca3af' }}>×</button>
          </div>

          <StatusBadge status={detail.status} />

          {detail.flag_reason && (
            <div style={{
              marginTop: 12, padding: '8px 10px', borderRadius: 6,
              background: '#fef2f2', border: '1px solid #fecaca',
              fontSize: 12, color: '#dc2626'
            }}>
              ⚠ {detail.flag_reason}
            </div>
          )}

          <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <DetailRow label="Category" value={detail.category} />
            <DetailRow label="Scope" value={`Scope ${detail.scope}`} />
            <DetailRow label="Quantity" value={`${detail.quantity_original} ${detail.unit_original}`} />
            <DetailRow label="kgCO₂e" value={detail.kgco2e ? parseFloat(detail.kgco2e).toFixed(2) : '—'} />
            <DetailRow label="Factor" value={detail.emission_factor_source} />
            <DetailRow label="Date" value={detail.activity_date || '—'} />
            <DetailRow label="Location" value={detail.location || '—'} />
          </div>

          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#9ca3af', marginBottom: 6, textTransform: 'uppercase' }}>Original Data</div>
            <pre style={{
              fontSize: 11, background: '#f9fafb', padding: 10,
              borderRadius: 6, overflow: 'auto', maxHeight: 200,
              border: '1px solid #e5e7eb', color: '#374151'
            }}>
              {JSON.stringify(detail.raw_data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }) {
  const s = STATUS_STYLE[status] || STATUS_STYLE.pending
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, padding: '2px 8px',
      borderRadius: 99, background: s.bg, color: s.color
    }}>
      {s.label}
    </span>
  )
}

function SummaryItem({ label, value, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: 13, color: '#6b7280' }}>{label}</span>
      <span style={{ fontSize: 15, fontWeight: 600, color }}>{value}</span>
    </div>
  )
}

function DetailRow({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: '#9ca3af', textTransform: 'uppercase', fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 13, color: '#374151', marginTop: 1 }}>{value}</div>
    </div>
  )
}
