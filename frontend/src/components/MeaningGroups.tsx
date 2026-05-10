import type { MeaningGroup } from '../types'
import { Favicon } from './Favicon'
import { normalizeScore } from '../utils'
import { EmptyState } from './EmptyState'

interface MeaningGroupsProps {
  groups: MeaningGroup[]
}

export function MeaningGroups({ groups }: MeaningGroupsProps) {
  if (!groups.length) return <EmptyState message="No ambiguity groups returned." />

  return (
    <div className="space-y-3">
      {groups.map((group, gi) => (
        <details
          key={gi}
          className="rounded-2xl bg-slate-950 border border-slate-800 p-4"
          open
        >
          <summary className="cursor-pointer list-none flex items-center justify-between gap-4">
            <div>
              <div className="font-semibold">{group.meaning || 'Unknown meaning'}</div>
              <div className="text-xs text-slate-500 mt-1">
                {(group.results || []).length} result(s)
              </div>
            </div>
            <div className="text-xs text-slate-400">Grouped by meaning</div>
          </summary>

          <div className="mt-3 space-y-3">
            {(group.results || []).map((item, ri) => {
              const score = normalizeScore(item)
              return (
                <div
                  key={ri}
                  className="rounded-xl bg-slate-900 border border-slate-800 p-3"
                >
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-cyan-300 hover:text-cyan-200"
                    >
                      {item.title || 'Untitled'}
                    </a>
                    <div className="text-xs text-slate-400 shrink-0">
                      {Number.isFinite(score) ? score.toFixed(2) : '-'}
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 mb-2 flex items-center gap-2">
                    <Favicon favicon={item.favicon} className="w-3.5 h-3.5" />
                    <span>{item.source || 'unknown source'}</span>
                  </div>
                  {item.snippet && (
                    <div className="text-sm text-slate-300 leading-relaxed">{item.snippet}</div>
                  )}
                </div>
              )
            })}
          </div>
        </details>
      ))}
    </div>
  )
}
