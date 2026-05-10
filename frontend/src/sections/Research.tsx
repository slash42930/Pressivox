import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Copy, Download, AlertTriangle, BookOpen, Sparkles, SlidersHorizontal, Calendar, ChevronDown, ChevronUp } from 'lucide-react'
import { apiClient } from '../api/client'
import { useToast } from '../components/Toast'
import { ProgressBar } from '../components/ProgressBar'
import type { SearchRequest, ResearchResponse, SearchResult } from '../types'
import { ResearchCards } from '../components/ResearchCards'
import { SelectedSources } from '../components/SelectedSources'
import { MeaningGroups } from '../components/MeaningGroups'
import { ComparePanel } from '../components/ComparePanel'
import { EmptyState } from '../components/EmptyState'
import { SkeletonResultCard, SkeletonSummary } from '../components/ui/Skeleton'
import { parseDomains, toIsoDate, copyToClipboard, downloadTextFile } from '../utils'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Label } from '../components/ui/Label'
import { SpotlightCard } from '../components/effects/AnimatedBackground'

interface ResearchForm {
  query: string
  topic: 'general' | 'news'
  language: 'english' | 'romanian'
  maxResults: number
  includeDomains: string
  excludeDomains: string
  timeRange: string
  maxAgeDays: number
  startDate: string
  endDate: string
}

interface ResearchSectionProps {
  initialQuery?: string
  onResearchComplete: (response: ResearchResponse) => void
}

function buildPayload(form: ResearchForm): SearchRequest {
  let start = form.startDate || null
  let end = form.endDate || null

  if (form.maxAgeDays > 0) {
    const now = new Date()
    const s = new Date(now)
    s.setDate(s.getDate() - form.maxAgeDays)
    start = toIsoDate(s)
    end = toIsoDate(now)
  }

  const manualDomains = parseDomains(form.includeDomains)
  return {
    query: form.query,
    topic: form.topic,
    language: form.language,
    max_results: form.maxResults,
    summarize: true,
    extract_top_results: true,
    include_domains: manualDomains,
    exclude_domains: parseDomains(form.excludeDomains),
    search_depth: 'advanced',
    time_range: start || end ? null : form.timeRange || null,
    start_date: start,
    end_date: end,
    exact_match: false,
    include_answer: true,
    include_raw_content: true,
    include_images: false,
    include_image_descriptions: false,
    include_favicon: true,
    auto_parameters: true,
  }
}

function SummaryView({ summary, points }: { summary: string; points: string[] }) {
  if (points.length) {
    return (
      <div className="rounded-2xl bg-slate-950 border border-slate-800 p-4">
        <div className="text-xs uppercase tracking-wide text-fuchsia-400 font-semibold mb-3">Key Points</div>
        <ul className="space-y-3 text-slate-200">
          {points.map((p, i) => {
            const colonIdx = p.indexOf(':')
            if (colonIdx > 0 && colonIdx < 40) {
              const label = p.slice(0, colonIdx).trim()
              const body = p.slice(colonIdx + 1).trim()
              return (
                <li key={i} className="flex items-start gap-3">
                  <span className="mt-2 w-2 h-2 rounded-full bg-fuchsia-400 shrink-0" />
                  <span className="leading-7">
                    <span className="font-semibold text-fuchsia-300">{label}:</span> {body}
                  </span>
                </li>
              )
            }
            return (
              <li key={i} className="flex items-start gap-3">
                <span className="mt-2 w-2 h-2 rounded-full bg-fuchsia-400 shrink-0" />
                <span className="leading-7">{p}</span>
              </li>
            )
          })}
        </ul>
      </div>
    )
  }

  if (summary) {
    return <p className="leading-8 text-slate-100">{summary}</p>
  }

  return <p className="text-slate-400 text-sm">No summary returned.</p>
}

export function ResearchSection({ initialQuery = 'artificial intelligence', onResearchComplete }: ResearchSectionProps) {
  const { addToast } = useToast()
  const [showFilters, setShowFilters] = useState(false)
  const [form, setForm] = useState<ResearchForm>({
    query: initialQuery,
    topic: 'general',
    language: 'english',
    maxResults: 5,
    includeDomains: '',
    excludeDomains: '',
    timeRange: 'month',
    maxAgeDays: 30,
    startDate: '',
    endDate: '',
  })
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [status, setStatus] = useState('')
  const [response, setResponse] = useState<ResearchResponse | null>(null)
  const [compareItems, setCompareItems] = useState<SearchResult[]>([])

  const handleRunResearch = useCallback(async () => {
    if (!form.query.trim()) return
    setLoading(true)
    setErrorMsg('')
    setStatus('Running research…')
    try {
      const payload = buildPayload(form)
      const data = await apiClient.research(payload)
      setResponse(data)
      setCompareItems(prev =>
        prev.filter(c => data.results.some(r => r.url + r.title === c.url + c.title)),
      )
      onResearchComplete(data)
      const msg = `Research complete — ${data.source_count} sources, ${data.summary_points.length} key points.`
      setStatus(msg)
      addToast(msg, 'success')
    } catch (err) {
      const msg = (err as Error).message
      setErrorMsg(msg)
      setStatus('')
      addToast(msg, 'error')
      setResponse(null)
    } finally {
      setLoading(false)
    }
  }, [form, onResearchComplete, addToast])

  const handleToggleCompare = useCallback((item: SearchResult) => {
    const key = item.url + item.title
    setCompareItems(prev => {
      if (prev.some(c => c.url + c.title === key)) return prev.filter(c => c.url + c.title !== key)
      if (prev.length >= 3) { addToast('Compare panel is full (max 3).', 'info'); return prev }
      return [...prev, item]
    })
  }, [addToast])

  const handleCopyLink = useCallback(async (url: string) => {
    try { await copyToClipboard(url); addToast('Link copied.', 'success') }
    catch { addToast('Copy failed.', 'error') }
  }, [addToast])

  const handleCopyMarkdown = useCallback(async () => {
    if (!response?.summary_markdown) { addToast('No markdown available.', 'info'); return }
    try { await copyToClipboard(response.summary_markdown); addToast('Research markdown copied.', 'success') }
    catch { addToast('Copy failed.', 'error') }
  }, [response, addToast])

  const handleDownloadMarkdown = useCallback(() => {
    if (!response?.summary_markdown) { addToast('Run research before downloading.', 'info'); return }
    downloadTextFile('research-summary.md', response.summary_markdown)
    addToast('Markdown downloaded.', 'success')
  }, [response, addToast])

  return (
    <div className="space-y-4">
      {/* ── Research form card ── */}
      <SpotlightCard className="rounded-3xl" spotlightColor="rgba(168,85,247,0.04)">
        <Card className="rounded-3xl p-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="font-display text-2xl font-bold text-slate-100 mb-1 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-fuchsia-400" />
                Research
              </h2>
              <p className="text-slate-400 text-sm">Get a structured overview with key points and best-matching sources.</p>
            </div>
          </div>

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

          <div className="space-y-4">
            <div>
              <Label htmlFor="research-query" className="mb-2 block">What do you want to research?</Label>
              <Input
                id="research-query"
                value={form.query}
                onChange={e => setForm(prev => ({ ...prev, query: e.target.value }))}
                onKeyDown={e => { if (e.key === 'Enter') handleRunResearch() }}
                className="h-12 text-base rounded-2xl"
                placeholder="e.g. artificial intelligence, quantum computing, climate change…"
                icon={<BookOpen className="w-4 h-4" />}
              />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <Label className="mb-2 block text-xs">Topic</Label>
                <select
                  value={form.topic}
                  onChange={e => setForm(prev => ({ ...prev, topic: e.target.value as 'general' | 'news' }))}
                  className="w-full rounded-xl bg-slate-900/80 border border-slate-700/60 px-3 py-2.5 text-sm text-slate-100 focus:border-fuchsia-500/50 focus:outline-none transition"
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
                  className="w-full rounded-xl bg-slate-900/80 border border-slate-700/60 px-3 py-2.5 text-sm text-slate-100 focus:border-fuchsia-500/50 focus:outline-none transition"
                >
                  <option value="english">english</option>
                  <option value="romanian">romanian</option>
                </select>
              </div>
              <div>
                <Label className="mb-2 block text-xs">Max Results</Label>
                <Input
                  type="number" min={1} max={20}
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
                        <Input value={form.includeDomains}
                          onChange={e => setForm(prev => ({ ...prev, includeDomains: e.target.value }))}
                          placeholder="hotnews.ro,digi24.ro" />
                      </div>
                      <div>
                        <Label className="mb-1.5 block text-xs">Exclude Domains</Label>
                        <Input value={form.excludeDomains}
                          onChange={e => setForm(prev => ({ ...prev, excludeDomains: e.target.value }))} />
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-500 font-medium uppercase tracking-wide mt-2 mb-2">
                      <Calendar className="w-3 h-3" /> Date Filters
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <div>
                        <Label className="mb-1.5 block text-xs">Time Range</Label>
                        <select value={form.timeRange}
                          onChange={e => setForm(prev => ({ ...prev, timeRange: e.target.value }))}
                          className="w-full rounded-xl bg-slate-900/80 border border-slate-700/60 px-3 py-2 text-sm text-slate-100 focus:outline-none transition"
                        >
                          <option value="">none</option>
                          <option value="day">day</option>
                          <option value="week">week</option>
                          <option value="month">month</option>
                          <option value="year">year</option>
                        </select>
                      </div>
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

          <div className="flex flex-wrap items-center gap-3 mt-5">
            <Button
              variant="fuchsia" size="lg" onClick={handleRunResearch} disabled={loading}
              className="rounded-2xl"
            >
              <Sparkles className="w-4 h-4" />
              {loading ? 'Running…' : 'Run Research'}
            </Button>
            <Button variant="ghost" size="sm"
              onClick={() => setForm(prev => ({ ...prev, query: 'artificial intelligence', topic: 'general', includeDomains: 'wikipedia.org', maxAgeDays: 0 }))}>
              AI Preset
            </Button>
            <Button variant="ghost" size="sm"
              onClick={() => setForm(prev => ({ ...prev, query: 'bank', topic: 'general', includeDomains: '', maxAgeDays: 0 }))}>
              Ambiguous Preset
            </Button>
          </div>

          {status && <p className="text-sm text-slate-400 mt-3">{status}</p>}
          <div className="mt-3">
            <ProgressBar active={loading} color="bg-fuchsia-500" />
          </div>
        </Card>
      </SpotlightCard>

      {/* ── Summary + Overview ── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <Card className="p-6 h-full">
            <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
              <div>
                <h3 className="font-display font-semibold text-slate-100">Research Summary</h3>
                {response && (
                  <p className="text-xs text-slate-500 mt-0.5">
                    {response.query} · {response.topic} · {response.response_time != null ? `${response.response_time.toFixed(2)}s` : '—'}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="secondary" size="sm" onClick={handleCopyMarkdown}>
                  <Copy className="w-3.5 h-3.5" /> Copy Markdown
                </Button>
                <Button variant="secondary" size="sm" onClick={handleDownloadMarkdown}>
                  <Download className="w-3.5 h-3.5" /> Download
                </Button>
              </div>
            </div>
            {loading ? (
              <SkeletonSummary />
            ) : response ? (
              <SummaryView summary={response.summary} points={response.summary_points} />
            ) : (
              <p className="text-slate-500 text-sm italic">Run a research query to see a summary here.</p>
            )}
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="p-6">
            <h3 className="font-display font-semibold text-slate-100 mb-3">Overview</h3>
            <div className="space-y-2 text-sm">
              {[
                ['Ambiguous', response ? (response.ambiguous ? 'Yes' : 'No') : '—'],
                ['Returned sources', String(response?.source_count ?? 0)],
                ['Selected sources', String((response?.selected_sources || []).length)],
                ['Extracted count', String(response?.extracted_count ?? 0)],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl bg-slate-950/60 border border-white/[0.05] px-3 py-2.5 flex items-center justify-between gap-3">
                  <span className="text-slate-500">{label}</span>
                  <span className="text-slate-300 font-mono text-xs">{value}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display font-semibold text-slate-100">Selected Sources</h3>
              <span className="text-xs text-slate-500">Best picks</span>
            </div>
            <SelectedSources sources={response?.selected_sources || []} />
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display font-semibold text-slate-100">Meaning Groups</h3>
              {response && (
                <Badge variant={response.ambiguous ? 'amber' : 'emerald'}>
                  {response.ambiguous ? 'Ambiguous' : 'Clear'}
                </Badge>
              )}
            </div>
            <MeaningGroups groups={response?.meaning_groups || []} />
          </Card>
        </div>
      </div>

      {/* ── All results ── */}
      <Card className="p-6">
        <div className="flex items-center justify-between gap-4 mb-4">
          <h3 className="font-display font-semibold text-slate-100">All Research Results</h3>
          {response && <Badge variant="fuchsia">{response.results.length} result(s)</Badge>}
        </div>
        {loading ? (
          <div className="space-y-3" aria-busy="true" aria-label="Loading research results">
            {[0, 1, 2].map(i => <SkeletonResultCard key={i} />)}
          </div>
        ) : response ? (
          <ResearchCards
            results={response.results}
            compareItems={compareItems}
            onToggleCompare={handleToggleCompare}
            onCopyLink={handleCopyLink}
          />
        ) : (
          <EmptyState variant="research" message="No research results yet. Run a query above." />
        )}
        <ComparePanel items={compareItems} kind="research" />
      </Card>
    </div>
  )
}
