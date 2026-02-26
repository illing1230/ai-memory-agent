import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore, useIsAuthenticated, setDevUser } from '../authStore'
import { renderHook, act } from '@testing-library/react'
import type { User } from '@/types'

const mockUser: User = {
  id: 'user-001',
  name: 'Test User',
  email: 'test@example.com',
  role: 'member',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const mockAdminUser: User = {
  id: 'admin-001',
  name: 'Admin User',
  email: 'admin@example.com',
  role: 'admin',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset the zustand store between tests
    act(() => {
      useAuthStore.setState({ user: null, token: null, isLoading: false })
    })
    localStorage.clear()
  })

  describe('initial state', () => {
    it('starts with null user and token', () => {
      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isLoading).toBe(false)
    })
  })

  describe('setUser', () => {
    it('sets the user', () => {
      act(() => {
        useAuthStore.getState().setUser(mockUser)
      })
      expect(useAuthStore.getState().user).toEqual(mockUser)
    })

    it('can set user to null', () => {
      act(() => {
        useAuthStore.getState().setUser(mockUser)
      })
      act(() => {
        useAuthStore.getState().setUser(null)
      })
      expect(useAuthStore.getState().user).toBeNull()
    })
  })

  describe('setToken', () => {
    it('sets the token and stores in localStorage', () => {
      act(() => {
        useAuthStore.getState().setToken('my-token-123')
      })

      expect(useAuthStore.getState().token).toBe('my-token-123')
      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'my-token-123')
    })

    it('removes token from localStorage when set to null', () => {
      act(() => {
        useAuthStore.getState().setToken('my-token-123')
      })
      act(() => {
        useAuthStore.getState().setToken(null)
      })

      expect(useAuthStore.getState().token).toBeNull()
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
    })
  })

  describe('login', () => {
    it('sets user and token', () => {
      act(() => {
        useAuthStore.getState().login(mockUser, 'login-token')
      })

      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockUser)
      expect(state.token).toBe('login-token')
    })

    it('stores token and user_id in localStorage', () => {
      act(() => {
        useAuthStore.getState().login(mockUser, 'login-token')
      })

      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'login-token')
      expect(localStorage.setItem).toHaveBeenCalledWith('user_id', 'user-001')
    })
  })

  describe('logout', () => {
    it('clears user and token', () => {
      act(() => {
        useAuthStore.getState().login(mockUser, 'login-token')
      })
      act(() => {
        useAuthStore.getState().logout()
      })

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
    })

    it('removes token and user_id from localStorage', () => {
      act(() => {
        useAuthStore.getState().login(mockUser, 'login-token')
      })
      act(() => {
        useAuthStore.getState().logout()
      })

      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('user_id')
    })
  })

  describe('setLoading', () => {
    it('sets isLoading to true', () => {
      act(() => {
        useAuthStore.getState().setLoading(true)
      })
      expect(useAuthStore.getState().isLoading).toBe(true)
    })

    it('sets isLoading to false', () => {
      act(() => {
        useAuthStore.getState().setLoading(true)
      })
      act(() => {
        useAuthStore.getState().setLoading(false)
      })
      expect(useAuthStore.getState().isLoading).toBe(false)
    })
  })
})

describe('useIsAuthenticated', () => {
  beforeEach(() => {
    act(() => {
      useAuthStore.setState({ user: null, token: null, isLoading: false })
    })
  })

  it('returns false when no user and no token', () => {
    const { result } = renderHook(() => useIsAuthenticated())
    expect(result.current).toBe(false)
  })

  it('returns false when user exists but no token', () => {
    act(() => {
      useAuthStore.setState({ user: mockUser, token: null })
    })
    const { result } = renderHook(() => useIsAuthenticated())
    expect(result.current).toBe(false)
  })

  it('returns false when token exists but no user', () => {
    act(() => {
      useAuthStore.setState({ user: null, token: 'some-token' })
    })
    const { result } = renderHook(() => useIsAuthenticated())
    expect(result.current).toBe(false)
  })

  it('returns true when both user and token exist', () => {
    act(() => {
      useAuthStore.setState({ user: mockUser, token: 'some-token' })
    })
    const { result } = renderHook(() => useIsAuthenticated())
    expect(result.current).toBe(true)
  })
})

describe('setDevUser', () => {
  beforeEach(() => {
    act(() => {
      useAuthStore.setState({ user: null, token: null, isLoading: false })
    })
    localStorage.clear()
  })

  it('sets a dev user in the store', () => {
    act(() => {
      setDevUser()
    })

    const user = useAuthStore.getState().user
    expect(user).not.toBeNull()
    expect(user?.id).toBe('dev-user-001')
    expect(user?.name).toBe('개발자')
    expect(user?.email).toBe('admin@test.com')
    expect(user?.role).toBe('admin')
  })

  it('sets user_id in localStorage', () => {
    act(() => {
      setDevUser()
    })

    expect(localStorage.setItem).toHaveBeenCalledWith('user_id', 'dev-user-001')
  })
})
