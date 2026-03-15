/** HTTP client for GitHub Doctor API. */

export const API_BASE =
  (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.replace(/\/$/, '')) || ''

/**
 * API error with detail, request_id when the API returns structured error.
 */
export class ApiError extends Error {
  constructor(message, { status, requestId, detail } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.requestId = requestId
    this.detail = detail
  }
}

export async function request(url, options = {}) {
  const { method = 'GET' } = options
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const detail = err.detail ?? res.statusText
    const message = typeof detail === 'string' ? detail : (detail[0]?.msg || res.statusText)
    throw new ApiError(message, {
      status: res.status,
      requestId: err.request_id ?? res.headers.get('X-Request-ID'),
      detail: err.detail,
    })
  }
  return res.json()
}

/**
 * Fetch repository health report for owner/repo.
 */
export async function getReport(owner, repo, raw = false) {
  const qs = raw ? '?raw=true' : ''
  const base = API_BASE || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000')
  return request(`${base}/analyze/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}${qs}`)
}

export const api = { getReport }
