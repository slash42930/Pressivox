import type {
  AuthResponse,
  AuthUser,
  SearchRequest,
  SearchResponse,
  ResearchResponse,
  ExtractResponse,
  QueryAnalysisResponse,
  HealthResponse,
  SearchHistoryItem,
  ExtractHistoryItem,
} from '../types'

const API_BASE = '/api/v1'
const AUTH_TOKEN_KEY = 'pressivox.auth_token'
const AUTH_REFRESH_TOKEN_KEY = 'pressivox.refresh_token'
const AUTH_USER_KEY = 'pressivox.auth_user'

// ─── Session ID ───────────────────────────────────────────────────────────────

function getSessionId(): string {
  const KEY = 'pressivox.session_id'
  const existing = sessionStorage.getItem(KEY)
  if (existing) return existing
  const created =
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`
  sessionStorage.setItem(KEY, created)
  return created
}

function getAccessToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

function setAuth(auth: AuthResponse): void {
  localStorage.setItem(AUTH_TOKEN_KEY, auth.access_token)
  localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, auth.refresh_token)
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(auth.user))
}

function clearAuth(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY)
  localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY)
  localStorage.removeItem(AUTH_USER_KEY)
}

function getRefreshToken(): string | null {
  return localStorage.getItem(AUTH_REFRESH_TOKEN_KEY)
}

async function tryRefreshAuth(): Promise<boolean> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return false

  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Session-Id': getSessionId(),
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!response.ok) {
    clearAuth()
    return false
  }

  const data = (await response.json()) as AuthResponse
  setAuth(data)
  return true
}

function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(AUTH_USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    return null
  }
}

// ─── Core fetch wrapper ───────────────────────────────────────────────────────

async function request<T>(
  path: string,
  method = 'GET',
  body?: unknown,
  allowRefresh = true,
): Promise<T> {
  const token = getAccessToken()
  const init: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Session-Id': getSessionId(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  }
  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }
  const response = await fetch(`${API_BASE}${path}`, init)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (response.status === 401) {
      const isAuthEndpoint = path.startsWith('/auth/login') || path.startsWith('/auth/register') || path.startsWith('/auth/refresh')
      if (allowRefresh && !isAuthEndpoint) {
        const refreshed = await tryRefreshAuth()
        if (refreshed) {
          return request<T>(path, method, body, false)
        }
      }
      const hadAnyAuth = Boolean(token || getRefreshToken())
      clearAuth()
      if (!isAuthEndpoint && !hadAnyAuth) {
        throw new Error('Please sign in to use this feature.')
      }
    }
    const detail = (data as { detail?: string }).detail
    throw new Error(detail || `HTTP ${response.status}`)
  }
  return data as T
}

// ─── API surface ──────────────────────────────────────────────────────────────

export const apiClient = {
  register: (username: string, password: string, fullName?: string) =>
    request<AuthResponse>('/auth/register', 'POST', {
      username,
      password,
      ...(fullName ? { full_name: fullName } : {}),
    }).then(data => {
      setAuth(data)
      return data
    }),

  login: (username: string, password: string) =>
    request<AuthResponse>('/auth/login', 'POST', { username, password }).then(data => {
      setAuth(data)
      return data
    }),

  me: () => request<AuthUser>('/auth/me'),

  logout: () => {
    clearAuth()
  },

  getStoredUser,

  health: () => request<HealthResponse>('/health'),

  search: (payload: SearchRequest) =>
    request<SearchResponse>('/search', 'POST', payload),

  searchAnalyze: (q: string, topic: string) =>
    request<QueryAnalysisResponse>(
      `/search/analyze?q=${encodeURIComponent(q)}&topic=${encodeURIComponent(topic)}`,
    ),

  searchHistory: (limit = 20) =>
    request<SearchHistoryItem[]>(`/search/history?limit=${limit}`),

  research: (payload: SearchRequest) =>
    request<ResearchResponse>('/research', 'POST', payload),

  extract: (url: string) =>
    request<ExtractResponse>('/extract', 'POST', { url }),

  extractHistory: (limit = 20) =>
    request<ExtractHistoryItem[]>(`/extract/history?limit=${limit}`),
}
