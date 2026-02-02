import { useState } from 'react'
import { Share2, X, User, Briefcase, Building2, Crown, Star, Eye, Trash2 } from 'lucide-react'
import { Button, Input, ScrollArea, Avatar } from '@/components/ui'
import { useResourceShares, useCreateShare, useUpdateShareRole, useDeleteShare } from '../hooks/useShare'
import { get } from '@/lib/api'
import type { ShareWithDetails, ShareRole, ShareTargetType, ResourceType } from '../api/shareApi'

interface ShareModalProps {
  isOpen: boolean
  onClose: () => void
  resourceType: ResourceType
  resourceId: string
  resourceName: string
}

interface User {
  id: string
  name: string
  email: string
}

interface Project {
  id: string
  name: string
}

interface Department {
  id: string
  name: string
}

export function ShareModal({
  isOpen,
  onClose,
  resourceType,
  resourceId,
  resourceName,
}: ShareModalProps) {
  const { data: shares = [], isLoading } = useResourceShares(resourceType, resourceId)
  const createShareMutation = useCreateShare()
  const updateShareMutation = useUpdateShareRole()
  const deleteShareMutation = useDeleteShare()

  const [targetType, setTargetType] = useState<ShareTargetType>('user')
  const [targetId, setTargetId] = useState('')
  const [role, setRole] = useState<ShareRole>('viewer')
  const [users, setUsers] = useState<User[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [departments, setDepartments] = useState<Department[]>([])

  // 데이터 로드
  const loadData = async () => {
    try {
      const [usersData, projectsData, departmentsData] = await Promise.all([
        get<User[]>('/users'),
        get<Project[]>('/users/projects'),
        get<Department[]>('/users/departments'),
      ])
      setUsers(usersData)
      setProjects(projectsData)
      setDepartments(departmentsData)
    } catch (e) {
      console.error('데이터 로드 실패:', e)
    }
  }

  if (isOpen && users.length === 0) {
    loadData()
  }

  const handleAddShare = async () => {
    if (!targetId.trim()) return

    // 이메일 또는 이름으로 사용자 ID 찾기
    let actualTargetId = targetId
    if (targetType === 'user') {
      const user = users.find(u => u.email === targetId || u.name === targetId)
      if (user) {
        actualTargetId = user.id
      }
    } else if (targetType === 'project') {
      const project = projects.find(p => p.name === targetId)
      if (project) {
        actualTargetId = project.id
      }
    } else if (targetType === 'department') {
      const department = departments.find(d => d.name === targetId)
      if (department) {
        actualTargetId = department.id
      }
    }

    try {
      await createShareMutation.mutateAsync({
        resource_type: resourceType,
        resource_id: resourceId,
        target_type: targetType,
        target_id: actualTargetId,
        role,
      })
      setTargetId('')
    } catch (e) {
      console.error('공유 추가 실패:', e)
      alert('공유 추가에 실패했습니다')
    }
  }

  const handleUpdateRole = async (shareId: string, newRole: ShareRole) => {
    try {
      await updateShareMutation.mutateAsync({ shareId, role: newRole })
    } catch (e) {
      console.error('역할 수정 실패:', e)
      alert('역할 수정에 실패했습니다')
    }
  }

  const handleDeleteShare = async (shareId: string) => {
    if (!confirm('공유를 삭제하시겠습니까?')) return

    try {
      await deleteShareMutation.mutateAsync(shareId)
    } catch (e) {
      console.error('공유 삭제 실패:', e)
      alert('공유 삭제에 실패했습니다')
    }
  }

  const getTargetIcon = (type: ShareTargetType) => {
    switch (type) {
      case 'user':
        return <User className="h-4 w-4" />
      case 'project':
        return <Briefcase className="h-4 w-4" />
      case 'department':
        return <Building2 className="h-4 w-4" />
    }
  }

  const getRoleIcon = (role: ShareRole) => {
    switch (role) {
      case 'owner':
        return <Crown className="h-4 w-4 text-warning" />
      case 'member':
        return <Star className="h-4 w-4 text-accent" />
      case 'viewer':
        return <Eye className="h-4 w-4 text-foreground-tertiary" />
    }
  }

  const getRoleLabel = (role: ShareRole) => {
    switch (role) {
      case 'owner':
        return '소유자'
      case 'member':
        return '멤버'
      case 'viewer':
        return '조회자'
    }
  }

  const getTargetLabel = (share: ShareWithDetails) => {
    if (share.target_type === 'user') {
      return share.target_name || 'Unknown'
    }
    return share.target_id
  }

  const getAvailableTargets = () => {
    switch (targetType) {
      case 'user':
        return users.filter(u => !shares.some(s => s.target_type === 'user' && s.target_id === u.id))
      case 'project':
        return projects.filter(p => !shares.some(s => s.target_type === 'project' && s.target_id === p.id))
      case 'department':
        return departments.filter(d => !shares.some(s => s.target_type === 'department' && s.target_id === d.id))
    }
  }

  if (!isOpen) return null

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-40 animate-fade-in"
        onClick={onClose}
      />
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div
          className="bg-background rounded-xl shadow-popup w-full max-w-2xl max-h-[80vh] flex flex-col animate-scale-in"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 헤더 */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div className="flex items-center gap-3">
              <Share2 className="h-5 w-5 text-accent" />
              <div>
                <h2 className="text-lg font-semibold">공유 설정</h2>
                <p className="text-sm text-foreground-muted">{resourceName}</p>
              </div>
            </div>
            <Button variant="ghost" size="icon-sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* 공유 추가 */}
          <div className="p-6 border-b border-border">
            <div className="flex gap-2">
              <select
                value={targetType}
                onChange={(e) => setTargetType(e.target.value as ShareTargetType)}
                className="h-9 px-3 rounded-md border border-border bg-background text-sm"
              >
                <option value="user">사용자</option>
                <option value="project">프로젝트</option>
                <option value="department">부서</option>
              </select>

              <Input
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                placeholder={targetType === 'user' ? '이메일 또는 이름 검색...' : '이름 검색...'}
                list="available-targets"
                className="flex-1"
              />
              <datalist id="available-targets">
                {getAvailableTargets().map((target: any) => (
                  <option key={target.id} value={target.email || target.name}>
                    {target.name} ({target.email})
                  </option>
                ))}
              </datalist>

              <select
                value={role}
                onChange={(e) => setRole(e.target.value as ShareRole)}
                className="h-9 px-3 rounded-md border border-border bg-background text-sm"
              >
                <option value="viewer">조회자</option>
                <option value="member">멤버</option>
                <option value="owner">소유자</option>
              </select>

              <Button
                onClick={handleAddShare}
                disabled={createShareMutation.isPending || !targetId.trim()}
              >
                추가
              </Button>
            </div>
          </div>

          {/* 공유 목록 */}
          <ScrollArea className="flex-1 p-6">
            {isLoading ? (
              <div className="text-center text-foreground-muted py-8">로딩 중...</div>
            ) : shares.length === 0 ? (
              <div className="text-center text-foreground-muted py-8">
                공유된 대상이 없습니다
              </div>
            ) : (
              <div className="space-y-2">
                {shares.map((share) => (
                  <div
                    key={share.id}
                    className="flex items-center gap-3 p-3 rounded-lg bg-background-secondary"
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {getTargetIcon(share.target_type)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {getTargetLabel(share)}
                        </p>
                        {share.target_type === 'user' && share.target_email && (
                          <p className="text-xs text-foreground-muted truncate">
                            {share.target_email}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <select
                        value={share.role}
                        onChange={(e) => handleUpdateRole(share.id, e.target.value as ShareRole)}
                        className="h-8 px-2 rounded-md border border-border bg-background text-xs"
                        disabled={updateShareMutation.isPending}
                      >
                        <option value="viewer">조회자</option>
                        <option value="member">멤버</option>
                        <option value="owner">소유자</option>
                      </select>

                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-foreground-muted hover:text-error"
                        onClick={() => handleDeleteShare(share.id)}
                        disabled={deleteShareMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* 권한 설명 */}
          <div className="p-4 border-t border-border bg-background-secondary">
            <p className="text-xs text-foreground-muted">
              <strong>조회자:</strong> 메모리 지식만 활용 가능 |{' '}
              <strong>멤버:</strong> 대화방 입장 및 메시지 전송 가능 |{' '}
              <strong>소유자:</strong> 모든 권한
            </p>
          </div>
        </div>
      </div>
    </>
  )
}
