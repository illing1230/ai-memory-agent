import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getDashboardStats,
  getAdminUsers,
  updateUserRole,
  deleteAdminUser,
  getAdminDepartments,
  getAdminProjects,
  getAdminChatRooms,
  deleteAdminChatRoom,
  getAdminMemories,
  deleteAdminMemory,
  getKnowledgeDashboard,
} from '../api/adminApi'

export function useDashboardStats() {
  return useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: getDashboardStats,
  })
}

export function useAdminUsers() {
  return useQuery({
    queryKey: ['admin', 'users'],
    queryFn: getAdminUsers,
  })
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      updateUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'dashboard'] })
    },
  })
}

export function useDeleteAdminUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => deleteAdminUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'dashboard'] })
    },
  })
}

export function useAdminDepartments() {
  return useQuery({
    queryKey: ['admin', 'departments'],
    queryFn: getAdminDepartments,
  })
}

export function useAdminProjects() {
  return useQuery({
    queryKey: ['admin', 'projects'],
    queryFn: getAdminProjects,
  })
}

export function useAdminChatRooms() {
  return useQuery({
    queryKey: ['admin', 'chatrooms'],
    queryFn: getAdminChatRooms,
  })
}

export function useDeleteAdminChatRoom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (roomId: string) => deleteAdminChatRoom(roomId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'chatrooms'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'dashboard'] })
    },
  })
}

export function useAdminMemories(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['admin', 'memories', limit, offset],
    queryFn: () => getAdminMemories(limit, offset),
    placeholderData: (prev) => prev,
  })
}

export function useDeleteAdminMemory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (memoryId: string) => deleteAdminMemory(memoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'memories'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'dashboard'] })
    },
  })
}

export function useKnowledgeDashboard() {
  return useQuery({
    queryKey: ['admin', 'knowledge-dashboard'],
    queryFn: getKnowledgeDashboard,
  })
}
