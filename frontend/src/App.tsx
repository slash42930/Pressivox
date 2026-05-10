import { useState, useCallback, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { X as CloseIcon } from 'lucide-react'
import { useLenis } from './hooks/useLenis'
import { apiClient } from './api/client'
import { ToastProvider } from './components/Toast'
import { AnimatedBackground } from './components/effects/AnimatedBackground'
import { Navbar } from './components/layout/Navbar'
import { Input } from './components/ui/Input'
import { Button } from './components/ui/Button'
import { Card } from './components/ui/Card'
import type { AuthUser, TabName, SessionStats, SearchResponse, ResearchResponse } from './types'
import { Dashboard } from './sections/Dashboard'
import { SearchSection } from './sections/Search'
import { ResearchSection } from './sections/Research'
import { ExtractSection } from './sections/Extract'
import { HistoriesSection } from './sections/Histories'
import { InfoSection } from './sections/InfoSection'

function initialStats(): SessionStats {
  return {
    searchRuns: 0,
    researchRuns: 0,
    extractRuns: 0,
    compareCount: 0,
    lastQuery: '',
    lastSearchSnap: null,
    lastResearchSnap: null,
  }
}

const tabVariants = {
  initial: { opacity: 0, y: 12, scale: 0.99 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -8, scale: 0.99 },
}

function AuthGate({
  onAuthenticated,
  onClose,
  compact = false,
}: {
  onAuthenticated: (user: AuthUser) => void
  onClose?: () => void
  compact?: boolean
}) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!username.trim() || !password.trim()) {
      setError('Username and password are required.')
      return
    }

    setLoading(true)
    setError('')
    try {
      const data = mode === 'login'
        ? await apiClient.login(username, password)
        : await apiClient.register(username, password, fullName || undefined)
      onAuthenticated(data.user)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const content = (
    <Card className="w-full max-w-md rounded-3xl p-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <img
            src="/pressivox_logo.png"
            alt="Pressivox"
            className="w-10 h-10 rounded-xl object-cover border border-white/[0.12]"
          />
          <div>
          <h1 className="font-display text-2xl font-bold text-slate-100">Pressivox Access</h1>
          <p className="text-sm text-slate-400 mt-1">
            {mode === 'login' ? 'Sign in to continue.' : 'Create an account to start searching.'}
          </p>
          </div>
        </div>
        {onClose && (
          <button
            className="rounded-lg border border-white/[0.12] p-1.5 text-slate-400 hover:bg-slate-800/70 hover:text-white transition"
            onClick={onClose}
            aria-label="Close sign in"
          >
            <CloseIcon className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

        {error && (
          <div className="rounded-xl border border-red-800/60 bg-red-950/60 px-3 py-2 text-sm text-red-200">{error}</div>
        )}

        <div className="space-y-3">
          <Input
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Username"
            autoComplete="username"
          />
          <Input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Password"
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          />
          {mode === 'register' && (
            <Input
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              placeholder="Full name (optional)"
              autoComplete="name"
            />
          )}
        </div>

        <div className="space-y-2">
          <Button className="w-full" onClick={handleSubmit} disabled={loading}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </Button>
          <button
            className="w-full text-sm text-slate-400 hover:text-slate-200 transition"
            onClick={() => {
              setMode(prev => (prev === 'login' ? 'register' : 'login'))
              setError('')
            }}
          >
            {mode === 'login' ? 'Need an account? Register' : 'Already have an account? Sign in'}
          </button>
        </div>
    </Card>
  )

  if (compact) {
    return content
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      {content}
    </div>
  )
}

function AuthModal({ onAuthenticated, onClose }: { onAuthenticated: (user: AuthUser) => void; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4" onClick={onClose}>
      <div className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <AuthGate
          onAuthenticated={(user) => {
            onAuthenticated(user)
            onClose()
          }}
          onClose={onClose}
          compact
        />
      </div>
    </div>
  )
}

export default function App() {
  useLenis()

  const [activeTab, setActiveTab] = useState<TabName>('dashboard')
  const [stats, setStats] = useState<SessionStats>(initialStats)

  const [searchInitialQuery, setSearchInitialQuery] = useState<string | undefined>(undefined)
  const [researchInitialQuery, setResearchInitialQuery] = useState<string | undefined>(undefined)
  const [extractInitialUrl, setExtractInitialUrl] = useState<string | undefined>(undefined)
  const [authUser, setAuthUser] = useState<AuthUser | null>(null)
  const [authDialogOpen, setAuthDialogOpen] = useState(false)

  const handleTabChange = useCallback((tab: TabName) => {
    if (tab === 'histories' && !authUser) {
      setAuthDialogOpen(true)
      return
    }
    setActiveTab(tab)
  }, [authUser])

  useEffect(() => {
    const bootstrapAuth = async () => {
      const stored = apiClient.getStoredUser()
      if (!stored) {
        return
      }

      try {
        const me = await apiClient.me()
        setAuthUser(me)
      } catch {
        apiClient.logout()
      }
    }

    void bootstrapAuth()
  }, [])

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== '/') return
      const tag = (e.target as HTMLElement).tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
      e.preventDefault()
      setActiveTab('search')
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const navigate = useCallback((tab: string, query?: string, _kind?: string) => {
    const t = tab as TabName
    if (t === 'histories' && !authUser) {
      setAuthDialogOpen(true)
      return
    }
    if (t === 'search' && query) setSearchInitialQuery(query)
    if (t === 'research' && query) setResearchInitialQuery(query)
    if (t === 'extract' && query) setExtractInitialUrl(query)
    setActiveTab(t)
  }, [authUser])

  const onSearchComplete = useCallback((response: SearchResponse) => {
    setStats(prev => ({
      ...prev,
      searchRuns: prev.searchRuns + 1,
      lastSearchSnap: response,
      lastQuery: response.query,
    }))
  }, [])

  const onResearchComplete = useCallback((response: ResearchResponse) => {
    setStats(prev => ({
      ...prev,
      researchRuns: prev.researchRuns + 1,
      lastResearchSnap: response,
      lastQuery: response.query,
    }))
  }, [])

  const onExtractComplete = useCallback(() => {
    setStats(prev => ({ ...prev, extractRuns: prev.extractRuns + 1 }))
  }, [])

  const handleLogout = useCallback(() => {
    apiClient.logout()
    setAuthUser(null)
  }, [])

  return (
    <ToastProvider>
      <AnimatedBackground />

      <div className="min-h-screen text-slate-100 flex flex-col">
        <Navbar
          activeTab={activeTab}
          onTabChange={handleTabChange}
          searchRuns={stats.searchRuns}
          researchRuns={stats.researchRuns}
          extractRuns={stats.extractRuns}
          username={authUser?.username}
          onAuthOpen={() => setAuthDialogOpen(true)}
          onLogout={handleLogout}
        />

        <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
          <AnimatePresence mode="wait">
            {activeTab === 'dashboard' && (
              <motion.div key="dashboard" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.22 }}>
                <Dashboard
                  searchRuns={stats.searchRuns}
                  researchRuns={stats.researchRuns}
                  extractRuns={stats.extractRuns}
                  compareCount={stats.compareCount}
                  lastSearchSnap={stats.lastSearchSnap}
                  lastResearchSnap={stats.lastResearchSnap}
                  onNavigate={navigate}
                />
              </motion.div>
            )}
            {activeTab === 'search' && (
              <motion.div key="search" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.22 }}>
                <SearchSection initialQuery={searchInitialQuery} onSearchComplete={onSearchComplete} />
              </motion.div>
            )}
            {activeTab === 'research' && (
              <motion.div key="research" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.22 }}>
                <ResearchSection initialQuery={researchInitialQuery} onResearchComplete={onResearchComplete} />
              </motion.div>
            )}
            {activeTab === 'extract' && (
              <motion.div key="extract" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.22 }}>
                <ExtractSection initialUrl={extractInitialUrl} onExtractComplete={onExtractComplete} />
              </motion.div>
            )}
            {activeTab === 'histories' && (
              <motion.div key="histories" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.22 }}>
                <HistoriesSection />
              </motion.div>
            )}
            {activeTab === 'info' && (
              <motion.div key="info" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.22 }}>
                <InfoSection />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* Footer */}
        <footer className="border-t border-white/[0.04] px-4 py-4 text-center text-xs text-slate-600">
          Web Search Workspace · Press{' '}
          <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px]">/</kbd>{' '}
          to jump to Search · {authUser ? `Signed in as @${authUser.username}` : 'Guest mode (sign in optional)'}
        </footer>
      </div>

      {authDialogOpen && (
        <AuthModal
          onAuthenticated={setAuthUser}
          onClose={() => setAuthDialogOpen(false)}
        />
      )}
    </ToastProvider>
  )
}
