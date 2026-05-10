import type { SearchResult } from '../types'
import { TRUSTED_SITES, DOMAIN_VIEW_WEIGHT, normalizeDomain, domainFromResult } from '../data/trusted-sites'

// ─── Score helpers ────────────────────────────────────────────────────────────

export function normalizeScore(item: SearchResult): number {
  const value = typeof item.rerank_score === 'number' ? item.rerank_score : item.score
  return typeof value === 'number' && Number.isFinite(value) ? value : -Infinity
}

export function recencyPoints(publishedDate?: string): number {
  if (!publishedDate) return 8
  const parsed = new Date(publishedDate)
  if (Number.isNaN(parsed.getTime())) return 8
  const ageDays = Math.max(0, (Date.now() - parsed.getTime()) / (1000 * 60 * 60 * 24))
  if (ageDays <= 1) return 28
  if (ageDays <= 2) return 24
  if (ageDays <= 4) return 20
  if (ageDays <= 7) return 14
  return 6
}

export function viewWeightForDomain(domain: string, language = 'english'): number {
  const normalized = normalizeDomain(domain)
  if (DOMAIN_VIEW_WEIGHT[normalized] != null) return DOMAIN_VIEW_WEIGHT[normalized]
  if (language === 'romanian' && normalized.endsWith('.ro')) return 12
  return 10
}

export function providerConfidence(item: SearchResult): number {
  const value = typeof item.rerank_score === 'number' ? item.rerank_score : item.score
  if (!Number.isFinite(value) || value === undefined) return 0
  return Math.max(0, Math.min(30, (value as number) * 6))
}

export function scoreWeeklyHeadline(item: SearchResult, language = 'english'): number {
  const domain = domainFromResult(item)
  const view = viewWeightForDomain(domain, language)
  const freshness = recencyPoints(item.published_date)
  const confidence = providerConfidence(item)
  return view * 0.65 + freshness * 0.7 + confidence
}

export function pickTopWeeklyHeadlines(
  results: SearchResult[],
  language = 'english',
  limit = 3,
): (SearchResult & { _dashboardDomain: string })[] {
  const scored = (Array.isArray(results) ? results : [])
    .map(item => ({
      item,
      domain: domainFromResult(item),
      rank: scoreWeeklyHeadline(item, language),
    }))
    .filter(entry => entry.item && entry.item.url && entry.item.title)
    .sort((a, b) => b.rank - a.rank)

  const picked: (SearchResult & { _dashboardDomain: string })[] = []
  const usedDomains = new Set<string>()
  for (const entry of scored) {
    if (picked.length >= limit) break
    if (entry.domain && usedDomains.has(entry.domain)) continue
    picked.push({ ...entry.item, _dashboardDomain: entry.domain || 'unknown source' })
    if (entry.domain) usedDomains.add(entry.domain)
  }
  return picked
}

export type ConfidenceTier = 'best' | 'good' | 'other'

export function confidenceTier(score: number, maxScore: number): ConfidenceTier {
  if (!Number.isFinite(score) || maxScore <= 0) return 'other'
  const ratio = score / maxScore
  if (ratio >= 0.8) return 'best'
  if (ratio >= 0.55) return 'good'
  return 'other'
}

export type SortMode = 'relevance' | 'date' | 'source' | 'title'

export function sortResults(results: SearchResult[], mode: SortMode): SearchResult[] {
  const copy = [...results]
  if (mode === 'date') {
    return copy.sort(
      (a, b) =>
        new Date(b.published_date || 0).getTime() -
        new Date(a.published_date || 0).getTime(),
    )
  }
  if (mode === 'source') {
    return copy.sort(
      (a, b) =>
        String(a.source || '').localeCompare(String(b.source || '')) ||
        normalizeScore(b) - normalizeScore(a),
    )
  }
  if (mode === 'title') {
    return copy.sort((a, b) => String(a.title || '').localeCompare(String(b.title || '')))
  }
  return copy.sort((a, b) => normalizeScore(b) - normalizeScore(a))
}

// ─── Formatting ───────────────────────────────────────────────────────────────

export function formatPublishedDate(dateValue?: string): string {
  if (!dateValue) return ''
  const parsed = new Date(dateValue)
  if (Number.isNaN(parsed.getTime())) return ''
  const ageDays = Math.max(
    0,
    Math.floor((Date.now() - parsed.getTime()) / (1000 * 60 * 60 * 24)),
  )
  return `${parsed.toLocaleString()} · ~${ageDays} day(s) old`
}

export function formatCreatedAt(value?: string): string {
  if (!value) return ''
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return ''
  return parsed.toLocaleString()
}

export function trustedBadgeClass(source = ''): string {
  const domain = normalizeDomain(source)
  return TRUSTED_SITES.includes(domain)
    ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
    : 'bg-slate-800 text-slate-300 border border-slate-700'
}

export function isTrusted(source = ''): boolean {
  return TRUSTED_SITES.includes(normalizeDomain(source))
}

// ─── Form helpers ─────────────────────────────────────────────────────────────

export function parseDomains(value: string): string[] {
  return value
    .split(',')
    .map(v => v.trim())
    .filter(Boolean)
}

export function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export function downloadTextFile(filename: string, text: string): void {
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function copyToClipboard(text: string): Promise<void> {
  await navigator.clipboard.writeText(text)
}
