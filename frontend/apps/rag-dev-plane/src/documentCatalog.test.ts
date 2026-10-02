import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, type DocumentPage } from './api'
import { loadDocumentCatalog } from './documentCatalog'

afterEach(() => vi.unstubAllGlobals())

function wirePage(id: string, revision = '1', model = 'default') {
  return { workspace_id: 'local', scope: { model_profile: model, chunking_profile: 'default' }, items: [{ doc_id: id, title: id, file_name: `${id}.txt`, document_type: 'text', last_ingested_at: null, indexed_chunk_count: 0 }], page: { limit: 25, has_more: false, next_cursor: null, list_revision: revision } }
}
const previous: DocumentPage = { workspaceId: 'local', scope: { modelProfile: 'default', chunkingProfile: 'default' }, items: [{ docId: 'old', title: 'old', fileName: 'old.txt', documentType: 'text', lastIngestedAt: null, indexedChunkCount: 0 }], page: { limit: 25, hasMore: true, nextCursor: 'cursor', listRevision: '1' } }

describe('document catalog pagination', () => {
  it('appends only pages of the same scope and revision', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json(wirePage('new'))))
    const restart = vi.fn()
    const result = await loadDocumentCatalog('local', previous, true, new AbortController().signal, restart)
    expect(result.items.map((item) => item.docId)).toEqual(['old', 'new'])
    expect(restart).not.toHaveBeenCalled()
  })
  it.each(['server-409', 'revision-change', 'profile-change'])('replaces old pages after %s and retries page one', async (scenario) => {
    const first = scenario === 'server-409' ? Response.json({ code: 'document_list_changed' }, { status: 409 }) : Response.json(wirePage('discarded', scenario === 'revision-change' ? '2' : '1', scenario === 'profile-change' ? 'bge-m3' : 'default'))
    const fetchMock = vi.fn().mockResolvedValueOnce(first).mockResolvedValueOnce(Response.json(wirePage('fresh', '2')))
    vi.stubGlobal('fetch', fetchMock)
    const restart = vi.fn()
    const result = await loadDocumentCatalog('local', previous, true, new AbortController().signal, restart)
    expect(result.items.map((item) => item.docId)).toEqual(['fresh'])
    expect(restart).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[1][0]).toBe('/workspaces/local/documents?limit=25')
  })
  it('stops after one automatic restart when the list keeps changing', async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(Response.json({ code: 'document_list_changed' }, { status: 409 })))
    vi.stubGlobal('fetch', fetchMock)
    await expect(loadDocumentCatalog('local', previous, true, new AbortController().signal, vi.fn())).rejects.toBeInstanceOf(ApiError)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
  it('ignores an aborted response even when the transport returns a result', async () => {
    const controller = new AbortController()
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => { controller.abort(); return Promise.resolve(Response.json(wirePage('stale'))) }))
    const restart = vi.fn()
    await expect(loadDocumentCatalog('local', previous, true, controller.signal, restart)).rejects.toMatchObject({ name: 'AbortError' })
    expect(restart).not.toHaveBeenCalled()
  })
})
