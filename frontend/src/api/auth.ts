import type { LoginInput, RegisterInput, User } from '@/types/user'

const BASE_URL = '/api/auth'

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail || `Request failed with status ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export function register(input: RegisterInput): Promise<User> {
  return fetch(`${BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(input),
  }).then((res) => handle<User>(res))
}

export function login(input: LoginInput): Promise<User> {
  return fetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(input),
  }).then((res) => handle<User>(res))
}

export function logout(): Promise<void> {
  return fetch(`${BASE_URL}/logout`, { method: 'POST', credentials: 'include' }).then((res) => handle<void>(res))
}

export function getCurrentUser(): Promise<User | null> {
  return fetch(`${BASE_URL}/me`, { credentials: 'include' }).then((res) => {
    if (res.status === 401) return null
    return handle<User>(res)
  })
}
