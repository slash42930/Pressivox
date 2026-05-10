import { memo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ExternalLink, Copy, GitCompare } from 'lucide-react'
import type { SearchResult } from '../types'
import { Favicon } from './Favicon'
import {
  normalizeScore,
  confidenceTier,
  formatPublishedDate,
  sortResults,
  trustedBadgeClass,
  isTrusted,
  type SortMode,
} from '../utils'
import { EmptyState } from './EmptyState'

interface SearchCardProps {
  item: SearchResult
  index: number
  isCompared: boolean
  onToggleCompare: (item: SearchResult) => void
  onCopyLink: (url: string) => void
}

const SearchCard = memo(function SearchCard({ item, index, isCompared, onToggleCompare, onCopyLink }: SearchCardProps) {
  const score = normalizeScore(item)
  const scorePercent = Number.isFinite(score) ? Math.min(score * 100, 100) : 0
  const publishedInfo = formatPublishedDate(item.published_date)
  const [expanded, setExpanded] = useState(false)
  const longSnippet = (item.snippet?.length ?? 0) > 160

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.97 }}
      transition={{ duration: 0.22, delay: index * 0.04 }}
      className="group rounded-2xl bg-slate-900/60 border border-white/[0.06] hover:border-cyan-500/40 hover:shadow-lg hover:shadow-cyan-900/10 hover:-translate-y-0.5 backdrop-blur-sm transition-all duration-200 overflow-hidden"
    >
      {/* Score bar at top */}
      <div className="h-0.5 bg-slate-800">
        <div
          className={`h-0.5 ${
            scorePercent >= 70 ? 'bg-cyan-400' : scorePercent >= 40 ? 'bg-emerald-400' : 'bg-slate-600'
          }`}
          style={{
            width: `${scorePercent}%`,
            transition: `width 600ms ease-out ${Math.round((index * 0.04 + 0.2) * 1000)}ms`,
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
              className="font-semibold text-cyan-300 group-hover:text-cyan-200 break-words transition-colors leading-6"
            >
              {item.title || 'Untitled'}
            </a>
          </div>
          <div className="text-right text-xs shrink-0 min-w-[48px]">
            <div className={`font-bold text-sm ${scorePercent >= 70 ? 'text-cyan-300' : scorePercent >= 40 ? 'text-emerald-300' : 'text-slate-400'}`}>
              {Number.isFinite(score) ? score.toFixed(2) : '-'}
            </div>
            <div className="text-slate-600 text-[10px]">score</div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 mb-3 text-xs text-slate-500">
          <Favicon favicon={item.favicon} />
          <span className="text-slate-400">{item.source || 'unknown source'}</span>
          <span className={`rounded-full px-2 py-0.5 font-medium ${trustedBadgeClass(item.source)}`}>
            {isTrusted(item.source) ? 'trusted' : 'external'}
          </span>
          {publishedInfo && (
            <span className="text-emerald-400 font-medium">{publishedInfo}</span>
          )}
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
                <motion.span
                  animate={{ rotate: expanded ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ChevronDown className="w-3 h-3" />
                </motion.span>
                {expanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>
        ) : (
          <p className="text-sm text-slate-600 italic">No preview available.</p>
        )}

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
                ? 'bg-cyan-900/40 border-cyan-600 text-cyan-300'
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

const TIER_CONFIG = [
  { key: 'best' as const, label: 'Best Match', dot: 'bg-cyan-400', text: 'text-cyan-300' },
  { key: 'good' as const, label: 'Good Match', dot: 'bg-emerald-400', text: 'text-emerald-300' },
  { key: 'other' as const, label: 'Other Results', dot: 'bg-slate-500', text: 'text-slate-400' },
]

interface SearchCardsProps {
  results: SearchResult[]
  sortMode: SortMode
  compareItems: SearchResult[]
  onToggleCompare: (item: SearchResult) => void
  onCopyLink: (url: string) => void
}

export function SearchCards({
  results,
  sortMode,
  compareItems,
  onToggleCompare,
  onCopyLink,
}: SearchCardsProps) {
  if (!results.length) return <EmptyState message="No results yet." />

  const sorted = sortResults(results, sortMode)
  const compareKeys = new Set(compareItems.map(i => i.url + i.title))

  if (sortMode !== 'relevance') {
    return (
      <div className="space-y-3">
        <AnimatePresence>
          {sorted.map((item, index) => (
            <SearchCard
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

  // Group by confidence tier
  const scores = sorted.map(r => normalizeScore(r)).filter(s => Number.isFinite(s))
  const maxScore = scores.length ? Math.max(...scores) : 0
  const groups: Record<'best' | 'good' | 'other', SearchResult[]> = { best: [], good: [], other: [] }
  sorted.forEach(item => groups[confidenceTier(normalizeScore(item), maxScore)].push(item))

  let globalIndex = 0
  return (
    <div className="space-y-1">
      {TIER_CONFIG.map(({ key, label, dot, text }) => {
        const items = groups[key]
        if (!items.length) return null
        const startIndex = globalIndex
        globalIndex += items.length
        return (
          <div key={key}>
            <div className="flex items-center gap-3 mt-5 mb-3 first:mt-0">
              <span className={`w-2 h-2 rounded-full ${dot} shrink-0`} />
              <span className={`text-xs font-semibold uppercase tracking-widest ${text}`}>{label}</span>
              <span className="text-xs text-slate-600">
                {items.length} result{items.length !== 1 ? 's' : ''}
              </span>
              <div className="flex-1 h-px bg-slate-800" />
            </div>
            <div className="space-y-3">
              <AnimatePresence>
                {items.map((item, i) => (
                  <SearchCard
                    key={item.url + item.title}
                    item={item}
                    index={startIndex + i}
                    isCompared={compareKeys.has(item.url + item.title)}
                    onToggleCompare={onToggleCompare}
                    onCopyLink={onCopyLink}
                  />
                ))}
              </AnimatePresence>
            </div>
          </div>
        )
      })}
    </div>
  )
}
