import { useEffect, useRef, useState } from 'react'
import { ApiError, type DocumentPage } from './api'
import { loadDocumentCatalog } from './documentCatalog'
import { getDocumentSizeBadge, getDocumentTypeBadge, documentSizeBadges, type DocumentBadge } from './documentBadges'

function Badge({ badge, description }: { badge: DocumentBadge; description: string }) {
  return <span className="document-badge" style={{ color: badge.color, background: badge.background }} aria-label={`${description}: ${badge.label}`}>{badge.label}</span>
}

export default function DocumentsPanel({ workspaceId, onAccessDenied }: { workspaceId: string; onAccessDenied: (unauthenticated: boolean) => void }) {
  const [catalog, setCatalog] = useState<DocumentPage | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [retryMore, setRetryMore] = useState(false)
  const [notice, setNotice] = useState('')
  const controller = useRef<AbortController | null>(null)
  const accessDenied = useRef(onAccessDenied)
  accessDenied.current = onAccessDenied

  async function load(more = false) {
    if (!workspaceId || (more && !catalog?.page.nextCursor)) return
    controller.current?.abort()
    const pending = new AbortController()
    controller.current = pending
    setBusy(true)
    setError('')
    setNotice('')
    setRetryMore(more)
    try {
      const result = await loadDocumentCatalog(workspaceId, catalog, more, pending.signal, () => {
        setCatalog(null)
        setRetryMore(false)
        setNotice('The document list changed. Reloaded the newest documents.')
      })
      if (pending.signal.aborted) return
      setCatalog(result)
    } catch (failure) {
      if (pending.signal.aborted) return
      if (failure instanceof ApiError && (failure.status === 401 || failure.status === 403)) {
        setCatalog(null)
        accessDenied.current(failure.status === 401)
        setError(failure.status === 401 ? 'Sign in again to view documents.' : 'Your access to this workspace changed.')
      } else if (failure instanceof ApiError && failure.status === 409) {
        setNotice('')
        setError('Documents are still changing. Refresh to load the latest list.')
      } else {
        setError(failure instanceof ApiError && failure.status === 503 ? 'Documents are temporarily unavailable. Try again.' : 'Unable to load documents. Try again.')
      }
    } finally {
      if (!pending.signal.aborted) setBusy(false)
    }
  }

  useEffect(() => {
    void load()
    const refreshOnReturn = () => { if (document.visibilityState === 'visible') void load() }
    document.addEventListener('visibilitychange', refreshOnReturn)
    return () => {
      controller.current?.abort()
      document.removeEventListener('visibilitychange', refreshOnReturn)
    }
  }, [workspaceId])

  return <aside className="documents-pane" aria-labelledby="documents-heading" aria-busy={busy}>
    <div className="documents-heading"><h2 id="documents-heading">Recent documents</h2><button type="button" className="secondary" disabled={!workspaceId || busy} onClick={() => void load()}>Refresh</button></div>
    <p className="muted">Newly ingested knowledge, newest first.</p>
    <details className="document-legend"><summary>Chunk size guide</summary><ul>{documentSizeBadges.map((badge, index) => <li key={badge.label}><Badge badge={badge} description="Document size"/> <span>{index === 0 ? '0' : (documentSizeBadges[index - 1].maxChunks + 1).toLocaleString()}{Number.isFinite(badge.maxChunks) ? `–${badge.maxChunks.toLocaleString()}` : '+'} chunks</span></li>)}</ul></details>
    {!workspaceId && <p className="muted">Select a workspace to view documents.</p>}
    <div role="status" aria-live="polite">{busy && <p className="muted">{catalog ? 'Updating documents…' : 'Loading documents…'}</p>}{notice && <p className="muted">{notice}</p>}</div>
    {error && <div role="alert"><p className="error-message">{error}</p>{catalog && <p className="muted">Showing previously loaded documents; this list may be out of date.</p>}<button className="secondary" type="button" disabled={busy || !workspaceId} onClick={() => void load(retryMore)}>Retry documents</button></div>}
    {catalog && !busy && !error && catalog.items.length === 0 && <p className="muted">No ingested documents in this workspace.</p>}
    {catalog && <ul className="document-list">{catalog.items.map((item) => <li className="document-card" key={item.docId}>
      <h3 dir="auto">{item.title}</h3><p className="document-filename" dir="auto">{item.fileName}</p>
      <div className="document-badges"><Badge badge={getDocumentTypeBadge(item.documentType)} description="Document type"/><Badge badge={getDocumentSizeBadge(item.indexedChunkCount)} description="Document size"/></div>
      <p className="document-metadata">{item.indexedChunkCount === null ? 'Chunk count unavailable' : `${item.indexedChunkCount.toLocaleString()} chunks`}</p>
      {item.lastIngestedAt ? <p className="document-time">Ingested <time dateTime={item.lastIngestedAt}>{new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(item.lastIngestedAt))}</time></p> : <p className="document-time">Ingestion time unavailable</p>}
    </li>)}</ul>}
    {catalog?.page.hasMore && <button className="secondary document-load-more" type="button" disabled={busy} onClick={() => void load(true)}>Load more documents</button>}
  </aside>
}
