import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  login: (user: User, token: string) => void
  logout: () => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,
      
      setUser: (user) => set({ user }),
      
      setToken: (token) => {
        if (token) {
          localStorage.setItem('access_token', token)
        } else {
          localStorage.removeItem('access_token')
        }
        set({ token })
      },
      
      login: (user, token) => {
        localStorage.setItem('access_token', token)
        localStorage.setItem('user_id', user.id)
        set({ user, token })
      },
      
      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_id')
        // persist 스토리지는 삭제하지 않고 상태만 초기화
        set({ user: null, token: null })
      },
      
      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, token: state.token }),
    }
  )
)

// 계산된 값: isAuthenticated
export const useIsAuthenticated = () => {
  const { user, token } = useAuthStore()
  return !!(user && token)
}

// 개발용 mock 사용자 설정
export function setDevUser() {
  const devUser: User = {
    id: 'dev-user-001',
    name: '개발자',
    email: 'admin@test.com',
    role: 'admin',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  
  localStorage.setItem('user_id', devUser.id)
  useAuthStore.getState().setUser(devUser)
}

// 개발 환경에서 자동으로 setDevUser()를 호출하지 않음
// 필요할 때 수동으로 호출하여 사용
// if (import.meta.env.DEV) {
//   setDevUser()
// }
