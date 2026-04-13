import { useState } from 'react'
import { Layout } from '../components'
import { getReport, getProfile, ApiError } from '../api'
import { parseRepoInput } from '../utils/parseRepo'
import { parseProfileInput } from '../utils/parseProfile'

export function HomePage() {
  const [mode, setMode] = useState('repo')
  const [input, setInput] = useState('')
  const [result, setResult] = useState(null)
  const [profileResult, setProfileResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [errorRequestId, setErrorRequestId] = useState(null)

  const handleAnalyze = async () => {
    setError(null)
    setErrorRequestId(null)
    setResult(null)
    setProfileResult(null)

    if (mode === 'repo') {
      const parsed = parseRepoInput(input)
      if (!parsed) {
        setError('Use owner/repo ou uma URL do GitHub (ex.: Noriuki/scrum-bot ou https://github.com/Noriuki/scrum-bot)')
        return
      }
      const { owner, repo } = parsed
      setLoading(true)
      try {
        const data = await getReport(owner, repo)
        setResult(data)
      } catch (err) {
        setError(err.message || 'Erro ao analisar repositório')
        if (err instanceof ApiError && err.requestId) setErrorRequestId(err.requestId)
      } finally {
        setLoading(false)
      }
      return
    }

    const username = parseProfileInput(input)
    if (!username) {
      setError('Informe o @ ou URL do perfil (ex.: Noriuki ou https://github.com/Noriuki)')
      return
    }
    setLoading(true)
    try {
      const data = await getProfile(username, false)
      setProfileResult(data)
    } catch (err) {
      setError(err.message || 'Erro ao analisar perfil')
      if (err instanceof ApiError && err.requestId) setErrorRequestId(err.requestId)
    } finally {
      setLoading(false)
    }
  }

  const doc = result?.documentation
  const tests = result?.tests
  const cicd = result?.cicd
  const deps = result?.dependencies

  const comp = profileResult?.completeness
  const highlights = profileResult?.highlights ?? []

  return (
    <Layout>
      <section className="panel">
        <div className="tabs">
          <button
            type="button"
            className={`tab ${mode === 'repo' ? 'active' : ''}`}
            onClick={() => {
              setMode('repo')
              setError(null)
              setResult(null)
              setProfileResult(null)
            }}
          >
            Repositório
          </button>
          <button
            type="button"
            className={`tab ${mode === 'profile' ? 'active' : ''}`}
            onClick={() => {
              setMode('profile')
              setError(null)
              setResult(null)
              setProfileResult(null)
            }}
          >
            Perfil GitHub
          </button>
        </div>

        <h2>{mode === 'repo' ? 'Analisar repositório' : 'Analisar perfil (portfólio)'}</h2>
        <p className="hint">
          {mode === 'repo' ? (
            <>
              Informe <code>owner/repo</code> ou cole a URL do repositório. A análise usa a API do GitHub (README, testes, CI/CD, dependências).
            </>
          ) : (
            <>
              Focado em <strong>primeira impressão para recrutadores</strong>: README de perfil (<code>user/user</code>), bio/links, repositórios fixados
              (com token GitHub) ou destaque por estrelas, e saúde média desses projetos.
            </>
          )}
        </p>
        <label htmlFor="repo">{mode === 'repo' ? 'Repositório' : 'Usuário ou URL do perfil'}</label>
        <input
          id="repo"
          type="text"
          className="input"
          placeholder={
            mode === 'repo'
              ? 'Noriuki/scrum-bot ou https://github.com/Noriuki/scrum-bot'
              : 'Noriuki ou https://github.com/Noriuki'
          }
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

        {result && !error && mode === 'repo' && (
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

        {profileResult && !error && mode === 'profile' && (
          <div className="result analysis-result profile-report">
            <div className="report-header">
              <div>
                <h3>
                  @{profileResult.username}
                  {profileResult.display_name && (
                    <span className="display-name"> · {profileResult.display_name}</span>
                  )}
                </h3>
                <p className="profile-meta">
                  {profileResult.followers} seguidores · {profileResult.public_repos} repos públicos
                  {profileResult.created_at && (
                    <> · conta desde {new Date(profileResult.created_at).getFullYear()}</>
                  )}
                </p>
              </div>
              <div className="health-score" data-score={profileResult.profile_score}>
                {Math.round(profileResult.profile_score)}%
              </div>
            </div>
            <p className="health-label">Profile score (portfólio)</p>

            <p className="recruiter-pitch">{profileResult.recruiter_pitch}</p>

            <div className="detail-block">
              <p className="detail-title">Completude do perfil</p>
              <p>{comp?.message}</p>
              <p className="completeness-score">Nota: {comp?.score ?? 0}/10</p>
            </div>

            <p className="pinned-source">
              Destaques:{' '}
              {profileResult.pinned_source === 'graphql_pinned'
                ? 'repositórios fixados (GitHub)'
                : 'repos públicos com mais estrelas (use token para pins reais)'}
            </p>

            {highlights.length > 0 && (
              <div className="detail-block">
                <p className="detail-title">Projetos em destaque + saúde</p>
                <ul className="highlights-list">
                  {highlights.map((h) => (
                    <li key={h.repository}>
                      <strong>{h.repository}</strong> ★{h.stars} · {Math.round(h.health_score)}% — {h.one_liner}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>
    </Layout>
  )
}
