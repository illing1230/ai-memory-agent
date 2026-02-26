import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useMemories, useMemorySearch, useDeleteMemory, useDeleteMemoriesByRoom, memoryKeys } from '../useMemory'

// Mock the memoryApi module
vi.mock('../../api/memoryApi', () => ({
  getMemories: vi.fn(),
  searchMemories: vi.fn(),
  deleteMemory: vi.fn(),
  deleteMemoriesByRoom: vi.fn(),
}))

import { getMemories, searchMemories, deleteMemory, deleteMemoriesByRoom } from '../../api/memoryApi'

const mockedGetMemories = vi.mocked(getMemories)
const mockedSearchMemories = vi.mocked(searchMemories)
const mockedDeleteMemory = vi.mocked(deleteMemory)
const mockedDeleteMemoriesByRoom = vi.mocked(deleteMemoriesByRoom)

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children)
  }
}

describe('memoryKeys', () => {
  it('generates correct key for all', () => {
    expect(memoryKeys.all).toEqual(['memory'])
  })

  it('generates correct key for list', () => {
    expect(memoryKeys.list()).toEqual(['memory', 'list', undefined])
    expect(memoryKeys.list({ limit: 10 })).toEqual(['memory', 'list', { limit: 10 }])
  })

  it('generates correct key for search', () => {
    expect(memoryKeys.search({ query: 'test' })).toEqual(['memory', 'search', { query: 'test' }])
  })
})

describe('useMemories', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches memories successfully', async () => {
    const mockData = [
      {
        memory: {
          id: '1',
          content: 'Test memory',
          scope: 'chatroom',
          owner_id: 'user-1',
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
        source_info: { chat_room_name: 'Room 1' },
      },
    ]
    mockedGetMemories.mockResolvedValueOnce(mockData)

    const { result } = renderHook(() => useMemories(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockData)
    expect(mockedGetMemories).toHaveBeenCalledWith(undefined)
  })

  it('passes params to getMemories', async () => {
    mockedGetMemories.mockResolvedValueOnce([])

    const params = { limit: 50, scope: 'agent' }
    const { result } = renderHook(() => useMemories(params), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedGetMemories).toHaveBeenCalledWith(params)
  })

  it('handles error state', async () => {
    mockedGetMemories.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useMemories(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error).toBeInstanceOf(Error)
  })
})

describe('useMemorySearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches search results when query is valid', async () => {
    const mockResults = [
      {
        memory: {
          id: '1',
          content: 'Found memory',
          scope: 'chatroom',
          owner_id: 'user-1',
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
        score: 0.9,
        source_info: {},
      },
    ]
    mockedSearchMemories.mockResolvedValueOnce(mockResults)

    const params = { query: 'test query', limit: 20 }
    const { result } = renderHook(() => useMemorySearch(params), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockResults)
    expect(mockedSearchMemories).toHaveBeenCalledWith(params)
  })

  it('is disabled when query is empty', () => {
    const { result } = renderHook(
      () => useMemorySearch({ query: '' }),
      { wrapper: createWrapper() }
    )

    // With enabled: false, the query should not run
    expect(result.current.fetchStatus).toBe('idle')
    expect(mockedSearchMemories).not.toHaveBeenCalled()
  })

  it('is disabled when query is less than 2 characters', () => {
    const { result } = renderHook(
      () => useMemorySearch({ query: 'a' }),
      { wrapper: createWrapper() }
    )

    expect(result.current.fetchStatus).toBe('idle')
    expect(mockedSearchMemories).not.toHaveBeenCalled()
  })

  it('is enabled when query has 2 or more characters', async () => {
    mockedSearchMemories.mockResolvedValueOnce([])

    const { result } = renderHook(
      () => useMemorySearch({ query: 'ab' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedSearchMemories).toHaveBeenCalled()
  })
})

describe('useDeleteMemory', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls deleteMemory and invalidates queries on success', async () => {
    mockedDeleteMemory.mockResolvedValueOnce(undefined)

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    const spy = vi.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: React.ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children)

    const { result } = renderHook(() => useDeleteMemory(), { wrapper })

    result.current.mutate('mem-1')

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedDeleteMemory).toHaveBeenCalledWith('mem-1')
    expect(spy).toHaveBeenCalledWith({ queryKey: memoryKeys.all })
  })
})

describe('useDeleteMemoriesByRoom', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls deleteMemoriesByRoom and invalidates queries on success', async () => {
    mockedDeleteMemoriesByRoom.mockResolvedValueOnce({ count: 3 })

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    const spy = vi.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: React.ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children)

    const { result } = renderHook(() => useDeleteMemoriesByRoom(), { wrapper })

    result.current.mutate('room-1')

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedDeleteMemoriesByRoom).toHaveBeenCalledWith('room-1')
    expect(spy).toHaveBeenCalledWith({ queryKey: memoryKeys.all })
  })
})
