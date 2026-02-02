import { useState, useEffect } from 'react'
import {
  MessageSquare,
  Plus,
  Crown,
  Star,
  User,
  Trash2,
  RefreshCw,
  ChevronRight,
  Share2,
  Users,
  Briefcase,
  Building2,
} from 'lucide-react'
import { Button, ScrollArea, Avatar } from '@/components/ui'
import { Loading } from '@/components/common/Loading'
import { EmptyState } from '@/components/common/EmptyState'
import { ShareModal } from '@/features/share/components/ShareModal'
import { cn } from '@/lib/utils'
import { get, del } from '@/lib/api'

interface ChatRoom {
  id: string
  name: string
  room_type: 'personal' | 'project' | 'department'
  owner_id: string
  project_id?: string
  department_id?: string
  member_role?: 'owner' | 'admin' | 'member'
  created_at: string
}

interface ChatRoomMember {
  id: string
  user_id: string
  user_name?: string
  user_email?: string
  role: 'owner' | 'admin' | 'member'
  joined_at: string
}

interface Project {
  id: string
  name: string
}

interface Department {
  id: string
  name: string
}

export function ChatRoomManagement() {
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([])
  const [selectedRoom, setSelectedRoom] = useState<ChatRoom | null>(null)
  const [members, setMembers] = useState<ChatRoomMember[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  
  const [isLoading, setIsLoading] = useState(true)
  const [isMembersLoading, setIsMembersLoading] = useState(false)
  
  // 공유 모달
  const [showShareModal, setShowShareModal] = useState(false)

  const userId = localStorage.getItem('user_id')

  // 채팅방 목록 로드
  const loadChatRooms = async () => {
    if (!userId) return
    setIsLoading(true)
    try {
      const data = await get<ChatRoom[]>(`/api/v1/chat-rooms/user/${userId}`)
      setChatRooms(data)
    } catch (e) {
      console.error('채팅방 로드 실패:', e)
    } finally {
      setIsLoading(false)
    }
  }

  // 멤버 목록 로드
  const loadMembers = async (roomId: string) => {
    setIsMembersLoading(true)
    try {
      const data = await get<ChatRoomMember[]>(`/api/v1/chat-rooms/${roomId}/members`)
      setMembers(data)
    } catch (e) {
      console.error('멤버 로드 실패:', e)
      setMembers([])
    } finally {
      setIsMembersLoading(false)
    }
  }

  // 프로젝트/부서 목록 로드
  const loadMetadata = async () => {
    try {
      const [projectsData, departmentsData] = await Promise.all([
        get<Project[]>('/users/projects'),
        get<Department[]>('/departments'),
      ])
      setProjects(projectsData)
      setDepartments(departmentsData)
    } catch (e) {
      console.error('메타데이터 로드 실패:', e)
    }
  }

  useEffect(() => {
    loadChatRooms()
    loadMetadata()
  }, [])

  useEffect(() => {
    if (selectedRoom) {
      loadMembers(selectedRoom.id)
    }
  }, [selectedRoom])

  // 채팅방 삭제
  const handleDeleteChatRoom = async () => {
    if (!selectedRoom) return
    if (!confirm(`"${selectedRoom.name}" 채팅방을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) return
    
    try {
      await del(`/api/v1/chat-rooms/${selectedRoom.id}`)
      setChatRooms(prev => prev.filter(r => r.id !== selectedRoom.id))
      setSelectedRoom(null)
    } catch (e) {
      console.error('채팅방 삭제 실패:', e)
      alert('채팅방 삭제에 실패했습니다')
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

  const roomTypeIcon = {
    personal: <User className="h-5 w-5 text-foreground-secondary shrink-0" />,
    project: <Briefcase className="h-5 w-5 text-accent shrink-0" />,
    department: <Building2 className="h-5 w-5 text-primary shrink-0" />,
  }

  const roomTypeLabel = {
    personal: '개인',
    project: '프로젝트',
    department: '부서',
  }

  const myRole = selectedRoom?.member_role
  const canDelete = myRole === 'owner'

  const getProjectName = (projectId?: string) => {
    if (!projectId) return '-'
    const project = projects.find(p => p.id === projectId)
    return project?.name || projectId
  }

  const getDepartmentName = (deptId?: string) => {
    if (!deptId) return '-'
    const dept = departments.find(d => d.id === deptId)
    return dept?.name || deptId
  }

  return (
    <div className="flex h-full bg-background">
      {/* 왼쪽: 채팅방 목록 */}
      <div className="w-80 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-semibold flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-accent" />
              채팅방
            </h1>
            <Button variant="ghost" size="icon-sm" onClick={loadChatRooms}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loading />
            </div>
          ) : chatRooms.length === 0 ? (
            <div className="p-4 text-center text-sm text-foreground-muted">
              채팅방이 없습니다
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {chatRooms.map((room) => (
                <button
                  key={room.id}
                  onClick={() => setSelectedRoom(room)}
                  className={cn(
                    'w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors',
                    selectedRoom?.id === room.id
                      ? 'bg-accent-muted'
                      : 'hover:bg-background-hover'
                  )}
                >
                  {roomTypeIcon[room.room_type]}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{room.name}</p>
                    <p className="text-xs text-foreground-muted">
                      {roomTypeLabel[room.room_type]} · {roleLabel[room.member_role!]}
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-foreground-muted" />
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* 오른쪽: 채팅방 상세 */}
      <div className="flex-1 flex flex-col">
        {selectedRoom ? (
          <>
            {/* 헤더 */}
            <div className="p-6 border-b border-border">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    {selectedRoom.name}
                    {roleIcon[myRole!]}
                  </h2>
                  <div className="flex items-center gap-4 mt-2 text-sm text-foreground-secondary">
                    <span>유형: {roomTypeLabel[selectedRoom.room_type]}</span>
                    {selectedRoom.project_id && (
                      <span>프로젝트: {getProjectName(selectedRoom.project_id)}</span>
                    )}
                    {selectedRoom.department_id && (
                      <span>부서: {getDepartmentName(selectedRoom.department_id)}</span>
                    )}
                  </div>
                  <p className="text-xs text-foreground-muted mt-2">
                    내 역할: {roleLabel[myRole!]}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowShareModal(true)}
                  >
                    <Share2 className="h-4 w-4 mr-1" />
                    공유
                  </Button>
                  {canDelete && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-error hover:text-error hover:bg-error/10"
                      onClick={handleDeleteChatRoom}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      삭제
                    </Button>
                  )}
                </div>
              </div>
            </div>

            {/* 멤버 섹션 */}
            <ScrollArea className="flex-1 p-6">
              <div className="space-y-3">
                <h3 className="text-sm font-medium flex items-center gap-2">
                  <Users className="h-4 w-4" />
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
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </ScrollArea>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              icon={MessageSquare}
              title="채팅방을 선택하세요"
              description="왼쪽에서 채팅방을 선택하세요"
            />
          </div>
        )}
      </div>

      {/* 공유 모달 */}
      {showShareModal && selectedRoom && (
        <ShareModal
          isOpen={showShareModal}
          onClose={() => setShowShareModal(false)}
          resourceType="chat_room"
          resourceId={selectedRoom.id}
          resourceName={selectedRoom.name}
        />
      )}
    </div>
  )
}
