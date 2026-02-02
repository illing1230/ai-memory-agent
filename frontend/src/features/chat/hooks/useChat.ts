import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getChatRooms,
  getChatRoom,
  createChatRoom,
  deleteChatRoom,
  getMessages,
  sendMessage,
  getChatRoomMembers,
  type CreateChatRoomParams,
  type SendMessageParams,
} from '../api/chatApi'

export const chatKeys = {
  all: ['chat'] as const,
  rooms: () => [...chatKeys.all, 'rooms'] as const,
  room: (id: string) => [...chatKeys.all, 'room', id] as const,
  messages: (roomId: string) => [...chatKeys.all, 'messages', roomId] as const,
  members: (roomId: string) => [...chatKeys.all, 'members', roomId] as const,
}

export function useChatRooms() {
  return useQuery({
    queryKey: chatKeys.rooms(),
    queryFn: getChatRooms,
  })
}

export function useChatRoom(roomId: string | undefined) {
  return useQuery({
    queryKey: chatKeys.room(roomId!),
    queryFn: () => getChatRoom(roomId!),
    enabled: !!roomId,
  })
}

export function useCreateChatRoom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: CreateChatRoomParams) => createChatRoom(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.rooms() })
    },
  })
}

export function useMessages(roomId: string | undefined) {
  return useQuery({
    queryKey: chatKeys.messages(roomId!),
    queryFn: () => getMessages(roomId!, { limit: 100 }),
    enabled: !!roomId,
    refetchInterval: 5000,
  })
}

export function useSendMessage(roomId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: SendMessageParams) => sendMessage(roomId, params),
    onSuccess: (response) => {
      queryClient.setQueryData(
        chatKeys.messages(roomId),
        (old: unknown[] | undefined) => {
          const messages = old || []
          const newMessages = [response.user_message]
          if (response.assistant_message) {
            newMessages.push(response.assistant_message)
          }
          return [...messages, ...newMessages]
        }
      )
    },
  })
}

export function useDeleteChatRoom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (roomId: string) => deleteChatRoom(roomId),
    onSuccess: (_, roomId) => {
      // 채팅방 목록 캐시 무효화
      queryClient.invalidateQueries({ queryKey: chatKeys.rooms() })
      // 삭제된 채팅방 캐시 제거
      queryClient.removeQueries({ queryKey: chatKeys.room(roomId) })
      // 삭제된 채팅방 메시지 캐시 제거
      queryClient.removeQueries({ queryKey: chatKeys.messages(roomId) })
      // 삭제된 채팅방 멤버 캐시 제거
      queryClient.removeQueries({ queryKey: chatKeys.members(roomId) })
    },
  })
}

export function useChatRoomMembers(roomId: string | undefined) {
  return useQuery({
    queryKey: chatKeys.members(roomId!),
    queryFn: () => getChatRoomMembers(roomId!),
    enabled: !!roomId,
  })
}
