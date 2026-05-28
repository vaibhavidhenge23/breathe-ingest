import { useState } from 'react'
import { uploadFile } from '../api'

const SOURCES = [
  {
    key: 'sap',
    label: 'SAP Fuel & Procurement',
    scope: 'Scope 1',
    hint: 'CSV export from SAP MM60/MB51. German headers (WERKS, MENGE, MEINS) supported.',
    accept: '.csv,.txt'
  },
  {
    key: 'utility',
    label: 'Utility Electricity',
    scope: 'Scope 2',
    hint: 'Portal CSV export. Billing periods do not need to align to calendar months.',
    accept: '.csv'
  },
  {
    key: 'travel',
    label: 'Corporate Travel',
    scope: 'Scope 3',
    hint: 'JSON export from Concur or Navan. Airport codes used to calculate distances.',
    accept: '.json'
  }
]

export default function Upload({ onUploaded }) {
  const [results, setResults] = useState({})
  const [loading, setLoading] = useState({})

  async function handleUpload(source, file) {
    setLoading(l => ({ ...l, [source]: true }))
    try {
      const result = await uploadFile(source, file)
      setResults(r => ({ ...r, [source]: result }))
      if (onUploaded) onUploaded()
    } catch (e) {
      setResults(r => ({ ...r, [source]: { error: 'Upload failed' } }))
    }
    setLoading(l => ({ ...l, [source]: false }))
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 4 }}>Ingest Data</h1>
      <p style={{ color: '#666', marginBottom: 32, fontSize: 14 }}>
        Upload files from each source. Records will be parsed, normalized, and queued for analyst review.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {SOURCES.map(src => (
          <UploadCard
            key={src.key}
            source={src}
            loading={loading[src.key]}
            result={results[src.key]}
            onFile={file => handleUpload(src.key, file)}
          />
        ))}
      </div>
    </div>
  )
}

function UploadCard({ source, loading, result, onFile }) {
  const [dragging, setDragging] = useState(false)

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }

  const scopeColor = {
    'Scope 1': '#dc2626',
    'Scope 2': '#2563eb',
    'Scope 3': '#7c3aed'
  }[source.scope]

  return (
    <div style={{
      border: dragging ? '2px dashed #2563eb' : '1px solid #e5e7eb',
      borderRadius: 10,
      padding: 20,
      background: dragging ? '#eff6ff' : '#fff',
      transition: 'all 0.15s'
    }}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 12 }}>
        <span style={{
          fontSize: 11, fontWeight: 600, padding: '2px 8px',
          borderRadius: 99, background: scopeColor + '15', color: scopeColor,
          marginTop: 2, whiteSpace: 'nowrap'
        }}>
          {source.scope}
        </span>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>{source.label}</div>
          <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>{source.hint}</div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <label style={{
          cursor: 'pointer', padding: '6px 14px', borderRadius: 6,
          border: '1px solid #d1d5db', fontSize: 13, background: '#f9fafb',
          color: '#374151', fontWeight: 500
        }}>
          {loading ? 'Uploading...' : 'Choose file'}
          <input
            type="file" accept={source.accept} style={{ display: 'none' }}
            onChange={e => e.target.files[0] && onFile(e.target.files[0])}
            disabled={loading}
          />
        </label>
        <span style={{ fontSize: 12, color: '#9ca3af' }}>or drag and drop</span>
      </div>

      {result && !result.error && (
        <div style={{
          marginTop: 12, padding: '8px 12px', borderRadius: 6,
          background: '#f0fdf4', border: '1px solid #bbf7d0',
          fontSize: 13, color: '#15803d'
        }}>
          ✓ {result.parsed} records parsed · {result.failed} failed
          {result.failed > 0 && <span style={{ color: '#dc2626' }}> (check dashboard)</span>}
        </div>
      )}
      {result?.error && (
        <div style={{
          marginTop: 12, padding: '8px 12px', borderRadius: 6,
          background: '#fef2f2', border: '1px solid #fecaca',
          fontSize: 13, color: '#dc2626'
        }}>
          {result.error}
        </div>
      )}
    </div>
  )
}
