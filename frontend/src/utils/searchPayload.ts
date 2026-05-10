import type { SearchRequest } from '../types'
import { parseDomains, toIsoDate } from './index'

export interface SearchPayloadFormValues {
  query: string
  topic: 'general' | 'news'
  language: 'english' | 'romanian'
  maxResults: number
  includeDomains: string
  excludeDomains: string
  maxAgeDays: number
  startDate: string
  endDate: string
  timeRange?: string
}

function resolveDateRange(form: SearchPayloadFormValues): { start: string | null; end: string | null } {
  let start = form.startDate || null
  let end = form.endDate || null

  if (form.maxAgeDays > 0) {
    const now = new Date()
    const rangeStart = new Date(now)
    rangeStart.setDate(rangeStart.getDate() - form.maxAgeDays)
    start = toIsoDate(rangeStart)
    end = toIsoDate(now)
  }

  return { start, end }
}

export function buildSearchPayload(
  form: SearchPayloadFormValues,
  options: { allowTimeRange: boolean },
): SearchRequest {
  const { start, end } = resolveDateRange(form)

  const includeDomains = parseDomains(form.includeDomains)
  const excludeDomains = parseDomains(form.excludeDomains)
  const timeRange = options.allowTimeRange && !start && !end ? form.timeRange || null : null

  return {
    query: form.query,
    topic: form.topic,
    language: form.language,
    max_results: form.maxResults,
    summarize: true,
    extract_top_results: true,
    include_domains: includeDomains,
    exclude_domains: excludeDomains,
    search_depth: 'advanced',
    time_range: timeRange,
    start_date: start,
    end_date: end,
    exact_match: false,
    include_answer: true,
    include_raw_content: true,
    include_images: false,
    include_image_descriptions: false,
    include_favicon: true,
    auto_parameters: true,
  }
}
