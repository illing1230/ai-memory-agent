import { get, post, del } from '@/lib/api'
import type { Memory, MemoryListResult, MemorySearchResult } from '@/types'

export interface GetMemoriesParams {
  limit?: number
  offset?: number
  scope?: string
  agent_instance_id?: string
  [key: string]: unknown
}

export async function getMemories(params?: GetMemoriesParams): Promise<MemoryListResult[]> {
  return get<MemoryListResult[]>('/memories', params)
}

export async function getMemory(memoryId: string): Promise<Memory> {
  return get<Memory>(`/memories/${memoryId}`)
}

export interface SearchMemoriesParams {
  query: string
  limit?: number
  scope?: string
  agent_instance_id?: string
}

interface MemorySearchResponse {
  results: MemorySearchResult[]
  total: number
  query: string
}

export async function searchMemories(params: SearchMemoriesParams): Promise<MemorySearchResult[]> {
  const response = await post<MemorySearchResponse>('/memories/search', params)
  return response.results
}

export interface CreateMemoryParams {
  content: string
  scope?: 'personal' | 'chatroom' | 'agent'
  chat_room_id?: string
  category?: string
  importance?: 'high' | 'medium' | 'low'
}

export async function createMemory(params: CreateMemoryParams): Promise<Memory> {
  return post<Memory>('/memories', params)
}

export async function deleteMemory(memoryId: string): Promise<void> {
  return del(`/memories/${memoryId}`)
}
