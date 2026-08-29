import { useEffect, useState, type FormEvent } from 'react'
import { ApiError, archiveSession, getSession, getSessions, getWorkspaces, renameSession, type ChatSession, type ChatSessionDetail, type Workspace } from './api'

type Pane = 'sources' | 'sessions'

function formatTimestamp(timestamp: string | null) {
  if (!timestamp) return null
  const date = new Date(timestamp)
  return Number.isNaN(date.valueOf()) ? null : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

export default function App() {
  const [activePane, setActivePane] = useState<Pane>('sessions')
  const [draft, setDraft] = useState('')
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [workspaceId, setWorkspaceId] = useState('')
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSession, setActiveSession] = useState<ChatSessionDetail | null>(null)
  const [workspaceStatus, setWorkspaceStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [sessionsStatus, setSessionsStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const [isRenaming, setIsRenaming] = useState(false)
  const [renameTitle, setRenameTitle] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    getWorkspaces(controller.signal)
      .then((discovery) => { setWorkspaces(discovery.workspaces); setWorkspaceStatus('ready') })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setWorkspaceStatus('error')
        setErrorMessage('Unable to load your workspaces. Try refreshing the page.')
      })
    return () => controller.abort()
  }, [])

  async function recoverWorkspaceAccess() {
    setWorkspaceId('')
    setSessions([])
    setActiveSession(null)
    setWorkspaceStatus('loading')
    try {
      const discovery = await getWorkspaces()
      setWorkspaces(discovery.workspaces)
      setWorkspaceStatus('ready')
      setErrorMessage('Your workspace access changed. Choose an available workspace to continue.')
    } catch {
      setWorkspaceStatus('error')
      setErrorMessage('Your workspace access changed, and available workspaces could not be refreshed.')
    }
  }

  useEffect(() => {
    if (!workspaceId) { setSessions([]); setActiveSession(null); setSessionsStatus('idle'); return }
    const controller = new AbortController()
    setSessionsStatus('loading')
    setErrorMessage('')
    getSessions(workspaceId, controller.signal)
      .then((availableSessions) => { setSessions(availableSessions); setActiveSession(null); setSessionsStatus('ready') })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        if (error instanceof ApiError && error.code === 'workspace_access_denied') {
          void recoverWorkspaceAccess()
          return
        }
        setSessionsStatus('error')
        setErrorMessage('Unable to load recent chats for this workspace.')
      })
    return () => controller.abort()
  }, [workspaceId])

  async function selectSession(session: ChatSession) {
    if (!workspaceId) return
    setErrorMessage('')
    try {
      const loadedSession = await getSession(session.sessionId)
      setActiveSession(loadedSession)
      setRenameTitle(loadedSession.title)
      setIsRenaming(false)
    } catch (error: unknown) {
      if (error instanceof ApiError && error.code === 'workspace_access_denied') {
        await recoverWorkspaceAccess()
        return
      }
      if (error instanceof ApiError && error.code === 'resource_not_found') {
        setSessions((current) => current.filter((item) => item.sessionId !== session.sessionId))
        setActiveSession(null)
        setErrorMessage('This chat is no longer available.')
        return
      }
      setErrorMessage('Unable to load this chat. Try again.')
    }
  }

  async function submitRename(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const title = renameTitle.trim()
    if (!activeSession || !title) return
    setErrorMessage('')
    try {
      await renameSession(activeSession.sessionId, title)
      setActiveSession({ ...activeSession, title })
      setSessions((current) => current.map((session) => session.sessionId === activeSession.sessionId ? { ...session, title } : session))
      setIsRenaming(false)
    } catch (error: unknown) {
      if (error instanceof ApiError && error.code === 'workspace_access_denied') {
        await recoverWorkspaceAccess()
        return
      }
      if (error instanceof ApiError && error.code === 'resource_not_found') {
        setSessions((current) => current.filter((session) => session.sessionId !== activeSession.sessionId))
        setActiveSession(null)
        setIsRenaming(false)
        setErrorMessage('This chat is no longer available.')
        return
      }
      setErrorMessage('Unable to rename this chat. Try again.')
    }
  }

  async function archiveActiveSession() {
    if (!activeSession || !window.confirm('Archive this chat? It will be removed from your recent chats.')) return
    const sessionId = activeSession.sessionId
    setErrorMessage('')
    try {
      await archiveSession(sessionId)
      setSessions((current) => current.filter((session) => session.sessionId !== sessionId))
      setActiveSession(null)
      setIsRenaming(false)
    } catch (error: unknown) {
      if (error instanceof ApiError && error.code === 'workspace_access_denied') {
        await recoverWorkspaceAccess()
        return
      }
      if (error instanceof ApiError && error.code === 'resource_not_found') {
        setSessions((current) => current.filter((session) => session.sessionId !== sessionId))
        setActiveSession(null)
        setIsRenaming(false)
        setErrorMessage('This chat is no longer available.')
        return
      }
      setErrorMessage('Unable to archive this chat. Try again.')
    }
  }

  function startNewChat() { setActiveSession(null); setDraft(''); setIsRenaming(false) }

  const selectedWorkspace = workspaces.find((workspace) => workspace.workspaceId === workspaceId)
  const chatTitle = activeSession?.title || (selectedWorkspace ? 'New chat' : 'Ask a question')

  return <main className="app-shell">
    <header className="topbar">
      <a className="brand" href="/" aria-label="Developer knowledge home">Developer knowledge</a>
      <label className="workspace-picker"><span>Workspace</span><select aria-label="Workspace" disabled={workspaceStatus !== 'ready'} value={workspaceId} onChange={(event) => setWorkspaceId(event.target.value)}>
        <option value="" disabled>{workspaceStatus === 'loading' ? 'Loading workspaces…' : 'Select a workspace'}</option>
        {workspaces.map((workspace) => <option key={workspace.workspaceId} value={workspace.workspaceId}>{workspace.displayName}</option>)}
      </select></label>
    </header>
    <section className="workspace" aria-label="Chat workspace">
      <aside className="sources-pane" aria-label="Sources"><h2>Sources</h2><p className="muted">Sources appear here when an answer includes grounded citations.</p></aside>
      <section className="chat-pane" aria-label="Chat">
        <div className="chat-heading"><div><p className="eyebrow">{selectedWorkspace?.displayName ?? 'Internal developer documentation'}</p><h1>{chatTitle}</h1></div><div className="heading-actions">{activeSession && <><button className="secondary" type="button" onClick={() => { setRenameTitle(activeSession.title); setIsRenaming(true) }}>Rename</button><button className="destructive" type="button" onClick={() => void archiveActiveSession()}>Archive chat</button></>}<button className="secondary" type="button" disabled={!workspaceId} onClick={startNewChat}>New chat</button></div></div>
        {isRenaming && activeSession && <form className="rename-form" onSubmit={(event) => void submitRename(event)}><label htmlFor="session-title">Chat title</label><div><input id="session-title" value={renameTitle} onChange={(event) => setRenameTitle(event.target.value)} maxLength={200} autoFocus /><button type="submit" disabled={!renameTitle.trim()}>Save</button><button className="secondary" type="button" onClick={() => setIsRenaming(false)}>Cancel</button></div></form>}
        <div className={activeSession ? 'conversation-view' : 'empty-state'} aria-live="polite">
          {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
          {!workspaceId && <><h2>Choose a workspace to begin</h2><p>Answers will stream here with their supporting sources.</p></>}
          {workspaceId && !activeSession && <><h2>Start a new chat</h2><p>Recent chats are available in the panel to the right.</p></>}
          {activeSession && <>
            <section className="history-summary" aria-labelledby="history-summary-heading"><h2 id="history-summary-heading">Earlier conversation summary</h2><p>{activeSession.summary ?? 'No earlier summary is available.'}</p></section>
            <section className="recent-turns" aria-labelledby="recent-turns-heading"><h2 id="recent-turns-heading">Recent conversation</h2>{activeSession.turns.length === 0 ? <p className="muted">No recent messages are available.</p> : <ol>{activeSession.turns.map((turn, index) => <li className={`turn turn-${turn.role}`} key={`${turn.createdAt}-${index}`}><div><strong>{turn.role === 'user' ? 'You' : 'Assistant'}</strong>{formatTimestamp(turn.createdAt) && <time dateTime={turn.createdAt}>{formatTimestamp(turn.createdAt)}</time>}</div><p>{turn.content}</p></li>)}</ol>}</section>
          </>}
        </div>
        <form className="composer" onSubmit={(event) => event.preventDefault()}><label className="sr-only" htmlFor="question">Your question</label><textarea id="question" value={draft} onChange={(event) => setDraft(event.target.value)} disabled={!workspaceId} placeholder="Ask about your developer documentation…" rows={3} /><button type="submit" disabled={!workspaceId || !draft.trim()}>Send</button></form>
      </section>
      <aside className="sessions-pane" aria-label="Recent chats">
        <div className="pane-tabs" role="tablist" aria-label="Workspace panels"><button className={activePane === 'sessions' ? 'active' : ''} type="button" role="tab" aria-selected={activePane === 'sessions'} onClick={() => setActivePane('sessions')}>Recent chats</button><button className={activePane === 'sources' ? 'active' : ''} type="button" role="tab" aria-selected={activePane === 'sources'} onClick={() => setActivePane('sources')}>Sources</button></div>
        {activePane === 'sources' && <p className="muted">No sources are available yet.</p>}
        {activePane === 'sessions' && !workspaceId && <p className="muted">Select a workspace to view recent chats.</p>}
        {activePane === 'sessions' && workspaceId && sessionsStatus === 'loading' && <p className="muted">Loading recent chats…</p>}
        {activePane === 'sessions' && workspaceId && sessionsStatus === 'ready' && sessions.length === 0 && <p className="muted">No recent chats in this workspace.</p>}
        {activePane === 'sessions' && sessions.length > 0 && <ul className="session-list">{sessions.map((session) => <li key={session.sessionId}><button className={activeSession?.sessionId === session.sessionId ? 'session active-session' : 'session'} type="button" onClick={() => void selectSession(session)}><span>{session.title}</span>{session.preview && <small>{session.preview}</small>}</button></li>)}</ul>}
      </aside>
    </section>
  </main>
}
