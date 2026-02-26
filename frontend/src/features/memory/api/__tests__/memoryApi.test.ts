import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getMemories,
  getMemory,
  searchMemories,
  createMemory,
  deleteMemory,
  deleteMemoriesByRoom,
} from '../memoryApi'

// Mock the api module
vi.mock('@/lib/api', () => ({
  get: vi.fn(),
  post: vi.fn(),
  del: vi.fn(),
}))

import { get, post, del } from '@/lib/api'

const mockedGet = vi.mocked(get)
const mockedPost = vi.mocked(post)
const mockedDel = vi.mocked(del)

describe('memoryApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getMemories', () => {
    it('calls get with /memories endpoint and no params when none provided', async () => {
      const mockResult = [
        { memory: { id: '1', content: 'test', scope: 'chatroom' }, source_info: {} },
      ]
      mockedGet.mockResolvedValueOnce(mockResult)

      const result = await getMemories()

      expect(mockedGet).toHaveBeenCalledWith('/memories', undefined)
      expect(result).toEqual(mockResult)
    })

    it('passes params to get', async () => {
      mockedGet.mockResolvedValueOnce([])

      await getMemories({ limit: 10, offset: 0, scope: 'agent' })

      expect(mockedGet).toHaveBeenCalledWith('/memories', {
        limit: 10,
        offset: 0,
        scope: 'agent',
      })
    })
  })

  describe('getMemory', () => {
    it('calls get with /memories/:id endpoint', async () => {
      const mockMemory = {
        id: 'mem-1',
        content: 'test memory',
        scope: 'chatroom',
        owner_id: 'user-1',
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      }
      mockedGet.mockResolvedValueOnce(mockMemory)

      const result = await getMemory('mem-1')

      expect(mockedGet).toHaveBeenCalledWith('/memories/mem-1')
      expect(result).toEqual(mockMemory)
    })
  })

  describe('searchMemories', () => {
    it('calls post with /memories/search endpoint and returns results', async () => {
      const searchResponse = {
        results: [
          {
            memory: { id: '1', content: 'test', scope: 'chatroom' },
            score: 0.95,
            source_info: {},
          },
        ],
        total: 1,
        query: 'test',
      }
      mockedPost.mockResolvedValueOnce(searchResponse)

      const params = { query: 'test', limit: 10 }
      const result = await searchMemories(params)

      expect(mockedPost).toHaveBeenCalledWith('/memories/search', params)
      // searchMemories extracts results from the response
      expect(result).toEqual(searchResponse.results)
    })

    it('passes scope parameter in search request', async () => {
      mockedPost.mockResolvedValueOnce({
        results: [],
        total: 0,
        query: 'agent query',
      })

      await searchMemories({ query: 'agent query', scope: 'agent' })

      expect(mockedPost).toHaveBeenCalledWith('/memories/search', {
        query: 'agent query',
        scope: 'agent',
      })
    })

    it('returns empty array when no results', async () => {
      mockedPost.mockResolvedValueOnce({
        results: [],
        total: 0,
        query: 'nonexistent',
      })

      const result = await searchMemories({ query: 'nonexistent' })
      expect(result).toEqual([])
    })
  })

  describe('createMemory', () => {
    it('calls post with /memories endpoint', async () => {
      const newMemory = {
        id: 'new-1',
        content: 'new memory',
        scope: 'chatroom' as const,
        owner_id: 'user-1',
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      }
      mockedPost.mockResolvedValueOnce(newMemory)

      const params = {
        content: 'new memory',
        scope: 'chatroom' as const,
        importance: 'high' as const,
      }
      const result = await createMemory(params)

      expect(mockedPost).toHaveBeenCalledWith('/memories', params)
      expect(result).toEqual(newMemory)
    })
  })

  describe('deleteMemory', () => {
    it('calls del with /memories/:id endpoint', async () => {
      mockedDel.mockResolvedValueOnce(undefined)

      await deleteMemory('mem-1')

      expect(mockedDel).toHaveBeenCalledWith('/memories/mem-1')
    })
  })

  describe('deleteMemoriesByRoom', () => {
    it('calls del with /memories/by-room/:chatRoomId endpoint', async () => {
      mockedDel.mockResolvedValueOnce({ count: 5 })

      const result = await deleteMemoriesByRoom('room-1')

      expect(mockedDel).toHaveBeenCalledWith('/memories/by-room/room-1')
      expect(result).toEqual({ count: 5 })
    })
  })
})
