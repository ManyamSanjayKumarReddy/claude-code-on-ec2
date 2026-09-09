export interface User {
  id: number
  email: string
  full_name: string
  created_at: string
}

export interface RegisterInput {
  email: string
  password: string
  full_name: string
}

export interface LoginInput {
  email: string
  password: string
}
