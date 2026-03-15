import { API_BASE } from '../api'

const apiBase = API_BASE || (typeof window !== 'undefined' ? '' : 'http://localhost:8000')

export function Footer() {
  const docs = apiBase ? `${apiBase}/docs` : '/docs'
  const health = apiBase ? `${apiBase}/health` : '/health'
  const metrics = apiBase ? `${apiBase}/metrics` : '/metrics'
  return (
    <footer className="footer">
      <a href={docs} target="_blank" rel="noreferrer">
        Documentação da API (OpenAPI)
      </a>
      {' · '}
      <a href={health} target="_blank" rel="noreferrer">
        Health
      </a>
      {' · '}
      <a href={metrics} target="_blank" rel="noreferrer">
        Metrics
      </a>
    </footer>
  )
}
