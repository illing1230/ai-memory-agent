import { get, post, put, del } from '@/lib/api'
import type { ChatRoom, ChatRoomMember, Message } from '@/types'

export async function getChatRooms(): Promise<ChatRoom[]> {
  return get<ChatRoom[]>('/chat-rooms')
}

export async function getChatRoom(roomId: string): Promise<ChatRoom> {
  return get<ChatRoom>(`/chat-rooms/${roomId}`)
}

export interface CreateChatRoomParams {
  name: string
  room_type?: 'personal' | 'project' | 'department'
  project_id?: string
  department_id?: string
}

export async function createChatRoom(params: CreateChatRoomParams): Promise<ChatRoom> {
  return post<ChatRoom>('/chat-rooms', params)
}

export interface UpdateChatRoomParams {
  name?: string
  context_sources?: ChatRoom['context_sources']
}

export async function updateChatRoom(roomId: string, params: UpdateChatRoomParams): Promise<ChatRoom> {
  return put<ChatRoom>(`/chat-rooms/${roomId}`, params)
}

export async function deleteChatRoom(roomId: string): Promise<void> {
  return del(`/chat-rooms/${roomId}`)
}

export async function getChatRoomMembers(roomId: string): Promise<ChatRoomMember[]> {
  return get<ChatRoomMember[]>(`/chat-rooms/${roomId}/members`)
}

export async function addChatRoomMember(roomId: string, userId: string, role: string = 'member'): Promise<ChatRoomMember> {
  return post<ChatRoomMember>(`/chat-rooms/${roomId}/members`, { user_id: userId, role })
}

export async function removeChatRoomMember(roomId: string, userId: string): Promise<void> {
  return del(`/chat-rooms/${roomId}/members/${userId}`)
}

export interface GetMessagesParams {
  limit?: number
  offset?: number
}

export async function getMessages(roomId: string, params?: GetMessagesParams): Promise<Message[]> {
  return get<Message[]>(`/chat-rooms/${roomId}/messages`, params)
}

export interface SendMessageParams {
  content: string
}

export interface SendMessageResponse {
  user_message: Message
  assistant_message?: Message
  extracted_memories?: Array<{ id: string; content: string }>
}

export async function sendMessage(roomId: string, params: SendMessageParams): Promise<SendMessageResponse> {
  return post<SendMessageResponse>(`/chat-rooms/${roomId}/messages`, params)
}
