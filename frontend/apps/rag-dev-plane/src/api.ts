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
export type SourceAsset = { assetId: string; mediaType: string; width: number | null; height: number | null; altText: string | null; caption: string | null; contentUrl: string | null }
export type SourceReference = { docId: string; chunkId: string; sourcePath: string; title: string | null; page: number | null; section: string | null; score: number | null; snippet: string | null; assets: SourceAsset[] }
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
export type AccountProfile = {
  profile: { display_name: string; email: string | null }
  workspaces: ApiWorkspace[]
  capabilities: {
    profile_editable: false
    preferences: { read: boolean; update: boolean; persistence: 'server' | 'process' | 'unavailable'; editable_fields: string[]; recent_chat_limit_options: number[]; recent_chat_limit_default: number }
    logout: { supported: boolean; reason?: string; owner?: string; method?: string; url?: string; scope?: string }
  }
}
export type AccountPreferences = { preferences: { recent_chat_limit: number }; persistence: 'server' | 'process' }
export type AuthSession = { authenticated: boolean; profile: AccountProfile['profile'] | null; csrf_token: string; idle_expires_at: string | null; absolute_expires_at: string | null; persistence: 'memory' | 'postgres' }
export type DevLogin = { provider: 'dev'; identities: Array<{ identity: string; display_name: string }>; session_url: '/auth/session'; login_url: '/auth/dev-login' }
let csrfToken: string | null = null
let authGeneration = 0
const pendingRequests = new Set<AbortController>()
const responseControllers = new WeakMap<Response, AbortController>()
function releaseResponse(response: Response) {
  const controller = responseControllers.get(response)
  if (controller) pendingRequests.delete(controller)
  responseControllers.delete(response)
}
const authListeners = new Set<() => void>()
export function onAuthenticationLost(listener: () => void): () => void {
  authListeners.add(listener)
  return () => { authListeners.delete(listener) }
}
export function clearAuthentication(): void {
  authGeneration += 1
  csrfToken = null
  for (const pending of pendingRequests) pending.abort()
  pendingRequests.clear()
  for (const listener of authListeners) listener()
}
function assertAuthGeneration(generation: number) {
  if (generation !== authGeneration) throw new DOMException('Request cancelled.', 'AbortError')
}
type ApiSourceAsset = { asset_id: string; media_type: string; width?: number | null; height?: number | null; alt_text?: string | null; caption?: string | null; content_url?: string | null }
type ApiSourceReference = { doc_id: string; chunk_id: string; source_path: string; title: string | null; page: number | null; section: string | null; score: number | null; snippet: string | null; assets?: ApiSourceAsset[] }
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
  const generation = authGeneration
  const controller = new AbortController()
  pendingRequests.add(controller)
  const headers = new Headers(init?.headers)
  if (csrfToken && ['POST', 'PATCH', 'PUT', 'DELETE'].includes(init?.method ?? 'GET')) headers.set('X-CSRF-Token', csrfToken)
  let response: Response
  try {
    response = await fetch(path, { ...init, headers, credentials: 'same-origin', cache: 'no-store', signal: init?.signal ? AbortSignal.any([init.signal, controller.signal]) : controller.signal })
    assertAuthGeneration(generation)
    init?.signal?.throwIfAborted()
  } catch (error) { pendingRequests.delete(controller); throw error }
  if (response.body) responseControllers.set(response, controller)
  else pendingRequests.delete(controller)
  if (!response.ok && !(init?.redirect === 'manual' && (response.type === 'opaqueredirect' || [302, 303].includes(response.status)))) {
    let body: ApiErrorBody = {}
    try { body = await response.json() as ApiErrorBody } catch { /* Use the status fallback. */ }
    releaseResponse(response)
    assertAuthGeneration(generation)
    if (response.status === 401) clearAuthentication()
    if (response.status === 403 && body.code === 'auth_request_denied' && path !== '/auth/session') {
      // Refresh context once, but leave the original action for explicit user retry.
      try { await getAuthSession() } catch { /* The original safe failure remains actionable. */ }
    }
    throw new ApiError(
      response.status,
      typeof body.code === 'string' ? body.code : 'unknown_error',
      typeof body.message === 'string' ? body.message : undefined,
    )
  }
  return response
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const generation = authGeneration
  const response = await request(path, init)
  try {
    const value = await response.json() as T
    assertAuthGeneration(generation)
    init?.signal?.throwIfAborted()
    return value
  } finally { releaseResponse(response) }
}

export async function getAccountProfile(signal?: AbortSignal): Promise<AccountProfile> {
  const value = await requestJson<AccountProfile>('/account/profile', {signal})
  const preferences = value?.capabilities?.preferences
  if (!value?.profile || typeof value.profile.display_name !== 'string' || (value.profile.email !== null && typeof value.profile.email !== 'string')
    || !Array.isArray(value.workspaces) || !value.workspaces.every((item) => typeof item.workspace_id === 'string' && typeof item.display_name === 'string' && ['owner', 'member'].includes(item.role))
    || !preferences || typeof preferences.read !== 'boolean' || typeof preferences.update !== 'boolean'
    || !['server', 'process', 'unavailable'].includes(preferences.persistence) || !Array.isArray(preferences.editable_fields)
    || !Array.isArray(preferences.recent_chat_limit_options) || preferences.recent_chat_limit_options.some((limit) => ![10, 20, 50, 100].includes(limit))
    || typeof value.capabilities.logout?.supported !== 'boolean') throw new ApiError(500, 'account_protocol_error')
  if (value.capabilities.logout.supported && (value.capabilities.logout.url !== '/auth/logout' || value.capabilities.logout.method !== 'POST' || value.capabilities.logout.owner !== 'gateway' || value.capabilities.logout.scope !== 'application')) throw new ApiError(500, 'account_protocol_error')
  return value
}
function validatePreferences(value: AccountPreferences): AccountPreferences {
  if (![10, 20, 50, 100].includes(value?.preferences?.recent_chat_limit) || !['server', 'process'].includes(value.persistence)) throw new ApiError(500, 'account_protocol_error')
  return value
}
export async function getAccountPreferences(signal?: AbortSignal): Promise<AccountPreferences> {
  return validatePreferences(await requestJson<AccountPreferences>('/account/preferences', {signal}))
}
export async function saveAccountPreferences(limit: number, signal?: AbortSignal): Promise<AccountPreferences> {
  if (![10, 20, 50, 100].includes(limit)) throw new ApiError(422, 'invalid_request')
  return validatePreferences(await requestJson<AccountPreferences>('/account/preferences', {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({recent_chat_limit: limit}), signal}))
}
async function readAuthSession(signal?: AbortSignal, notifyAnonymous = true): Promise<AuthSession> {
  const generation = authGeneration
  const value = await requestJson<AuthSession>('/auth/session', {signal})
  assertAuthGeneration(generation)
  if (typeof value?.authenticated !== 'boolean' || typeof value.csrf_token !== 'string' || !value.csrf_token || !['memory', 'postgres'].includes(value.persistence)
    || (value.authenticated && (!value.profile || typeof value.profile.display_name !== 'string' || !Number.isFinite(Date.parse(value.idle_expires_at ?? '')) || !Number.isFinite(Date.parse(value.absolute_expires_at ?? ''))))) throw new ApiError(500, 'auth_protocol_error')
  if (!value.authenticated && notifyAnonymous) clearAuthentication()
  csrfToken = value.csrf_token
  return value
}
export async function getAuthSession(signal?: AbortSignal): Promise<AuthSession> { return readAuthSession(signal) }
export async function logout(signal?: AbortSignal): Promise<void> {
  if (!csrfToken) await getAuthSession(signal)
  const generation = authGeneration
  const response = await request('/auth/logout', {method: 'POST', signal})
  assertAuthGeneration(generation)
  if (response.status !== 204) throw new ApiError(500, 'auth_protocol_error')
  clearAuthentication()
}
export async function getLoginOptions(signal?: AbortSignal): Promise<DevLogin | null> {
  const generation = authGeneration
  const response = await request('/auth/login', {redirect: 'manual', signal})
  if (response.type === 'opaqueredirect' || response.status === 302) return null
  let value: DevLogin
  try { value = await response.json() as DevLogin } finally { releaseResponse(response) }
  assertAuthGeneration(generation)
  if (value?.provider !== 'dev' || value.login_url !== '/auth/dev-login' || value.session_url !== '/auth/session' || !Array.isArray(value.identities)
    || !value.identities.every((item) => typeof item.identity === 'string' && typeof item.display_name === 'string')) throw new ApiError(500, 'auth_protocol_error')
  return value
}
export async function devLogin(identity: string, signal?: AbortSignal): Promise<AuthSession> {
  await readAuthSession(signal, false)
  const response = await request('/auth/dev-login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({identity}), redirect: 'manual', signal})
  if (response.type !== 'opaqueredirect' && response.status !== 303) throw new ApiError(500, 'auth_protocol_error')
  return getAuthSession(signal)
}
export type IngestedDocument = {
  docId: string; title: string; fileName: string; documentType: string
  lastIngestedAt: string | null; indexedChunkCount: number | null
}
export type DocumentPage = {
  workspaceId: string
  scope: { modelProfile: string; chunkingProfile: string }
  items: IngestedDocument[]
  page: { limit: number; hasMore: boolean; nextCursor: string | null; listRevision: string }
}

export async function getDocuments(workspaceId: string, cursor?: string, signal?: AbortSignal): Promise<DocumentPage> {
  const query = new URLSearchParams({ limit: '25', ...(cursor ? { cursor } : {}) })
  const response = await requestJson<{
    workspace_id: string; scope: { model_profile: string; chunking_profile: string }
    items: Array<{ doc_id: string; title: string; file_name: string; document_type: string; last_ingested_at: string | null; indexed_chunk_count?: unknown }>
    page: { limit: number; has_more: boolean; next_cursor: string | null; list_revision: string }
  }>(`/workspaces/${encodeURIComponent(workspaceId)}/documents?${query}`, { signal, headers: { Accept: 'application/json' }, cache: 'no-store' })
  if (response.workspace_id !== workspaceId || !response.scope || !Array.isArray(response.items) || !response.page
    || typeof response.scope.model_profile !== 'string' || typeof response.scope.chunking_profile !== 'string'
    || typeof response.page.has_more !== 'boolean' || typeof response.page.list_revision !== 'string'
    || response.page.limit !== 25
    || (response.page.has_more ? typeof response.page.next_cursor !== 'string' || !response.page.next_cursor : response.page.next_cursor !== null)) {
    throw new ApiError(500, 'document_protocol_error')
  }
  return {
    workspaceId: response.workspace_id,
    scope: { modelProfile: response.scope.model_profile, chunkingProfile: response.scope.chunking_profile },
    items: response.items.map((item) => {
      if (!item || typeof item.doc_id !== 'string' || !item.doc_id || typeof item.title !== 'string' || typeof item.file_name !== 'string') throw new ApiError(500, 'document_protocol_error')
      return {
        docId: item.doc_id, title: item.title, fileName: item.file_name,
        documentType: typeof item.document_type === 'string' ? item.document_type : 'unknown',
        lastIngestedAt: typeof item.last_ingested_at === 'string' && Number.isFinite(Date.parse(item.last_ingested_at)) ? item.last_ingested_at : null,
        indexedChunkCount: typeof item.indexed_chunk_count === 'number' && Number.isSafeInteger(item.indexed_chunk_count) && item.indexed_chunk_count >= 0 ? item.indexed_chunk_count : null,
      }
    }),
    page: { limit: response.page.limit, hasMore: response.page.has_more, nextCursor: response.page.next_cursor, listRevision: response.page.list_revision },
  }
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

// Normalize every list response before applying a display cap in the UI.
export function normalizeSessions(sessions: ChatSession[]): ChatSession[] {
  const timestamp = (session: ChatSession) => {
    const value = session.updatedAt ? Date.parse(session.updatedAt) : NaN
    return Number.isFinite(value) ? value : -Infinity
  }
  const ordered = [...sessions].sort((a, b) => {
    const left = timestamp(a)
    const right = timestamp(b)
    if (left !== right) return left > right ? -1 : 1
    // Date.parse keeps milliseconds; preserve the backend's finer UTC precision.
    if (left !== -Infinity) {
      const fraction = (value: string) => (value.match(/\.(\d+)(?:Z|[+-]\d\d:\d\d)$/)?.[1] ?? '').padEnd(9, '0')
      const aFraction = fraction(a.updatedAt!)
      const bFraction = fraction(b.updatedAt!)
      if (aFraction !== bFraction) return aFraction > bFraction ? -1 : 1
    }
    return a.sessionId < b.sessionId ? -1 : a.sessionId > b.sessionId ? 1 : 0
  })
  const unique = new Map<string, ChatSession>()
  for (const session of ordered) {
    if (!unique.has(session.sessionId)) unique.set(session.sessionId, session)
  }
  return [...unique.values()]
}
export async function getSessions(workspaceId: string, signal?: AbortSignal): Promise<ChatSession[]> {
  const response = await requestJson<ApiSession[]>(`/chat/sessions?${new URLSearchParams({ workspace_id: workspaceId })}`, { signal })
  return normalizeSessions(response.map(toSession))
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
  const assets = source.assets ?? []
  if (!assets.every((asset) => asset && typeof asset.asset_id === 'string' && typeof asset.media_type === 'string')) throw new ApiError(500, 'stream_protocol_error')
  return {
    docId: source.doc_id, chunkId: source.chunk_id, sourcePath: source.source_path,
    title: source.title, page: source.page, section: source.section, score: source.score,
    snippet: source.snippet,
    assets: assets.map((asset) => ({
      assetId: asset.asset_id, mediaType: asset.media_type,
      width: asset.width ?? null, height: asset.height ?? null,
      altText: asset.alt_text ?? null, caption: asset.caption ?? null,
      contentUrl: asset.content_url ?? null,
    })),
  }
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
  const generation = authGeneration
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
    assertAuthGeneration(generation)
    if (signal.aborted) throw new DOMException('Request cancelled.', 'AbortError')
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
      if (error.code === 'authentication_required') clearAuthentication()
    } else {
      if (completed) throw new ApiError(500, 'stream_protocol_error')
      const reason = (payload as { reason?: unknown })?.reason
      if ((terminal === 'meta' && reason === 'completed') || (terminal === 'error' && reason === 'error')) completed = true
      else throw new ApiError(500, 'stream_protocol_error')
    }
  }
  try {
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
  } finally {
    releaseResponse(response)
    await reader.cancel().catch(() => {})
    reader.releaseLock()
  }
}
