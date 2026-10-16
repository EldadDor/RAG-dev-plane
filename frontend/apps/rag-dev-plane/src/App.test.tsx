import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import type {ReactElement} from 'react'

// Exercise the component's event handlers and delayed requests without a DOM dependency.
const hooks = vi.hoisted(() => ({slots: [] as unknown[], cursor: 0}))
vi.mock('react', () => ({
    useState: (initial: unknown) => {
        const index = hooks.cursor++
        if (!(index in hooks.slots)) hooks.slots[index] = typeof initial === 'function' ? initial() : initial
        return [hooks.slots[index], (next: unknown) => {
            hooks.slots[index] = typeof next === 'function' ? next(hooks.slots[index]) : next
        }]
    },
    useRef: (initial: unknown) => {
        const index = hooks.cursor++
        if (!(index in hooks.slots)) hooks.slots[index] = {current: initial}
        return hooks.slots[index]
    },
    useEffect: () => {},
}))
vi.mock('./DocumentsPanel', () => ({default: () => null}))
vi.mock('./api', async (original) => ({
    ...await original<typeof import('./api')>(),
    getSession: vi.fn(), getSessions: vi.fn(), streamChat: vi.fn(),
    renameSession: vi.fn(), archiveSession: vi.fn(),
}))

import App from './App'
import {archiveSession, getSession, getSessions, renameSession, streamChat, type ChatSessionDetail, type StreamHandlers} from './api'

type Element = ReactElement<Record<string, any>>
let tree: Element
const session: ChatSessionDetail = {sessionId: 'old', workspaceId: 'local', title: 'Old chat', preview: null, updatedAt: null, summary: null, turns: []}
function render() { hooks.cursor = 0; tree = App() as Element }
function nodes(node: unknown = tree): Element[] {
    if (Array.isArray(node)) return node.flatMap((child) => nodes(child))
    if (!node || typeof node !== 'object' || !('props' in node)) return []
    const element = node as Element
    return [element, ...(element.props.children === undefined ? [] : nodes(element.props.children))]
}
function find(predicate: (element: Element) => boolean) {
    const result = nodes().find(predicate)
    if (!result) throw new Error('Expected UI element missing')
    return result
}
function button(label: string) { return find((n) => n.type === 'button' && n.props.children === label) }
function draft(value: string) {
    find((n) => n.type === 'textarea').props.onChange({target: {value}})
    render()
}
function newChat() { button('New chat').props.onClick(); render() }
function submit() { find((n) => n.type === 'form' && n.props.className === 'composer').props.onSubmit({preventDefault() {}}); render() }
function deferred<T>() {
    let resolve!: (value: T) => void
    let reject!: (error: unknown) => void
    const promise = new Promise<T>((yes, no) => {resolve = yes; reject = no})
    return {promise, resolve, reject}
}
async function flush() { for (let i = 0; i < 12; i++) await Promise.resolve(); render() }
function expectFresh() {
    expect(nodes().some((n) => n.type === 'h2' && n.props.children === 'Start a new chat')).toBe(true)
    expect(find((n) => n.type === 'textarea').props.value).toBe('')
    expect(nodes().some((n) => n.props.className === 'streaming-turns')).toBe(false)
    expect(nodes().some((n) => n.props.role === 'alert')).toBe(false)
}

beforeEach(() => {
    hooks.slots = []; hooks.cursor = 0
    vi.resetAllMocks()
    vi.stubGlobal('window', {confirm: vi.fn(() => true)})
    render()
    find((n) => n.type === 'select').props.onChange({target: {value: 'local'}})
    render()
    vi.mocked(getSessions).mockResolvedValue([session])
})
afterEach(() => vi.unstubAllGlobals())

describe('FP-14 New chat', () => {
    it('keeps a declined draft and resets an accepted draft without changing workspace', () => {
        draft('Unsent question')
        vi.mocked(window.confirm).mockReturnValueOnce(false)
        newChat()
        expect(find((n) => n.type === 'textarea').props.value).toBe('Unsent question')
        newChat()
        expectFresh()
        expect(find((n) => n.type === 'select').props.value).toBe('local')
    })

    it('does not confirm an empty or whitespace-only fresh chat', () => {
        newChat(); draft('   '); newChat()
        expect(window.confirm).not.toHaveBeenCalled()
        expectFresh()
    })

    it('ignores a session selection that finishes after New chat', async () => {
        const load = deferred<ChatSessionDetail>()
        vi.mocked(getSession).mockReturnValueOnce(load.promise)
        // Seed the already discovered list through a completed answer.
        vi.mocked(streamChat).mockResolvedValueOnce()
        draft('first'); submit(); await flush()
        find((n) => n.props.className === 'session').props.onClick()
        const signal = vi.mocked(getSession).mock.calls[0][1]!
        newChat()
        expect(signal.aborted).toBe(true)
        load.resolve(session); await flush()
        expectFresh()
        expect(window.confirm).not.toHaveBeenCalled()
    })

    it('preserves a declined active answer, aborts an accepted reset and ignores old stream events', async () => {
        const answer = deferred<void>()
        let handlers!: StreamHandlers
        vi.mocked(streamChat).mockImplementationOnce(async (_request, callbacks) => {handlers = callbacks; await answer.promise})
        draft('question'); submit()
        const signal = vi.mocked(streamChat).mock.calls[0][2]
        vi.mocked(window.confirm).mockReturnValueOnce(false)
        newChat()
        expect(signal.aborted).toBe(false)
        newChat()
        expect(signal.aborted).toBe(true)
        handlers.onAnswer('late answer')
        handlers.onMeta({sessionId: 'old', grounded: true, sources: []})
        answer.resolve(); await flush()
        expectFresh()
        draft('fresh question'); submit()
        expect(vi.mocked(streamChat).mock.calls[1][0].sessionId).toBeUndefined()
    })

    it('ignores completion history arriving after New chat', async () => {
        const load = deferred<ChatSessionDetail>()
        vi.mocked(getSession).mockReturnValueOnce(load.promise)
        vi.mocked(streamChat).mockImplementationOnce(async (_request, handlers) => {
            handlers.onMeta({sessionId: 'old', grounded: true, sources: []})
        })
        draft('question'); submit(); await flush()
        newChat(); load.resolve(session); await flush()
        expectFresh()
    })

    it('cancels the interrupted-chat refresh before it can send an old-session question', async () => {
        vi.mocked(streamChat).mockImplementationOnce(async (_request, handlers) => {
            handlers.onMeta({sessionId: 'old', grounded: true, sources: []})
            throw new Error('Interrupted after meta')
        })
        draft('first question'); submit(); await flush()
        const refresh = deferred<ChatSessionDetail>()
        vi.mocked(getSession).mockReturnValueOnce(refresh.promise)
        draft('retry question'); submit()
        newChat(); refresh.resolve(session); await flush()
        expectFresh()
        expect(streamChat).toHaveBeenCalledTimes(1)
    })

    it('does not let a cancelled stream change a newer answer or its busy state', async () => {
        const old = deferred<void>()
        const current = deferred<void>()
        let oldHandlers!: StreamHandlers
        vi.mocked(streamChat)
            .mockImplementationOnce(async (_request, handlers) => {oldHandlers = handlers; await old.promise})
            .mockImplementationOnce(() => current.promise)
        draft('old'); submit(); newChat()
        draft('new'); submit()
        oldHandlers.onAnswer('stale')
        oldHandlers.onMeta({sessionId: 'old', grounded: true, sources: []})
        old.reject(new Error('late error')); await flush()
        expect(button('Stop')).toBeDefined()
        const turn = find((n) => n.props.className === 'streaming-turns')
        expect(nodes(turn).some((n) => n.type === 'p' && n.props.children === 'stale')).toBe(false)
        expect(nodes().some((n) => n.props.role === 'alert')).toBe(false)
        newChat(); current.resolve(); await flush()
    })

    it.each(['rename', 'archive'])('ignores a late %s result after New chat', async (operation) => {
        vi.mocked(getSession).mockResolvedValue(session)
        vi.mocked(streamChat).mockImplementationOnce(async (_request, handlers) => {
            handlers.onMeta({sessionId: 'old', grounded: true, sources: []})
        })
        draft('question'); submit(); await flush()
        const mutation = deferred<void>()
        if (operation === 'rename') {
            vi.mocked(renameSession).mockReturnValueOnce(mutation.promise)
            button('Rename').props.onClick(); render()
            find((n) => n.type === 'form' && n.props.className === 'rename-form').props.onSubmit({preventDefault() {}})
        } else {
            vi.mocked(archiveSession).mockReturnValueOnce(mutation.promise)
            button('Archive chat').props.onClick()
        }
        newChat(); mutation.resolve(); await flush()
        expectFresh()
    })
})

describe('FP-15 recent-chat display limit', () => {
    it('defaults to 10 and switches to 20/50/100 without another fetch or clearing the selected chat', async () => {
        const sessions = Array.from({length: 105}, (_, index) => ({...session, sessionId: String(index), title: `Chat ${index}`}))
        vi.mocked(getSessions).mockResolvedValue(sessions)
        vi.mocked(getSession).mockResolvedValue({...session, title: 'Selected chat'})
        vi.mocked(streamChat).mockImplementationOnce(async (_request, handlers) => {
            handlers.onMeta({sessionId: 'old', grounded: false, sources: []})
        })
        draft('question'); submit(); await flush()
        const count = () => nodes(find((n) => n.props.className === 'session-list')).filter((n) => n.type === 'li').length
        expect(count()).toBe(10)
        const fetches = vi.mocked(getSessions).mock.calls.length
        for (const limit of [20, 50, 100, 10]) {
            find((n) => n.props['aria-label'] === 'Number of recent chats').props.onChange({target: {value: String(limit)}})
            render()
            expect(count()).toBe(limit)
            expect(nodes().some((n) => n.type === 'h1' && n.props.children === 'Selected chat')).toBe(true)
        }
        expect(getSessions).toHaveBeenCalledTimes(fetches)
        newChat()
        expect(count()).toBe(10)
        expect(find((n) => n.props['aria-label'] === 'Number of recent chats').props.value).toBe(10)
    })

    it('offers only supported sizes and ignores unsupported values', () => {
        const selector = find((n) => n.props['aria-label'] === 'Number of recent chats')
        expect(nodes(selector).filter((n) => n.type === 'option').map((n) => n.props.value)).toEqual([10, 20, 50, 100])
        selector.props.onChange({target: {value: '7'}}); render()
        expect(find((n) => n.props['aria-label'] === 'Number of recent chats').props.value).toBe(10)
    })
})
