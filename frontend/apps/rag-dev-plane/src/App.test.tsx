import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import type {ReactElement} from 'react'

// Exercise component state, effects and delayed requests without a DOM dependency.
const hooks = vi.hoisted(() => ({slots: [] as unknown[], cursor: 0, effects: [] as Array<() => void>}))
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
    useEffect: (effect: () => void | (() => void), dependencies?: unknown[]) => {
        const index = hooks.cursor++
        const previous = hooks.slots[index] as {dependencies?: unknown[]; cleanup?: () => void} | undefined
        if (!previous || !dependencies || dependencies.some((value, i) => !Object.is(value, previous.dependencies?.[i]))) {
            hooks.effects.push(() => { previous?.cleanup?.(); hooks.slots[index] = {dependencies, cleanup: effect()} })
        }
    },
}))
vi.mock('./DocumentsPanel', () => ({default: () => null}))
vi.mock('./api', async (original) => ({
    ...await original<typeof import('./api')>(),
    getSession: vi.fn(), getSessions: vi.fn(), streamChat: vi.fn(),
    renameSession: vi.fn(), archiveSession: vi.fn(),
    getWorkspaces: vi.fn(), getAccountProfile: vi.fn(), getAccountPreferences: vi.fn(), saveAccountPreferences: vi.fn(),
    getAuthSession: vi.fn(), logout: vi.fn(), getLoginOptions: vi.fn(), devLogin: vi.fn(),
}))

import App from './App'
import {archiveSession, getSession, getSessions, renameSession, streamChat, getWorkspaces, getAccountProfile, getAccountPreferences, saveAccountPreferences, getAuthSession, clearAuthentication, logout, getLoginOptions, devLogin, type AccountProfile, type ChatSessionDetail, type StreamHandlers} from './api'

type Element = ReactElement<Record<string, any>>
let tree: Element
const session: ChatSessionDetail = {sessionId: 'old', workspaceId: 'local', title: 'Old chat', preview: null, updatedAt: null, summary: null, turns: []}
function render() { hooks.cursor = 0; tree = App() as Element; hooks.effects.splice(0).forEach((effect) => effect()) }
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

const profile: AccountProfile = {
    profile: {display_name: 'Ada', email: null}, workspaces: [{workspace_id: 'local', display_name: 'Local', role: 'owner'}],
    capabilities: {profile_editable: false, preferences: {read: true, update: true, persistence: 'server', editable_fields: ['recent_chat_limit'], recent_chat_limit_options: [10, 20, 50, 100], recent_chat_limit_default: 10}, logout: {supported: false, reason: 'fixed_local_identity'}},
}
beforeEach(async () => {
    hooks.slots = []; hooks.cursor = 0
    hooks.effects = []
    vi.resetAllMocks()
    vi.stubGlobal('window', {confirm: vi.fn(() => true), setTimeout, clearTimeout, location: {assign: vi.fn()}})
    vi.stubGlobal('document', {visibilityState: 'visible', addEventListener: vi.fn(), removeEventListener: vi.fn()})
    vi.mocked(getWorkspaces).mockResolvedValue({principalDisplayName: 'Ada', workspaces: [{workspaceId: 'local', displayName: 'Local', role: 'owner'}]})
    vi.mocked(getAccountProfile).mockResolvedValue(profile)
    vi.mocked(getAccountPreferences).mockResolvedValue({preferences: {recent_chat_limit: 10}, persistence: 'server'})
    vi.mocked(saveAccountPreferences).mockImplementation(async (limit) => ({preferences: {recent_chat_limit: limit}, persistence: 'server'}))
    vi.mocked(getSessions).mockResolvedValue([session])
    render()
    await flush()
    find((n) => n.type === 'select').props.onChange({target: {value: 'local'}})
    render()
    await flush()
})
afterEach(() => {
    hooks.slots.forEach((slot) => { if (slot && typeof slot === 'object' && 'cleanup' in slot) (slot as {cleanup?: () => void}).cleanup?.() })
    vi.unstubAllGlobals()
})

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
            await flush()
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

function openAccount(panel: 'Profile' | 'Settings') {
    find((n) => n.props['aria-label'] === 'User menu').props.onClick(); render()
    button(panel).props.onClick(); render()
}
async function gatewayAccount() {
    vi.mocked(getAccountProfile).mockResolvedValue({...profile, capabilities: {...profile.capabilities, logout: {supported: true, method: 'POST', owner: 'gateway', url: '/auth/logout', scope: 'application'}}})
    vi.mocked(getAuthSession).mockResolvedValue({authenticated: true, profile: profile.profile, csrf_token: 'test-only', idle_expires_at: '2099-01-01T00:00:00Z', absolute_expires_at: '2099-01-02T00:00:00Z', persistence: 'memory'})
    openAccount('Profile')
    button('Refresh account').props.onClick(); await flush()
}

describe('FP-16 account actions', () => {
    it('shows trusted read-only profile fields and an explicit unsupported logout state', async () => {
        openAccount('Profile')
        expect(nodes().some((n) => n.type === 'dd' && n.props.children === 'Ada')).toBe(true)
        expect(nodes().some((n) => n.type === 'dd' && n.props.children === 'Not provided')).toBe(true)
        find((n) => n.props['aria-label'] === 'User menu').props.onClick(); render()
        button('Sign out').props.onClick(); await flush()
        expect(logout).not.toHaveBeenCalled()
        expect(find((n) => n.type === 'select' && n.props['aria-label'] === 'Workspace').props.value).toBe('local')
        expect(nodes().some((n) => n.type === 'p' && n.props.children === 'This fixed local development identity cannot sign out.')).toBe(true)
    })

    it('keeps the saved display limit on a failed save and applies confirmed settings with their lifetime', async () => {
        openAccount('Settings')
        vi.mocked(saveAccountPreferences).mockRejectedValueOnce(new Error('unavailable'))
        find((n) => n.props['aria-label'] === 'Account recent chat limit').props.onChange({target: {value: '20'}})
        await flush()
        expect(find((n) => n.props['aria-label'] === 'Account recent chat limit').props.value).toBe(10)
        expect(nodes().some((n) => n.props.children === 'Settings were not saved. Try again.')).toBe(true)
        vi.mocked(saveAccountPreferences).mockResolvedValueOnce({preferences: {recent_chat_limit: 20}, persistence: 'process'})
        find((n) => n.props['aria-label'] === 'Account recent chat limit').props.onChange({target: {value: '20'}})
        await flush()
        expect(find((n) => n.props['aria-label'] === 'Number of recent chats').props.value).toBe(20)
        expect(nodes().some((n) => n.props.children === 'Applies across workspaces until the backend process restarts.')).toBe(true)
    })

    it('disables unsupported preferences and sends no save', async () => {
        vi.mocked(getAccountProfile).mockResolvedValue({...profile, capabilities: {...profile.capabilities, preferences: {...profile.capabilities.preferences, read: false, update: false, persistence: 'unavailable', editable_fields: []}}})
        openAccount('Settings'); button('Refresh account').props.onClick(); await flush()
        const selector = find((n) => n.props['aria-label'] === 'Account recent chat limit')
        expect(selector.props.disabled).toBe(true)
        selector.props.onChange({target: {value: '20'}}); await flush()
        expect(saveAccountPreferences).not.toHaveBeenCalled()
    })

    it('keeps chat usable when preferences are unavailable and exposes retry without claiming persistence', async () => {
        vi.mocked(getAccountPreferences).mockRejectedValueOnce(new Error('unavailable'))
        openAccount('Settings'); button('Refresh account').props.onClick(); await flush()
        expect(find((n) => n.props['aria-label'] === 'Account recent chat limit').props.disabled).toBe(true)
        expect(find((n) => n.type === 'textarea').props.disabled).toBe(false)
        expect(button('Retry account')).toBeDefined()
        expect(nodes().some((n) => n.props.children === 'Saved preferences are currently unavailable.')).toBe(true)
    })

    it('retains protected data when logout fails, and clears it on confirmed logout', async () => {
        await gatewayAccount()
        vi.mocked(logout).mockRejectedValueOnce(new Error('unavailable')).mockImplementationOnce(async () => clearAuthentication())
        button('Sign out of application').props.onClick(); await flush()
        expect(find((n) => n.props['aria-label'] === 'Workspace').props.value).toBe('local')
        expect(nodes().some((n) => n.props.children === 'Sign out was not confirmed. Your data remains open; try again.')).toBe(true)
        button('Sign out of application').props.onClick(); await flush()
        expect(button('Sign in')).toBeDefined()
        expect(find((n) => n.props['aria-label'] === 'Workspace').props.value).toBe('')
        expect(nodes().some((n) => n.props.className === 'session-list')).toBe(false)
        expect(find((n) => n.type === 'textarea').props.value).toBe('')
    })

    it('aborts an active answer on authentication loss and ignores late protected stream callbacks', async () => {
        const answer = deferred<void>()
        let callbacks!: StreamHandlers
        vi.mocked(streamChat).mockImplementationOnce(async (_request, handlers) => {callbacks = handlers; await answer.promise})
        draft('private question'); submit()
        const signal = vi.mocked(streamChat).mock.calls[0][2]
        clearAuthentication(); render()
        expect(signal.aborted).toBe(true)
        callbacks.onAnswer('private late answer'); callbacks.onMeta({sessionId: 'old', grounded: true, sources: []})
        answer.resolve(); await flush()
        expect(button('Sign in')).toBeDefined()
        expect(nodes().some((n) => n.props.className === 'streaming-turns')).toBe(false)
        expect(find((n) => n.type === 'textarea').props.disabled).toBe(true)
    })

    it('does not restore settings from a response that arrives after authentication loss', async () => {
        const saved = deferred<{preferences: {recent_chat_limit: number}; persistence: 'server'}>()
        vi.mocked(saveAccountPreferences).mockReturnValueOnce(saved.promise)
        openAccount('Settings')
        find((n) => n.props['aria-label'] === 'Account recent chat limit').props.onChange({target: {value: '100'}})
        clearAuthentication(); render()
        saved.resolve({preferences: {recent_chat_limit: 100}, persistence: 'server'}); await flush()
        expect(button('Sign in')).toBeDefined()
        expect(nodes().some((n) => n.props['aria-label'] === 'Account recent chat limit')).toBe(false)
    })

    it('offers only server-provided dev identities and reloads account/workspaces after confirmed sign-in', async () => {
        clearAuthentication(); render()
        vi.mocked(getLoginOptions).mockResolvedValue({provider: 'dev', identities: [{identity: 'test-2', display_name: 'Test identity'}], session_url: '/auth/session', login_url: '/auth/dev-login'})
        vi.mocked(devLogin).mockResolvedValue({authenticated: true, profile: profile.profile, csrf_token: 'test-only', idle_expires_at: '2099-01-01T00:00:00Z', absolute_expires_at: '2099-01-02T00:00:00Z', persistence: 'memory'})
        button('Sign in').props.onClick(); await flush()
        button('Test identity').props.onClick(); await flush(); await flush()
        expect(devLogin).toHaveBeenCalledWith('test-2', expect.any(AbortSignal))
        expect(getWorkspaces).toHaveBeenCalledTimes(2)
        expect(nodes().some((n) => n.props['aria-label'] === 'User menu')).toBe(true)
        expect(streamChat).not.toHaveBeenCalled()
    })
})
