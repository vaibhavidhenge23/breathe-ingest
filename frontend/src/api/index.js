//const BASE = '/api'
const BASE = 'https://breathe-ingest-backend.onrender.com/api'

export async function uploadFile(source, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/ingest/${source}/`, { method: 'POST', body: form })
  return res.json()
}

export async function getRecords(params = {}) {
  const q = new URLSearchParams(params).toString()
  const res = await fetch(`${BASE}/analyst/records/?${q}`)
  return res.json()
}

export async function getSummary() {
  const res = await fetch(`${BASE}/analyst/summary/`)
  return res.json()
}

export async function approveRecord(id) {
  const res = await fetch(`${BASE}/analyst/records/${id}/approve/`, { method: 'POST' })
  return res.json()
}

export async function bulkApprove(batchId) {
  const res = await fetch(`${BASE}/analyst/bulk-approve/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ batch_id: batchId })
  })
  return res.json()
}

export async function getRecordDetail(id) {
  const res = await fetch(`${BASE}/analyst/records/${id}/`)
  return res.json()
}

export async function getBatches() {
  const res = await fetch(`${BASE}/ingest/batches/`)
  return res.json()
}
