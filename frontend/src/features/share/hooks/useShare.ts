import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  createShare,
  getResourceShares,
  updateShareRole,
  deleteShare,
  getSharedWithMe,
  type ShareCreate,
  type ShareUpdate,
  type ShareWithDetails,
  type Share,
  type ResourceType,
} from '../api/shareApi'

// 리소스의 공유 설정 조회
export function useResourceShares(resourceType: ResourceType, resourceId: string) {
  return useQuery({
    queryKey: ['shares', resourceType, resourceId],
    queryFn: () => getResourceShares(resourceType, resourceId),
    enabled: !!resourceId,
  })
}

// 나와 공유된 리소스 조회
export function useSharedWithMe() {
  return useQuery({
    queryKey: ['shared-with-me'],
    queryFn: getSharedWithMe,
  })
}

// 공유 설정 생성
export function useCreateShare() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ShareCreate) => createShare(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['shares', variables.resource_type, variables.resource_id],
      })
    },
  })
}

// 공유 설정 역할 수정
export function useUpdateShareRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ shareId, role }: { shareId: string; role: string }) =>
      updateShareRole(shareId, role as any),
    onSuccess: (_, variables) => {
      // 공유 설정이 속한 리소스의 공유 목록 갱신
      queryClient.invalidateQueries({
        queryKey: ['shares'],
      })
    },
  })
}

// 공유 설정 삭제
export function useDeleteShare() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (shareId: string) => deleteShare(shareId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['shares'],
      })
    },
  })
}
