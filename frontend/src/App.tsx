import { useState } from 'react'

type Pane = 'sources' | 'sessions'

const unavailableWorkspaces = ['Select a workspace']

export default function App() {
  const [activePane, setActivePane] = useState<Pane>('sessions')
  const [draft, setDraft] = useState('')

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Developer knowledge home">Developer knowledge</a>
        <label className="workspace-picker">
          <span>Workspace</span>
          <select aria-label="Workspace" defaultValue="">
            <option value="" disabled>Select a workspace</option>
            {unavailableWorkspaces.map((workspace) => <option key={workspace}>{workspace}</option>)}
          </select>
        </label>
      </header>

      <section className="workspace" aria-label="Chat workspace">
        <aside className="sources-pane" aria-label="Sources">
          <h2>Sources</h2>
          <p className="muted">Sources appear here when an answer includes grounded citations.</p>
        </aside>

        <section className="chat-pane" aria-label="Chat">
          <div className="chat-heading">
            <div>
              <p className="eyebrow">Internal developer documentation</p>
              <h1>Ask a question</h1>
            </div>
            <button className="secondary" type="button">New chat</button>
          </div>

          <div className="empty-state">
            <h2>Choose a workspace to begin</h2>
            <p>Answers will stream here with their supporting sources.</p>
          </div>

          <form className="composer" onSubmit={(event) => event.preventDefault()}>
            <label className="sr-only" htmlFor="question">Your question</label>
            <textarea id="question" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask about your developer documentation…" rows={3} />
            <button type="submit" disabled={!draft.trim()}>Send</button>
          </form>
        </section>

        <aside className="sessions-pane" aria-label="Recent chats">
          <div className="pane-tabs" role="tablist" aria-label="Workspace panels">
            <button className={activePane === 'sessions' ? 'active' : ''} type="button" role="tab" aria-selected={activePane === 'sessions'} onClick={() => setActivePane('sessions')}>Recent chats</button>
            <button className={activePane === 'sources' ? 'active' : ''} type="button" role="tab" aria-selected={activePane === 'sources'} onClick={() => setActivePane('sources')}>Sources</button>
          </div>
          {activePane === 'sessions' ? <p className="muted">Recent chats will be shown after a workspace is selected.</p> : <p className="muted">No sources are available yet.</p>}
        </aside>
      </section>
    </main>
  )
}
