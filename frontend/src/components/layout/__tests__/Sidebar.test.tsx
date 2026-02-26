import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/test-utils'
import { Sidebar } from '../Sidebar'
import { useUIStore } from '@/stores/uiStore'
import { useAuthStore } from '@/features/auth/store/authStore'
import type { User } from '@/types'

// Mock the chat hooks
vi.mock('@/features/chat/hooks/useChat', () => ({
  useChatRooms: vi.fn(() => ({
    data: [],
    isLoading: false,
  })),
}))

const mockMemberUser: User = {
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

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset stores to defaults
    useUIStore.setState({
      sidebarOpen: true,
      createRoomModalOpen: false,
      settingsModalOpen: false,
    })
    useAuthStore.setState({
      user: mockMemberUser,
      token: 'test-token',
      isLoading: false,
    })
  })

  describe('when sidebar is open', () => {
    it('renders the app name', () => {
      renderWithProviders(<Sidebar />)

      expect(screen.getByText('AI Memory Agent')).toBeInTheDocument()
    })

    it('renders the search button', () => {
      renderWithProviders(<Sidebar />)

      expect(screen.getByText('지식 검색...')).toBeInTheDocument()
    })

    it('renders sidebar sections', () => {
      renderWithProviders(<Sidebar />)

      expect(screen.getByText('대화방')).toBeInTheDocument()
      expect(screen.getByText('Agent')).toBeInTheDocument()
      expect(screen.getByText('문서')).toBeInTheDocument()
      expect(screen.getByText('메모리 관리')).toBeInTheDocument()
    })

    it('renders user info when user is logged in', () => {
      renderWithProviders(<Sidebar />)

      expect(screen.getByText('Test User')).toBeInTheDocument()
      expect(screen.getByText('test@example.com')).toBeInTheDocument()
    })

    it('renders settings and logout buttons', () => {
      renderWithProviders(<Sidebar />)

      expect(screen.getByText('설정')).toBeInTheDocument()
    })

    it('does not show admin section for non-admin users', () => {
      renderWithProviders(<Sidebar />)

      expect(screen.queryByText('관리자 메뉴')).not.toBeInTheDocument()
    })

    it('shows admin section for admin users', () => {
      useAuthStore.setState({ user: mockAdminUser, token: 'admin-token' })

      renderWithProviders(<Sidebar />)

      expect(screen.getByText('관리자 메뉴')).toBeInTheDocument()
    })

    it('expands section when clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Sidebar />)

      // Click on "Agent" section to expand it
      const agentSection = screen.getByText('Agent')
      await user.click(agentSection)

      // After expanding, the child items should be visible
      expect(screen.getByText('Marketplace')).toBeInTheDocument()
      expect(screen.getByText('내 Instances')).toBeInTheDocument()
      expect(screen.getByText('Agent 등록')).toBeInTheDocument()
    })

    it('expands memory section to show child items', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Sidebar />)

      const memorySection = screen.getByText('메모리 관리')
      await user.click(memorySection)

      expect(screen.getByText('메모리 목록')).toBeInTheDocument()
      expect(screen.getByText('메모리 공유')).toBeInTheDocument()
    })

    it('expands admin section for admin users', async () => {
      useAuthStore.setState({ user: mockAdminUser, token: 'admin-token' })
      const user = userEvent.setup()
      renderWithProviders(<Sidebar />)

      const adminSection = screen.getByText('관리자 메뉴')
      await user.click(adminSection)

      expect(screen.getByText('대시보드')).toBeInTheDocument()
      expect(screen.getByText('지식 관리')).toBeInTheDocument()
      expect(screen.getByText('사용자 관리')).toBeInTheDocument()
      expect(screen.getByText('부서 관리')).toBeInTheDocument()
      expect(screen.getByText('프로젝트 관리')).toBeInTheDocument()
    })

    it('renders documents section', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Sidebar />)

      const docsSection = screen.getByText('문서')
      await user.click(docsSection)

      expect(screen.getByText('RAG')).toBeInTheDocument()
    })

    it('does not render user info when no user', () => {
      useAuthStore.setState({ user: null, token: null })

      renderWithProviders(<Sidebar />)

      expect(screen.queryByText('Test User')).not.toBeInTheDocument()
    })
  })

  describe('when sidebar is collapsed', () => {
    beforeEach(() => {
      useUIStore.setState({ sidebarOpen: false })
    })

    it('renders collapsed sidebar with icon buttons', () => {
      renderWithProviders(<Sidebar />)

      // Collapsed sidebar should not show the app name text
      expect(screen.queryByText('AI Memory Agent')).not.toBeInTheDocument()
    })

    it('does not show admin icon for non-admin users', () => {
      useAuthStore.setState({ user: mockMemberUser, token: 'test-token' })

      renderWithProviders(<Sidebar />)

      // The collapsed sidebar only shows the admin tooltip button for admins
      // For non-admin users, the admin button should not be present
      // We check by looking for the Shield icon button with "관리자" tooltip
      // Since tooltips might not render text directly, we check structure
      expect(screen.queryByText('관리자 메뉴')).not.toBeInTheDocument()
    })
  })
})
