import { useState } from 'react'
import { Layout } from '../components'
import { getReport, ApiError } from '../api'

export function HomePage() {
  const [input, setInput] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [errorRequestId, setErrorRequestId] = useState(null)

  const handleAnalyze = async () => {
    const trimmed = input.trim()
    if (!trimmed) return
    const parts = trimmed.split('/').map((s) => s.trim()).filter(Boolean)
    if (parts.length < 2) {
      setError('Digite no formato owner/repo (ex.: octocat/Hello-World)')
      setResult(null)
      return
    }
    const [owner, ...repoParts] = parts
    const repo = repoParts.join('/')
    setError(null)
    setErrorRequestId(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await getReport(owner, repo)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Erro ao analisar repositório')
      if (err instanceof ApiError && err.requestId) {
        setErrorRequestId(err.requestId)
      }
    } finally {
      setLoading(false)
    }
  }

  const doc = result?.documentation
  const tests = result?.tests
  const cicd = result?.cicd
  const deps = result?.dependencies

  return (
    <Layout>
      <section className="panel">
        <h2>Analisar repositório</h2>
        <p className="hint">
          Informe um repositório GitHub no formato <code>owner/repo</code>. A análise usa a API do GitHub (README, testes, CI/CD, dependências).
        </p>
        <label htmlFor="repo">Repositório (owner/repo)</label>
        <input
          id="repo"
          type="text"
          className="input"
          placeholder="Ex.: octocat/Hello-World"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
        />
        <button
          type="button"
          className="btn primary"
          onClick={handleAnalyze}
          disabled={loading || !input.trim()}
        >
          {loading ? 'Analisando…' : 'Analisar'}
        </button>

        {error && (
          <div className="result error" role="alert">
            <p className="error-message">{error}</p>
            {errorRequestId && (
              <p className="error-request-id">Request ID: {errorRequestId}</p>
            )}
          </div>
        )}

        {result && !error && (
          <div className="result analysis-result">
            <div className="report-header">
              <h3>{result.repository}</h3>
              <div className="health-score" data-score={result.health_score}>
                {Math.round(result.health_score)}%
              </div>
            </div>
            <p className="health-label">Health Score</p>

            <div className="metrics">
              <div className="score-row">
                <span className="score-label">Documentação</span>
                <span>{doc ? `${doc.score}/10` : '—'}</span>
              </div>
              <div className="score-row">
                <span className="score-label">Testes</span>
                <span>{tests?.message ?? '—'}</span>
              </div>
              <div className="score-row">
                <span className="score-label">CI/CD</span>
                <span>{cicd?.message ?? '—'}</span>
              </div>
              <div className="score-row">
                <span className="score-label">Dependências</span>
                <span>{deps?.message ?? '—'}</span>
              </div>
            </div>

            {doc?.has_readme && (
              <div className="detail-block">
                <p className="detail-title">Documentação</p>
                <ul>
                  <li>README: {doc.readme_size_bytes} bytes</li>
                  <li>Badges: {doc.has_badges ? 'Sim' : 'Não'}</li>
                  <li>Instalação: {doc.has_installation ? 'Sim' : 'Não'}</li>
                  <li>Uso: {doc.has_usage ? 'Sim' : 'Não'}</li>
                </ul>
              </div>
            )}

            {tests?.test_dirs?.length > 0 && (
              <div className="detail-block">
                <p className="detail-title">Testes</p>
                <p>Pastas: {tests.test_dirs.join(', ')} · Arquivos (amostra): {tests.test_files_count}</p>
              </div>
            )}

            {cicd?.detected && cicd.workflow_files?.length > 0 && (
              <div className="detail-block">
                <p className="detail-title">CI/CD</p>
                <p>Workflows: {cicd.workflow_files.join(', ')}</p>
              </div>
            )}

            {deps?.dependency_files?.length > 0 && (
              <div className="detail-block">
                <p className="detail-title">Dependências</p>
                <p>Arquivos: {deps.dependency_files.join(', ')}</p>
                <p>Total: {deps.total_dependencies} · Desatualizadas: {deps.outdated_count}</p>
              </div>
            )}
          </div>
        )}
      </section>
    </Layout>
  )
}
