import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, MessageSquare, Briefcase, Building2, ChevronDown } from 'lucide-react'
import { Button, Input } from '@/components/ui'
import { useCreateChatRoom } from '@/features/chat/hooks/useChat'
import { getUserProjects } from '@/features/project/api/projectApi'
import { useAuthStore } from '@/features/auth/store/authStore'
import { cn } from '@/lib/utils'
import type { Project } from '@/types'

interface CreateRoomModalProps {
  open: boolean
  onClose: () => void
}

type RoomType = 'personal' | 'project' | 'department'

export function CreateRoomModal({ open, onClose }: CreateRoomModalProps) {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [name, setName] = useState('')
  const [roomType, setRoomType] = useState<RoomType>('personal')
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoadingProjects, setIsLoadingProjects] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showProjectDropdown, setShowProjectDropdown] = useState(false)

  const createRoom = useCreateChatRoom()

  // 프로젝트 목록 로드
  useEffect(() => {
    if (open && user && roomType === 'project') {
      loadProjects()
    }
  }, [open, user, roomType])

  const loadProjects = async () => {
    if (!user) return
    
    setIsLoadingProjects(true)
    try {
      const userProjects = await getUserProjects(user.id)
      setProjects(userProjects)
      if (userProjects.length > 0) {
        setSelectedProject(userProjects[0].id)
      }
    } catch (error) {
      console.error('프로젝트 목록 로드 실패:', error)
    } finally {
      setIsLoadingProjects(false)
    }
  }

  if (!open) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || isSubmitting) return

    // 프로젝트 타입인 경우 프로젝트 선택 필수
    if (roomType === 'project' && !selectedProject) {
      alert('프로젝트를 선택해주세요.')
      return
    }

    setIsSubmitting(true)
    try {
      const room = await createRoom.mutateAsync({ 
        name: name.trim(), 
        room_type: roomType,
        project_id: roomType === 'project' ? selectedProject : undefined
      })
      onClose()
      setName('')
      setRoomType('personal')
      setSelectedProject('')
      navigate(`/chat/${room.id}`)
    } catch (error) {
      console.error('채팅방 생성 실패:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const roomTypes: { type: RoomType; label: string; icon: React.ElementType; desc: string }[] = [
    { type: 'personal', label: '개인', icon: MessageSquare, desc: '나만 사용하는 채팅방' },
    { type: 'project', label: '프로젝트', icon: Briefcase, desc: '프로젝트 팀원과 공유' },
    { type: 'department', label: '부서', icon: Building2, desc: '부서 전체와 공유' },
  ]

  const selectedProjectData = projects.find(p => p.id === selectedProject)

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40 animate-fade-in" onClick={onClose} />

      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div className="bg-background rounded-xl shadow-popup w-full max-w-md animate-scale-in" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between px-6 py-4 border-b border-border">
            <h2 className="text-lg font-semibold">새 채팅방 만들기</h2>
            <Button variant="ghost" size="icon-sm" onClick={onClose}><X className="h-4 w-4" /></Button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">채팅방 이름</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="예: 품질검사팀 회의" autoFocus />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">유형 선택</label>
              <div className="grid grid-cols-3 gap-2">
                {roomTypes.map(({ type, label, icon: Icon, desc }) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => {
                      setRoomType(type)
                      if (type === 'project') {
                        setShowProjectDropdown(true)
                      }
                    }}
                    className={cn(
                      'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
                      'hover:border-accent hover:bg-accent-muted',
                      roomType === type ? 'border-accent bg-accent-muted' : 'border-border'
                    )}
                  >
                    <Icon className={cn('h-6 w-6', roomType === type ? 'text-accent' : 'text-foreground-secondary')} />
                    <span className={cn('text-sm font-medium', roomType === type ? 'text-accent' : 'text-foreground')}>{label}</span>
                    <span className="text-xs text-foreground-tertiary text-center">{desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 프로젝트 선택 (프로젝트 타입일 때만 표시) */}
            {roomType === 'project' && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">프로젝트 선택</label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowProjectDropdown(!showProjectDropdown)}
                    className="w-full flex items-center justify-between px-3 py-2 border border-border rounded-md bg-background hover:bg-background-hover transition-colors"
                  >
                    <span className="text-sm">
                      {selectedProjectData ? selectedProjectData.name : '프로젝트를 선택하세요'}
                    </span>
                    <ChevronDown className="h-4 w-4 text-foreground-secondary" />
                  </button>
                  
                  {showProjectDropdown && (
                    <div className="absolute z-10 w-full mt-1 bg-background border border-border rounded-md shadow-lg max-h-48 overflow-y-auto">
                      {isLoadingProjects ? (
                        <div className="px-3 py-2 text-sm text-foreground-secondary">로딩 중...</div>
                      ) : projects.length === 0 ? (
                        <div className="px-3 py-2 text-sm text-foreground-secondary">프로젝트가 없습니다</div>
                      ) : (
                        projects.map((project) => (
                          <button
                            key={project.id}
                            type="button"
                            onClick={() => {
                              setSelectedProject(project.id)
                              setShowProjectDropdown(false)
                            }}
                            className={cn(
                              'w-full px-3 py-2 text-left text-sm hover:bg-background-hover transition-colors',
                              selectedProject === project.id && 'bg-accent-muted text-accent'
                            )}
                          >
                            {project.name}
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="ghost" onClick={onClose}>취소</Button>
              <Button type="submit" disabled={!name.trim() || isSubmitting || (roomType === 'project' && !selectedProject)}>
                {isSubmitting ? '생성 중...' : '만들기'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
