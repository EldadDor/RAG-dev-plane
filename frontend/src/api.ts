export type Workspace = { workspaceId: string; displayName: string; role: string }
export type ChatSession = { sessionId: string; title: string; preview?: string }
type ApiWorkspace = { workspace_id: string; display_name: string; role: string }
type ApiSession = { session_id: string; title: string; preview?: string }

async function requestJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal })
  if (!response.ok) throw new Error(`Request failed with ${response.status}`)
  return response.json() as Promise<T>
}
export async function getWorkspaces(signal?: AbortSignal): Promise<Workspace[]> {
  const response = await requestJson<{ workspaces: ApiWorkspace[] }>('/workspaces', signal)
  return response.workspaces.map((workspace) => ({ workspaceId: workspace.workspace_id, displayName: workspace.display_name, role: workspace.role }))
}
function toSession(session: ApiSession): ChatSession { return { sessionId: session.session_id, title: session.title, preview: session.preview } }
export async function getSessions(workspaceId: string, signal?: AbortSignal): Promise<ChatSession[]> {
  const response = await requestJson<{ sessions: ApiSession[] }>(`/chat/sessions?${new URLSearchParams({ workspace_id: workspaceId })}`, signal)
  return response.sessions.map(toSession)
}
export async function getSession(sessionId: string, workspaceId: string): Promise<ChatSession> {
  const response = await requestJson<ApiSession>(`/chat/sessions/${encodeURIComponent(sessionId)}?${new URLSearchParams({ workspace_id: workspaceId })}`)
  return toSession(response)
}
