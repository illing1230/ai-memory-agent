import { get, put, del } from '@/lib/api'
import type {
  DashboardStats,
  AdminUser,
  AdminChatRoom,
  AdminDepartment,
  AdminProject,
  PaginatedMemories,
} from '@/types'

export async function getDashboardStats(): Promise<DashboardStats> {
  return get<DashboardStats>('/admin/dashboard')
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  return get<AdminUser[]>('/admin/users')
}

export async function updateUserRole(userId: string, role: string): Promise<void> {
  await put('/admin/users/' + userId + '/role', { role })
}

export async function deleteAdminUser(userId: string): Promise<void> {
  await del('/admin/users/' + userId)
}

export async function getAdminDepartments(): Promise<AdminDepartment[]> {
  return get<AdminDepartment[]>('/admin/departments')
}

export async function getAdminProjects(): Promise<AdminProject[]> {
  return get<AdminProject[]>('/admin/projects')
}

export async function getAdminChatRooms(): Promise<AdminChatRoom[]> {
  return get<AdminChatRoom[]>('/admin/chat-rooms')
}

export async function deleteAdminChatRoom(roomId: string): Promise<void> {
  await del('/admin/chat-rooms/' + roomId)
}

export async function getAdminMemories(limit = 20, offset = 0): Promise<PaginatedMemories> {
  return get<PaginatedMemories>('/admin/memories', { limit, offset })
}

export async function deleteAdminMemory(memoryId: string): Promise<void> {
  await del('/admin/memories/' + memoryId)
}
