import { useState, useEffect } from 'react'
import { X, AlertTriangle, Loader2 } from 'lucide-react'
import { Button, ScrollArea } from '@/components/ui'
import { cn } from '@/lib/utils'
import { get, put } from '@/lib/api'
import type { ChatRoom } from '@/types'

interface ContextSourcesModalProps {
  room: ChatRoom
  open: boolean
  onClose: () => void
  onSave: () => void
}

interface Project {
  id: string
  name: string
  description?: string
}

interface Department {
  id: string
  name: string
}

interface ContextSources {
  memory?: {
    include_this_room?: boolean
    other_chat_rooms?: string[]
    include_personal?: boolean
    projects?: string[]
    departments?: string[]
  }
  rag?: {
    collections?: string[]
    filters?: Record<string, unknown>
  }
}

export function ContextSourcesModal({ room, open, onClose, onSave }: ContextSourcesModalProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  
  // 데이터
  const [myChatRooms, setMyChatRooms] = useState<ChatRoom[]>([])
  const [myProjects, setMyProjects] = useState<Project[]>([])
  const [myDepartment, setMyDepartment] = useState<Department | null>(null)
  
  // 설정 값
  const [includeThisRoom, setIncludeThisRoom] = useState(true)
  const [selectedRooms, setSelectedRooms] = useState<string[]>([])
  const [includePersonal, setIncludePersonal] = useState(false)
  const [selectedProjects, setSelectedProjects] = useState<string[]>([])
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([])

  // 데이터 로드
  useEffect(() => {
    if (!open) return

    const loadData = async () => {
      setIsLoading(true)
      try {
        // 채팅방 목록
        const rooms = await get<ChatRoom[]>('/chat-rooms')
        setMyChatRooms(rooms.filter(r => r.id !== room.id))

        // 프로젝트 목록
        const userId = localStorage.getItem('user_id')
        if (userId) {
          try {
            const projects = await get<Project[]>(`/users/${userId}/projects`)
            setMyProjects(projects)
          } catch {
            setMyProjects([])
          }

          // 부서 정보
          try {
            const dept = await get<Department>(`/users/${userId}/department`)
            setMyDepartment(dept)
          } catch {
            setMyDepartment(null)
          }
        }

        // 기존 설정 로드
        const ctx = room.context_sources?.memory
        if (ctx) {
          setIncludeThisRoom(ctx.include_this_room ?? true)
          setSelectedRooms(ctx.other_chat_rooms || [])
          setIncludePersonal(ctx.include_personal ?? false)
          setSelectedProjects(ctx.projects || [])
          setSelectedDepartments(ctx.departments || [])
        }
      } catch (e) {
        console.error('데이터 로드 실패:', e)
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [open, room.id, room.context_sources])

  // 저장
  const handleSave = async () => {
    setIsSaving(true)
    try {
      const contextSources: ContextSources = {
        memory: {
          include_this_room: includeThisRoom,
          other_chat_rooms: selectedRooms,
          include_personal: includePersonal,
          projects: selectedProjects,
          departments: selectedDepartments,
        },
        rag: room.context_sources?.rag || { collections: [], filters: {} },
      }

      await put(`/chat-rooms/${room.id}`, { context_sources: contextSources })
      onSave()
      onClose()
    } catch (e) {
      console.error('저장 실패:', e)
    } finally {
      setIsSaving(false)
    }
  }

  // 체크박스 토글
  const toggleRoom = (roomId: string) => {
    setSelectedRooms(prev =>
      prev.includes(roomId) ? prev.filter(id => id !== roomId) : [...prev, roomId]
    )
  }

  const toggleProject = (projectId: string) => {
    setSelectedProjects(prev =>
      prev.includes(projectId) ? prev.filter(id => id !== projectId) : [...prev, projectId]
    )
  }

  const toggleDepartment = (deptId: string) => {
    setSelectedDepartments(prev =>
      prev.includes(deptId) ? prev.filter(id => id !== deptId) : [...prev, deptId]
    )
  }

  if (!open) return null

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40 animate-fade-in" onClick={onClose} />

      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div
          className="bg-background rounded-xl shadow-popup w-full max-w-lg max-h-[80vh] flex flex-col animate-scale-in"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-border">
            <div>
              <h2 className="text-lg font-semibold">메모리 소스 설정</h2>
              <p className="text-sm text-foreground-secondary mt-0.5">
                AI가 참조할 메모리 범위를 선택하세요
              </p>
            </div>
            <Button variant="ghost" size="icon-sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Content */}
          <ScrollArea className="flex-1 p-6">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-accent" />
              </div>
            ) : (
              <div className="space-y-6">
                {/* 기본: 이 채팅방 */}
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">기본 메모리</h3>
                  <label className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-background-hover cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeThisRoom}
                      onChange={(e) => setIncludeThisRoom(e.target.checked)}
                      className="w-4 h-4 rounded border-border text-accent focus:ring-accent"
                    />
                    <div>
                      <p className="text-sm font-medium">이 채팅방 메모리</p>
                      <p className="text-xs text-foreground-muted">
                        현재 채팅방에서 저장된 메모리
                      </p>
                    </div>
                  </label>
                </div>

                {/* 개인 메모리 전체 */}
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">개인 메모리</h3>
                  <label className={cn(
                    'flex items-start gap-3 p-3 rounded-lg border cursor-pointer',
                    includePersonal ? 'border-warning bg-warning/5' : 'border-border hover:bg-background-hover'
                  )}>
                    <input
                      type="checkbox"
                      checked={includePersonal}
                      onChange={(e) => setIncludePersonal(e.target.checked)}
                      className="w-4 h-4 mt-0.5 rounded border-border text-accent focus:ring-accent"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium">내 개인 메모리 전체</p>
                        <AlertTriangle className="h-4 w-4 text-warning" />
                      </div>
                      <p className="text-xs text-foreground-muted">
                        모든 개인 메모리가 AI 컨텍스트에 포함됩니다
                      </p>
                      {includePersonal && (
                        <p className="text-xs text-warning mt-1">
                          ⚠️ 민감한 정보가 공유될 수 있습니다
                        </p>
                      )}
                    </div>
                  </label>
                </div>

                {/* 다른 채팅방 */}
                {myChatRooms.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">다른 채팅방 메모리</h3>
                    <div className="space-y-1">
                      {myChatRooms.map((r) => (
                        <label
                          key={r.id}
                          className="flex items-center gap-3 p-2 rounded-md hover:bg-background-hover cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedRooms.includes(r.id)}
                            onChange={() => toggleRoom(r.id)}
                            className="w-4 h-4 rounded border-border text-accent focus:ring-accent"
                          />
                          <span className="text-sm">{r.name}</span>
                          <span className="text-xs text-foreground-muted ml-auto">
                            {r.room_type === 'personal' ? '개인' : r.room_type === 'project' ? '프로젝트' : '부서'}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* 프로젝트 */}
                {myProjects.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">프로젝트 메모리</h3>
                    <div className="space-y-1">
                      {myProjects.map((proj) => (
                        <label
                          key={proj.id}
                          className="flex items-center gap-3 p-2 rounded-md hover:bg-background-hover cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedProjects.includes(proj.id)}
                            onChange={() => toggleProject(proj.id)}
                            className="w-4 h-4 rounded border-border text-accent focus:ring-accent"
                          />
                          <div>
                            <p className="text-sm">{proj.name}</p>
                            {proj.description && (
                              <p className="text-xs text-foreground-muted">{proj.description}</p>
                            )}
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* 부서 */}
                {myDepartment && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">부서 메모리</h3>
                    <label className="flex items-center gap-3 p-2 rounded-md hover:bg-background-hover cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedDepartments.includes(myDepartment.id)}
                        onChange={() => toggleDepartment(myDepartment.id)}
                        className="w-4 h-4 rounded border-border text-accent focus:ring-accent"
                      />
                      <span className="text-sm">{myDepartment.name}</span>
                    </label>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>

          {/* Footer */}
          <div className="flex justify-end gap-2 px-6 py-4 border-t border-border">
            <Button variant="ghost" onClick={onClose}>취소</Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                  저장 중...
                </>
              ) : (
                '저장'
              )}
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
