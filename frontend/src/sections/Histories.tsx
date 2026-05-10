import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { apiClient } from '../api/client'
import type { SearchHistoryItem, ExtractHistoryItem } from '../types'
import { SearchHistoryCard, ExtractHistoryCard } from '../components/HistoryCards'
import { EmptyState } from '../components/EmptyState'

export function HistoriesSection() {
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([])
  const [extractHistory, setExtractHistory] = useState<ExtractHistoryItem[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [extractLoading, setExtractLoading] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [extractError, setExtractError] = useState('')

  const loadSearchHistory = useCallback(async () => {
    setSearchLoading(true)
    setSearchError('')
    try {
      const data = await apiClient.searchHistory()
      setSearchHistory(Array.isArray(data) ? data : [])
    } catch (err) {
      setSearchError(`Loading search history failed: ${(err as Error).message}`)
    } finally {
      setSearchLoading(false)
    }
  }, [])

  const loadExtractHistory = useCallback(async () => {
    setExtractLoading(true)
    setExtractError('')
    try {
      const data = await apiClient.extractHistory()
      setExtractHistory(Array.isArray(data) ? data : [])
    } catch (err) {
      setExtractError(`Loading extract history failed: ${(err as Error).message}`)
    } finally {
      setExtractLoading(false)
    }
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25 }}
    >
      <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 mb-6">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold">Histories</h2>
          <p className="text-slate-400">Reopen your recent searches and extracted pages.</p>
        </div>
        <div className="mb-6 rounded-2xl bg-slate-950 border border-slate-800 px-4 py-3 text-sm text-slate-300">
          Tip: histories are useful for continuing work without repeating the same query.
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={loadSearchHistory}
            disabled={searchLoading}
            className="rounded-2xl bg-cyan-600 hover:bg-cyan-500 px-4 py-3 font-medium transition disabled:opacity-60"
          >
            {searchLoading ? 'Loading…' : 'Load Search History'}
          </button>
          <button
            onClick={loadExtractHistory}
            disabled={extractLoading}
            className="rounded-2xl bg-amber-600 hover:bg-amber-500 px-4 py-3 font-medium transition disabled:opacity-60"
          >
            {extractLoading ? 'Loading…' : 'Load Extract History'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6">
          <h3 className="text-xl font-semibold mb-4">Search history</h3>
          {searchError ? (
            <EmptyState message={searchError} />
          ) : searchHistory.length > 0 ? (
            <div className="space-y-3">
              {searchHistory.map((item, i) => (
                <SearchHistoryCard key={i} item={item} />
              ))}
            </div>
          ) : (
            <EmptyState message="Load history above to see recent searches." />
          )}
        </div>

        <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6">
          <h3 className="text-xl font-semibold mb-4">Extract history</h3>
          {extractError ? (
            <EmptyState message={extractError} />
          ) : extractHistory.length > 0 ? (
            <div className="space-y-3">
              {extractHistory.map((item, i) => (
                <ExtractHistoryCard key={i} item={item} />
              ))}
            </div>
          ) : (
            <EmptyState message="Load history above to see recent extractions." />
          )}
        </div>
      </div>
    </motion.div>
  )
}
