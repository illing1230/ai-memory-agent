import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from '@/components/layout/MainLayout'
import { ChatRoom } from '@/features/chat/components/ChatRoom'
import { MemorySearch } from '@/features/memory/components/MemorySearch'
import { MemoryList } from '@/features/memory/components/MemoryList'
import { LoginForm } from '@/features/auth/components/LoginForm'
import { useAuthStore } from '@/features/auth/store/authStore'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore()
  const isDev = import.meta.env.DEV
  
  if (!isDev && !isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
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
        <Route path="/login" element={<LoginForm />} />
        
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
          <Route path="memory" element={<Navigate to="/memory/search" replace />} />
          <Route path="memory/search" element={<MemorySearch />} />
          <Route path="memory/list" element={<MemoryList />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
