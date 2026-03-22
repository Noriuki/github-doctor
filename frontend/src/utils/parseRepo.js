/**
 * Extrai owner e repo a partir de:
 * - owner/repo
 * - https://github.com/owner/repo
 * - https://github.com/owner/repo/tree/main
 * - github.com/owner/repo
 */
export function parseRepoInput(raw) {
  const trimmed = raw.trim()
  if (!trimmed) return null

  const noScheme = trimmed.replace(/^https?:\/\//i, '').replace(/^www\./i, '')

  if (noScheme.toLowerCase().startsWith('github.com/')) {
    const path = noScheme.slice('github.com/'.length)
    return segmentsToOwnerRepo(path.split('/').filter(Boolean))
  }

  if (/^https?:\/\//i.test(trimmed)) {
    try {
      const u = new URL(trimmed)
      if (!/github\.com$/i.test(u.hostname)) return null
      const segments = u.pathname.split('/').filter(Boolean)
      return segmentsToOwnerRepo(segments)
    } catch {
      return null
    }
  }

  const parts = trimmed.split('/').map((s) => s.trim()).filter(Boolean)
  if (parts.length >= 2) {
    return { owner: parts[0], repo: parts.slice(1).join('/') }
  }

  return null
}

function segmentsToOwnerRepo(segments) {
  if (segments.length < 2) return null
  let owner = segments[0]
  let repo = segments[1]
  if (repo.endsWith('.git')) repo = repo.slice(0, -4)
  return { owner, repo }
}
