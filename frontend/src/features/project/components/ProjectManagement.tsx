import { useState, useEffect } from 'react'
import {
  Briefcase,
  Plus,
  Crown,
  Star,
  User,
  Trash2,
  UserPlus,
  RefreshCw,
  ChevronRight,
} from 'lucide-react'
import { Button, Input, ScrollArea, Avatar } from '@/components/ui'
import { Loading } from '@/components/common/Loading'
import { EmptyState } from '@/components/common/EmptyState'
import { cn } from '@/lib/utils'
import { get, post, del } from '@/lib/api'

interface Project {
  id: string
  name: string
  description?: string
  member_role?: string
  created_at: string
}

interface ProjectMember {
  id: string
  user_id: string
  user_name?: string
  user_email?: string
  role: 'owner' | 'admin' | 'member'
  joined_at: string
}

interface User {
  id: string
  name: string
  email: string
}

export function ProjectManagement() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [members, setMembers] = useState<ProjectMember[]>([])
  const [allUsers, setAllUsers] = useState<User[]>([])
  
  const [isLoading, setIsLoading] = useState(true)
  const [isMembersLoading, setIsMembersLoading] = useState(false)
  
  // 새 프로젝트 생성
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDesc, setNewProjectDesc] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  
  // 멤버 초대
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<'member' | 'admin'>('member')
  const [isInviting, setIsInviting] = useState(false)

  const userId = localStorage.getItem('user_id')

  // 프로젝트 목록 로드
  const loadProjects = async () => {
    if (!userId) return
    setIsLoading(true)
    try {
      const data = await get<Project[]>(`/users/${userId}/projects`)
      setProjects(data)
    } catch (e) {
      console.error('프로젝트 로드 실패:', e)
    } finally {
      setIsLoading(false)
    }
  }

  // 멤버 목록 로드
  const loadMembers = async (projectId: string) => {
    setIsMembersLoading(true)
    try {
      const data = await get<ProjectMember[]>(`/users/projects/${projectId}/members`)
      setMembers(data)
    } catch (e) {
      console.error('멤버 로드 실패:', e)
      setMembers([])
    } finally {
      setIsMembersLoading(false)
    }
  }

  // 전체 사용자 목록
  const loadAllUsers = async () => {
    try {
      const data = await get<User[]>('/users')
      setAllUsers(data)
    } catch (e) {
      console.error('사용자 로드 실패:', e)
    }
  }

  useEffect(() => {
    loadProjects()
    loadAllUsers()
  }, [])

  useEffect(() => {
    if (selectedProject) {
      loadMembers(selectedProject.id)
    }
  }, [selectedProject])

  // 프로젝트 생성
  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return
    setIsCreating(true)
    try {
      const result = await post<Project>('/users/projects', {
        name: newProjectName.trim(),
        description: newProjectDesc.trim() || undefined,
      })
      setProjects(prev => [...prev, { ...result, member_role: 'owner' }])
      setNewProjectName('')
      setNewProjectDesc('')
      setShowCreateForm(false)
      setSelectedProject({ ...result, member_role: 'owner' })
    } catch (e) {
      console.error('프로젝트 생성 실패:', e)
    } finally {
      setIsCreating(false)
    }
  }

  // 프로젝트 삭제
  const handleDeleteProject = async () => {
    if (!selectedProject) return
    if (!confirm(`"${selectedProject.name}" 프로젝트를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) return
    
    try {
      await del(`/users/projects/${selectedProject.id}`)
      setProjects(prev => prev.filter(p => p.id !== selectedProject.id))
      setSelectedProject(null)
    } catch (e) {
      console.error('프로젝트 삭제 실패:', e)
    }
  }

  // 멤버 초대
  const handleInviteMember = async () => {
    if (!selectedProject || !inviteEmail.trim()) return
    
    const user = allUsers.find(u => u.email.toLowerCase() === inviteEmail.toLowerCase())
    if (!user) {
      alert('해당 이메일의 사용자를 찾을 수 없습니다')
      return
    }

    setIsInviting(true)
    try {
      await post(`/users/projects/${selectedProject.id}/members`, {
        user_id: user.id,
        role: inviteRole,
      })
      await loadMembers(selectedProject.id)
      setInviteEmail('')
    } catch (e) {
      console.error('멤버 초대 실패:', e)
    } finally {
      setIsInviting(false)
    }
  }

  // 멤버 제거
  const handleRemoveMember = async (memberId: string) => {
    if (!selectedProject) return
    if (!confirm('이 멤버를 제거하시겠습니까?')) return
    
    try {
      await del(`/users/projects/${selectedProject.id}/members/${memberId}`)
      await loadMembers(selectedProject.id)
    } catch (e) {
      console.error('멤버 제거 실패:', e)
    }
  }

  const roleIcon = {
    owner: <Crown className="h-4 w-4 text-warning" />,
    admin: <Star className="h-4 w-4 text-accent" />,
    member: <User className="h-4 w-4 text-foreground-tertiary" />,
  }

  const roleLabel = {
    owner: '소유자',
    admin: '관리자',
    member: '멤버',
  }

  const myRole = selectedProject?.member_role as 'owner' | 'admin' | 'member' | undefined
  const canManageMembers = myRole === 'owner' || myRole === 'admin'
  const canDelete = myRole === 'owner'

  // 초대 가능한 사용자
  const availableUsers = allUsers.filter(
    u => !members.some(m => m.user_id === u.id)
  )

  return (
    <div className="flex h-full bg-background">
      {/* 왼쪽: 프로젝트 목록 */}
      <div className="w-80 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-semibold flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-accent" />
              프로젝트
            </h1>
            <Button variant="ghost" size="icon-sm" onClick={loadProjects}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
          
          <Button
            variant="outline"
            className="w-full justify-start gap-2"
            onClick={() => setShowCreateForm(true)}
          >
            <Plus className="h-4 w-4" />
            새 프로젝트
          </Button>
        </div>

        <ScrollArea className="flex-1">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loading />
            </div>
          ) : projects.length === 0 ? (
            <div className="p-4 text-center text-sm text-foreground-muted">
              프로젝트가 없습니다
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {projects.map((proj) => (
                <button
                  key={proj.id}
                  onClick={() => setSelectedProject(proj)}
                  className={cn(
                    'w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors',
                    selectedProject?.id === proj.id
                      ? 'bg-accent-muted'
                      : 'hover:bg-background-hover'
                  )}
                >
                  <Briefcase className="h-5 w-5 text-foreground-secondary shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{proj.name}</p>
                    <p className="text-xs text-foreground-muted">
                      {roleLabel[proj.member_role as keyof typeof roleLabel] || '멤버'}
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-foreground-muted" />
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* 오른쪽: 프로젝트 상세 */}
      <div className="flex-1 flex flex-col">
        {selectedProject ? (
          <>
            {/* 헤더 */}
            <div className="p-6 border-b border-border">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    {selectedProject.name}
                    {roleIcon[myRole!]}
                  </h2>
                  {selectedProject.description && (
                    <p className="text-sm text-foreground-secondary mt-1">
                      {selectedProject.description}
                    </p>
                  )}
                  <p className="text-xs text-foreground-muted mt-2">
                    내 역할: {roleLabel[myRole!]}
                  </p>
                </div>
                {canDelete && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-error hover:text-error hover:bg-error/10"
                    onClick={handleDeleteProject}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    삭제
                  </Button>
                )}
              </div>
            </div>

            {/* 멤버 섹션 */}
            <ScrollArea className="flex-1 p-6">
              <div className="space-y-6">
                {/* 멤버 초대 */}
                {canManageMembers && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium flex items-center gap-2">
                      <UserPlus className="h-4 w-4" />
                      멤버 초대
                    </h3>
                    <div className="flex gap-2">
                      <Input
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        placeholder="이메일 입력..."
                        list="available-project-users"
                        className="flex-1"
                      />
                      <datalist id="available-project-users">
                        {availableUsers.map(u => (
                          <option key={u.id} value={u.email}>{u.name}</option>
                        ))}
                      </datalist>
                      <select
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value as 'member' | 'admin')}
                        className="h-9 px-3 rounded-md border border-border bg-background text-sm"
                      >
                        <option value="member">멤버</option>
                        <option value="admin">관리자</option>
                      </select>
                      <Button onClick={handleInviteMember} disabled={isInviting || !inviteEmail.trim()}>
                        초대
                      </Button>
                    </div>
                  </div>
                )}

                {/* 멤버 목록 */}
                <div className="space-y-3">
                  <h3 className="text-sm font-medium">
                    멤버 ({members.length})
                  </h3>
                  
                  {isMembersLoading ? (
                    <Loading />
                  ) : (
                    <div className="space-y-2">
                      {members.map((member) => (
                        <div
                          key={member.id}
                          className="flex items-center gap-3 p-3 rounded-lg bg-background-secondary"
                        >
                          <Avatar
                            alt={member.user_name || 'User'}
                            fallback={member.user_name?.charAt(0) || 'U'}
                            size="md"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm">
                                {member.user_name || 'Unknown'}
                              </span>
                              {roleIcon[member.role]}
                            </div>
                            <span className="text-xs text-foreground-muted">
                              {member.user_email}
                            </span>
                          </div>
                          <span className="text-xs text-foreground-tertiary">
                            {roleLabel[member.role]}
                          </span>
                          {canManageMembers && member.role !== 'owner' && (
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              className="text-foreground-muted hover:text-error"
                              onClick={() => handleRemoveMember(member.user_id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </ScrollArea>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              icon={Briefcase}
              title="프로젝트를 선택하세요"
              description="왼쪽에서 프로젝트를 선택하거나 새로 만드세요"
            />
          </div>
        )}
      </div>

      {/* 프로젝트 생성 모달 */}
      {showCreateForm && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 animate-fade-in"
            onClick={() => setShowCreateForm(false)}
          />
          <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
            <div
              className="bg-background rounded-xl shadow-popup w-full max-w-md animate-scale-in"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 space-y-4">
                <h2 className="text-lg font-semibold">새 프로젝트</h2>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium">프로젝트 이름</label>
                  <Input
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="예: PLM 시스템 개선"
                    autoFocus
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">설명 (선택)</label>
                  <textarea
                    value={newProjectDesc}
                    onChange={(e) => setNewProjectDesc(e.target.value)}
                    placeholder="프로젝트에 대한 간단한 설명..."
                    rows={3}
                    className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="ghost" onClick={() => setShowCreateForm(false)}>
                    취소
                  </Button>
                  <Button
                    onClick={handleCreateProject}
                    disabled={isCreating || !newProjectName.trim()}
                  >
                    {isCreating ? '생성 중...' : '생성'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
