import { afterEach, describe, expect, it, vi } from 'vitest'

import { archiveSession, getDocuments, getSession, getSessions, getWorkspaces, normalizeSessions, renameSession, streamChat, clearAuthentication, onAuthenticationLost, getAuthSession, getAccountProfile, getAccountPreferences, saveAccountPreferences, logout, getLoginOptions, devLogin, type ChatSession } from './api'

afterEach(() => {
  clearAuthentication()
  vi.unstubAllGlobals()
})

const authenticatedSession = {authenticated: true, profile: {display_name: 'Ada', email: null}, csrf_token: 'test-only-csrf', idle_expires_at: '2099-01-01T00:00:00Z', absolute_expires_at: '2099-01-02T00:00:00Z', persistence: 'memory'}
const anonymousSession = {...authenticatedSession, authenticated: false, profile: null, idle_expires_at: null, absolute_expires_at: null, csrf_token: 'test-bootstrap'}
const wireProfile = {profile: {display_name: 'Ada', email: null}, workspaces: [], capabilities: {profile_editable: false, preferences: {read: true, update: true, persistence: 'server', editable_fields: ['recent_chat_limit'], recent_chat_limit_options: [10, 20, 50, 100], recent_chat_limit_default: 10}, logout: {supported: false, reason: 'fixed_local_identity'}}}

describe('FP-16 account and session transport', () => {
  it('reads account capabilities and preferences without identity selectors or cached responses', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(Response.json(wireProfile)).mockResolvedValueOnce(Response.json({preferences: {recent_chat_limit: 20}, persistence: 'process'}))
    vi.stubGlobal('fetch', fetchMock)
    await expect(getAccountProfile()).resolves.toMatchObject({profile: {email: null}})
    await expect(getAccountPreferences()).resolves.toEqual({preferences: {recent_chat_limit: 20}, persistence: 'process'})
    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual(['/account/profile', '/account/preferences'])
    expect(fetchMock.mock.calls[0][1]).toMatchObject({cache: 'no-store', credentials: 'same-origin'})
    expect([...new Headers(fetchMock.mock.calls[0][1].headers).keys()]).toEqual([])
  })

  it('sends the in-memory CSRF token on every protected mutation and only the preference field on save', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(Response.json(authenticatedSession))
      .mockResolvedValueOnce(Response.json({preferences: {recent_chat_limit: 50}, persistence: 'server'}))
      .mockResolvedValueOnce(Response.json({ok: true}))
      .mockResolvedValueOnce(new Response(null, {status: 204}))
      .mockResolvedValueOnce(streamResponse('event: meta\ndata: {"session_id":"s","grounded":false,"sources":[]}\n\nevent: done\ndata: {"reason":"completed"}\n\n'))
    vi.stubGlobal('fetch', fetchMock)
    await getAuthSession()
    await saveAccountPreferences(50)
    await renameSession('s', 'Title')
    await archiveSession('s')
    await streamChat({question: 'Hi'}, {onAnswer: vi.fn(), onMeta: vi.fn()}, new AbortController().signal)
    for (const [, init] of fetchMock.mock.calls.slice(1)) expect(new Headers(init.headers).get('X-CSRF-Token')).toBe('test-only-csrf')
    expect(fetchMock.mock.calls[1][1].body).toBe(JSON.stringify({recent_chat_limit: 50}))
    await expect(saveAccountPreferences(7)).rejects.toMatchObject({status: 422})
    expect(fetchMock).toHaveBeenCalledTimes(5)
  })

  it('refreshes denied session context once without replaying the mutation', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(Response.json({code: 'auth_request_denied'}, {status: 403}))
      .mockResolvedValueOnce(Response.json(authenticatedSession))
    vi.stubGlobal('fetch', fetchMock)
    await expect(renameSession('s', 'Title')).rejects.toMatchObject({code: 'auth_request_denied'})
    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual(['/chat/sessions/s', '/auth/session'])
  })

  it('does not treat workspace denial as a session refresh or logout', async () => {
    const listener = vi.fn()
    const unsubscribe = onAuthenticationLost(listener)
    const fetchMock = vi.fn().mockResolvedValue(Response.json({code: 'workspace_access_denied'}, {status: 403}))
    vi.stubGlobal('fetch', fetchMock)
    await expect(getSessions('local')).rejects.toMatchObject({status: 403})
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(listener).not.toHaveBeenCalled()
    unsubscribe()
  })

  it('clears authentication on 401 and ignores an older response even when fetch ignores cancellation', async () => {
    let resolveOld!: (value: Response) => void
    const old = new Promise<Response>((resolve) => {resolveOld = resolve})
    const fetchMock = vi.fn().mockReturnValueOnce(old).mockResolvedValueOnce(Response.json({code: 'authentication_required'}, {status: 401}))
    vi.stubGlobal('fetch', fetchMock)
    const listener = vi.fn()
    const unsubscribe = onAuthenticationLost(listener)
    const pending = getSessions('local')
    await expect(getAccountProfile()).rejects.toMatchObject({status: 401})
    expect(listener).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[0][1].signal.aborted).toBe(true)
    resolveOld(Response.json([]))
    await expect(pending).rejects.toMatchObject({name: 'AbortError'})
    unsubscribe()
  })

  it('keeps state on failed logout and clears it only after 204 confirmation', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(Response.json(authenticatedSession))
      .mockResolvedValueOnce(Response.json({code: 'auth_unavailable'}, {status: 503}))
      .mockResolvedValueOnce(new Response(null, {status: 204}))
    vi.stubGlobal('fetch', fetchMock)
    const listener = vi.fn()
    const unsubscribe = onAuthenticationLost(listener)
    await getAuthSession()
    await expect(logout()).rejects.toMatchObject({status: 503})
    expect(listener).not.toHaveBeenCalled()
    await logout()
    expect(listener).toHaveBeenCalledTimes(1)
    unsubscribe()
  })

  it('aborts an in-flight response body and ignores its parsed data after auth loss', async () => {
    let resolveBody!: (value: unknown[]) => void
    const body = new Promise<unknown[]>((resolve) => {resolveBody = resolve})
    const response = Response.json([])
    const parsed = vi.spyOn(response, 'json').mockReturnValue(body)
    const fetchMock = vi.fn().mockResolvedValue(response)
    vi.stubGlobal('fetch', fetchMock)
    const pending = getSessions('local')
    for (let i = 0; i < 5; i++) await Promise.resolve()
    expect(parsed).toHaveBeenCalled()
    clearAuthentication()
    expect(fetchMock.mock.calls[0][1].signal.aborted).toBe(true)
    resolveBody([])
    await expect(pending).rejects.toMatchObject({name: 'AbortError'})
  })

  it('clears protected state on a post-start authentication failure', async () => {
    const listener = vi.fn()
    const unsubscribe = onAuthenticationLost(listener)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse('event: error\ndata: {"code":"authentication_required"}\n\nevent: done\ndata: {"reason":"error"}\n\n')))
    await expect(streamChat({question: 'Hi'}, {onAnswer: vi.fn(), onMeta: vi.fn()}, new AbortController().signal)).rejects.toMatchObject({name: 'AbortError'})
    expect(listener).toHaveBeenCalledTimes(1)
    unsubscribe()
  })

  it('uses a bootstrap token and server-defined local login route, then confirms the resulting session', async () => {
    const choices = {provider: 'dev', identities: [{identity: 'local-dev', display_name: 'Local Developer'}], session_url: '/auth/session', login_url: '/auth/dev-login'}
    const fetchMock = vi.fn().mockResolvedValueOnce(Response.json(choices)).mockResolvedValueOnce(Response.json(anonymousSession))
      .mockResolvedValueOnce(new Response(null, {status: 303})).mockResolvedValueOnce(Response.json(authenticatedSession))
    vi.stubGlobal('fetch', fetchMock)
    await expect(getLoginOptions()).resolves.toEqual(choices)
    await expect(devLogin('local-dev')).resolves.toMatchObject({authenticated: true})
    expect(fetchMock.mock.calls[2][0]).toBe('/auth/dev-login')
    expect(fetchMock.mock.calls[2][1].body).toBe('{"identity":"local-dev"}')
    expect(new Headers(fetchMock.mock.calls[2][1].headers).get('X-CSRF-Token')).toBe('test-bootstrap')
  })

  it('returns control for normal provider navigation rather than following redirects in fetch', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, {status: 302})))
    await expect(getLoginOptions()).resolves.toBeNull()
  })

  it('rejects malformed settings, session tokens and arbitrary logout URLs', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(Response.json({preferences: {recent_chat_limit: 7}, persistence: 'server'}))
      .mockResolvedValueOnce(Response.json({...authenticatedSession, csrf_token: ''}))
      .mockResolvedValueOnce(Response.json({...wireProfile, capabilities: {...wireProfile.capabilities, logout: {supported: true, url: 'https://example.com', method: 'POST', owner: 'gateway', scope: 'application'}}}))
    vi.stubGlobal('fetch', fetchMock)
    await expect(getAccountPreferences()).rejects.toMatchObject({code: 'account_protocol_error'})
    await expect(getAuthSession()).rejects.toMatchObject({code: 'auth_protocol_error'})
    await expect(getAccountProfile()).rejects.toMatchObject({code: 'account_protocol_error'})
  })
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
  it('deduplicates IDs using the newest record, sorts newest first and keeps identical titles with distinct IDs', async () => {
    const entries = [
      { session_id: 'z', updated_at: null, title: 'Same title' },
      { session_id: 'duplicate', updated_at: '2026-10-15T10:00:00Z', title: 'Old title' },
      { session_id: 'b', updated_at: '2026-10-16T10:00:00Z', title: 'Same title' },
      { session_id: 'a', updated_at: '2026-10-16T10:00:00Z', title: 'Same title' },
      { session_id: 'duplicate', updated_at: '2026-10-16T11:00:00Z', title: 'New title' },
      { session_id: 'A', updated_at: null, title: 'Same title' },
    ].map((session) => ({ ...session, workspace_id: 'local', last_preview: null }))
    const fetchMock = vi.fn().mockResolvedValue(Response.json(entries))
    vi.stubGlobal('fetch', fetchMock)
    const result = await getSessions('local')
    expect(result.map((session) => session.sessionId)).toEqual(['duplicate', 'a', 'b', 'A', 'z'])
    expect(result[0].title).toBe('New title')
    expect(fetchMock.mock.calls[0][0]).toBe('/chat/sessions?workspace_id=local')
  })

  it('orders fractional UTC timestamps precisely and puts invalid or missing timestamps last without mutating input', () => {
    const base: ChatSession = {sessionId: 'base', workspaceId: 'local', title: 'Title', preview: null, updatedAt: null}
    const input = [
      {...base, sessionId: 'a', updatedAt: '2026-10-16T10:00:00.123001Z'},
      {...base, sessionId: 'z', updatedAt: '2026-10-16T10:00:00.123999Z'},
      {...base, sessionId: 'bad', updatedAt: 'invalid'},
      {...base, sessionId: 'none'},
    ]
    expect(normalizeSessions(input).map((session) => session.sessionId)).toEqual(['z', 'a', 'bad', 'none'])
    expect(input[0].sessionId).toBe('a')
    expect(normalizeSessions([])).toEqual([])
  })

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
    expect(fetchMock).toHaveBeenCalledWith('/workspaces/team%20%2F%20%D7%90/documents?limit=25&cursor=cursor%2B%2F%3D%3F', expect.objectContaining({ signal: expect.any(AbortSignal), cache: 'no-store', credentials: 'same-origin' }))
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
