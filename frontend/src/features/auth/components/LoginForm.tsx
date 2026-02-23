import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Brain, Mail, Lock, User, Loader2, MessageSquare, Shield } from 'lucide-react'
import { Button, Input } from '@/components/ui'
import { useAuthStore } from '../store/authStore'
import { login, register, ssoLogin } from '../api/authApi'
import { cn } from '@/lib/utils'

type Mode = 'login' | 'register'

export function LoginForm() {
  const navigate = useNavigate()
  const { login: storeLogin } = useAuthStore()
  
  const [mode, setMode] = useState<Mode>('login')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      if (mode === 'login') {
        const result = await login({
          email: formData.email,
          password: formData.password,
        })
        storeLogin(result.user, result.access_token)
      } else {
        const result = await register({
          name: formData.name,
          email: formData.email,
          password: formData.password,
        })
        storeLogin(result.user, result.access_token)
      }
      navigate('/chat')
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || '오류가 발생했습니다')
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background-secondary p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent text-white mb-4">
            <Brain className="h-8 w-8" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">AI Memory Agent</h1>
          <p className="text-sm text-foreground-secondary mt-1">
            멀티채팅 환경에서 권한 기반 메모리 관리
          </p>
        </div>

        {/* Form Card */}
        <div className="card p-6">
          {/* Mode Toggle */}
          <div className="flex gap-2 p-1 bg-background-secondary rounded-lg mb-6">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={cn(
                'flex-1 py-2 text-sm font-medium rounded-md transition-colors',
                mode === 'login'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-foreground-secondary hover:text-foreground'
              )}
            >
              로그인
            </button>
            <button
              type="button"
              onClick={() => setMode('register')}
              className={cn(
                'flex-1 py-2 text-sm font-medium rounded-md transition-colors',
                mode === 'register'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-foreground-secondary hover:text-foreground'
              )}
            >
              회원가입
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-error/10 text-error text-sm">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">이름</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
                  <Input
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="홍길동"
                    className="pl-10"
                    required
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">이메일</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
                <Input
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="example@company.com"
                  className="pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">비밀번호</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
                <Input
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="••••••••"
                  className="pl-10"
                  required
                  minLength={4}
                />
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  처리 중...
                </>
              ) : mode === 'login' ? (
                '로그인'
              ) : (
                '회원가입'
              )}
            </Button>
          </form>

          {/* Dev Mode */}
          <div className="mt-6 pt-4 border-t border-border">
            <p className="text-xs text-foreground-muted text-center mb-2">
              데모용 테스트 계정
            </p>
            <Button
              type="button"
              variant="ghost"
              className="w-full text-xs"
              onClick={() => {
                setFormData({
                  name: 'hy.joo',
                  email: 'admin@test.com',
                  password: 'test123',
                })
              }}
            >
              테스트 계정으로 채우기 (hy.joo)
            </Button>
          </div>

          {/* SSO / Mattermost Login */}
          <div className="mt-6 pt-4 border-t border-border space-y-2">
            <p className="text-xs text-foreground-muted text-center mb-2">
              외부 인증
            </p>
            {/* SSO (SAML) Login */}
            <Button
              type="button"
              variant="outline"
              className="w-full gap-2"
              onClick={async () => {
                setError(null)
                setIsLoading(true)
                try {
                  const email = formData.email || 'admin@test.com'
                  const name = formData.name || email.split('@')[0]
                  const result = await ssoLogin({
                    email,
                    name,
                    sso_provider: 'saml',
                    sso_id: `saml-${email.replace('@', '-')}`,
                  })
                  storeLogin(result.user, result.access_token)
                  navigate('/chat')
                } catch (err: unknown) {
                  const error = err as { response?: { data?: { detail?: string } } }
                  setError(error.response?.data?.detail || 'SSO 로그인 실패')
                } finally {
                  setIsLoading(false)
                }
              }}
              disabled={isLoading}
            >
              <Shield className="h-4 w-4" />
              {isLoading ? '처리 중...' : 'SSO 로그인'}
            </Button>
            {/* Mattermost Login */}
            <Button
              type="button"
              variant="outline"
              className="w-full gap-2"
              onClick={async () => {
                setError(null)
                setIsLoading(true)
                try {
                  const email = formData.email || 'admin@test.com'
                  const name = formData.name || email.split('@')[0]
                  const result = await ssoLogin({
                    email,
                    name,
                    sso_provider: 'mattermost',
                    sso_id: `mm-${email.replace('@', '-')}`,
                  })
                  storeLogin(result.user, result.access_token)
                  navigate('/chat')
                } catch (err: unknown) {
                  const error = err as { response?: { data?: { detail?: string } } }
                  setError(error.response?.data?.detail || 'Mattermost 로그인 실패')
                } finally {
                  setIsLoading(false)
                }
              }}
              disabled={isLoading}
            >
              <MessageSquare className="h-4 w-4" />
              {isLoading ? '처리 중...' : 'Mattermost로 로그인'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
