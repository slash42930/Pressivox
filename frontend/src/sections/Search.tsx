import { useState, useCallback, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Sparkles, SlidersHorizontal, Calendar, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { apiClient } from '../api/client'
import { useToast } from '../components/Toast'
import { ProgressBar } from '../components/ProgressBar'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { Label } from '../components/ui/Label'
import { SkeletonResultCard } from '../components/ui/Skeleton'
import { SpotlightCard } from '../components/effects/AnimatedBackground'
import type { SearchResponse, SearchResult, QueryAnalysisResponse } from '../types'
import { SearchCards } from '../components/SearchCards'
import { SelectedSources } from '../components/SelectedSources'
import { MeaningGroups } from '../components/MeaningGroups'
import { ComparePanel } from '../components/ComparePanel'
import { EmptyState } from '../components/EmptyState'
import { copyToClipboard, sortResults, type SortMode } from '../utils'
import { buildSearchPayload, type SearchPayloadFormValues } from '../utils/searchPayload'
import { toggleCompareItems } from '../utils/compare'
import { useAsyncAction } from '../hooks/useAsyncAction'

interface SearchForm extends SearchPayloadFormValues {}

interface SearchSectionProps {
  initialQuery?: string
  onSearchComplete: (response: SearchResponse) => void
}

function defaultInclude(topic: string, language: string): string {
  const normalizedTopic = topic.toLowerCase()
  if (language === 'romanian') {
    return normalizedTopic === 'news' ? 'hotnews.ro,digi24.ro,g4media.ro' : 'digi24.ro,hotnews.ro,adevarul.ro'
  }
  return normalizedTopic === 'news' ? 'reuters.com,bbc.com,apnews.com' : 'wikipedia.org'
}

export function SearchSection({ initialQuery = 'latest AI news', onSearchComplete }: SearchSectionProps) {
  const { addToast } = useToast()
  const queryRef = useRef<HTMLInputElement>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [form, setForm] = useState<SearchForm>({
    query: initialQuery,
    topic: 'news',
    language: 'english',
    maxResults: 5,
    includeDomains: '',
    excludeDomains: '',
    maxAgeDays: 7,
    startDate: '',
    endDate: '',
  })
  const { loading, status, errorMsg, runAction } = useAsyncAction()
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [sortMode, setSortMode] = useState<SortMode>('relevance')
  const [compareItems, setCompareItems] = useState<SearchResult[]>([])
  const [analysis, setAnalysis] = useState<QueryAnalysisResponse | null>(null)

  useEffect(() => { queryRef.current?.focus() }, [])

  const handleRunSearch = useCallback(async () => {
    if (!form.query.trim()) return
    const payload = buildSearchPayload(form, { allowTimeRange: false })
    await runAction(
      () => apiClient.search(payload),
      {
        pendingStatus: 'Searching…',
        successStatus: data => (
          data.ambiguous
            ? `Found ${data.results.length} results (ambiguous query).`
            : `Found ${data.results.length} results.`
        ),
        onSuccess: data => {
          setResponse(data)
          setSortMode('relevance')
          setCompareItems(prev =>
            prev.filter(c => data.results.some(r => r.url + r.title === c.url + c.title)),
          )
          onSearchComplete(data)
          const msg = data.ambiguous
            ? `Found ${data.results.length} results (ambiguous query).`
            : `Found ${data.results.length} results.`
          addToast(msg, 'success')
        },
        onError: (msg: string) => {
          addToast(msg, 'error')
          setResponse(null)
        },
      },
    )
  }, [form, onSearchComplete, addToast, runAction])

  const handleAnalyze = useCallback(async () => {
    if (!form.query.trim()) return
    setAnalysisLoading(true)
    try {
      const data = await apiClient.searchAnalyze(form.query, form.topic)
      setAnalysis(data)
      addToast('Query analyzed.', 'info')
    } catch (err) {
      addToast(`Analysis failed: ${(err as Error).message}`, 'error')
    } finally {
      setAnalysisLoading(false)
    }
  }, [form.query, form.topic, addToast])

  const handleToggleCompare = useCallback((item: SearchResult) => {
    setCompareItems(prev => {
      const update = toggleCompareItems(prev, item, 3)
      if (update.maxReached) {
        addToast('Compare panel is full (max 3 items).', 'info')
      }
      return update.next
    })
  }, [addToast])

  const handleCopyLink = useCallback(async (url: string) => {
    try { await copyToClipboard(url); addToast('Link copied.', 'success') }
    catch { addToast('Copy failed.', 'error') }
  }, [addToast])

  const applyPreset = (preset: { query: string; topic: 'general' | 'news'; include: string }) => {
    setForm(prev => ({ ...prev, query: preset.query, topic: preset.topic, includeDomains: preset.include, maxAgeDays: 0, startDate: '', endDate: '' }))
  }

  return (
    <div className="space-y-4">
      {/* ── Search form card ── */}
      <SpotlightCard className="rounded-3xl" spotlightColor="rgba(6,182,212,0.04)">
        <Card className="rounded-3xl p-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="font-display text-2xl font-bold text-slate-100 mb-1 flex items-center gap-2">
                <Search className="w-5 h-5 text-cyan-400" />
                Search
              </h2>
              <p className="text-slate-400 text-sm">Find relevant results quickly and browse them as clean cards.</p>
            </div>
          </div>

          {/* Error banner */}
          <AnimatePresence>
            {errorMsg && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-4 rounded-xl bg-red-950/60 border border-red-800/60 px-4 py-3 flex items-start gap-3 text-sm text-red-200 overflow-hidden"
              >
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-red-400" />
                <span>{errorMsg}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Main query */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="search-query" className="mb-2 block">What do you want to find?</Label>
              <Input
                id="search-query"
                ref={queryRef}
                value={form.query}
                onChange={e => setForm(prev => ({ ...prev, query: e.target.value }))}
                onKeyDown={e => { if (e.key === 'Enter') handleRunSearch() }}
                className="h-12 text-base rounded-2xl"
                placeholder="e.g. latest AI news, climate change, quantum computing…"
                icon={<Search className="w-4 h-4" />}
              />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <Label className="mb-2 block text-xs">Topic</Label>
                <select
                  value={form.topic}
                  onChange={e => setForm(prev => ({ ...prev, topic: e.target.value as 'general' | 'news' }))}
                  className="w-full rounded-xl bg-slate-900/80 border border-slate-700/60 px-3 py-2.5 text-sm text-slate-100 focus:border-cyan-500/50 focus:outline-none transition"
                >
                  <option value="general">general</option>
                  <option value="news">news</option>
                </select>
              </div>
              <div>
                <Label className="mb-2 block text-xs">Language</Label>
                <select
                  value={form.language}
                  onChange={e => setForm(prev => ({ ...prev, language: e.target.value as 'english' | 'romanian' }))}
                  className="w-full rounded-xl bg-slate-900/80 border border-slate-700/60 px-3 py-2.5 text-sm text-slate-100 focus:border-cyan-500/50 focus:outline-none transition"
                >
                  <option value="english">english</option>
                  <option value="romanian">romanian</option>
                </select>
              </div>
              <div>
                <Label className="mb-2 block text-xs">Max Results</Label>
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={form.maxResults}
                  onChange={e => setForm(prev => ({ ...prev, maxResults: Number(e.target.value) }))}
                  className="h-10"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={() => setShowFilters(v => !v)}
                  className="w-full flex items-center justify-center gap-2 h-10 rounded-xl border border-slate-700/60 text-slate-400 hover:text-slate-200 hover:border-slate-600 hover:bg-slate-800/40 transition text-sm"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                  Filters
                  {showFilters ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
              </div>
            </div>

            {/* Expandable filters */}
            <AnimatePresence>
              {showFilters && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.22 }}
                  className="overflow-hidden"
                >
                  <div className="rounded-2xl bg-slate-950/60 border border-white/[0.05] p-4 space-y-4">
                    <div className="flex items-center gap-2 text-xs text-slate-500 font-medium uppercase tracking-wide mb-2">
                      <SlidersHorizontal className="w-3 h-3" /> Source Filters
                    </div>
                    <p className="text-xs text-slate-500">Leave Include Domains empty for automatic source suggestions.</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <Label className="mb-1.5 block text-xs">Include Domains</Label>
                        <Input
                          value={form.includeDomains}
                          onChange={e => setForm(prev => ({ ...prev, includeDomains: e.target.value }))}
                          placeholder="reuters.com,bbc.com"
                        />
                      </div>
                      <div>
                        <Label className="mb-1.5 block text-xs">Exclude Domains</Label>
                        <Input
                          value={form.excludeDomains}
                          onChange={e => setForm(prev => ({ ...prev, excludeDomains: e.target.value }))}
                          placeholder="example.com"
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-500 font-medium uppercase tracking-wide mt-2 mb-2">
                      <Calendar className="w-3 h-3" /> Date Filters
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div>
                        <Label className="mb-1.5 block text-xs">Max Age (days)</Label>
                        <Input type="number" min={0} max={3650} value={form.maxAgeDays}
                          onChange={e => setForm(prev => ({ ...prev, maxAgeDays: Number(e.target.value) }))} />
                      </div>
                      <div>
                        <Label className="mb-1.5 block text-xs">Start Date</Label>
                        <Input type="date" value={form.startDate}
                          onChange={e => setForm(prev => ({ ...prev, startDate: e.target.value }))} />
                      </div>
                      <div>
                        <Label className="mb-1.5 block text-xs">End Date</Label>
                        <Input type="date" value={form.endDate}
                          onChange={e => setForm(prev => ({ ...prev, endDate: e.target.value }))} />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap items-center gap-3 mt-5">
            <Button variant="default" size="lg" onClick={handleRunSearch} disabled={loading} className="rounded-2xl">
              <Search className="w-4 h-4" />
              {loading ? 'Searching…' : 'Run Search'}
            </Button>
            <Button variant="secondary" onClick={handleAnalyze} disabled={analysisLoading}>
              <Sparkles className="w-3.5 h-3.5" />
              {analysisLoading ? 'Analyzing…' : 'Analyze Query'}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => applyPreset({ query: 'latest AI news', topic: 'news', include: defaultInclude('news', form.language) })}>
              News Preset
            </Button>
            <Button variant="ghost" size="sm" onClick={() => applyPreset({ query: 'artificial intelligence', topic: 'general', include: defaultInclude('general', form.language) })}>
              Wikipedia Preset
            </Button>
          </div>

          {status && <p className="text-sm text-slate-400 mt-3">{status}</p>}
          <div className="mt-3">
            <ProgressBar active={loading} color="bg-cyan-500" />
          </div>
        </Card>
      </SpotlightCard>

      {/* ── Results ── */}
      <div className="grid grid-cols-1 2xl:grid-cols-3 gap-4">
        <div className="2xl:col-span-2 space-y-4">
          <Card className="p-6">
            <div className="flex items-center justify-between gap-4 mb-4 flex-wrap">
              <h3 className="font-display font-semibold text-slate-100">Search Results</h3>
              <div className="flex items-center gap-3 flex-wrap">
                <select
                  value={sortMode}
                  onChange={e => setSortMode(e.target.value as SortMode)}
                  className="rounded-xl bg-slate-950 border border-slate-700/60 px-3 py-1.5 text-sm text-slate-300 focus:border-cyan-500/50 focus:outline-none transition"
                >
                  <option value="relevance">Sort: relevance</option>
                  <option value="date">Sort: date</option>
                  <option value="source">Sort: source</option>
                  <option value="title">Sort: title</option>
                </select>
                {response && (
                  <Badge variant="cyan">{sortResults(response.results, sortMode).length} result(s)</Badge>
                )}
              </div>
            </div>

            {loading ? (
              <div className="space-y-3" aria-busy="true" aria-label="Loading search results">
                {[0, 1, 2].map(i => <SkeletonResultCard key={i} />)}
              </div>
            ) : response ? (
              <SearchCards
                results={response.results}
                sortMode={sortMode}
                compareItems={compareItems}
                onToggleCompare={handleToggleCompare}
                onCopyLink={handleCopyLink}
              />
            ) : (
              <EmptyState
                variant="search"
                message="No results yet. Run a search above to see results here."
              />
            )}
            <ComparePanel items={compareItems} kind="search" />
          </Card>
        </div>

        <div className="space-y-4">
          {/* Summary */}
          <Card className="p-6">
            <h3 className="font-display font-semibold text-slate-100 mb-3">Summary</h3>
            <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
              {loading ? (
                <div className="space-y-2" aria-busy="true">
                  <div className="h-3 rounded bg-slate-800/60 w-full animate-shimmer" />
                  <div className="h-3 rounded bg-slate-800/60 w-5/6 animate-shimmer" />
                  <div className="h-3 rounded bg-slate-800/60 w-4/6 animate-shimmer" />
                </div>
              ) : response
                ? response.summary || response.extracted_summary || response.answer || 'No summary returned.'
                : <span className="text-slate-500 italic">No summary yet.</span>}
            </div>
          </Card>

          {/* Diagnostics */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display font-semibold text-slate-100">Diagnostics</h3>
              {response && (
                <Badge variant={response.ambiguous ? 'amber' : 'emerald'}>
                  {response.ambiguous ? 'Ambiguous' : 'Clear'}
                </Badge>
              )}
            </div>
            <div className="space-y-2 text-sm">
              {[
                ['Response time', response?.response_time != null ? `${response.response_time.toFixed(2)}s` : '—'],
                ['Request ID', response?.request_id || '—'],
                ['Selected sources', String((response?.selected_sources || []).length)],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl bg-slate-950/60 border border-white/[0.05] px-3 py-2.5 flex items-center justify-between gap-3">
                  <span className="text-slate-500">{label}</span>
                  <span className="text-slate-300 font-mono text-xs truncate max-w-[120px]">{value}</span>
                </div>
              ))}
              {analysis && (
                <div className="rounded-xl bg-slate-950/60 border border-white/[0.05] px-3 py-2.5">
                  <div className="text-slate-500 mb-1.5">Query analysis</div>
                  <div className="text-xs text-slate-300 leading-5 font-mono whitespace-pre-wrap">
                    {[
                      `Topic: ${analysis.topic}`,
                      `Tokens: ${analysis.token_count}`,
                      `Short: ${analysis.is_short_query ? 'yes' : 'no'}`,
                      `Ambiguous: ${analysis.ambiguous_likely ? 'yes' : 'no'}`,
                      ...(analysis.recommended_topic && analysis.recommended_topic !== analysis.topic
                        ? [`Suggested: ${analysis.recommended_topic}`] : []),
                    ].join('\n')}
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Selected sources */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display font-semibold text-slate-100">Selected Sources</h3>
              <span className="text-xs text-slate-500">Backend picks</span>
            </div>
            <SelectedSources sources={response?.selected_sources || []} />
          </Card>

          {/* Meaning groups */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display font-semibold text-slate-100">Meaning Groups</h3>
              <span className="text-xs text-slate-500">Shown when ambiguous</span>
            </div>
            <MeaningGroups groups={response?.meaning_groups || []} />
          </Card>
        </div>
      </div>
    </div>
  )
}
