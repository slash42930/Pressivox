import type { SearchResult } from '../types'
import { Favicon } from './Favicon'
import { normalizeScore } from '../utils'
import { EmptyState } from './EmptyState'

interface SelectedSourcesProps {
  sources: SearchResult[]
}

export function SelectedSources({ sources }: SelectedSourcesProps) {
  if (!sources.length) return <EmptyState message="No selected sources returned." />

  return (
    <div className="space-y-3">
      {sources.map((item, index) => {
        const score = normalizeScore(item)
        return (
          <div
            key={item.url + index}
            className="rounded-2xl bg-slate-950 border border-slate-800 p-4 hover:border-fuchsia-500/30 transition-colors"
          >
            <div className="flex items-start justify-between gap-4 mb-2">
              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">
                  Selected #{index + 1}
                </div>
                {item.meaning && (
                  <div className="text-xs text-fuchsia-300 mb-1">{item.meaning}</div>
                )}
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-semibold text-fuchsia-300 hover:text-fuchsia-200"
                >
                  {item.title || 'Untitled'}
                </a>
              </div>
              <div className="text-xs text-slate-400">
                {Number.isFinite(score) ? score.toFixed(2) : '-'}
              </div>
            </div>
            <div className="text-sm text-slate-400 flex items-center gap-2">
              <Favicon favicon={item.favicon} />
              <span>{item.source || 'unknown source'}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
