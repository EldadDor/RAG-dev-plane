import {useEffect, useRef, useState, type FormEvent} from 'react'
import DocumentsPanel from './DocumentsPanel'
import {ApiError, archiveSession, getSession, getSessions, getWorkspaces, renameSession, streamChat, getAccountProfile, getAccountPreferences, saveAccountPreferences, getAuthSession, onAuthenticationLost, logout, getLoginOptions, devLogin, type AccountProfile, type AccountPreferences, type DevLogin, type AuthSession, type ChatSession, type ChatSessionDetail, type SourceReference, type Workspace} from './api'

type Pane = 'sources' | 'sessions'
type StreamingTurn = { question: string; answer: string; status: 'streaming' | 'cancelled' | 'error' }
export const themeOptions = ['dark', 'white', 'new-age'] as const
export type Theme = typeof themeOptions[number]
const themeLabels: Record<Theme, string> = {dark: 'Dark', white: 'White', 'new-age': 'New-age'}
const themeBackgrounds: Record<Theme, string> = {dark: '#0c1322', white: '#f6f8fc', 'new-age': '#0b0f17'}
export function readTheme(): Theme {
    try {
        const cached = window.localStorage.getItem('rag-dev-plane.theme')
        if (themeOptions.includes(cached as Theme)) return cached as Theme
    } catch { /* Cosmetic storage is optional. */ }
    return 'dark'
}
export function applyTheme(theme: Theme): boolean {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme === 'white' ? 'light' : 'dark'
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', themeBackgrounds[theme])
    try {
        window.localStorage.setItem('rag-dev-plane.theme', theme)
        return true
    } catch { return false }
}

function formatTimestamp(timestamp: string | null) {
    if (!timestamp) return null
    const date = new Date(timestamp)
    return Number.isNaN(date.valueOf()) ? null : new Intl.DateTimeFormat(undefined, {dateStyle: 'medium', timeStyle: 'short'}).format(date)
}

export default function App() {
    const [theme, setTheme] = useState<Theme>(readTheme)
    const [themeStored, setThemeStored] = useState(true)
    useEffect(() => { setThemeStored(applyTheme(theme)) }, [theme])

    function renderThemePicker(location: 'header' | 'settings') {
        return <fieldset className="theme-picker" aria-label={`${location === 'header' ? 'Header' : 'Settings'} appearance`}>
            <legend className={location === 'header' ? 'sr-only' : undefined}>Theme</legend>
            <div className="theme-options">{themeOptions.map((choice) => <label className="theme-option" key={choice}>
                <input className="sr-only" type="radio" name={`theme-${location}`} value={choice} checked={theme === choice} onChange={() => setTheme(choice)}/>
                <span className="theme-choice"><span className="theme-preview" data-preview={choice} aria-hidden="true"><span/></span><span>{themeLabels[choice]}</span></span>
            </label>)}</div>
            <p className="theme-status" aria-live={location === 'settings' ? 'polite' : 'off'}>{themeStored ? 'Saved in this browser only' : 'Applied for this visit only. Browser storage is unavailable.'}</p>
        </fieldset>
    }
    const [activePane, setActivePane] = useState<Pane>('sessions')
    const [draft, setDraft] = useState('')
    const [workspaces, setWorkspaces] = useState<Workspace[]>([])
    const [workspaceId, setWorkspaceId] = useState('')
    const [sessions, setSessions] = useState<ChatSession[]>([])
    const [recentChatLimit, setRecentChatLimit] = useState(10)
    const [activeSession, setActiveSession] = useState<ChatSessionDetail | null>(null)
    const [workspaceStatus, setWorkspaceStatus] = useState<'loading' | 'ready' | 'error'>('loading')
    const [sessionsStatus, setSessionsStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')
    const [workspaceReloadKey, setWorkspaceReloadKey] = useState(0)
    const [sessionsReloadKey, setSessionsReloadKey] = useState(0)
    const [errorMessage, setErrorMessage] = useState('')
    const [isRenaming, setIsRenaming] = useState(false)
    const [renameTitle, setRenameTitle] = useState('')
    const [sources, setSources] = useState<SourceReference[]>([])
    const [expandedSourceIds, setExpandedSourceIds] = useState<Set<string>>(() => new Set())
    const [grounded, setGrounded] = useState<boolean | null>(null)
    const [streamingTurn, setStreamingTurn] = useState<StreamingTurn | null>(null)
    const [profileMenuOpen, setProfileMenuOpen] = useState(false)
    const streamController = useRef<AbortController | null>(null)
    const sessionController = useRef<AbortController | null>(null)
    const conversationGeneration = useRef(0)
    const composer = useRef<HTMLTextAreaElement | null>(null)
    const focusComposer = useRef(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const refreshBeforeNextTurn = useRef<string | null>(null)
    const [accountPane, setAccountPane] = useState<'profile' | 'settings' | null>(null)
    const [account, setAccount] = useState<AccountProfile | null>(null)
    const [preferences, setPreferences] = useState<AccountPreferences | null>(null)
    const [accountBusy, setAccountBusy] = useState(false)
    const [accountReady, setAccountReady] = useState(false)
    const [accountMessage, setAccountMessage] = useState('')
    const [signedOut, setSignedOut] = useState(false)
    const [loginOptions, setLoginOptions] = useState<DevLogin | null>(null)
    const [authSession, setAuthSession] = useState<AuthSession | null>(null)
    const [authEpoch, setAuthEpoch] = useState(0)
    const authGeneration = useRef(0)
    const accountController = useRef<AbortController | null>(null)

    function clearProtectedState() {
        authGeneration.current += 1
        accountController.current?.abort()
        invalidateConversation()
        setAuthEpoch((value) => value + 1)
        setAccount(null); setPreferences(null); setAccountReady(false); setAccountBusy(false)
        setAuthSession(null); setLoginOptions(null); setAccountPane(null); setProfileMenuOpen(false)
        setWorkspaces([]); setWorkspaceId(''); setSessions([]); setActiveSession(null)
        setSources([]); setExpandedSourceIds(new Set()); setGrounded(null); setStreamingTurn(null)
        setDraft(''); setRenameTitle(''); setIsRenaming(false); setRecentChatLimit(10)
        refreshBeforeNextTurn.current = null
        setWorkspaceStatus('ready'); setSessionsStatus('idle'); setSignedOut(true)
        setAccountMessage(''); setErrorMessage('You are signed out. Sign in to continue.')
    }

    async function loadAccount() {
        accountController.current?.abort()
        const controller = new AbortController()
        accountController.current = controller
        const generation = authGeneration.current
        const current = () => !controller.signal.aborted && generation === authGeneration.current
        setAccountBusy(true); setAccountMessage(''); setAccountReady(false); setPreferences(null)
        try {
            const profile = await getAccountProfile(controller.signal)
            if (!current()) return
            if (profile.capabilities.logout.supported) {
                const session = await getAuthSession(controller.signal)
                if (!current() || !session.authenticated) return
                setAuthSession(session)
            }
            setAccount(profile); setSignedOut(false); setAccountReady(true)
            if (profile.capabilities.preferences.read) {
                try {
                    const saved = await getAccountPreferences(controller.signal)
                    if (!current()) return
                    setPreferences(saved); setRecentChatLimit(saved.preferences.recent_chat_limit)
                } catch {
                    if (current()) setAccountMessage('Settings could not be loaded. Retry account to try again.')
                }
            }
        } catch {
            if (current()) setAccountMessage('Account information is unavailable. Retry account to continue.')
        } finally { if (current()) setAccountBusy(false) }
    }

    async function changeRecentChatLimit(limit: number) {
        const capability = account?.capabilities.preferences
        if (!accountReady || !preferences || !capability?.update || !capability.editable_fields.includes('recent_chat_limit') || !capability.recent_chat_limit_options.includes(limit) || accountBusy) return
        const generation = authGeneration.current
        const controller = new AbortController()
        accountController.current = controller
        setAccountBusy(true); setAccountMessage('')
        try {
            const saved = await saveAccountPreferences(limit, controller.signal)
            if (generation !== authGeneration.current || controller.signal.aborted) return
            setPreferences(saved); setRecentChatLimit(saved.preferences.recent_chat_limit)
            setAccountMessage('Settings saved.')
        } catch (error) {
            if (generation !== authGeneration.current || controller.signal.aborted) return
            setAccountMessage(error instanceof ApiError && error.code === 'auth_request_denied' ? 'Session context refreshed. Choose the setting again to retry.' : 'Settings were not saved. Try again.')
        } finally { if (generation === authGeneration.current && !controller.signal.aborted) setAccountBusy(false) }
    }

    async function signOut() {
        setProfileMenuOpen(false)
        if (!account?.capabilities.logout.supported) {
            setAccountPane('profile')
            setAccountMessage('Sign out is unavailable with the current authentication setup.')
            return
        }
        if (accountBusy) return
        const generation = authGeneration.current
        const controller = new AbortController()
        accountController.current = controller
        setAccountBusy(true); setAccountMessage(''); setAccountPane('profile')
        try { await logout(controller.signal) }
        catch {
            if (generation === authGeneration.current && !controller.signal.aborted) setAccountMessage('Sign out was not confirmed. Your data remains open; try again.')
        } finally { if (generation === authGeneration.current && !controller.signal.aborted) setAccountBusy(false) }
    }

    async function signIn(identity?: string) {
        if (accountBusy) return
        const generation = authGeneration.current
        const controller = new AbortController()
        accountController.current = controller
        setAccountBusy(true); setAccountMessage('')
        try {
            if (identity) {
                if (!loginOptions?.identities.some((choice) => choice.identity === identity)) return
                const session = await devLogin(identity, controller.signal)
                if (generation !== authGeneration.current || controller.signal.aborted) return
                if (!session.authenticated) throw new Error('Sign-in not confirmed')
                setAuthSession(session); setSignedOut(false); setLoginOptions(null); setErrorMessage('')
                retryWorkspaceDiscovery()
                void loadAccount()
            } else {
                const choices = await getLoginOptions(controller.signal)
                if (generation !== authGeneration.current || controller.signal.aborted) return
                if (choices) setLoginOptions(choices)
                else window.location.assign('/auth/login')
            }
        } catch {
            if (generation === authGeneration.current && !controller.signal.aborted) setAccountMessage('Sign-in is unavailable. Try again.')
        } finally { if (generation === authGeneration.current && !controller.signal.aborted) setAccountBusy(false) }
    }

    useEffect(() => onAuthenticationLost(clearProtectedState), [])
    useEffect(() => {
        void loadAccount()
        return () => { accountController.current?.abort(); authGeneration.current += 1 }
    }, [])
    useEffect(() => {
        if (!authSession?.authenticated) return
        const controller = new AbortController()
        const generation = authGeneration.current
        const checkSession = () => {
            void getAuthSession(controller.signal).then((session) => {
                if (!controller.signal.aborted && generation === authGeneration.current && session.authenticated) setAuthSession(session)
            }).catch(() => {
                if (!controller.signal.aborted && generation === authGeneration.current) setAccountMessage('Session could not be checked. Retry account.')
            })
        }
        const onReturn = () => { if (document.visibilityState === 'visible') checkSession() }
        const expiry = Math.min(Date.parse(authSession.idle_expires_at!), Date.parse(authSession.absolute_expires_at!))
        const timer = window.setTimeout(checkSession, Math.min(2_147_483_647, Math.max(0, expiry - Date.now())))
        document.addEventListener('visibilitychange', onReturn)
        return () => { controller.abort(); window.clearTimeout(timer); document.removeEventListener('visibilitychange', onReturn) }
    }, [authSession])

    function cancelStream(showPartial = false) {
        streamController.current?.abort()
        streamController.current = null
        setIsSubmitting(false)
        if (showPartial) setStreamingTurn((current) => current ? {...current, status: 'cancelled'} : current)
    }

    function invalidateConversation() {
        conversationGeneration.current += 1
        sessionController.current?.abort()
        sessionController.current = null
        cancelStream()
    }

    useEffect(() => () => invalidateConversation(), [])
    useEffect(() => {
        if (focusComposer.current) {
            focusComposer.current = false
            composer.current?.focus()
        }
    })

    useEffect(() => {
        const controller = new AbortController()
        const generation = authGeneration.current
        getWorkspaces(controller.signal)
            .then((discovery) => {
                if (controller.signal.aborted || generation !== authGeneration.current) return
                setWorkspaces(discovery.workspaces);
                setWorkspaceStatus('ready')
            })
            .catch((error: unknown) => {
                if (controller.signal.aborted || generation !== authGeneration.current) return
                if (error instanceof DOMException && error.name === 'AbortError') return
                setWorkspaceStatus('error')
                setErrorMessage('Unable to load your workspaces. Try refreshing the page.')
            })
        return () => controller.abort()
    }, [workspaceReloadKey])

    function retryWorkspaceDiscovery() {
        setErrorMessage('')
        setWorkspaceStatus('loading')
        setWorkspaceReloadKey((current) => current + 1)
    }

    async function recoverWorkspaceAccess() {
        const generation = authGeneration.current
        invalidateConversation()
        setSources([])
        setGrounded(null)
        setStreamingTurn(null)
        refreshBeforeNextTurn.current = null
        setWorkspaceId('')
        setSessions([])
        setActiveSession(null)
        setWorkspaceStatus('loading')
        try {
            const discovery = await getWorkspaces()
            if (generation !== authGeneration.current) return
            setWorkspaces(discovery.workspaces)
            setWorkspaceStatus('ready')
            setErrorMessage('Your workspace access changed. Choose an available workspace to continue.')
        } catch {
            if (generation !== authGeneration.current) return
            setWorkspaceStatus('error')
            setErrorMessage('Your workspace access changed, and available workspaces could not be refreshed.')
        }
    }

    useEffect(() => {
        if (!workspaceId) {
            cancelStream();
            setSessions([]);
            setActiveSession(null);
            setSessionsStatus('idle');
            return
        }
        const controller = new AbortController()
        const generation = authGeneration.current
        setSessionsStatus('loading')
        setErrorMessage('')
        getSessions(workspaceId, controller.signal)
            .then((availableSessions) => {
                if (controller.signal.aborted || generation !== authGeneration.current) return
                setSessions(availableSessions);
                setSessionsStatus('ready')
            })
            .catch((error: unknown) => {
                if (controller.signal.aborted || generation !== authGeneration.current) return
                if (error instanceof DOMException && error.name === 'AbortError') return
                if (error instanceof ApiError && error.code === 'workspace_access_denied') {
                    void recoverWorkspaceAccess()
                    return
                }
                setSessionsStatus('error')
                setErrorMessage('Unable to load recent chats for this workspace.')
            })
        return () => controller.abort()
    }, [workspaceId, sessionsReloadKey])

    function retrySessions() {
        if (!workspaceId) return
        setErrorMessage('')
        setSessionsStatus('loading')
        setSessionsReloadKey((current) => current + 1)
    }

    async function selectSession(session: ChatSession) {
        if (!workspaceId) return
        invalidateConversation()
        const generation = conversationGeneration.current
        const controller = new AbortController()
        sessionController.current = controller
        setActiveSession(null)
        refreshBeforeNextTurn.current = null
        setStreamingTurn(null)
        setSources([])
        setGrounded(null)
        setErrorMessage('')
        setProfileMenuOpen(false)
        try {
            const loadedSession = await getSession(session.sessionId, controller.signal)
            if (generation !== conversationGeneration.current || controller.signal.aborted) return
            setActiveSession(loadedSession)
            setRenameTitle(loadedSession.title)
            setIsRenaming(false)
        } catch (error: unknown) {
            if (generation !== conversationGeneration.current || controller.signal.aborted) return
            if (error instanceof ApiError && error.code === 'workspace_access_denied') {
                await recoverWorkspaceAccess()
                return
            }
            if (error instanceof ApiError && error.code === 'resource_not_found') {
                setSessions((current) => current.filter((item) => item.sessionId !== session.sessionId))
                setActiveSession(null)
                setErrorMessage('This chat is no longer available.')
                return
            }
            setErrorMessage('Unable to load this chat. Try again.')
        } finally {
            if (sessionController.current === controller) sessionController.current = null
        }
    }

    async function submitRename(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        const title = renameTitle.trim()
        if (!accountReady || signedOut || !activeSession || !title) return
        const generation = conversationGeneration.current
        setErrorMessage('')
        try {
            await renameSession(activeSession.sessionId, title)
            if (generation !== conversationGeneration.current) return
            setActiveSession({...activeSession, title})
            setSessions((current) => current.map((session) => session.sessionId === activeSession.sessionId ? {...session, title} : session))
            setIsRenaming(false)
            try {
                const refreshed = await getSessions(workspaceId)
                if (generation !== conversationGeneration.current) return
                setSessions(refreshed)
            } catch {
                if (generation !== conversationGeneration.current) return
                setErrorMessage('Chat renamed, but recent chats could not be refreshed. Retry recent chats to update their order.')
                setSessionsStatus('error')
            }
        } catch (error: unknown) {
            if (generation !== conversationGeneration.current) return
            if (error instanceof ApiError && error.code === 'workspace_access_denied') {
                await recoverWorkspaceAccess()
                return
            }
            if (error instanceof ApiError && error.code === 'resource_not_found') {
                setSessions((current) => current.filter((session) => session.sessionId !== activeSession.sessionId))
                setActiveSession(null)
                setIsRenaming(false)
                setErrorMessage('This chat is no longer available.')
                return
            }
            setErrorMessage('Unable to rename this chat. Try again.')
        }
    }

    async function archiveActiveSession() {
        if (!accountReady || signedOut || !activeSession || !window.confirm('Archive this chat? It will be removed from your recent chats.')) return
        const sessionId = activeSession.sessionId
        const generation = conversationGeneration.current
        setErrorMessage('')
        try {
            await archiveSession(sessionId)
            if (generation !== conversationGeneration.current) return
            setSessions((current) => current.filter((session) => session.sessionId !== sessionId))
            setActiveSession(null)
            setIsRenaming(false)
        } catch (error: unknown) {
            if (generation !== conversationGeneration.current) return
            if (error instanceof ApiError && error.code === 'workspace_access_denied') {
                await recoverWorkspaceAccess()
                return
            }
            if (error instanceof ApiError && error.code === 'resource_not_found') {
                setSessions((current) => current.filter((session) => session.sessionId !== sessionId))
                setActiveSession(null)
                setIsRenaming(false)
                setErrorMessage('This chat is no longer available.')
                return
            }
            setErrorMessage('Unable to archive this chat. Try again.')
        }
    }

    function startNewChat() {
        if ((draft.trim() || streamController.current) && !window.confirm('Start a new chat? This will stop the current answer and discard any unsent draft.')) return
        invalidateConversation();
        refreshBeforeNextTurn.current = null;
        setActiveSession(null);
        setDraft('');
        setIsRenaming(false);
        setRenameTitle('');
        setErrorMessage('');
        setStreamingTurn(null);
        setSources([]);
        setExpandedSourceIds(new Set());
        setGrounded(null);
        setProfileMenuOpen(false)
        focusComposer.current = true
    }

    function toggleSource(sourceId: string) {
        setExpandedSourceIds((current) => {
            const next = new Set(current)
            if (next.has(sourceId)) next.delete(sourceId)
            else next.add(sourceId)
            return next
        })
    }

    async function submitQuestion(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        const question = draft.trim()
        if (!accountReady || signedOut || !workspaceId || !question || streamController.current) return
        invalidateConversation()
        const generation = conversationGeneration.current
        const controller = new AbortController()
        const isCurrent = () => generation === conversationGeneration.current && streamController.current === controller && !controller.signal.aborted
        streamController.current = controller
        setIsSubmitting(true)
        let sessionId = activeSession?.sessionId
        let responseSessionId: string | undefined
        try {
            if (refreshBeforeNextTurn.current) {
                try {
                    const refreshedSession = await getSession(refreshBeforeNextTurn.current, controller.signal)
                    if (!isCurrent()) return
                    setActiveSession(refreshedSession)
                    sessionId = refreshedSession.sessionId
                    refreshBeforeNextTurn.current = null
                } catch {
                    if (!isCurrent()) return
                    setErrorMessage('Unable to refresh the interrupted chat. Try again.')
                    return
                }
            }
            setDraft('')
            setErrorMessage('')
            setSources([])
            setGrounded(null)
            setStreamingTurn({question, answer: '', status: 'streaming'})
            await streamChat({question, workspaceId, sessionId}, {
                onAnswer: (delta) => {
                    if (isCurrent()) setStreamingTurn((current) => current ? {...current, answer: current.answer + delta} : current)
                },
                onMeta: (meta) => {
                    if (!isCurrent()) return
                    responseSessionId = meta.sessionId;
                    refreshBeforeNextTurn.current = meta.sessionId;
                    setSources(meta.sources);
                    setExpandedSourceIds(new Set())
                    setGrounded(meta.grounded)
                },
            }, controller.signal)
            if (!isCurrent()) return
            const availableSessions = await getSessions(workspaceId, controller.signal)
            if (!isCurrent()) return
            setSessions(availableSessions)
            if (responseSessionId) {
                const completedSession = await getSession(responseSessionId, controller.signal)
                if (!isCurrent()) return
                setActiveSession(completedSession)
                refreshBeforeNextTurn.current = null
            }
            if (isCurrent()) setStreamingTurn(null)
        } catch (error: unknown) {
            if (!isCurrent()) return
            if (error instanceof DOMException && error.name === 'AbortError') return
            setStreamingTurn((current) => current ? {...current, status: 'error'} : current)
            setErrorMessage(error instanceof ApiError && error.code === 'upstream_unavailable' ? 'The answer service is temporarily unavailable. Try again when you are ready.' : 'The answer stream could not be completed. Try again when you are ready.')
        } finally {
            if (streamController.current === controller) {
                streamController.current = null
                setIsSubmitting(false)
            }
        }
    }

    const selectedWorkspace = workspaces.find((workspace) => workspace.workspaceId === workspaceId)
    const chatTitle = activeSession?.title || (selectedWorkspace ? 'New chat' : 'Ask a question')
    const relatedImages = sources
        .flatMap((source) => source.assets.map((asset) => ({source, asset})))
        .filter((item, index, items) => item.asset.contentUrl && items.findIndex((candidate) => candidate.asset.assetId === item.asset.assetId) === index)

    return <main className="app-shell">
        <header className="topbar">
            <a className="brand" href="/" aria-label="Developer knowledge home">Developer knowledge</a>
            <div className="topbar-actions">
                {renderThemePicker('header')}
                <label className="workspace-picker"><span>Workspace</span><select aria-label="Workspace" disabled={workspaceStatus !== 'ready'} value={workspaceId} onChange={(event) => {
                    invalidateConversation();
                    setActiveSession(null);
                    refreshBeforeNextTurn.current = null;
                    setStreamingTurn(null);
                    setSources([]);
                    setGrounded(null);
                    setWorkspaceId(event.target.value)
                }}>
                    <option value="" disabled>{workspaceStatus === 'loading' ? 'Loading workspaces…' : 'Select a workspace'}</option>
                    {workspaces.map((workspace) => <option key={workspace.workspaceId} value={workspace.workspaceId}>{workspace.displayName}</option>)}
                </select></label>
                <button className="primary" type="button" disabled={!workspaceId} onClick={startNewChat}>New chat</button>
                <div className="profile-menu">
                    {signedOut ? <button type="button" disabled={accountBusy} onClick={() => void signIn()}>Sign in</button> : <button className="avatar" type="button" aria-haspopup="menu" aria-expanded={profileMenuOpen} aria-label="User menu" onClick={() => setProfileMenuOpen((open) => !open)}>{account?.profile.display_name.slice(0, 1) || 'U'}</button>}
                    {profileMenuOpen && <div className="profile-menu-panel" role="menu" aria-label="User menu">
                        <button type="button" role="menuitem" onClick={() => {setAccountPane('profile'); setProfileMenuOpen(false)}}>Profile</button>
                        <button type="button" role="menuitem" onClick={() => {setAccountPane('settings'); setProfileMenuOpen(false)}}>Settings</button>
                        <button type="button" role="menuitem" disabled={accountBusy} onClick={() => void signOut()}>Sign out</button>
                    </div>}
                </div>
            </div>
        </header>
        <section className="account-area" aria-label="Account" aria-busy={accountBusy}>
            {accountBusy && <p role="status">Loading account…</p>}
            {accountMessage && <p role="status">{accountMessage}</p>}
            {!signedOut && !accountBusy && (!accountReady || (account?.capabilities.preferences.read && !preferences) || (accountMessage && accountMessage !== 'Settings saved.')) && <button type="button" onClick={() => void loadAccount()}>Retry account</button>}
            {loginOptions && <div aria-label="Local test identities"><p>Choose a local test identity</p>{loginOptions.identities.map((choice) => <button type="button" key={choice.identity} disabled={accountBusy} onClick={() => void signIn(choice.identity)}>{choice.display_name}</button>)}</div>}
            {accountPane && <div className="account-panel" role="region" aria-label={accountPane === 'profile' ? 'Profile' : 'Settings'}>
                <div className="account-heading"><h2>{accountPane === 'profile' ? 'Profile' : 'Settings'}</h2><button type="button" disabled={accountBusy} onClick={() => void loadAccount()}>Refresh account</button><button type="button" onClick={() => setAccountPane(null)}>Close account panel</button></div>
                {accountPane === 'settings' && <section className="theme-settings" aria-label="Appearance settings">
                    {renderThemePicker('settings')}
                    <p className="muted">Account theme sync is not available yet.</p>
                </section>}
                {account && accountPane === 'profile' && <>
                    <dl><dt>Name</dt><dd dir="auto">{account.profile.display_name}</dd><dt>Email</dt><dd dir="auto">{account.profile.email || 'Not provided'}</dd></dl>
                    <p>Profile details and workspace roles are read-only.</p>
                    <h3>Workspace access</h3>{account.workspaces.length ? <ul>{account.workspaces.map((workspace) => <li key={workspace.workspace_id} dir="auto">{workspace.display_name} — {workspace.role}</li>)}</ul> : <p>No workspace memberships.</p>}
                    {account.capabilities.logout.supported ? <><p>Sign out ends this application session. Your Microsoft sign-in and other devices are unaffected.</p><button type="button" disabled={accountBusy} onClick={() => void signOut()}>Sign out of application</button></> : <p>{account.capabilities.logout.reason === 'fixed_local_identity' ? 'This fixed local development identity cannot sign out.' : 'Sign out is not configured for this application.'}</p>}
                </>}
                {account && accountPane === 'settings' && <>
                    <label>Recent chats<select aria-label="Account recent chat limit" value={recentChatLimit} disabled={accountBusy || !preferences || !account.capabilities.preferences.update || !account.capabilities.preferences.editable_fields.includes('recent_chat_limit')} onChange={(event) => void changeRecentChatLimit(Number(event.target.value))}>{account.capabilities.preferences.recent_chat_limit_options.map((limit) => <option key={limit} value={limit}>{limit}</option>)}</select></label>
                    <p>{preferences?.persistence === 'server' ? 'Saved to your account across workspaces and sign-ins.' : preferences?.persistence === 'process' ? 'Applies across workspaces until the backend process restarts.' : 'Saved preferences are currently unavailable.'}</p>
                    {!account.capabilities.preferences.update && <p>Settings changes are unsupported in this configuration.</p>}
                </>}
            </div>}
        </section>
        <section className="workspace" aria-label="Chat workspace">
            <DocumentsPanel key={`${authEpoch}:${workspaceId}`} workspaceId={workspaceId} onAccessDenied={(unauthenticated) => {
                invalidateConversation()
                setSources([])
                setGrounded(null)
                setStreamingTurn(null)
                if (unauthenticated) {
                    clearProtectedState()
                } else void recoverWorkspaceAccess()
            }}/>
            <section className="chat-pane" aria-label="Chat" aria-busy={isSubmitting}>
                <div className="chat-heading">
                    <div><p className="eyebrow">{selectedWorkspace?.displayName ?? 'Internal developer documentation'}</p><h1>{chatTitle}</h1></div>
                    <div className="heading-actions">{activeSession && <>
                        <button className="secondary" type="button" disabled={!accountReady} onClick={() => {
                            setRenameTitle(activeSession.title);
                            setIsRenaming(true)
                        }}>Rename
                        </button>
                        <button className="destructive" type="button" disabled={!accountReady} onClick={() => void archiveActiveSession()}>Archive chat</button>
                    </>}</div>
                </div>
                {isRenaming && activeSession && <form className="rename-form" aria-label="Rename chat" onSubmit={(event) => void submitRename(event)}><label htmlFor="session-title">Chat title</label>
                    <div><input id="session-title" value={renameTitle} onChange={(event) => setRenameTitle(event.target.value)} maxLength={200} autoFocus/>
                        <button type="submit" disabled={!accountReady || !renameTitle.trim()}>Save</button>
                        <button className="secondary" type="button" onClick={() => setIsRenaming(false)}>Cancel</button>
                    </div>
                </form>}
                <div className={activeSession ? 'conversation-view' : 'empty-state'} aria-live="polite">
                    {errorMessage ? <p className="error-message" role="alert">{errorMessage}</p> : null}
                    {workspaceStatus === 'error' && <button className="secondary" type="button" onClick={retryWorkspaceDiscovery}>Retry workspaces</button>}
                    {!workspaceId && <><h2>Choose a workspace to begin</h2><p>Answers will stream here with their supporting sources.</p></>}
                    {workspaceId && !activeSession && <><h2>Start a new chat</h2><p>Recent chats are available in the panel to the right.</p></>}
                    {activeSession && <>
                        <section className="history-summary" aria-labelledby="history-summary-heading"><h2 id="history-summary-heading">Earlier conversation summary</h2><p>{activeSession.summary ?? 'No earlier summary is available.'}</p></section>
                        <section className="recent-turns" aria-labelledby="recent-turns-heading"><h2 id="recent-turns-heading">Recent conversation</h2>{activeSession.turns.length === 0 ? <p className="muted">No recent messages are available.</p> :
                            <ol>{activeSession.turns.map((turn, index) => <li className={`turn turn-${turn.role}`} key={`${turn.createdAt}-${index}`}>
                                <div><strong>{turn.role === 'user' ? 'You' : 'Assistant'}</strong>{formatTimestamp(turn.createdAt) && <time dateTime={turn.createdAt}>{formatTimestamp(turn.createdAt)}</time>}</div>
                                <p>{turn.content}</p></li>)}</ol>}</section>
                    </>}
                    {streamingTurn && <section className="streaming-turns" aria-live="polite">
                        <div className="turn turn-user"><strong>You</strong><p>{streamingTurn.question}</p></div>
                        <div className="turn turn-assistant"><strong>Assistant</strong><p>{streamingTurn.answer || 'Thinking…'}</p>{streamingTurn.status === 'streaming' &&
                            <p className="muted" role="status">Streaming answer…</p>}{streamingTurn.status === 'cancelled' && <p className="muted" role="status">Answer stopped before completion.</p>}{streamingTurn.status === 'error' &&
                            <p className="error-message" role="alert">Answer incomplete.</p>}</div>
                    </section>}
                    {relatedImages.length > 0 && <section className="related-images" aria-labelledby="related-images-heading"><h2 id="related-images-heading">Related source images</h2>
                        <div>{relatedImages.map(({source, asset}) => <figure key={asset.assetId}><a href={asset.contentUrl ?? undefined} target="_blank" rel="noreferrer"><img src={asset.contentUrl ?? undefined}
                                                                                                                                                                               alt={asset.altText ?? asset.caption ?? `Image from ${source.title ?? source.sourcePath}`}
                                                                                                                                                                               loading="lazy"/></a>
                            <figcaption>{asset.caption ?? asset.altText ?? `Image from ${source.title ?? source.sourcePath}`}</figcaption>
                        </figure>)}</div>
                    </section>}
                </div>
                <form className="composer" onSubmit={(event) => void submitQuestion(event)}><label className="sr-only" htmlFor="question">Your question</label><textarea ref={composer} id="question" value={draft} onChange={(event) => setDraft(event.target.value)}
                                                                                                                                                                         disabled={!accountReady || !workspaceId || isSubmitting}
                                                                                                                                                                         placeholder="Ask about your developer documentation…"
                                                                                                                                                                         rows={3}/>{isSubmitting ?
                    <button className="secondary" type="button" onClick={() => cancelStream(true)}>Stop</button> : <button type="submit" disabled={!accountReady || !workspaceId || !draft.trim()}>Send</button>}</form>
            </section>
            <aside className="sessions-pane" aria-label="Recent chats">
                <div className="pane-tabs" aria-label="Workspace panels">
                    <button className={activePane === 'sessions' ? 'active' : ''} type="button" aria-pressed={activePane === 'sessions'} onClick={() => setActivePane('sessions')}>Recent chats</button>
                    <button className={activePane === 'sources' ? 'active' : ''} type="button" aria-pressed={activePane === 'sources'} onClick={() => setActivePane('sources')}>Sources</button>
                </div>
                {activePane === 'sources' && <div aria-live="polite">{grounded === false && <p className="muted">This answer was not grounded in retrieved sources.</p>}{sources.length === 0 && grounded !== false &&
                    <p className="muted">No sources are available yet.</p>}{sources.length > 0 && <ol className="source-list">{sources.map((source, index) => {
                    const sourceId = `source-${index}`
                    const contentId = `source-details-${index}`
                    const isExpanded = expandedSourceIds.has(sourceId)
                    return <li key={source.chunkId} className={isExpanded ? 'source-item expanded' : 'source-item'}>
                        <button className="source-toggle" type="button" aria-expanded={isExpanded} aria-controls={contentId} onClick={() => toggleSource(sourceId)}>
                            <span className="source-title">{source.title ?? source.sourcePath}</span><span className="source-chevron" aria-hidden="true"/>
                        </button>
                        <div id={contentId} className="source-details" aria-hidden={!isExpanded}><div className="source-details-inner">
                            <span>{source.sourcePath}{source.section ? ` · ${source.section}` : ''}{source.page !== null ? ` · Page ${source.page}` : ''}</span>{source.snippet &&
                            <p>{source.snippet}</p>}{source.assets.filter((asset) => asset.contentUrl).map((asset) => <figure key={asset.assetId}><a href={asset.contentUrl ?? undefined} target="_blank" rel="noreferrer" tabIndex={isExpanded ? 0 : -1}><img
                            src={asset.contentUrl ?? undefined} alt={asset.altText ?? asset.caption ?? `Image from ${source.title ?? source.sourcePath}`} loading="lazy"/></a>{(asset.caption || asset.altText) &&
                            <figcaption>{asset.caption ?? asset.altText}</figcaption>}</figure>)}</div></div>
                    </li>
                })}</ol>}</div>}
                {activePane === 'sessions' && !workspaceId && <p className="muted">Select a workspace to view recent chats.</p>}
                {activePane === 'sessions' && workspaceId && <label className="recent-chat-limit">Show recent chats
                    <select aria-label="Number of recent chats" value={recentChatLimit} disabled={accountBusy || !preferences || !account?.capabilities.preferences.update} onChange={(event) => void changeRecentChatLimit(Number(event.target.value))}>{(account?.capabilities.preferences.recent_chat_limit_options ?? [10, 20, 50, 100]).map((limit) => <option key={limit} value={limit}>{limit}</option>)}</select>
                </label>}
                {activePane === 'sessions' && workspaceId && sessionsStatus === 'loading' && <p className="muted">Loading recent chats…</p>}
                {activePane === 'sessions' && workspaceId && sessionsStatus === 'error' && <button className="secondary" type="button" onClick={retrySessions}>Retry recent chats</button>}
                {activePane === 'sessions' && workspaceId && sessionsStatus === 'ready' && sessions.length === 0 && <p className="muted">No recent chats in this workspace.</p>}
                {activePane === 'sessions' && sessions.length > 0 && <ul className="session-list">{sessions.slice(0, recentChatLimit).map((session) => <li key={session.sessionId}>
                    <button className={activeSession?.sessionId === session.sessionId ? 'session active-session' : 'session'} type="button" aria-current={activeSession?.sessionId === session.sessionId ? 'page' : undefined}
                            onClick={() => void selectSession(session)}><span>{session.title}</span>{session.preview && <small>{session.preview}</small>}</button>
                </li>)}</ul>}
            </aside>
        </section>
    </main>
}
