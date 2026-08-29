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
