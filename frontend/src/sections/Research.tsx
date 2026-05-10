import { useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Copy, Download, AlertTriangle, BookOpen, Sparkles, SlidersHorizontal, Calendar, ChevronDown, ChevronUp, RefreshCw, Timer } from 'lucide-react'
import { apiClient } from '../api/client'
import { useToast } from '../components/Toast'
import { ProgressBar } from '../components/ProgressBar'
import type { ResearchResponse, SearchResult } from '../types'
import { ResearchCards } from '../components/ResearchCards'
import { SelectedSources } from '../components/SelectedSources'
import { MeaningGroups } from '../components/MeaningGroups'
import { ComparePanel } from '../components/ComparePanel'
import { EmptyState } from '../components/EmptyState'
import { SkeletonResultCard, SkeletonSummary } from '../components/ui/Skeleton'
import { copyToClipboard, downloadTextFile } from '../utils'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Label } from '../components/ui/Label'
import { SpotlightCard } from '../components/effects/AnimatedBackground'
import { buildSearchPayload, type SearchPayloadFormValues } from '../utils/searchPayload'
import { toggleCompareItems } from '../utils/compare'
import { useAsyncAction } from '../hooks/useAsyncAction'

interface ResearchForm extends SearchPayloadFormValues {
  timeRange: string
}

interface ResearchSectionProps {
  initialQuery?: string
  onResearchComplete: (response: ResearchResponse) => void
  isAdmin?: boolean
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

export function StructuredResearchSections({ response }: { response: ResearchResponse }) {
  const sections = response.sections
  const conciseSummary = sections?.concise_summary || response.summary
  const keyFindings = sections?.key_findings?.length ? sections.key_findings : response.summary_points
  const detailedAnalysis = sections?.detailed_analysis || response.summary_markdown
  const limitations = sections?.limitations || []
  const followUps = sections?.suggested_follow_up_queries || []
  const sourceCards = sections?.sources?.length ? sections.sources : response.results

  return (
    <div className="space-y-5">
      <section aria-labelledby="research-concise-summary" className="space-y-2">
        <h4 id="research-concise-summary" className="text-sm font-semibold uppercase tracking-wide text-fuchsia-300">
          Concise Summary
        </h4>
        <p className="text-slate-200 leading-7">{conciseSummary || 'No concise summary available.'}</p>
      </section>

      <section aria-labelledby="research-key-findings" className="space-y-2">
        <h4 id="research-key-findings" className="text-sm font-semibold uppercase tracking-wide text-fuchsia-300">
          Key Findings
        </h4>
        <SummaryView summary={conciseSummary} points={keyFindings} />
      </section>

      <section aria-labelledby="research-detailed-analysis" className="space-y-2">
        <h4 id="research-detailed-analysis" className="text-sm font-semibold uppercase tracking-wide text-fuchsia-300">
          Detailed Analysis
        </h4>
        <pre className="whitespace-pre-wrap text-slate-200 leading-7 text-sm rounded-2xl bg-slate-950 border border-slate-800 p-4">
          {detailedAnalysis || 'No detailed analysis available.'}
        </pre>
      </section>

      {limitations.length > 0 && (
        <section aria-labelledby="research-limitations" className="space-y-2">
          <h4 id="research-limitations" className="text-sm font-semibold uppercase tracking-wide text-amber-300">
            Limitations or Missing Information
          </h4>
          <ul className="space-y-2 text-slate-300 text-sm">
            {limitations.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400" aria-hidden="true" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {followUps.length > 0 && (
        <section aria-labelledby="research-follow-ups" className="space-y-2">
          <h4 id="research-follow-ups" className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
            Suggested Follow-up Queries
          </h4>
          <ul className="flex flex-wrap gap-2">
            {followUps.map((item, idx) => (
              <li key={idx} className="rounded-full border border-cyan-700/40 bg-cyan-950/20 px-3 py-1 text-xs text-cyan-200">
                {item}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section aria-labelledby="research-sources" className="space-y-2">
        <h4 id="research-sources" className="text-sm font-semibold uppercase tracking-wide text-emerald-300">
          Sources
        </h4>
        {sourceCards.length === 0 ? (
          <p className="text-sm text-slate-400">No sources available.</p>
        ) : (
          <div className="space-y-2">
            {sourceCards.slice(0, 8).map((item, idx) => (
              <a
                key={`${item.url}-${idx}`}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-xl border border-emerald-900/40 bg-emerald-950/10 p-3 hover:border-emerald-600/60 transition-colors"
              >
                <p className="text-sm font-semibold text-emerald-200 break-words">{item.title || 'Untitled source'}</p>
                <p className="text-xs text-emerald-300/80 break-words">{item.source || 'unknown source'}</p>
                {item.snippet && <p className="text-xs text-slate-300 mt-1 line-clamp-2">{item.snippet}</p>}
              </a>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export function ResearchSection({ initialQuery = 'artificial intelligence', onResearchComplete, isAdmin = false }: ResearchSectionProps) {
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
  const { loading, errorMsg, status, runAction } = useAsyncAction()
  const [response, setResponse] = useState<ResearchResponse | null>(null)
  const [compareItems, setCompareItems] = useState<SearchResult[]>([])
  const [taskQuery, setTaskQuery] = useState(initialQuery)
  const [taskFocus, setTaskFocus] = useState('')
  const [taskMaxSources, setTaskMaxSources] = useState(20)
  const [taskId, setTaskId] = useState('')
  const [taskStatus, setTaskStatus] = useState<string>('')
  const [taskResultCount, setTaskResultCount] = useState(0)
  const [taskResultPreview, setTaskResultPreview] = useState<Array<{ title: string; url: string; source?: string }>>([])
  const [taskError, setTaskError] = useState('')
  const [taskBusy, setTaskBusy] = useState(false)
  const [autoPoll, setAutoPoll] = useState(false)
  const intervalRef = useRef<number | null>(null)

  const handleRunResearch = useCallback(async () => {
    if (!form.query.trim()) {
      addToast('Please enter a research query.', 'info')
      return
    }
    const payload = buildSearchPayload(form, { allowTimeRange: true })
    await runAction(
      () => apiClient.research(payload),
      {
        pendingStatus: 'Running research…',
        successStatus: data => (
          `Research complete — ${data.source_count} sources, ${data.summary_points.length} key points.`
        ),
        onSuccess: data => {
          setResponse(data)
          setCompareItems(prev =>
            prev.filter(c => data.results.some(r => r.url + r.title === c.url + c.title)),
          )
          onResearchComplete(data)
          addToast(
            `Research complete — ${data.source_count} sources, ${data.summary_points.length} key points.`,
            'success',
          )
        },
        onError: (msg: string) => {
          addToast(msg, 'error')
          setResponse(null)
        },
      },
    )
  }, [form, onResearchComplete, addToast, runAction])

  const handleToggleCompare = useCallback((item: SearchResult) => {
    setCompareItems(prev => {
      const update = toggleCompareItems(prev, item, 3)
      if (update.maxReached) { addToast('Compare panel is full (max 3).', 'info') }
      return update.next
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

  const handleSubmitTask = useCallback(async () => {
    const query = taskQuery.trim()
    if (!query) {
      addToast('Task query is required.', 'info')
      return
    }

    setTaskBusy(true)
    setTaskError('')
    try {
      const created = await apiClient.submitResearchTask({
        query,
        focus: taskFocus.trim() || undefined,
        max_sources: taskMaxSources,
      })
      setTaskId(created.task_id)
      setTaskStatus(created.status)
      setTaskResultCount(0)
      setTaskResultPreview([])
      addToast(`Task created: ${created.task_id}`, 'success')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to create task.'
      setTaskError(msg)
      addToast(msg, 'error')
    } finally {
      setTaskBusy(false)
    }
  }, [taskQuery, taskFocus, taskMaxSources, addToast])

  const handlePollTask = useCallback(async () => {
    const normalizedTaskId = taskId.trim()
    if (!normalizedTaskId) {
      addToast('Task ID is required to poll.', 'info')
      return
    }

    setTaskBusy(true)
    setTaskError('')
    try {
      const polled = await apiClient.getResearchTask(normalizedTaskId)
      setTaskStatus(polled.status)
      setTaskResultCount(polled.result_count)
      setTaskResultPreview(polled.result_sources.slice(0, 5))
      setTaskError(polled.error_message || '')

      if (polled.is_terminal) {
        setAutoPoll(false)
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to poll task.'
      setTaskError(msg)
      setAutoPoll(false)
      addToast(msg, 'error')
    } finally {
      setTaskBusy(false)
    }
  }, [taskId, addToast])

  useEffect(() => {
    if (!autoPoll || !taskId.trim()) {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    intervalRef.current = window.setInterval(() => {
      void handlePollTask()
    }, 3000)

    return () => {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [autoPoll, taskId, handlePollTask])

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
                role="alert"
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
              aria-label="Run research query"
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

          {status && <p className="text-sm text-slate-400 mt-3" role="status" aria-live="polite">{status}</p>}
          <div className="mt-3">
            <ProgressBar active={loading} color="bg-fuchsia-500" />
          </div>
        </Card>
      </SpotlightCard>

      {isAdmin && (
        <Card className="p-6">
          <div className="flex items-center justify-between gap-3 mb-4">
            <div>
              <h3 className="font-display font-semibold text-slate-100">Admin Tavily Task Polling</h3>
              <p className="text-xs text-slate-500">Optional async task flow for /research/tasks endpoints.</p>
            </div>
            <Badge variant="amber">Admin</Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
            <div className="md:col-span-2">
              <Label className="mb-1.5 block text-xs">Task Query</Label>
              <Input value={taskQuery} onChange={e => setTaskQuery(e.target.value)} />
            </div>
            <div>
              <Label className="mb-1.5 block text-xs">Focus</Label>
              <Input value={taskFocus} onChange={e => setTaskFocus(e.target.value)} placeholder="Optional focus" />
            </div>
            <div>
              <Label className="mb-1.5 block text-xs">Max Sources</Label>
              <Input type="number" min={1} max={50} value={taskMaxSources} onChange={e => setTaskMaxSources(Number(e.target.value || 20))} />
            </div>
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            <Button variant="secondary" size="sm" onClick={handleSubmitTask} disabled={taskBusy}>
              <Sparkles className="w-3.5 h-3.5" /> Submit Task
            </Button>
            <Button variant="secondary" size="sm" onClick={handlePollTask} disabled={taskBusy || !taskId.trim()}>
              <RefreshCw className="w-3.5 h-3.5" /> Poll Now
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setAutoPoll(v => !v)}
              disabled={!taskId.trim()}
              aria-pressed={autoPoll}
            >
              <Timer className="w-3.5 h-3.5" /> {autoPoll ? 'Stop Auto Poll' : 'Start Auto Poll'}
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <Label className="mb-1.5 block text-xs">Task ID</Label>
              <Input value={taskId} onChange={e => setTaskId(e.target.value)} placeholder="Paste task id" />
            </div>
            <div className="rounded-xl bg-slate-950/60 border border-white/[0.05] px-3 py-2.5">
              <p className="text-xs text-slate-500">Status</p>
              <p className="text-sm text-slate-200 mt-1" role="status" aria-live="polite">{taskStatus || 'idle'}</p>
            </div>
            <div className="rounded-xl bg-slate-950/60 border border-white/[0.05] px-3 py-2.5">
              <p className="text-xs text-slate-500">Result Count</p>
              <p className="text-sm text-slate-200 mt-1">{taskResultCount}</p>
            </div>
          </div>

          {taskError && (
            <div className="mt-3 rounded-xl bg-red-950/60 border border-red-800/60 px-4 py-3 text-sm text-red-200" role="alert">
              {taskError}
            </div>
          )}

          {taskResultPreview.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-xs uppercase tracking-wide text-slate-500">Task Result Preview</p>
              {taskResultPreview.map((item, index) => (
                <a
                  key={`${item.url}-${index}`}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block rounded-xl border border-slate-800 bg-slate-950/50 px-3 py-2 hover:border-fuchsia-600/60 transition-colors"
                >
                  <p className="text-sm text-fuchsia-300 break-words">{item.title}</p>
                  <p className="text-xs text-slate-500 break-words">{item.source || item.url}</p>
                </a>
              ))}
            </div>
          )}
        </Card>
      )}

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
              <StructuredResearchSections response={response} />
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
