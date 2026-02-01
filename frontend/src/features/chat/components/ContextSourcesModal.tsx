import { useState, useEffect } from 'react'
import { X, AlertTriangle, Loader2, FileText, Upload, Link2, Unlink } from 'lucide-react'
import { Button, ScrollArea } from '@/components/ui'
import { cn } from '@/lib/utils'
import { get, put, post, del } from '@/lib/api'
import type { ChatRoom, Document } from '@/types'
import { DocumentUpload } from '@/features/document/components/DocumentUpload'

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
  
  // 문서 데이터
  const [linkedDocuments, setLinkedDocuments] = useState<Document[]>([])
  const [allMyDocuments, setAllMyDocuments] = useState<Document[]>([])
  const [showUpload, setShowUpload] = useState(false)
  const [showLinkPicker, setShowLinkPicker] = useState(false)

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

        // 문서 목록 로드
        try {
          const roomDocs = await get<Document[]>('/documents', { chat_room_id: room.id })
          setLinkedDocuments(roomDocs)
        } catch {
          setLinkedDocuments([])
        }

        try {
          const myDocs = await get<Document[]>('/documents')
          setAllMyDocuments(myDocs)
        } catch {
          setAllMyDocuments([])
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

  const handleLinkDocument = async (docId: string) => {
    try {
      await post(`/documents/${docId}/link/${room.id}`)
      const roomDocs = await get<Document[]>('/documents', { chat_room_id: room.id })
      setLinkedDocuments(roomDocs)
      setShowLinkPicker(false)
    } catch (e) {
      console.error('문서 연결 실패:', e)
    }
  }

  const handleUnlinkDocument = async (docId: string) => {
    try {
      await del(`/documents/${docId}/link/${room.id}`)
      setLinkedDocuments(prev => prev.filter(d => d.id !== docId))
    } catch (e) {
      console.error('문서 연결 해제 실패:', e)
    }
  }

  const handleUploadSuccess = async () => {
    try {
      const roomDocs = await get<Document[]>('/documents', { chat_room_id: room.id })
      setLinkedDocuments(roomDocs)
      const myDocs = await get<Document[]>('/documents')
      setAllMyDocuments(myDocs)
      setShowUpload(false)
    } catch {
      // ignore
    }
  }

  // 연결 가능한 문서 (이미 연결된 문서 제외)
  const linkableDocs = allMyDocuments.filter(
    d => d.status === 'completed' && !linkedDocuments.some(ld => ld.id === d.id)
  )

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
              <h2 className="text-lg font-semibold">컨텍스트 소스 설정</h2>
              <p className="text-sm text-foreground-secondary mt-0.5">
                AI가 참조할 메모리와 문서를 설정하세요
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

                {/* RAG 문서 */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium">RAG 문서</h3>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs h-7"
                        onClick={() => { setShowUpload(!showUpload); setShowLinkPicker(false) }}
                      >
                        <Upload className="h-3 w-3 mr-1" />
                        업로드
                      </Button>
                      {linkableDocs.length > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-xs h-7"
                          onClick={() => { setShowLinkPicker(!showLinkPicker); setShowUpload(false) }}
                        >
                          <Link2 className="h-3 w-3 mr-1" />
                          연결
                        </Button>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-foreground-muted">
                    업로드된 문서를 AI 답변의 참고 자료로 사용합니다. (대화 &gt; 문서 &gt; 메모리 순 우선순위)
                  </p>

                  {/* 업로드 영역 */}
                  {showUpload && (
                    <div className="p-3 border border-border rounded-lg">
                      <DocumentUpload chatRoomId={room.id} onSuccess={handleUploadSuccess} />
                    </div>
                  )}

                  {/* 기존 문서 연결 */}
                  {showLinkPicker && linkableDocs.length > 0 && (
                    <div className="p-3 border border-border rounded-lg space-y-1">
                      <p className="text-xs text-foreground-muted mb-2">연결할 문서를 선택하세요</p>
                      {linkableDocs.map(doc => (
                        <button
                          key={doc.id}
                          className="flex items-center gap-2 w-full p-2 rounded-md hover:bg-background-hover text-left"
                          onClick={() => handleLinkDocument(doc.id)}
                        >
                          <FileText className="h-4 w-4 text-accent shrink-0" />
                          <span className="text-sm truncate flex-1">{doc.name}</span>
                          <span className="text-xs text-foreground-muted">{doc.chunk_count} chunks</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* 연결된 문서 목록 */}
                  {linkedDocuments.length > 0 ? (
                    <div className="space-y-1">
                      {linkedDocuments.map(doc => (
                        <div
                          key={doc.id}
                          className="flex items-center gap-2 p-2 rounded-md border border-border"
                        >
                          <FileText className="h-4 w-4 text-accent shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm truncate">{doc.name}</p>
                            <p className="text-xs text-foreground-muted">
                              {doc.file_type.toUpperCase()} · {doc.chunk_count} chunks
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => handleUnlinkDocument(doc.id)}
                            title="연결 해제"
                          >
                            <Unlink className="h-3.5 w-3.5 text-foreground-muted" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-foreground-muted py-2">연결된 문서가 없습니다</p>
                  )}
                </div>
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
