import type { SearchResult } from '../types'
import { normalizeScore, formatPublishedDate } from '../utils'

interface ComparePanelProps {
  items: SearchResult[]
  kind: 'search' | 'research'
}

export function ComparePanel({ items, kind }: ComparePanelProps) {
  if (!items.length) return null

  const title = kind === 'search' ? 'Search compare' : 'Research compare'

  return (
    <div className="rounded-3xl bg-slate-950 border border-slate-800 p-4 mt-6">
      <div className="flex items-center justify-between gap-4 mb-4">
        <h4 className="text-lg font-semibold">{title}</h4>
        <span className="text-sm text-slate-400">Up to 3 items</span>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {items.map((item, i) => {
          const score = normalizeScore(item)
          const publishedInfo = formatPublishedDate(item.published_date)
          return (
            <div key={i} className="rounded-2xl bg-slate-900 border border-slate-800 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                {item.source || 'unknown source'}
              </div>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-cyan-300 hover:text-cyan-200"
              >
                {item.title || 'Untitled'}
              </a>
              {item.meaning && (
                <div className="text-xs text-fuchsia-300 mt-2">{item.meaning}</div>
              )}
              {publishedInfo && (
                <div className="text-xs text-emerald-300 mt-2">{publishedInfo}</div>
              )}
              {item.snippet && (
                <p className="text-sm text-slate-300 mt-3 leading-6 line-clamp-3">
                  {item.snippet}
                </p>
              )}
              <div className="text-xs text-slate-500 mt-3">
                Confidence: {Number.isFinite(score) ? score.toFixed(2) : '-'}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
