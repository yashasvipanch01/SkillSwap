const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'
const TOKEN_KEY = 'skillswap-token'

export type Me = {
  id: number
  name: string
  username: string
  initials: string
  email: string
  bio: string
  teach: string[]
  learn: string[]
  verified: string[]
  preferences: string[]
  availability: string[]
  points: number
  rating: number | null
  rating_count: number
  onboarding_complete: boolean
}
export type Person = Omit<Me, 'email' | 'onboarding_complete'>
export type Match = { person: Person; score: number; reciprocal: boolean; they_teach_you: string[]; you_teach_them: string[]; shared_availability: string[]; shared_preferences: string[] }
export type ExchangeItem = { id: number; status: 'pending' | 'accepted' | 'rejected' | 'cancelled' | 'completed'; topic: string; note: string; role: 'requester' | 'partner'; person: { id: number; name: string; username: string; initials: string } }
export type AssessmentSummary = { id: number; skill: string; title: string }
export type AssessmentDetail = AssessmentSummary & { pass_mark: number; questions: { id: number; position: number; prompt: string; options: string[] }[] }
export type Attempt = { id: number; skill: string; score: number; correct_count: number; total: number; passed: boolean; verified: boolean; newly_verified: boolean }
export type Progress = { points: number; level: number; points_to_next_level: number; verified_skills: number; completed_exchanges: number; completed_sessions: number; learning_goals: string[]; achievements: { code: string; title: string; description: string }[] }

export const getToken = () => (typeof window === 'undefined' ? null : window.localStorage.getItem(TOKEN_KEY))
export const setToken = (token: string) => window.localStorage.setItem(TOKEN_KEY, token)
export const clearToken = () => window.localStorage.removeItem(TOKEN_KEY)

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

export function messageOf(error: unknown) {
  return error instanceof Error ? error.message : 'Something went wrong'
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken()
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers },
    })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Is the backend running on port 8000?')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = Array.isArray(body.detail) ? body.detail[0]?.msg : body.detail
    throw new ApiError(response.status, typeof detail === 'string' ? detail : 'Something went wrong')
  }
  return response.json() as Promise<T>
}

export const post = <T>(path: string, body?: unknown) => api<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
