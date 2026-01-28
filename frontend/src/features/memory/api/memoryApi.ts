import { get, post, del } from '@/lib/api'
import type { Memory, MemorySearchResult } from '@/types'

export interface GetMemoriesParams {
  limit?: number
  offset?: number
  scope?: string
}

export async function getMemories(params?: GetMemoriesParams): Promise<Memory[]> {
  return get<Memory[]>('/memories', params)
}

export async function getMemory(memoryId: string): Promise<Memory> {
  return get<Memory>(`/memories/${memoryId}`)
}

export interface SearchMemoriesParams {
  query: string
  limit?: number
  scope?: string
}

export async function searchMemories(params: SearchMemoriesParams): Promise<MemorySearchResult[]> {
  return post<MemorySearchResult[]>('/memories/search', params)
}

export interface CreateMemoryParams {
  content: string
  scope?: 'personal' | 'chatroom' | 'project' | 'department'
  chat_room_id?: string
  project_id?: string
  department_id?: string
  category?: string
  importance?: 'high' | 'medium' | 'low'
}

export async function createMemory(params: CreateMemoryParams): Promise<Memory> {
  return post<Memory>('/memories', params)
}

export async function deleteMemory(memoryId: string): Promise<void> {
  return del(`/memories/${memoryId}`)
}
