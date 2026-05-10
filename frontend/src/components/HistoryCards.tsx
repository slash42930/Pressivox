import type { SearchHistoryItem, ExtractHistoryItem } from '../types'
import { formatCreatedAt } from '../utils'

interface SearchHistoryCardProps {
  item: SearchHistoryItem
}

export function SearchHistoryCard({ item }: SearchHistoryCardProps) {
  const createdAt = formatCreatedAt(item.created_at)
  return (
    <div className="rounded-2xl bg-slate-950 border border-slate-800 p-4">
      <div className="font-medium mb-1">{item.query || '-'}</div>
      <div className="text-sm text-slate-400 mb-2">topic: {item.topic || '-'}</div>
      <div className="text-sm text-slate-300 mb-2">results: {item.result_count ?? 0}</div>
      <div className="text-xs text-slate-400 mb-2">
        selected sources: {item.selected_source_count ?? 0} · meaning groups:{' '}
        {item.meaning_group_count ?? 0}
      </div>
      <div className="flex flex-wrap gap-2 mb-2">
        <span
          className={`rounded-full px-2 py-1 text-xs border ${
            item.ambiguous
              ? 'bg-fuchsia-500/10 text-fuchsia-300 border-fuchsia-500/30'
              : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
          }`}
        >
          {item.ambiguous ? 'ambiguous' : 'clear'}
        </span>
        <span
          className={`rounded-full px-2 py-1 text-xs border ${
            item.has_summary
              ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
              : 'bg-slate-800 text-slate-300 border-slate-700'
          }`}
        >
          {item.has_summary ? 'summary' : 'no summary'}
        </span>
      </div>
      {createdAt && <div className="text-xs text-slate-500 mb-2">{createdAt}</div>}
      {item.answer && (
        <div className="text-sm text-slate-400 line-clamp-4">{item.answer}</div>
      )}
    </div>
  )
}

interface ExtractHistoryCardProps {
  item: ExtractHistoryItem
}

export function ExtractHistoryCard({ item }: ExtractHistoryCardProps) {
  const createdAt = formatCreatedAt(item.created_at)
  return (
    <div className="rounded-2xl bg-slate-950 border border-slate-800 p-4">
      <a
        href={item.url}
        target="_blank"
        rel="noopener noreferrer"
        className="font-medium text-cyan-300 hover:text-cyan-200"
      >
        {item.title || 'Untitled'}
      </a>
      <div className="text-sm text-slate-400 mt-1">{item.source || 'unknown source'}</div>
      <div className="text-sm text-slate-300 mt-2">length: {item.content_length ?? 0}</div>
      {createdAt && <div className="text-xs text-slate-500 mt-2">{createdAt}</div>}
    </div>
  )
}
