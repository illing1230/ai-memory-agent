import { get, post, put, del } from '@/lib/api'

export type ShareRole = 'owner' | 'member' | 'viewer'
export type ShareTargetType = 'user' | 'project' | 'department'
export type ResourceType = 'project' | 'document' | 'chat_room'

export interface Share {
  id: string
  resource_type: ResourceType
  resource_id: string
  target_type: ShareTargetType
  target_id: string
  role: ShareRole
  created_at: string
  created_by: string
}

export interface ShareWithDetails extends Share {
  target_name?: string
  target_email?: string
  creator_name?: string
}

export interface ShareCreate {
  resource_type: ResourceType
  resource_id: string
  target_type: ShareTargetType
  target_id: string
  role: ShareRole
}

export interface ShareUpdate {
  role: ShareRole
}

// 공유 설정 생성
export async function createShare(data: ShareCreate): Promise<Share> {
  return post<Share>('/api/v1/shares', data)
}

// 공유 설정 조회
export async function getShare(shareId: string): Promise<Share> {
  return get<Share>(`/api/v1/shares/${shareId}`)
}

// 리소스의 모든 공유 설정 조회
export async function getResourceShares(
  resourceType: ResourceType,
  resourceId: string
): Promise<ShareWithDetails[]> {
  return get<ShareWithDetails[]>(
    `/api/v1/shares/resource/${resourceType}/${resourceId}`
  )
}

// 나와 공유된 모든 리소스 조회
export async function getSharedWithMe(): Promise<Share[]> {
  return get<Share[]>('/api/v1/shares/shared-with-me')
}

// 공유 설정 역할 수정
export async function updateShareRole(
  shareId: string,
  role: ShareRole
): Promise<Share> {
  return put<Share>(`/api/v1/shares/${shareId}`, { role })
}

// 공유 설정 삭제
export async function deleteShare(shareId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/api/v1/shares/${shareId}`)
}
