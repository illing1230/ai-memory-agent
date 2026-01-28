import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from '@/components/layout/MainLayout'
import { ChatRoom } from '@/features/chat/components/ChatRoom'
import { MemorySearch } from '@/features/memory/components/MemorySearch'
import { LoginForm } from '@/features/auth/components/LoginForm'
import { useAuthStore } from '@/features/auth/store/authStore'

// 인증 필요한 라우트 래퍼
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore()
  
  // 개발 모드에서는 인증 우회
  const isDev = import.meta.env.DEV
  
  if (!isDev && !isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  // 개발 모드에서 사용자가 없으면 자동 설정
  if (isDev && !user) {
    useAuthStore.getState().setUser({
      id: 'dev-user-001',
      name: '개발자',
      email: 'dev@test.local',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    localStorage.setItem('user_id', 'dev-user-001')
  }
  
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 공개 라우트 */}
        <Route path="/login" element={<LoginForm />} />
        
        {/* 보호된 라우트 */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="chat" element={<ChatRoom />} />
          <Route path="chat/:roomId" element={<ChatRoom />} />
          <Route path="memory" element={<MemorySearch />} />
          <Route path="memory/search" element={<MemorySearch />} />
        </Route>
        
        {/* 404 */}
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
