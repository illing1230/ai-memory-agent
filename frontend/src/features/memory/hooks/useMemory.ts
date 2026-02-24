import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getMemories,
  searchMemories,
  deleteMemory,
  type GetMemoriesParams,
  type SearchMemoriesParams,
} from '../api/memoryApi'
import { deleteChatRoom } from '@/features/chat/api/chatApi'
import { chatKeys } from '@/features/chat/hooks/useChat'

export const memoryKeys = {
  all: ['memory'] as const,
  list: (params?: GetMemoriesParams) => [...memoryKeys.all, 'list', params] as const,
  search: (params: SearchMemoriesParams) => [...memoryKeys.all, 'search', params] as const,
}

export function useMemories(params?: GetMemoriesParams) {
  return useQuery({
    queryKey: memoryKeys.list(params),
    queryFn: () => getMemories(params),
  })
}

export function useMemorySearch(params: SearchMemoriesParams) {
  return useQuery({
    queryKey: memoryKeys.search(params),
    queryFn: () => searchMemories(params),
    enabled: !!params.query && params.query.length >= 2,
  })
}

export function useDeleteMemory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (memoryId: string) => deleteMemory(memoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.all })
    },
  })
}

export function useDeleteChatRoom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (roomId: string) => deleteChatRoom(roomId),
    onSuccess: () => {
      // 메모리 목록 새로고침 (대화방 삭제로 인해 메모리 삭제됨)
      queryClient.invalidateQueries({ queryKey: memoryKeys.all })
      // 채팅 목록도 새로고침
      queryClient.invalidateQueries({ queryKey: chatKeys.all })
    },
  })
}
