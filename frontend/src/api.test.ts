import { afterEach, describe, expect, it, vi } from 'vitest'

import { archiveSession, getSession, getSessions, getWorkspaces, renameSession, streamChat } from './api'

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
        page: null, section: 'Intro', score: 0.9, snippet: 'Hello world',
      }],
    })
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
