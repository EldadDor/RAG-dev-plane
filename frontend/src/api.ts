export type Workspace = { workspaceId: string; displayName: string; role: 'owner' | 'member' }
export type WorkspaceDiscovery = { principalDisplayName: string; workspaces: Workspace[] }
export type ChatSession = {
  sessionId: string
  workspaceId: string
  title: string
  preview: string | null
  updatedAt: string | null
}
export type ChatTurn = { role: 'user' | 'assistant'; content: string; createdAt: string }
export type ChatSessionDetail = ChatSession & { summary: string | null; turns: ChatTurn[] }
export type SourceReference = { docId: string; chunkId: string; sourcePath: string; title: string | null; page: number | null; section: string | null; score: number | null; snippet: string | null }
export type StreamMeta = { sessionId: string; grounded: boolean; sources: SourceReference[] }
export type StreamRequest = { question: string; workspaceId?: string; sessionId?: string }
export type StreamHandlers = { onAnswer: (delta: string) => void; onMeta: (meta: StreamMeta) => void }

type ApiWorkspace = { workspace_id: string; display_name: string; role: 'owner' | 'member' }
type ApiWorkspaceDiscovery = { principal: { display_name: string }; workspaces: ApiWorkspace[] }
type ApiSession = {
  session_id: string
  workspace_id: string
  title: string
  last_preview: string | null
  updated_at: string | null
}
type ApiSessionDetail = ApiSession & {
  summary: string | null
  turns: Array<{ role: 'user' | 'assistant'; content: string; created_at: string }>
}
type ApiErrorBody = { code?: unknown; message?: unknown }
type ApiSourceReference = { doc_id: string; chunk_id: string; source_path: string; title: string | null; page: number | null; section: string | null; score: number | null; snippet: string | null }
type ApiStreamMeta = { session_id: string; grounded: boolean; sources: ApiSourceReference[]; debug: object | null }

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly fallbackMessage?: string,
  ) {
    super(`Request failed with ${status} (${code})`)
    this.name = 'ApiError'
  }
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(path, init)
  if (!response.ok) {
    let body: ApiErrorBody = {}
    try { body = await response.json() as ApiErrorBody } catch { /* Use the status fallback. */ }
    throw new ApiError(
      response.status,
      typeof body.code === 'string' ? body.code : 'unknown_error',
      typeof body.message === 'string' ? body.message : undefined,
    )
  }
  return response
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await request(path, init)
  return response.json() as Promise<T>
}
export async function getWorkspaces(signal?: AbortSignal): Promise<WorkspaceDiscovery> {
  const response = await requestJson<ApiWorkspaceDiscovery>('/workspaces', { signal })
  return {
    principalDisplayName: response.principal.display_name,
    workspaces: response.workspaces.map((workspace) => ({ workspaceId: workspace.workspace_id, displayName: workspace.display_name, role: workspace.role })),
  }
}
function toSession(session: ApiSession): ChatSession {
  return {
    sessionId: session.session_id,
    workspaceId: session.workspace_id,
    title: session.title,
    preview: session.last_preview,
    updatedAt: session.updated_at,
  }
}
export async function getSessions(workspaceId: string, signal?: AbortSignal): Promise<ChatSession[]> {
  const response = await requestJson<ApiSession[]>(`/chat/sessions?${new URLSearchParams({ workspace_id: workspaceId })}`, { signal })
  return response.map(toSession)
}
export async function getSession(sessionId: string, signal?: AbortSignal): Promise<ChatSessionDetail> {
  const response = await requestJson<ApiSessionDetail>(`/chat/sessions/${encodeURIComponent(sessionId)}`, { signal })
  return {
    ...toSession(response),
    summary: response.summary,
    turns: response.turns.map((turn) => ({ role: turn.role, content: turn.content, createdAt: turn.created_at })),
  }
}

export async function renameSession(sessionId: string, title: string): Promise<void> {
  await requestJson<{ ok: true }>(`/chat/sessions/${encodeURIComponent(sessionId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
}

export async function archiveSession(sessionId: string): Promise<void> {
  await request(`/chat/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' })
}

function toSourceReference(source: ApiSourceReference): SourceReference {
  return { docId: source.doc_id, chunkId: source.chunk_id, sourcePath: source.source_path, title: source.title, page: source.page, section: source.section, score: source.score, snippet: source.snippet }
}

function parseEvent(block: string): { name: string; data: string } | null {
  let name = 'message'
  const data: string[] = []
  for (const line of block.split(/\r?\n/)) {
    if (!line || line.startsWith(':')) continue
    const separator = line.indexOf(':')
    const field = separator === -1 ? line : line.slice(0, separator)
    const value = separator === -1 ? '' : line.slice(separator + 1).replace(/^ /, '')
    if (field === 'event') name = value
    if (field === 'data') data.push(value)
  }
  return data.length ? { name, data: data.join('\n') } : null
}

export async function streamChat(requestBody: StreamRequest, handlers: StreamHandlers, signal: AbortSignal): Promise<void> {
  const response = await request('/chat/stream', {
    method: 'POST', headers: { Accept: 'text/event-stream', 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: requestBody.question, ...(requestBody.workspaceId ? { workspace_id: requestBody.workspaceId } : {}), ...(requestBody.sessionId ? { session_id: requestBody.sessionId } : {}), include_debug: false }), signal,
  })
  if (!response.body) throw new ApiError(500, 'stream_unavailable')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let terminal: 'meta' | 'error' | null = null
  let completed = false
  let postStartError: ApiError | null = null
  const processBlock = (block: string) => {
    const event = parseEvent(block)
    if (!event || !['answer', 'meta', 'error', 'done'].includes(event.name)) return
    let payload: unknown
    try { payload = JSON.parse(event.data) } catch { throw new ApiError(500, 'stream_protocol_error') }
    if (event.name === 'answer') {
      if (terminal) throw new ApiError(500, 'stream_protocol_error')
      if (!payload || typeof payload !== 'object' || typeof (payload as { delta?: unknown }).delta !== 'string') throw new ApiError(500, 'stream_protocol_error')
      handlers.onAnswer((payload as { delta: string }).delta)
    } else if (event.name === 'meta') {
      if (terminal) throw new ApiError(500, 'stream_protocol_error')
      const meta = payload as Partial<ApiStreamMeta>
      if (!meta || typeof meta.session_id !== 'string' || typeof meta.grounded !== 'boolean' || !Array.isArray(meta.sources)) throw new ApiError(500, 'stream_protocol_error')
      terminal = 'meta'
      handlers.onMeta({ sessionId: meta.session_id, grounded: meta.grounded, sources: meta.sources.map(toSourceReference) })
    } else if (event.name === 'error') {
      if (terminal) throw new ApiError(500, 'stream_protocol_error')
      const error = payload as ApiErrorBody
      terminal = 'error'
      postStartError = new ApiError(200, typeof error.code === 'string' ? error.code : 'stream_interrupted', typeof error.message === 'string' ? error.message : undefined)
    } else {
      if (completed) throw new ApiError(500, 'stream_protocol_error')
      const reason = (payload as { reason?: unknown })?.reason
      if ((terminal === 'meta' && reason === 'completed') || (terminal === 'error' && reason === 'error')) completed = true
      else throw new ApiError(500, 'stream_protocol_error')
    }
  }
  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const blocks = buffer.split(/\r?\n\r?\n/)
    buffer = blocks.pop() ?? ''
    for (const block of blocks) processBlock(block)
    if (done) break
  }
  if (!completed) throw new ApiError(500, 'stream_incomplete')
  if (postStartError) throw postStartError
}
