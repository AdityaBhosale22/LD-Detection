// Thin client for the Django REST API. The auth token is kept in localStorage
// and sent as "Authorization: Token <key>".

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')
const TOKEN_KEY = 'ld_token'

export type Role = 'student' | 'teacher' | 'parent'
export type TestKind = 'math' | 'grammar' | 'reading' | 'memory' | 'scenario'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  role: Role
}

export interface Intake {
  id?: number
  age: number
  gender: 'male' | 'female' | 'other'
  reading_difficulties: boolean
  attention_span: 'low' | 'medium' | 'high'
  academic_history: string
  learning_issues_notes: string
  created_at?: string
}

export interface Prediction {
  id: number
  label: string
  probability: number
  intake_id: number
  created_at: string
}

export interface TestResult {
  id: number
  completed: boolean
  duration_seconds: number
  completed_at?: string
  num_correct?: number
  num_total?: number
  details?: Record<string, unknown>[]
  // reading test only
  passage?: string
  transcript?: string
  wpm?: number
  accuracy?: number
}

export interface Dashboard {
  user: User
  intake: Intake | null
  prediction: Prediction | null
  tests: Record<TestKind, TestResult | null>
  areas: { area: TestKind; score: number }[]
}

export interface Recommendation {
  area: TestKind
  area_label: string
  title: string
  description: string
  url: string
  score: number
}

export interface Question {
  prompt: string
  options: string[]
}

export interface StartedTest {
  id: number
  kind: TestKind
  questions?: ({ a: number; b: number; op: '+' | '-' } | Question)[]
  passage?: string
  sequence?: number[]
  display_seconds?: number
  text?: string
}

export class ApiError extends Error {
  status: number
  fields: Record<string, string>

  constructor(status: number, message: string, fields: Record<string, string> = {}) {
    super(message)
    this.status = status
    this.fields = fields
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // storage unavailable (private mode); the session just won't persist
  }
}

let onUnauthorized: () => void = () => {}
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler
}

// DRF errors look like {"detail": "..."}, {"non_field_errors": [...]} or {"field": ["..."]}
function parseError(status: number, body: unknown): ApiError {
  if (body && typeof body === 'object') {
    const data = body as Record<string, unknown>
    if (typeof data.detail === 'string') return new ApiError(status, data.detail)
    const fields: Record<string, string> = {}
    for (const [key, value] of Object.entries(data)) {
      fields[key] = Array.isArray(value) ? String(value[0]) : String(value)
    }
    const message = fields.non_field_errors ?? Object.values(fields)[0] ?? 'Something went wrong.'
    return new ApiError(status, message, fields)
  }
  return new ApiError(status, 'Something went wrong. Please try again.')
}

async function send(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  const token = getToken()
  if (token) headers.set('Authorization', `Token ${token}`)
  if (init.body) headers.set('Content-Type', 'application/json')

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your connection and try again.')
  }

  if (response.status === 401 && token) onUnauthorized()
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw parseError(response.status, body)
  }
  return response
}

async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await send(path, { method, body: body === undefined ? undefined : JSON.stringify(body) })
  return (response.status === 204 ? undefined : await response.json()) as T
}

export const api = {
  register: (data: { email: string; password: string; first_name: string; last_name: string; role: Role }) =>
    request<{ token: string; user: User }>('/api/auth/register/', 'POST', data),
  login: (email: string, password: string) =>
    request<{ token: string; user: User }>('/api/auth/login/', 'POST', { email, password }),
  logout: () => request<void>('/api/auth/logout/', 'POST'),
  me: () => request<User>('/api/auth/me/'),

  dashboard: () => request<Dashboard>('/api/dashboard/'),
  getIntake: () => request<Intake | null>('/api/intake/'),
  saveIntake: (data: Intake) => request<Intake>('/api/intake/', 'POST', data),
  runPrediction: () => request<Prediction>('/api/predictions/', 'POST'),

  startTest: (kind: TestKind) => request<StartedTest>(`/api/tests/${kind}/start/`, 'POST'),
  submitTest: (kind: TestKind, id: number, data: unknown) =>
    request<TestResult>(`/api/tests/${kind}/${id}/submit/`, 'POST', data),
  getResult: (kind: TestKind, id: number) => request<TestResult>(`/api/tests/${kind}/${id}/`),

  recommendations: () => request<Recommendation[]>('/api/recommendations/'),

  async downloadReport() {
    const response = await send('/api/report/')
    const url = URL.createObjectURL(await response.blob())
    const link = document.createElement('a')
    link.href = url
    link.download = 'ld-report.pdf'
    link.click()
    URL.revokeObjectURL(url)
  },

  // Free-tier hosting sleeps when idle; ping early so it is awake by the time the user logs in.
  wake: () => fetch(`${API_URL}/healthz/`).catch(() => undefined),
}
