import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, FlaskConical, FileText, LayoutDashboard, Clock, Info, Menu, X } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { TabName } from '../../types'

const NAV_ITEMS: { id: TabName; label: string; icon: React.ElementType; accent: string; activeBg: string }[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    accent: 'text-slate-300',
    activeBg: 'bg-slate-800/80',
  },
  {
    id: 'search',
    label: 'Search',
    icon: Search,
    accent: 'text-cyan-400',
    activeBg: 'bg-cyan-950/40 border-cyan-800/30',
  },
  {
    id: 'research',
    label: 'Research',
    icon: FlaskConical,
    accent: 'text-fuchsia-400',
    activeBg: 'bg-fuchsia-950/40 border-fuchsia-800/30',
  },
  {
    id: 'extract',
    label: 'Extract',
    icon: FileText,
    accent: 'text-amber-400',
    activeBg: 'bg-amber-950/40 border-amber-800/30',
  },
  {
    id: 'histories',
    label: 'Histories',
    icon: Clock,
    accent: 'text-slate-300',
    activeBg: 'bg-slate-800/80',
  },
  {
    id: 'info',
    label: 'Info',
    icon: Info,
    accent: 'text-slate-300',
    activeBg: 'bg-slate-800/80',
  },
]

interface NavbarProps {
  activeTab: TabName
  onTabChange: (tab: TabName) => void
  searchRuns: number
  researchRuns: number
  extractRuns: number
  username?: string
  onAuthOpen: () => void
  onLogout: () => void
}

export function Navbar({ activeTab, onTabChange, searchRuns, researchRuns, extractRuns, username, onAuthOpen, onLogout }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      {/* Top navbar */}
      <header className="sticky top-0 z-40">
        <div className="glass border-b border-white/[0.06] px-4 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
            {/* Logo */}
            <div className="flex items-center gap-2.5 shrink-0">
              <div className="relative p-[2px] rounded-full bg-gradient-to-br from-cyan-500 via-fuchsia-500 to-cyan-400 shadow-lg shadow-cyan-900/40">
                <div className="w-8 h-8 rounded-full overflow-hidden bg-slate-950 flex items-center justify-center">
                  <img
                    src="/pressivox_logo.png"
                    alt="Pressivox"
                    className="w-full h-full object-contain p-0.5"
                  />
                </div>
              </div>
              <div className="hidden sm:block">
                <span className="font-display font-semibold tracking-wide text-slate-100">Pressivox</span>
              </div>
            </div>

            {/* Desktop nav pills */}
            <nav className="hidden lg:flex items-center gap-1 bg-slate-900/60 border border-white/[0.06] rounded-2xl p-1">
              {NAV_ITEMS.map(({ id, label, icon: Icon, accent }) => {
                const isActive = activeTab === id
                return (
                  <button
                    key={id}
                    onClick={() => onTabChange(id)}
                    aria-current={isActive ? 'page' : undefined}
                    className={cn(
                      'relative flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-medium transition-all duration-200',
                      isActive
                        ? cn('text-white', id === 'search' ? 'text-cyan-300' : id === 'research' ? 'text-fuchsia-300' : id === 'extract' ? 'text-amber-300' : 'text-slate-200')
                        : 'text-slate-500 hover:text-slate-300',
                    )}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="navbar-pill"
                        className="absolute inset-0 rounded-xl bg-slate-800/80 border border-white/[0.08]"
                        transition={{ type: 'spring', stiffness: 400, damping: 34 }}
                      />
                    )}
                    <Icon className={cn('relative z-10 w-3.5 h-3.5 shrink-0', isActive ? accent : '')} />
                    <span className="relative z-10">{label}</span>
                  </button>
                )
              })}
            </nav>

            {/* Session stats pill (desktop) */}
            <div className="hidden lg:flex items-center gap-3 px-4 py-2 rounded-2xl bg-slate-900/60 border border-white/[0.06] text-xs text-slate-500">
              <span><span className="text-cyan-400 font-semibold">{searchRuns}</span> searches</span>
              <span className="w-px h-3 bg-slate-700" />
              <span><span className="text-fuchsia-400 font-semibold">{researchRuns}</span> research</span>
              <span className="w-px h-3 bg-slate-700" />
              <span><span className="text-amber-400 font-semibold">{extractRuns}</span> extracts</span>
            </div>

            <div className="hidden lg:flex items-center gap-2">
              {username ? (
                <>
                  <span className="text-xs text-slate-400">@{username}</span>
                  <button
                    onClick={onLogout}
                    className="px-3 py-1.5 rounded-xl border border-white/[0.08] text-xs text-slate-300 hover:text-white hover:bg-slate-800/70 transition"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <button
                  onClick={onAuthOpen}
                  className="px-3 py-1.5 rounded-xl border border-cyan-800/50 bg-cyan-950/40 text-xs text-cyan-300 hover:text-cyan-200 hover:bg-cyan-900/50 transition"
                >
                  Sign in
                </button>
              )}
            </div>

            {/* Mobile menu button */}
            <button
              className="lg:hidden p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition"
              onClick={() => setMobileOpen(v => !v)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile menu overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18 }}
            className="fixed inset-x-0 top-[57px] z-30 lg:hidden"
          >
            <div className="glass border-b border-white/[0.06] px-4 py-3">
              <nav className="flex flex-col gap-1">
                {NAV_ITEMS.map(({ id, label, icon: Icon, accent }) => {
                  const isActive = activeTab === id
                  return (
                    <button
                      key={id}
                      onClick={() => { onTabChange(id); setMobileOpen(false) }}
                      aria-current={isActive ? 'page' : undefined}
                      className={cn(
                        'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition',
                        isActive
                          ? 'bg-slate-800/80 border border-white/[0.08] text-slate-100'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40',
                      )}
                    >
                      <Icon className={cn('w-4 h-4 shrink-0', isActive ? accent : 'text-slate-500')} />
                      {label}
                    </button>
                  )
                })}
              </nav>

              {/* Mobile session stats */}
              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-white/[0.06] text-xs text-slate-500">
                <span><span className="text-cyan-400 font-semibold">{searchRuns}</span> searches</span>
                <span><span className="text-fuchsia-400 font-semibold">{researchRuns}</span> research</span>
                <span><span className="text-amber-400 font-semibold">{extractRuns}</span> extracts</span>
              </div>

              <div className="mt-3 flex items-center justify-between text-xs">
                {username ? (
                  <>
                    <span className="text-slate-400">@{username}</span>
                    <button
                      onClick={() => { onLogout(); setMobileOpen(false) }}
                      className="px-3 py-1.5 rounded-xl border border-white/[0.08] text-slate-300 hover:text-white hover:bg-slate-800/70 transition"
                    >
                      Log out
                    </button>
                  </>
                ) : (
                  <>
                    <span className="text-slate-500">Guest mode</span>
                    <button
                      onClick={() => { onAuthOpen(); setMobileOpen(false) }}
                      className="px-3 py-1.5 rounded-xl border border-cyan-800/50 bg-cyan-950/40 text-cyan-300 hover:text-cyan-200 hover:bg-cyan-900/50 transition"
                    >
                      Sign in
                    </button>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
