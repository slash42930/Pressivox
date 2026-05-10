import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, Zap, AlertTriangle } from 'lucide-react'
import { apiClient } from '../api/client'
import type { ExtractResponse } from '../types'
import { EmptyState } from '../components/EmptyState'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Label } from '../components/ui/Label'
import { SpotlightCard } from '../components/effects/AnimatedBackground'
import { ProgressBar } from '../components/ProgressBar'

interface ExtractSectionProps {
  initialUrl?: string
  onExtractComplete: () => void
}

export function ExtractSection({
  initialUrl = 'https://en.wikipedia.org/wiki/Artificial_intelligence',
  onExtractComplete,
}: ExtractSectionProps) {
  const [url, setUrl] = useState(initialUrl)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [response, setResponse] = useState<ExtractResponse | null>(null)

  const handleExtract = useCallback(async () => {
    const trimmed = url.trim()
    if (!trimmed) return
    setLoading(true)
    setErrorMsg('')
    setStatus('Extracting…')
    try {
      const data = await apiClient.extract(trimmed)
      setResponse(data)
      onExtractComplete()
      setStatus(`Extraction completed.`)
    } catch (err) {
      setErrorMsg(`Extraction failed: ${(err as Error).message}`)
      setStatus('')
      setResponse(null)
    } finally {
      setLoading(false)
    }
  }, [url, onExtractComplete])

  return (
    <div className="space-y-4">
      {/* ── Extract form card ── */}
      <SpotlightCard className="rounded-3xl" spotlightColor="rgba(245,158,11,0.04)">
        <Card className="rounded-3xl p-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="font-display text-2xl font-bold text-slate-100 mb-1 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-400" />
                Extract
              </h2>
              <p className="text-slate-400 text-sm">Open one page and read the important content in a cleaner format.</p>
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

          <div className="rounded-xl bg-amber-950/20 border border-amber-800/30 px-4 py-3 text-sm text-amber-200/80 mb-4">
            Tip: paste any article link, then use <span className="font-medium text-amber-300">Important Passages</span> for a fast skim.
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="extract-url" className="mb-2 block">URL to extract</Label>
              <Input
                id="extract-url"
                value={url}
                onChange={e => setUrl(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleExtract() }}
                className="h-12 text-base rounded-2xl"
                placeholder="https://example.com/article"
                icon={<Link className="w-4 h-4" />}
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-3 mt-5">
            <Button variant="amber" size="lg" onClick={handleExtract} disabled={loading} className="rounded-2xl">
              <Zap className="w-4 h-4" />
              {loading ? 'Extracting…' : 'Extract URL'}
            </Button>
            <Button variant="ghost" size="sm"
              onClick={() => setUrl('https://en.wikipedia.org/wiki/Artificial_intelligence')}>
              Wikipedia Preset
            </Button>
          </div>

          {status && <p className="text-sm text-slate-400 mt-3">{status}</p>}
          <div className="mt-3">
            <ProgressBar active={loading} color="bg-amber-500" />
          </div>
        </Card>
      </SpotlightCard>

      {/* ── Results ── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Extracted text */}
        <div className="xl:col-span-2">
          <Card className="p-6 h-full">
            <div className="flex items-center justify-between gap-4 mb-4 flex-wrap">
              <h3 className="font-display font-semibold text-slate-100">Extracted Text</h3>
              {response && (
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="amber">{response.content_length || 0} chars</Badge>
                  <span className="text-xs text-slate-500">{response.source || 'unknown source'}</span>
                </div>
              )}
            </div>
            {response ? (
              <div className="text-sm text-slate-300 whitespace-pre-wrap max-h-[720px] overflow-auto leading-7 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
                {response.extracted_text}
              </div>
            ) : (
              <EmptyState variant="extract" message="No extracted content yet. Enter a URL and click Extract." />
            )}
          </Card>
        </div>

        <div className="space-y-4">
          {/* Important passages */}
          <Card className="p-6">
            <h3 className="font-display font-semibold text-slate-100 mb-3">Important Passages</h3>
            {response?.important_passages?.length ? (
              <div className="space-y-3">
                {response.important_passages.map((passage, i) => (
                  <div key={i} className="rounded-xl bg-slate-950/60 border border-white/[0.05] p-3.5">
                    <div className="text-xs text-amber-500/70 font-medium mb-1.5">Passage {i + 1}</div>
                    <div className="text-sm text-slate-300 leading-6">{passage}</div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState variant="extract" message="No important passages returned." />
            )}
          </Card>

          {/* Page info */}
          <Card className="p-6">
            <h3 className="font-display font-semibold text-slate-100 mb-3">Page Info</h3>
            {response ? (
              <div className="space-y-2 text-sm">
                {[
                  ['Title', response.title || '—'],
                  ['Source', response.source || '—'],
                  ['Original URL', response.url || '—'],
                  ['Final URL', response.final_url || '—'],
                  ['Content length', response.content_length != null ? String(response.content_length) : '—'],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-xl bg-slate-950/60 border border-white/[0.05] px-3 py-2.5">
                    <div className="text-slate-500 text-xs mb-0.5">{label}</div>
                    <div className="text-slate-200 break-all text-xs font-mono">{value}</div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState variant="extract" message="No page info yet." />
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
