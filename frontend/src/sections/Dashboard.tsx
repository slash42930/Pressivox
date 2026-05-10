import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw, Search, FlaskConical, FileText, TrendingUp, Globe, X } from 'lucide-react'
import { apiClient } from '../api/client'
import type { SearchResponse, ResearchResponse, SearchResult } from '../types'
import { Favicon } from '../components/Favicon'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { SpotlightCard } from '../components/effects/AnimatedBackground'
import { GradientText } from '../components/effects/TypewriterText'
import {
  ROMANIAN_NEWS_DOMAINS,
  getTrustedSitesForTopic,
} from '../data/trusted-sites'
import { formatPublishedDate, pickTopWeeklyHeadlines } from '../utils'

const QUICK_CHIPS = [
  { label: 'AI', query: 'artificial intelligence news' },
  { label: 'Technology', query: 'technology news' },
  { label: 'Science', query: 'science breakthroughs' },
  { label: 'Business', query: 'business news today' },
  { label: 'Climate', query: 'climate change latest' },
  { label: 'Health', query: 'health and medicine news' },
  { label: 'Space', query: 'space exploration news' },
  { label: 'Security', query: 'cybersecurity threats' },
]

const PRESETS = [
  {
    label: 'AI overview',
    description: 'Research AI using Wikipedia as source',
    kind: 'research' as const,
    query: 'artificial intelligence',
    topic: 'general' as const,
    include: 'wikipedia.org',
    color: 'fuchsia' as const,
  },
  {
    label: 'Latest AI news',
    description: 'Search the freshest AI headlines',
    kind: 'search' as const,
    query: 'latest AI news',
    topic: 'news' as const,
    color: 'cyan' as const,
  },
  {
    label: 'Extract one page',
    description: 'Read and extract any Wikipedia article',
    kind: 'extract' as const,
    url: 'https://en.wikipedia.org/wiki/Artificial_intelligence',
    color: 'amber' as const,
  },
]

interface DashboardProps {
  searchRuns: number
  researchRuns: number
  extractRuns: number
  compareCount: number
  lastSearchSnap: SearchResponse | null
  lastResearchSnap: ResearchResponse | null
  onNavigate: (tab: string, query?: string, kind?: string) => void
}

interface TopNewsState {
  english: (SearchResult & { _dashboardDomain: string })[]
  romanian: (SearchResult & { _dashboardDomain: string })[]
  lastUpdated: string
  loading: boolean
  error: string
}

async function fetchWeeklyHeadlines(language: 'english' | 'romanian') {
  const isRomanian = language === 'romanian'
  const includeDomains = isRomanian
    ? ROMANIAN_NEWS_DOMAINS
    : getTrustedSitesForTopic('news', 'global world weekly headlines', 60)
  const query = isRomanian
    ? 'cele mai importante stiri ale saptamanii in lume'
    : 'top world news of the week'

  const payload = {
    query,
    topic: 'news' as const,
    language,
    max_results: 12,
    summarize: false,
    extract_top_results: false,
    include_domains: includeDomains,
    exclude_domains: [],
    search_depth: 'advanced' as const,
    include_answer: false,
    include_raw_content: false,
    include_images: false,
    include_image_descriptions: false,
    include_favicon: true,
    exact_match: false,
    time_range: 'week',
    start_date: null,
    end_date: null,
    auto_parameters: true,
  }
  const data = await apiClient.search(payload)
  return pickTopWeeklyHeadlines(Array.isArray(data.results) ? data.results : [], language, 3)
}

const presetColorMap = {
  cyan: 'border-cyan-800/30 hover:border-cyan-500/40 bg-cyan-950/20',
  fuchsia: 'border-fuchsia-800/30 hover:border-fuchsia-500/40 bg-fuchsia-950/20',
  amber: 'border-amber-800/30 hover:border-amber-500/40 bg-amber-950/20',
}

const presetLabelColor = {
  cyan: 'text-cyan-300',
  fuchsia: 'text-fuchsia-300',
  amber: 'text-amber-300',
}

export function Dashboard({
  searchRuns,
  researchRuns,
  extractRuns,
  compareCount,
  lastSearchSnap,
  lastResearchSnap,
  onNavigate,
}: DashboardProps) {
  const [quickQuery, setQuickQuery] = useState('')
  const [activeChip, setActiveChip] = useState<string | null>(null)
  const [topNews, setTopNews] = useState<TopNewsState>({
    english: [],
    romanian: [],
    lastUpdated: '',
    loading: true,
    error: '',
  })
  const [status, setStatus] = useState('Ready.')

  const loadTopNews = useCallback(async () => {
    setTopNews(prev => ({ ...prev, loading: true, error: '' }))
    setStatus('Refreshing weekly top news...')
    try {
      const [english, romanian] = await Promise.all([
        fetchWeeklyHeadlines('english'),
        fetchWeeklyHeadlines('romanian'),
      ])
      setTopNews({
        english,
        romanian,
        lastUpdated: new Date().toLocaleString(),
        loading: false,
        error: '',
      })
      setStatus('Top weekly news refreshed (EN + RO).')
    } catch (err) {
      const msg = `Top weekly news refresh failed: ${(err as Error).message}`
      setTopNews(prev => ({ ...prev, english: [], romanian: [], lastUpdated: '', loading: false, error: msg }))
      setStatus(msg)
    }
  }, [])

  useEffect(() => { loadTopNews() }, [loadTopNews])

  const handleQuickSearch = () => { const q = quickQuery.trim(); if (!q) return; onNavigate('search', q) }
  const handleQuickResearch = () => { const q = quickQuery.trim(); if (!q) return; onNavigate('research', q) }
  const handleChipAction = (kind: 'search' | 'research') => { if (!activeChip) return; onNavigate(kind, activeChip, kind); setActiveChip(null) }

  return (
    <div className="space-y-6">
      {/* ── Hero search bar ── */}
      <SpotlightCard className="rounded-3xl overflow-hidden">
        <div className="relative rounded-3xl border border-white/[0.08] bg-gradient-to-br from-slate-900 via-slate-900/95 to-cyan-950/20 p-8">
          {/* subtle top accent line */}
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent" />

          <div className="mb-6">
            <h2 className="font-display text-3xl font-bold tracking-tight text-slate-100 mb-2">
              What do you want to <GradientText>know?</GradientText>
            </h2>
            <p className="text-slate-400 text-sm">
              Search or research any topic — results appear instantly.
            </p>
          </div>

          <div className="flex gap-3 flex-wrap sm:flex-nowrap mb-5">
            <Input
              value={quickQuery}
              onChange={e => setQuickQuery(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleQuickSearch() }}
              className="flex-1 min-w-0 h-12 text-base px-5 rounded-2xl"
              placeholder="e.g. latest AI news, climate change, quantum computing…"
              icon={<Search className="w-4 h-4" />}
            />
            <Button
              variant="default"
              size="lg"
              onClick={handleQuickSearch}
              className="whitespace-nowrap shrink-0 rounded-2xl shadow-lg"
            >
              <Search className="w-4 h-4" />
              Search
            </Button>
            <Button
              variant="fuchsia"
              size="lg"
              onClick={handleQuickResearch}
              className="whitespace-nowrap shrink-0 rounded-2xl shadow-lg"
            >
              <FlaskConical className="w-4 h-4" />
              Research
            </Button>
          </div>

          {/* Topic chips */}
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-slate-500 self-center">Quick topics:</span>
            {QUICK_CHIPS.map(chip => (
              <button
                key={chip.query}
                onClick={() => setActiveChip(prev => prev === chip.query ? null : chip.query)}
                className={`rounded-full border px-3.5 py-1 text-xs font-medium transition-all duration-200 ${
                  activeChip === chip.query
                    ? 'border-cyan-500/60 text-cyan-300 bg-cyan-950/40 shadow-sm shadow-cyan-500/20'
                    : 'border-white/[0.08] text-slate-400 bg-slate-800/40 hover:border-cyan-500/30 hover:text-slate-200'
                }`}
              >
                {chip.label}
              </button>
            ))}
          </div>

          <AnimatePresence>
            {activeChip && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.22 }}
                className="overflow-hidden"
              >
                <div className="flex items-center gap-3 mt-4 pt-4 border-t border-white/[0.06]">
                  <span className="text-sm text-slate-400">
                    Run <strong className="text-white">{QUICK_CHIPS.find(c => c.query === activeChip)?.label}</strong> as:
                  </span>
                  <Button size="sm" variant="default" onClick={() => handleChipAction('search')} className="rounded-full">
                    Search
                  </Button>
                  <Button size="sm" variant="fuchsia" onClick={() => handleChipAction('research')} className="rounded-full">
                    Research
                  </Button>
                  <button onClick={() => setActiveChip(null)} className="ml-auto p-1 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </SpotlightCard>

      {/* ── Session stats bento row ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Searches', value: searchRuns, icon: <Search className="w-4 h-4" />, color: 'text-cyan-400', iconBg: 'bg-cyan-950/60 border-cyan-800/30', accent: 'from-cyan-500/8' },
          { label: 'Research', value: researchRuns, icon: <FlaskConical className="w-4 h-4" />, color: 'text-fuchsia-400', iconBg: 'bg-fuchsia-950/60 border-fuchsia-800/30', accent: 'from-fuchsia-500/8' },
          { label: 'Extracts', value: extractRuns, icon: <FileText className="w-4 h-4" />, color: 'text-amber-400', iconBg: 'bg-amber-950/60 border-amber-800/30', accent: 'from-amber-500/8' },
          { label: 'Compared', value: compareCount, icon: <TrendingUp className="w-4 h-4" />, color: 'text-emerald-400', iconBg: 'bg-emerald-950/60 border-emerald-800/30', accent: 'from-emerald-500/8' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05, duration: 0.3 }}
          >
            <Card className="relative overflow-hidden p-4">
              <div className={`absolute inset-x-0 top-0 h-px bg-gradient-to-r ${stat.accent} to-transparent`} />
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">{stat.label}</span>
                <div className={`w-8 h-8 rounded-lg border flex items-center justify-center ${stat.iconBg} ${stat.color}`}>
                  {stat.icon}
                </div>
              </div>
              <div className={`font-display text-3xl font-bold ${stat.color}`}>{stat.value}</div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* ── Last snapshots + Quick start ── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Last search */}
        <Card glow="cyan" className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="font-display font-semibold text-slate-100">Last Search</div>
            <Button variant="ghost" size="sm" onClick={() => onNavigate('search')} className="text-cyan-400 hover:text-cyan-300 text-xs">
              Open →
            </Button>
          </div>
          {lastSearchSnap ? (
            <div>
              <Badge variant="cyan" className="mb-3">{lastSearchSnap.query}</Badge>
              <div className="space-y-2">
                {lastSearchSnap.results.slice(0, 3).map((item, i) => (
                  <div key={i} className="rounded-xl bg-slate-950/60 border border-white/[0.05] px-3 py-2">
                    <a href={item.url} target="_blank" rel="noopener noreferrer"
                      className="text-sm font-medium text-cyan-300 hover:text-cyan-200 line-clamp-1 block transition">
                      {item.title || 'Untitled'}
                    </a>
                    <div className="text-xs text-slate-500 mt-0.5">{item.source || ''}</div>
                  </div>
                ))}
              </div>
              <div className="text-xs text-slate-500 mt-3">{lastSearchSnap.results.length} results</div>
            </div>
          ) : (
            <div className="text-sm text-slate-500 italic">No search run yet this session.</div>
          )}
        </Card>

        {/* Last research */}
        <Card glow="fuchsia" className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="font-display font-semibold text-slate-100">Last Research</div>
            <Button variant="ghost" size="sm" onClick={() => onNavigate('research')} className="text-fuchsia-400 hover:text-fuchsia-300 text-xs">
              Open →
            </Button>
          </div>
          {lastResearchSnap ? (
            <div>
              <Badge variant="fuchsia" className="mb-3">{lastResearchSnap.query}</Badge>
              {lastResearchSnap.summary && (
                <p className="text-slate-300 text-sm leading-relaxed mb-3 line-clamp-3">
                  {lastResearchSnap.summary}
                </p>
              )}
              {lastResearchSnap.summary_points.slice(0, 3).map((p, i) => (
                <div key={i} className="flex gap-2 text-sm text-slate-400 mb-1.5">
                  <span className="mt-2 w-1 h-1 rounded-full bg-fuchsia-400 shrink-0" />
                  <span className="line-clamp-1">{p}</span>
                </div>
              ))}
              <div className="text-xs text-slate-500 mt-3">
                {lastResearchSnap.selected_sources.length} sources · {lastResearchSnap.source_count} results
              </div>
            </div>
          ) : (
            <div className="text-sm text-slate-500 italic">No research run yet this session.</div>
          )}
        </Card>

        {/* Quick start */}
        <Card className="p-6">
          <div className="font-display font-semibold text-slate-100 mb-1">Quick Start</div>
          <p className="text-sm text-slate-500 mb-4">Jump into common workflows.</p>
          <div className="space-y-2">
            {PRESETS.map(preset => (
              <SpotlightCard
                key={preset.label}
                spotlightColor={
                  preset.color === 'cyan' ? 'rgba(6,182,212,0.06)'
                  : preset.color === 'fuchsia' ? 'rgba(192,38,211,0.06)'
                  : 'rgba(245,158,11,0.06)'
                }
                className="rounded-xl"
              >
                <button
                  onClick={() => {
                    if (preset.kind === 'extract' && 'url' in preset) {
                      onNavigate('extract', preset.url, 'extract')
                    } else if ('query' in preset) {
                      onNavigate(preset.kind, preset.query, preset.kind)
                    }
                  }}
                  className={`w-full rounded-xl border p-3.5 text-left transition-all duration-200 ${presetColorMap[preset.color]}`}
                >
                  <div className={`font-medium text-sm mb-0.5 ${presetLabelColor[preset.color]}`}>{preset.label}</div>
                  <div className="text-xs text-slate-500">{preset.description}</div>
                </button>
              </SpotlightCard>
            ))}
          </div>
          <div className="mt-4 rounded-xl bg-slate-950/60 border border-white/[0.05] px-3 py-2.5 text-xs text-slate-500 font-mono">
            {status}
          </div>
        </Card>
      </div>

      {/* ── Top News of the Week ── */}
      <Card className="p-6">
        <div className="flex items-center justify-between gap-4 mb-1">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-slate-400" />
            <span className="font-display font-semibold text-slate-100">Top News of the Week</span>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={loadTopNews}
            disabled={topNews.loading}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${topNews.loading ? 'animate-spin' : ''}`} />
            {topNews.loading ? 'Loading…' : 'Refresh'}
          </Button>
        </div>
        <div className="text-xs text-slate-500 mb-5">
          {topNews.error ? topNews.error : topNews.lastUpdated ? `Updated ${topNews.lastUpdated}` : 'Loading headlines…'}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {(['english', 'romanian'] as const).map(lang => (
            <div key={lang}>
              <div className="flex items-center gap-2 mb-3">
                <Badge variant={lang === 'english' ? 'cyan' : 'fuchsia'}>
                  {lang === 'english' ? 'English' : 'Romanian'}
                </Badge>
              </div>
              <div className="space-y-2">
                {topNews[lang].length === 0 ? (
                  <div className="text-sm text-slate-500 italic">
                    {topNews.loading ? 'Loading…' : 'No headlines found.'}
                  </div>
                ) : (
                  topNews[lang].map((item, i) => (
                    <SpotlightCard key={i} spotlightColor="rgba(6,182,212,0.05)" className="rounded-xl">
                      <div className="rounded-xl border border-white/[0.05] bg-slate-950/40 p-3 hover:border-cyan-500/20 transition-colors">
                        <div className="text-[10px] text-slate-600 mb-1">#{i + 1}</div>
                        <a href={item.url} target="_blank" rel="noopener noreferrer"
                          className="text-sm font-medium text-slate-200 hover:text-cyan-300 line-clamp-2 block transition leading-snug">
                          {item.title || 'Untitled'}
                        </a>
                        <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                          <Favicon favicon={item.favicon} className="w-3.5 h-3.5" />
                          <span>{item._dashboardDomain}</span>
                          {item.published_date && (
                            <span className="text-slate-600">· {formatPublishedDate(item.published_date)}</span>
                          )}
                        </div>
                      </div>
                    </SpotlightCard>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
