import { memo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Copy, ExternalLink, GitCompare } from 'lucide-react'
import type { SearchResult } from '../types'
import { Favicon } from './Favicon'
import { normalizeScore, formatPublishedDate } from '../utils'
import { EmptyState } from './EmptyState'

interface ResearchCardProps {
  item: SearchResult
  index: number
  isCompared: boolean
  onToggleCompare: (item: SearchResult) => void
  onCopyLink: (url: string) => void
}

const ResearchCard = memo(function ResearchCard({ item, index, isCompared, onToggleCompare, onCopyLink }: ResearchCardProps) {
  const score = normalizeScore(item)
  const publishedInfo = formatPublishedDate(item.published_date)
  const scorePercent = Number.isFinite(score) ? Math.min(Math.round(score * 100), 100) : 0
  const [expanded, setExpanded] = useState(false)
  const longSnippet = (item.snippet?.length ?? 0) > 160

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.97 }}
      transition={{ duration: 0.22, delay: index * 0.04 }}
      className="group rounded-2xl bg-slate-900/60 border border-white/[0.06] hover:border-fuchsia-500/40 hover:shadow-lg hover:shadow-fuchsia-900/10 hover:-translate-y-0.5 backdrop-blur-sm transition-all duration-200 overflow-hidden"
    >
      {/* Animated confidence bar at top */}
      <div className="h-0.5 bg-slate-800">
        <div
          className="h-0.5 bg-fuchsia-400"
          style={{
            width: `${scorePercent}%`,
            transition: `width 700ms ease-out ${Math.round((index * 0.04 + 0.2) * 1000)}ms`,
          }}
        />
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">#{index + 1}</div>
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-fuchsia-300 group-hover:text-fuchsia-200 break-words transition-colors leading-6"
            >
              {item.title || 'Untitled'}
            </a>
          </div>
          <div className="text-right text-xs shrink-0 min-w-[48px]">
            <div className="font-bold text-sm text-fuchsia-300">
              {Number.isFinite(score) ? score.toFixed(2) : '-'}
            </div>
            <div className="text-slate-600 text-[10px]">confidence</div>
            {Number.isFinite(score) && (
              <div className="mt-1.5 h-1 rounded-full bg-slate-700 overflow-hidden w-full">
                <div
                  className="h-1 rounded-full bg-fuchsia-400"
                  style={{
                    width: `${scorePercent}%`,
                    transition: `width 700ms ease-out ${Math.round((index * 0.04 + 0.3) * 1000)}ms`,
                  }}
                />
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 mb-3 text-xs text-slate-500">
          <Favicon favicon={item.favicon} />
          <span className="text-slate-400">{item.source || 'unknown source'}</span>
          {publishedInfo && <span className="text-emerald-400 font-medium">{publishedInfo}</span>}
        </div>

        {item.snippet ? (
          <div>
            <p className={`text-sm text-slate-300 leading-6 ${!expanded && longSnippet ? 'line-clamp-3' : ''}`}>
              {item.snippet}
            </p>
            {longSnippet && (
              <button
                onClick={() => setExpanded(e => !e)}
                className="mt-1.5 flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
              >
                <motion.span animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
                  <ChevronDown className="w-3 h-3" />
                </motion.span>
                {expanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>
        ) : null}

        <div className="flex flex-wrap gap-2 mt-4">
          <button
            className="rounded-xl bg-slate-800 hover:bg-slate-700 border border-transparent hover:border-slate-600 px-3 py-1.5 text-xs font-medium transition-all flex items-center gap-1.5"
            onClick={() => onCopyLink(item.url)}
          >
            <Copy className="w-3 h-3" /> Copy link
          </button>
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-xl bg-slate-800 hover:bg-slate-700 border border-transparent hover:border-slate-600 px-3 py-1.5 text-xs font-medium transition-all flex items-center gap-1.5"
          >
            <ExternalLink className="w-3 h-3" /> Open
          </a>
          <button
            className={`rounded-xl border px-3 py-1.5 text-xs font-medium transition-all flex items-center gap-1.5 ${
              isCompared
                ? 'bg-fuchsia-900/40 border-fuchsia-600 text-fuchsia-300'
                : 'bg-slate-800 hover:bg-slate-700 border-transparent hover:border-slate-600'
            }`}
            onClick={() => onToggleCompare(item)}
          >
            <GitCompare className="w-3 h-3" />
            {isCompared ? 'In compare' : 'Compare'}
          </button>
        </div>
      </div>
    </motion.div>
  )
}, (prev, next) => {
  return (
    prev.isCompared === next.isCompared &&
    prev.index === next.index &&
    prev.item.url === next.item.url &&
    prev.item.title === next.item.title &&
    prev.item.snippet === next.item.snippet &&
    prev.item.score === next.item.score &&
    prev.item.rerank_score === next.item.rerank_score &&
    prev.item.published_date === next.item.published_date &&
    prev.item.source === next.item.source &&
    prev.item.favicon === next.item.favicon
  )
})

interface ResearchCardsProps {
  results: SearchResult[]
  compareItems: SearchResult[]
  onToggleCompare: (item: SearchResult) => void
  onCopyLink: (url: string) => void
}

export function ResearchCards({
  results,
  compareItems,
  onToggleCompare,
  onCopyLink,
}: ResearchCardsProps) {
  if (!results.length) return <EmptyState message="No research results yet." />

  const compareKeys = new Set(compareItems.map(i => i.url + i.title))

  return (
    <div className="space-y-3">
      <AnimatePresence>
        {results.map((item, index) => (
          <ResearchCard
            key={item.url + item.title}
            item={item}
            index={index}
            isCompared={compareKeys.has(item.url + item.title)}
            onToggleCompare={onToggleCompare}
            onCopyLink={onCopyLink}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}
