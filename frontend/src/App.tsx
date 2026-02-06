import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from '@/components/layout/MainLayout'
import { ChatRoom } from '@/features/chat/components/ChatRoom'
import { MemorySearch } from '@/features/memory/components/MemorySearch'
import { MemoryList } from '@/features/memory/components/MemoryList'
import { ProjectManagement } from '@/features/project/components/ProjectManagement'
import { AdminPage } from '@/features/admin/components/AdminPage'
import { DocumentPage } from '@/features/document/components/DocumentPage'
import { ChatRoomManagement } from '@/features/chatroom/components/ChatRoomManagement'
import { LoginForm } from '@/features/auth/components/LoginForm'
import { AgentMarketplace, MyAgentInstances, AgentTypeManagement } from '@/features/agent/components'
import { useIsAuthenticated } from '@/features/auth/store/authStore'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useIsAuthenticated()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
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
          <Route path="projects" element={<ProjectManagement />} />
          <Route path="documents" element={<DocumentPage />} />
          <Route path="chatrooms" element={<ChatRoomManagement />} />
          <Route path="admin" element={<AdminPage />} />
          <Route path="agents" element={<Navigate to="/agents/marketplace" replace />} />
          <Route path="agents/marketplace" element={<AgentMarketplace />} />
          <Route path="agents/my-instances" element={<MyAgentInstances />} />
          <Route path="agents/types" element={<AgentTypeManagement />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
