import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/test-utils'
import { MemoryList } from '../MemoryList'

// Mock the useMemory hooks
vi.mock('../../hooks/useMemory', () => ({
  useMemories: vi.fn(),
  useDeleteMemory: vi.fn(() => ({
    mutateAsync: vi.fn(),
  })),
  useDeleteMemoriesByRoom: vi.fn(() => ({
    mutate: vi.fn(),
  })),
}))

// Mock the document API
vi.mock('@/features/document/api/documentApi', () => ({
  getDocuments: vi.fn().mockResolvedValue([]),
  deleteDocument: vi.fn(),
}))

import { useMemories } from '../../hooks/useMemory'

const mockedUseMemories = vi.mocked(useMemories)

const mockMemoryListData = [
  {
    memory: {
      id: 'mem-1',
      content: 'React is a JavaScript library for building user interfaces',
      scope: 'chatroom' as const,
      owner_id: 'user-1',
      category: 'tech',
      importance: 'high' as const,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
    source_info: {
      owner_name: 'John',
      chat_room_name: 'Dev Room',
    },
  },
  {
    memory: {
      id: 'mem-2',
      content: 'Agent memory about user preferences',
      scope: 'agent' as const,
      owner_id: 'user-1',
      metadata: { source: 'agent', agent_instance_id: 'agent-1' },
      created_at: '2024-01-16T10:00:00Z',
      updated_at: '2024-01-16T10:00:00Z',
    },
    source_info: {
      agent_instance_name: 'My Agent',
    },
  },
]

describe('MemoryList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedUseMemories.mockReturnValue({
      data: mockMemoryListData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
      isRefetching: false,
    } as unknown as ReturnType<typeof useMemories>)
  })

  it('renders the page header', () => {
    renderWithProviders(<MemoryList />)

    expect(screen.getByText('내 지식 목록')).toBeInTheDocument()
    expect(screen.getByText('저장된 모든 메모리를 확인하고 관리하세요')).toBeInTheDocument()
  })

  it('renders tab buttons', () => {
    renderWithProviders(<MemoryList />)

    expect(screen.getByText('전체')).toBeInTheDocument()
    expect(screen.getByText('대화방')).toBeInTheDocument()
    expect(screen.getByText('에이전트')).toBeInTheDocument()
    expect(screen.getByText('문서')).toBeInTheDocument()
  })

  it('renders the refresh button', () => {
    renderWithProviders(<MemoryList />)

    expect(screen.getByText('새로고침')).toBeInTheDocument()
  })

  it('shows memory count', () => {
    renderWithProviders(<MemoryList />)

    // "총 2개의 메모리" - shows total count from displayedMemories
    expect(screen.getByText(/총.*2.*개의 메모리/)).toBeInTheDocument()
  })

  it('renders memory content in the list', () => {
    renderWithProviders(<MemoryList />)

    // The first memory content should appear (possibly truncated at 80 chars)
    expect(
      screen.getByText('React is a JavaScript library for building user interfaces')
    ).toBeInTheDocument()
  })

  it('switches to chatroom tab when clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<MemoryList />)

    const chatroomTab = screen.getByText('대화방')
    await user.click(chatroomTab)

    // After switching, only chatroom scope memories should appear
    // mem-1 has scope chatroom, mem-2 has scope agent
    expect(screen.getByText(/총.*1.*개의 메모리/)).toBeInTheDocument()
  })

  it('switches to agent tab when clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<MemoryList />)

    const agentTab = screen.getByText('에이전트')
    await user.click(agentTab)

    // Only agent scope memories should show
    expect(screen.getByText(/총.*1.*개의 메모리/)).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockedUseMemories.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
      isRefetching: false,
    } as unknown as ReturnType<typeof useMemories>)

    renderWithProviders(<MemoryList />)

    // The loading spinner has sr-only text "로딩 중..."
    expect(screen.getByText('로딩 중...')).toBeInTheDocument()
  })

  it('shows error state', () => {
    mockedUseMemories.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Failed to load'),
      refetch: vi.fn(),
      isRefetching: false,
    } as unknown as ReturnType<typeof useMemories>)

    renderWithProviders(<MemoryList />)

    expect(screen.getByText('메모리를 불러오는 중 오류가 발생했습니다')).toBeInTheDocument()
    expect(screen.getByText('Failed to load')).toBeInTheDocument()
  })

  it('shows empty state when no memories exist', () => {
    mockedUseMemories.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
      isRefetching: false,
    } as unknown as ReturnType<typeof useMemories>)

    renderWithProviders(<MemoryList />)

    expect(screen.getByText('저장된 메모리가 없습니다')).toBeInTheDocument()
  })

  it('shows empty state when data is null/undefined', () => {
    mockedUseMemories.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
      isRefetching: false,
    } as unknown as ReturnType<typeof useMemories>)

    renderWithProviders(<MemoryList />)

    expect(screen.getByText('저장된 메모리가 없습니다')).toBeInTheDocument()
  })

  it('calls refetch when refresh button is clicked', async () => {
    const mockRefetch = vi.fn()
    mockedUseMemories.mockReturnValue({
      data: mockMemoryListData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
      isRefetching: false,
    } as unknown as ReturnType<typeof useMemories>)

    const user = userEvent.setup()
    renderWithProviders(<MemoryList />)

    const refreshButton = screen.getByText('새로고침')
    await user.click(refreshButton)

    expect(mockRefetch).toHaveBeenCalled()
  })

  it('switches to document tab and shows document empty state', async () => {
    const user = userEvent.setup()
    renderWithProviders(<MemoryList />)

    const documentTab = screen.getByText('문서')
    await user.click(documentTab)

    // Since we mock getDocuments to return [], should eventually show empty state
    await waitFor(() => {
      expect(screen.getByText('저장된 문서가 없습니다')).toBeInTheDocument()
    })
  })
})
