// ─── Request types ────────────────────────────────────────────────────────────

export interface SearchRequest {
  query: string
  topic: 'general' | 'news'
  language: 'english' | 'romanian'
  max_results: number
  summarize: boolean
  extract_top_results: boolean
  include_domains: string[]
  exclude_domains: string[]
  search_depth: 'basic' | 'advanced'
  time_range: string | null
  start_date: string | null
  end_date: string | null
  exact_match: boolean
  include_answer: boolean
  include_raw_content: boolean
  include_images: boolean
  include_image_descriptions: boolean
  include_favicon: boolean
  auto_parameters: boolean
}

export interface ExtractRequest {
  url: string
}

// ─── Result / item types ──────────────────────────────────────────────────────

export interface SearchResult {
  title: string
  url: string
  source?: string
  score?: number
  rerank_score?: number
  published_date?: string
  favicon?: string
  snippet?: string
  meaning?: string
}

export interface MeaningGroup {
  meaning: string
  results: SearchResult[]
}

export interface SearchHistoryItem {
  id?: number
  query: string
  topic: string
  result_count: number
  selected_source_count: number
  meaning_group_count: number
  has_summary: boolean
  ambiguous: boolean
  answer?: string
  created_at: string
}

export interface ExtractHistoryItem {
  id?: number
  url: string
  title: string
  source: string
  content_length: number
  created_at: string
}

// ─── Response types ───────────────────────────────────────────────────────────

export interface SearchResponse {
  query: string
  topic: string
  provider: string
  summary?: string
  extracted_summary?: string
  answer?: string
  results: SearchResult[]
  selected_sources: SearchResult[]
  meaning_groups: MeaningGroup[]
  ambiguous: boolean
  request_id?: string
  response_time?: number
  usage?: Record<string, unknown>
}

export interface ResearchResponse {
  query: string
  topic: string
  provider: string
  summary: string
  summary_points: string[]
  summary_markdown: string
  results: SearchResult[]
  selected_sources: SearchResult[]
  source_count: number
  extracted_count: number
  ambiguous: boolean
  sections?: ResearchSections
  meaning_groups: MeaningGroup[]
  request_id?: string
  response_time?: number
  usage?: Record<string, unknown>
}

export interface ResearchSourceItem {
  title: string
  url: string
  source?: string
  snippet?: string
  score?: number
  published_date?: string
}

export interface ResearchSections {
  concise_summary: string
  key_findings: string[]
  detailed_analysis: string
  sources: ResearchSourceItem[]
  limitations: string[]
  suggested_follow_up_queries: string[]
  confidence?: 'low' | 'medium' | 'high'
}

export interface ExtractResponse {
  title: string
  url: string
  source: string
  final_url: string
  content_length: number
  extracted_text: string
  important_passages: string[]
}

export interface QueryAnalysisResponse {
  topic: string
  token_count: number
  is_short_query: boolean
  ambiguous_likely: boolean
  recommended_topic?: string
  suggested_queries?: string[]
}

export interface HealthResponse {
  status: string
}

export interface ResearchTaskResponse {
  task_id: string
  status: string
  created_at: string
}

export interface ResearchTaskStatusResponse {
  task_id: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'unknown'
  is_terminal: boolean
  result_count: number
  result_sources: Array<{
    title: string
    url: string
    source?: string
    snippet?: string
  }>
  error_message?: string | null
}

export interface AuthUser {
  id: number
  username: string
  role: string
  full_name?: string | null
  created_at: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}

// ─── UI state helpers ─────────────────────────────────────────────────────────

export type TabName = 'dashboard' | 'search' | 'research' | 'extract' | 'info' | 'histories'

export type SortMode = 'relevance' | 'date' | 'source' | 'title'

export interface SessionStats {
  searchRuns: number
  researchRuns: number
  extractRuns: number
  compareCount: number
  lastQuery: string
  lastSearchSnap: SearchResponse | null
  lastResearchSnap: ResearchResponse | null
}
