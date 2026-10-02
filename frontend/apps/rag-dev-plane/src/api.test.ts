import { afterEach, describe, expect, it, vi } from 'vitest'

import { archiveSession, getDocuments, getSession, getSessions, getWorkspaces, renameSession, streamChat } from './api'

afterEach(() => {
  vi.unstubAllGlobals()
})

function streamResponse(...chunks: string[]): Response {
  const encoder = new TextEncoder()
  return new Response(new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
      controller.close()
    },
  }))
}

describe('API client', () => {
  it('maps scoped documents, preserves zero and unknown counts, and encodes opaque pagination', async () => {
    const fetchMock = vi.fn().mockResolvedValue(Response.json({
      workspace_id: 'team / א', scope: { model_profile: 'bge-m3', chunking_profile: 'default' },
      items: [0, null, -1, 1.5, Number.MAX_SAFE_INTEGER + 1].map((count, index) => ({
        doc_id: `doc-${index}`, title: 'מדריך', file_name: 'guide.docx', document_type: 'word', last_ingested_at: null, indexed_chunk_count: count,
      })),
      page: { limit: 25, has_more: true, next_cursor: 'opaque-next', list_revision: '18' },
    }))
    vi.stubGlobal('fetch', fetchMock)
    const signal = new AbortController().signal
    const result = await getDocuments('team / א', 'cursor+/=?', signal)
    expect(result.scope).toEqual({ modelProfile: 'bge-m3', chunkingProfile: 'default' })
    expect(result.items.map((item) => item.indexedChunkCount)).toEqual([0, null, null, null, null])
    expect(result.items[0]).toMatchObject({ title: 'מדריך', lastIngestedAt: null, fileName: 'guide.docx' })
    expect(result.page).toMatchObject({ hasMore: true, nextCursor: 'opaque-next', listRevision: '18' })
    expect(fetchMock).toHaveBeenCalledWith('/workspaces/team%20%2F%20%D7%90/documents?limit=25&cursor=cursor%2B%2F%3D%3F', expect.objectContaining({ signal, cache: 'no-store' }))
  })

  it('rejects a different workspace and incomplete pagination rather than displaying protected or partial records', async () => {
    const payload = { workspace_id: 'other', scope: { model_profile: 'default', chunking_profile: 'default' }, items: [], page: { limit: 25, has_more: false, next_cursor: null, list_revision: '1' } }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json(payload)))
    await expect(getDocuments('local')).rejects.toMatchObject({ code: 'document_protocol_error' })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ ...payload, workspace_id: 'local', page: { ...payload.page, has_more: true } })))
    await expect(getDocuments('local')).rejects.toMatchObject({ code: 'document_protocol_error' })
  })

  it.each([[401, 'authentication_required'], [403, 'workspace_access_denied'], [409, 'document_list_changed'], [503, 'document_list_unavailable']])('preserves document recovery status %s', async (status, code) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ code, message: 'Safe message' }, { status: status as number })))
    await expect(getDocuments('local')).rejects.toMatchObject({ status, code })
  })

  it('maps workspace and session payloads from the proxy contract', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(Response.json({
        principal: { display_name: 'Ada Lovelace' },
        workspaces: [{ workspace_id: 'platform', display_name: 'Platform', role: 'owner' }],
      }))
      .mockResolvedValueOnce(Response.json([{
        session_id: 'session 1', workspace_id: 'platform', title: 'Release process',
        last_preview: null, updated_at: '2026-09-05T10:00:00Z',
      }]))
    vi.stubGlobal('fetch', fetchMock)

    await expect(getWorkspaces()).resolves.toEqual({
      principalDisplayName: 'Ada Lovelace',
      workspaces: [{ workspaceId: 'platform', displayName: 'Platform', role: 'owner' }],
    })
    await expect(getSessions('platform space')).resolves.toEqual([{
      sessionId: 'session 1', workspaceId: 'platform', title: 'Release process',
      preview: null, updatedAt: '2026-09-05T10:00:00Z',
    }])
    expect(fetchMock.mock.calls[1]?.[0]).toBe('/chat/sessions?workspace_id=platform+space')
  })

  it('exposes only the documented safe error envelope', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: 'workspace_access_denied', message: 'You do not have access to this workspace.', detail: 'private upstream detail',
    }), { status: 403, headers: { 'Content-Type': 'application/json' } })))

    await expect(getWorkspaces()).rejects.toMatchObject({
      status: 403,
      code: 'workspace_access_denied',
      fallbackMessage: 'You do not have access to this workspace.',
    })
  })

  it('maps session detail and sends encoded rename and archive requests', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(Response.json({
        session_id: 'session 1', workspace_id: 'platform', title: 'Release process',
        last_preview: 'Earlier answer', updated_at: '2026-09-05T10:00:00Z', summary: 'A summary',
        turns: [{ role: 'assistant', content: 'Hello', created_at: '2026-09-05T09:00:00Z' }],
      }))
      .mockResolvedValueOnce(Response.json({ ok: true }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(getSession('session 1')).resolves.toEqual({
      sessionId: 'session 1', workspaceId: 'platform', title: 'Release process', preview: 'Earlier answer',
      updatedAt: '2026-09-05T10:00:00Z', summary: 'A summary',
      turns: [{ role: 'assistant', content: 'Hello', createdAt: '2026-09-05T09:00:00Z' }],
    })
    await renameSession('session 1', 'New title')
    await archiveSession('session 1')

    expect(fetchMock.mock.calls[1]).toEqual(['/chat/sessions/session%201', expect.objectContaining({
      method: 'PATCH', body: JSON.stringify({ title: 'New title' }),
    })])
    expect(fetchMock.mock.calls[2]).toEqual(['/chat/sessions/session%201', expect.objectContaining({ method: 'DELETE' })])
  })

  it('parses split SSE answer and meta events, then requires done', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse(
      'event: answer\ndata: {"delta":"Hello "}\n\n',
      'event: answer\ndata: {"delta":"world"}\n\n',
      'event: meta\ndata: {"session_id":"session-1","grounded":true,"sources":[{"doc_id":"doc-1","chunk_id":"doc-1:1","source_path":"docs/guide.md","title":"Guide","page":null,"section":"Intro","score":0.9,"snippet":"Hello world"}],"debug":null}\n\n',
      'event: done\ndata: {"reason":"completed"}\n\n',
    )))
    const onAnswer = vi.fn()
    const onMeta = vi.fn()

    await expect(streamChat({ question: 'Hi', workspaceId: 'platform' }, { onAnswer, onMeta }, new AbortController().signal)).resolves.toBeUndefined()

    expect(onAnswer).toHaveBeenNthCalledWith(1, 'Hello ')
    expect(onAnswer).toHaveBeenNthCalledWith(2, 'world')
    expect(onMeta).toHaveBeenCalledWith({
      sessionId: 'session-1', grounded: true, sources: [{
        docId: 'doc-1', chunkId: 'doc-1:1', sourcePath: 'docs/guide.md', title: 'Guide',
        page: null, section: 'Intro', score: 0.9, snippet: 'Hello world', assets: [],
      }],
    })
  })

  it('maps optional source image assets and rejects malformed asset entries', async () => {
    const valid = 'event: meta\ndata: {"session_id":"session-1","grounded":true,"sources":[{"doc_id":"doc-1","chunk_id":"chunk-1","source_path":"guide.docx","title":"Guide","page":null,"section":"Deploy","score":0.9,"snippet":"Console","assets":[{"asset_id":"asset-1","media_type":"image/png","alt_text":"Console","content_url":"/workspaces/local/assets/asset-1"}]}],"debug":null}\n\nevent: done\ndata: {"reason":"completed"}\n\n'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse(valid)))
    const onMeta = vi.fn()
    await streamChat({ question: 'Show it' }, { onAnswer: vi.fn(), onMeta }, new AbortController().signal)
    expect(onMeta.mock.calls[0]?.[0].sources[0].assets[0]).toEqual({
      assetId: 'asset-1', mediaType: 'image/png', width: null, height: null,
      altText: 'Console', caption: null, contentUrl: '/workspaces/local/assets/asset-1',
    })

    const malformed = 'event: meta\ndata: {"session_id":"session-1","grounded":true,"sources":[{"doc_id":"doc-1","chunk_id":"chunk-1","source_path":"guide.docx","title":"Guide","page":null,"section":null,"score":0.9,"snippet":"Console","assets":[{"media_type":"image/png"}]}],"debug":null}\n\n'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse(malformed)))
    await expect(streamChat({ question: 'Show it' }, { onAnswer: vi.fn(), onMeta: vi.fn() }, new AbortController().signal))
      .rejects.toMatchObject({ code: 'stream_protocol_error' })
  })

  it('treats an SSE response without its terminal done event as incomplete', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse(
      'event: answer\ndata: {"delta":"Partial answer"}\n\n',
      'event: meta\ndata: {"session_id":"session-1","grounded":true,"sources":[],"debug":null}\n\n',
    )))

    await expect(streamChat({ question: 'Hi' }, { onAnswer: vi.fn(), onMeta: vi.fn() }, new AbortController().signal))
      .rejects.toMatchObject({ status: 500, code: 'stream_incomplete' })
  })

  it('propagates a safe terminal SSE error only after the done event', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse(
      'event: error\ndata: {"code":"stream_interrupted","message":"Please try again."}\n\n',
      'event: done\ndata: {"reason":"error"}\n\n',
    )))

    await expect(streamChat({ question: 'Hi' }, { onAnswer: vi.fn(), onMeta: vi.fn() }, new AbortController().signal))
      .rejects.toMatchObject({ status: 200, code: 'stream_interrupted', fallbackMessage: 'Please try again.' })
  })
})
