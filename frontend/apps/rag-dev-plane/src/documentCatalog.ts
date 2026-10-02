import { ApiError, getDocuments, type DocumentPage } from './api'

// Retry a changed list once per user action, replacing rather than appending old pages.
export async function loadDocumentCatalog(workspaceId: string, previous: DocumentPage | null, more: boolean, signal: AbortSignal, onRestart: () => void): Promise<DocumentPage> {
  try {
    const result = await getDocuments(workspaceId, more ? previous?.page.nextCursor ?? undefined : undefined, signal)
    signal.throwIfAborted()
    if (!more || !previous) return result
    if (result.page.listRevision !== previous.page.listRevision || result.scope.modelProfile !== previous.scope.modelProfile || result.scope.chunkingProfile !== previous.scope.chunkingProfile) throw new ApiError(409, 'document_list_changed')
    return { ...result, items: [...previous.items, ...result.items.filter((item) => !previous.items.some((old) => old.docId === item.docId))] }
  } catch (error) {
    signal.throwIfAborted()
    if (!(error instanceof ApiError) || error.status !== 409) throw error
    onRestart()
    const result = await getDocuments(workspaceId, undefined, signal)
    signal.throwIfAborted()
    return result
  }
}
