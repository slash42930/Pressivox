import type { SearchResult } from '../types'

export function toggleCompareItems(
  current: SearchResult[],
  item: SearchResult,
  maxItems = 3,
): { next: SearchResult[]; changed: boolean; maxReached: boolean } {
  const key = item.url + item.title
  const exists = current.some(c => c.url + c.title === key)

  if (exists) {
    return {
      next: current.filter(c => c.url + c.title !== key),
      changed: true,
      maxReached: false,
    }
  }

  if (current.length >= maxItems) {
    return { next: current, changed: false, maxReached: true }
  }

  return {
    next: [...current, item],
    changed: true,
    maxReached: false,
  }
}
