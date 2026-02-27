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
  getMchatStatus,
  getMchatChannels,
  toggleMchatChannelSync,
  getMchatUsers,
  updateDepartment,
  deleteDepartment,
  updateProject,
  deleteProject,
  getAgentDashboard,
  getAdminAgentApiLogs,
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

export function useMchatStatus() {
  return useQuery({
    queryKey: ['mchat', 'status'],
    queryFn: getMchatStatus,
    refetchInterval: 30000,
  })
}

export function useMchatChannels() {
  return useQuery({
    queryKey: ['mchat', 'channels'],
    queryFn: getMchatChannels,
  })
}

export function useToggleMchatChannelSync() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (mappingId: string) => toggleMchatChannelSync(mappingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mchat', 'channels'] })
    },
  })
}

export function useMchatUsers() {
  return useQuery({
    queryKey: ['mchat', 'users'],
    queryFn: getMchatUsers,
  })
}

// Department management hooks
export function useUpdateDepartment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ departmentId, data }: { departmentId: string; data: { name: string; description?: string } }) =>
      updateDepartment(departmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] })
    },
  })
}

export function useDeleteDepartment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (departmentId: string) => deleteDepartment(departmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] })
    },
  })
}

// Project management hooks
export function useUpdateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: { name: string; description?: string; department_id?: string } }) =>
      updateProject(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'dashboard'] })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (projectId: string) => deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'dashboard'] })
    },
  })
}

// Agent dashboard hooks
export function useAgentDashboard() {
  return useQuery({
    queryKey: ['admin', 'agent-dashboard'],
    queryFn: getAgentDashboard,
  })
}

export function useAdminAgentApiLogs(params?: { 
  instanceId?: string
  dateFrom?: string
  dateTo?: string
  limit?: number
  offset?: number
}) {
  return useQuery({
    queryKey: ['admin', 'agent-api-logs', params],
    queryFn: () => getAdminAgentApiLogs(params),
  })
}
