import { post, get } from '@/lib/api'
import type { User } from '@/types'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
  department_id?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export async function login(params: LoginRequest): Promise<AuthResponse> {
  return post<AuthResponse>('/auth/login', params)
}

export async function register(params: RegisterRequest): Promise<AuthResponse> {
  return post<AuthResponse>('/auth/register', params)
}

export async function getMe(): Promise<User> {
  return get<User>('/auth/me')
}

export async function verifyToken(): Promise<{ valid: boolean; user_id: string | null }> {
  return post('/auth/verify')
}

export interface SSOLoginRequest {
  email: string
  name: string
  sso_provider: string
  sso_id: string
  department_id?: string
}

export async function ssoLogin(params: SSOLoginRequest): Promise<AuthResponse> {
  return post<AuthResponse>('/auth/sso', params)
}
