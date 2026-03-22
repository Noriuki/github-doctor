/**
 * Extrai username do GitHub a partir de URL ou handle.
 */
export function parseProfileInput(raw) {
  const trimmed = raw.trim().replace(/^@/, '')
  if (!trimmed) return null

  const noScheme = trimmed.replace(/^https?:\/\//i, '').replace(/^www\./i, '')

  if (noScheme.toLowerCase().startsWith('github.com/')) {
    const rest = noScheme.slice('github.com/'.length)
    const segment = rest.split(/[/?#]/)[0]
    return segment && /^[a-zA-Z0-9-]+$/.test(segment) ? segment : null
  }

  if (/^https?:\/\//i.test(trimmed)) {
    try {
      const u = new URL(trimmed)
      if (!/github\.com$/i.test(u.hostname)) return null
      const seg = u.pathname.split('/').filter(Boolean)[0]
      return seg && /^[a-zA-Z0-9-]+$/.test(seg) ? seg : null
    } catch {
      return null
    }
  }

  if (!trimmed.includes('/') && !trimmed.includes(' ') && /^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$/.test(trimmed)) {
    return trimmed
  }

  return null
}
