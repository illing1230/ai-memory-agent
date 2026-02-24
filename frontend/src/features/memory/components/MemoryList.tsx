import { useState, useEffect, useMemo } from 'react'
import { Brain, Trash2, Clock, Tag, RefreshCw, ChevronDown, ChevronRight, Bot, FileText, Download, User } from 'lucide-react'
import { Button, ScrollArea } from '@/components/ui'
import { Loading } from '@/components/common/Loading'
import { EmptyState } from '@/components/common/EmptyState'
import { useMemories, useDeleteMemory } from '../hooks/useMemory'
import { getDocuments, deleteDocument } from '@/features/document/api/documentApi'
import { formatDate, cn, formatFileSize } from '@/lib/utils'
import type { MemoryListResult, Memory, Document } from '@/types'

type TabType = 'all' | 'personal' | 'chatroom' | 'agent' | 'document'

export function MemoryList() {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<TabType>('all')
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null)
  const { data: memories, isLoading, isError, error, refetch, isRefetching } = useMemories({ limit: 100 })
  const deleteMemory = useDeleteMemory()
  
  // 문서 관련 상태
  const [documents, setDocuments] = useState<Document[]>([])
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [documentsError, setDocumentsError] = useState<string | null>(null)
  
  // 문서 목록 로드
  const loadDocuments = async () => {
    setDocumentsLoading(true)
    setDocumentsError(null)
    try {
      const docs = await getDocuments()
      setDocuments(docs)
    } catch (err) {
      setDocumentsError(err instanceof Error ? err.message : '문서를 불러오는 중 오류가 발생했습니다')
    } finally {
      setDocumentsLoading(false)
    }
  }
  
  // 탭이 변경될 때 문서 로드
  useEffect(() => {
    if (activeTab === 'document') {
      loadDocuments()
    }
  }, [activeTab])
  
  // 문서 삭제
  const handleDeleteDocument = async (docId: string) => {
    if (confirm('이 문서를 삭제하시겠습니까?')) {
      try {
        await deleteDocument(docId)
        setDocuments(prev => prev.filter(doc => doc.id !== docId))
      } catch (err) {
        alert(err instanceof Error ? err.message : '문서 삭제 중 오류가 발생했습니다')
      }
    }
  }

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleDelete = async (memoryId: string) => {
    if (confirm('이 메모리를 삭제하시겠습니까?')) {
      await deleteMemory.mutateAsync(memoryId)
    }
  }

  const scopeLabel: Record<string, string> = {
    personal: '개인',
    chatroom: '대화방',
    agent: '에이전트',
  }

  const importanceColor: Record<string, string> = {
    high: 'bg-error/10 text-error',
    medium: 'bg-warning/10 text-warning',
    low: 'bg-foreground-muted/10 text-foreground-muted',
  }

  // 탭별 필터링된 메모리
  const filteredMemories = useMemo(() => {
    let result = memories || []
    
    // 탭별 필터링
    result = result.filter(memoryResult => {
      const memory = memoryResult.memory
      if (activeTab === 'all') return true
      if (activeTab === 'agent') {
        return memory.scope === 'agent'
      }
      return memory.scope === activeTab
    })
    
    return result
  }, [memories, activeTab])
  
  // 대화방별 그룹화 (대화방 탭에서만)
  const chatroomGroups = useMemo(() => {
    if (activeTab !== 'chatroom') return {}
    
    const result = filteredMemories.reduce((acc, memoryResult) => {
      const memory = memoryResult.memory
      const sourceInfo = memoryResult.source_info
      const roomName = sourceInfo?.chat_room_name || '알 수 없는 대화방'
      
      if (!acc[roomName]) {
        acc[roomName] = {
          name: roomName,
          count: 0,
          memories: [] as MemoryListResult[]
        }
      }
      acc[roomName].memories.push(memoryResult)
      acc[roomName].count++
      return acc
    }, {} as Record<string, { name: string; count: number; memories: MemoryListResult[] }>)
    
    return result
  }, [filteredMemories, activeTab])
  
  // 선택된 대화방의 메모리
  const displayedMemories = useMemo(() => {
    if (activeTab === 'chatroom' && selectedRoomId) {
      const groupName = Object.keys(chatroomGroups).find(key => 
        chatroomGroups[key].name === selectedRoomId
      )
      return groupName ? chatroomGroups[groupName].memories : filteredMemories
    }
    return filteredMemories
  }, [activeTab, selectedRoomId, chatroomGroups, filteredMemories])
  
  // 에이전트별 그룹화 (에이전트 탭에서만)
  const agentGroups = useMemo(() => {
    if (activeTab !== 'agent') return {}
    
    const result = filteredMemories.reduce((acc, memoryResult) => {
      const sourceInfo = memoryResult.source_info
      const agentName = sourceInfo?.agent_instance_name || '알 수 없는 에이전트'
      
      if (!acc[agentName]) {
        acc[agentName] = {
          name: agentName,
          count: 0,
          memories: [] as MemoryListResult[]
        }
      }
      acc[agentName].memories.push(memoryResult)
      acc[agentName].count++
      return acc
    }, {} as Record<string, { name: string; count: number; memories: MemoryListResult[] }>)
    
    return result
  }, [filteredMemories, activeTab])

  const tabs: { id: TabType; label: string; icon: any }[] = [
    { id: 'all', label: '전체', icon: Brain },
    { id: 'personal', label: '개인', icon: Brain },
    { id: 'chatroom', label: '대화방', icon: Brain },
    { id: 'agent', label: '에이전트', icon: Bot },
    { id: 'document', label: '문서', icon: FileText },
  ]

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <Brain className="h-5 w-5 text-accent" />
              내 지식 목록
            </h1>
            <p className="text-sm text-foreground-secondary mt-1">
              저장된 모든 메모리를 확인하고 관리하세요
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={cn('h-4 w-4 mr-1', isRefetching && 'animate-spin')} />
            새로고침
          </Button>
        </div>
      </header>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="px-6 py-4">
          {/* 탭 */}
          <div className="flex gap-2 mb-6 border-b border-border pb-4">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                  activeTab === tab.id
                    ? 'bg-accent text-accent-foreground'
                    : 'text-foreground-secondary hover:text-foreground hover:bg-background-secondary'
                )}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === 'chatroom' && Object.keys(chatroomGroups).length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              <button
                onClick={() => setSelectedRoomId(null)}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-lg transition-colors',
                  selectedRoomId === null
                    ? 'bg-accent text-accent-foreground'
                    : 'bg-background-secondary text-foreground-secondary hover:text-foreground'
                )}
              >
                전체 ({filteredMemories.length})
              </button>
              {Object.entries(chatroomGroups).map(([roomName, group]) => (
                <button
                  key={roomName}
                  onClick={() => setSelectedRoomId(roomName)}
                  className={cn(
                    'px-3 py-1.5 text-sm rounded-lg transition-colors',
                    selectedRoomId === roomName
                      ? 'bg-accent text-accent-foreground'
                      : 'bg-background-secondary text-foreground-secondary hover:text-foreground'
                  )}
                >
                  {roomName} ({group.count})
                </button>
              ))}
            </div>
          )}
          
          {activeTab === 'agent' && Object.keys(agentGroups).length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              <button
                onClick={() => setSelectedRoomId(null)}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-lg transition-colors',
                  selectedRoomId === null
                    ? 'bg-accent text-accent-foreground'
                    : 'bg-background-secondary text-foreground-secondary hover:text-foreground'
                )}
              >
                전체 ({filteredMemories.length})
              </button>
              {Object.entries(agentGroups).map(([agentName, group]) => (
                <button
                  key={agentName}
                  onClick={() => setSelectedRoomId(agentName)}
                  className={cn(
                    'px-3 py-1.5 text-sm rounded-lg transition-colors',
                    selectedRoomId === agentName
                      ? 'bg-accent text-accent-foreground'
                      : 'bg-background-secondary text-foreground-secondary hover:text-foreground'
                  )}
                >
                  {agentName} ({group.count})
                </button>
              ))}
            </div>
          )}
          
          {activeTab === 'document' ? (
            // 문서 탭
            documentsLoading ? (
              <div className="flex justify-center py-12">
                <Loading size="lg" />
              </div>
            ) : documentsError ? (
              <EmptyState
                icon={FileText}
                title="문서를 불러오는 중 오류가 발생했습니다"
                description={documentsError}
                action={<Button variant="secondary" size="sm" onClick={loadDocuments}>다시 시도</Button>}
              />
            ) : !documents || documents.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="저장된 문서가 없습니다"
                description="문서를 업로드하여 지식 베이스를 구축하세요"
              />
            ) : (
              <div className="space-y-6">
                <p className="text-sm text-foreground-secondary">
                  총 {documents.length}개의 문서
                </p>
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <div key={doc.id} className="card p-4 hover:shadow-medium transition-shadow">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0">
                          <FileText className="h-8 w-8 text-accent" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-foreground mb-1">
                            {doc.name}
                          </h3>
                          <div className="flex items-center gap-3 text-xs text-foreground-tertiary">
                            <span className="px-1.5 py-0.5 rounded bg-background-secondary">
                              {doc.file_type.toUpperCase()}
                            </span>
                            <span className="flex items-center gap-1">
                              <Tag className="h-3 w-3" />
                              {formatFileSize(doc.file_size)}
                            </span>
                            {doc.chunk_count > 0 && (
                              <span className="flex items-center gap-1">
                                <Brain className="h-3 w-3" />
                                {doc.chunk_count}개 청크
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatDate(doc.created_at)}
                            </span>
                          </div>
                          {doc.status === 'processing' && (
                            <div className="mt-2 text-xs text-warning">
                              처리 중...
                            </div>
                          )}
                          {doc.status === 'failed' && (
                            <div className="mt-2 text-xs text-error">
                              처리 실패
                            </div>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          className="text-foreground-muted hover:text-error shrink-0"
                          onClick={() => handleDeleteDocument(doc.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          ) : isLoading ? (
            <div className="flex justify-center py-12">
              <Loading size="lg" />
            </div>
          ) : isError ? (
            <EmptyState
              icon={Brain}
              title="메모리를 불러오는 중 오류가 발생했습니다"
              description={(error as Error)?.message || '잠시 후 다시 시도해주세요'}
              action={<Button variant="secondary" size="sm" onClick={() => refetch()}>다시 시도</Button>}
            />
          ) : !memories || memories.length === 0 ? (
            <EmptyState
              icon={Brain}
              title="저장된 메모리가 없습니다"
              description="채팅에서 /remember 명령어를 사용하거나 AI가 자동으로 메모리를 추출합니다"
            />
          ) : (
            <div className="space-y-6">
              <p className="text-sm text-foreground-secondary">
                총 {displayedMemories.length}개의 메모리
              </p>

              <div className="space-y-2">
                {displayedMemories.map((memoryResult) => {
                  const memory = memoryResult.memory
                  const sourceInfo = memoryResult.source_info
                  const isExpanded = expandedIds.has(memory.id)
                  const preview = memory.content.length > 80
                    ? memory.content.slice(0, 80) + '...'
                    : memory.content

                  return (
                    <div
                      key={memory.id}
                      className="card p-3 hover:shadow-medium transition-shadow"
                    >
                      <div className="flex items-start gap-3">
                        <button
                          onClick={() => toggleExpand(memory.id)}
                          className="mt-0.5 text-foreground-muted hover:text-foreground"
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </button>

                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-foreground">
                            {isExpanded ? memory.content : preview}
                          </p>

                          <div className="flex items-center gap-3 mt-2 text-xs text-foreground-tertiary">
                            {sourceInfo?.owner_name && (
                              <span className="px-1.5 py-0.5 rounded bg-background-secondary flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {sourceInfo.owner_name}
                              </span>
                            )}
                            {sourceInfo?.agent_instance_name && (
                              <span className="px-1.5 py-0.5 rounded bg-background-secondary text-accent flex items-center gap-1">
                                <Bot className="h-3 w-3" />
                                {sourceInfo.agent_instance_name}
                              </span>
                            )}
                            {sourceInfo?.chat_room_name && (
                              <span className="px-1.5 py-0.5 rounded bg-background-secondary text-accent">
                                {sourceInfo.chat_room_name}
                              </span>
                            )}
                            {memory.category && (
                              <span className="px-1.5 py-0.5 rounded bg-background-secondary">
                                {memory.category}
                              </span>
                            )}
                            {memory.importance && (
                              <span className={cn(
                                'px-1.5 py-0.5 rounded',
                                importanceColor[memory.importance]
                              )}>
                                {memory.importance === 'high' ? '높음' : 
                                 memory.importance === 'medium' ? '중간' : '낮음'}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatDate(memory.created_at)}
                            </span>
                          </div>
                        </div>

                        <Button
                          variant="ghost"
                          size="icon-sm"
                          className="text-foreground-muted hover:text-error shrink-0"
                          onClick={() => handleDelete(memory.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
