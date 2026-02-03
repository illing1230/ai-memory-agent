import { useState } from 'react'
import { Brain, Trash2, Clock, Tag, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react'
import { Button, ScrollArea } from '@/components/ui'
import { Loading } from '@/components/common/Loading'
import { EmptyState } from '@/components/common/EmptyState'
import { useMemories, useDeleteMemory } from '../hooks/useMemory'
import { formatDate, cn } from '@/lib/utils'
import type { MemoryListResult, Memory } from '@/types'

export function MemoryList() {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const { data: memories, isLoading, isError, error, refetch, isRefetching } = useMemories({ limit: 100 })
  const deleteMemory = useDeleteMemory()

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
    project: '프로젝트',
    department: '부서',
  }

  const importanceColor: Record<string, string> = {
    high: 'bg-error/10 text-error',
    medium: 'bg-warning/10 text-warning',
    low: 'bg-foreground-muted/10 text-foreground-muted',
  }

  // 그룹화: scope별로
  const groupedMemories = memories?.reduce((acc, memoryResult) => {
    const memory = memoryResult.memory
    const scope = memory.scope
    if (!acc[scope]) acc[scope] = []
    acc[scope].push(memoryResult)
    return acc
  }, {} as Record<string, MemoryListResult[]>) || {}

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <Brain className="h-5 w-5 text-accent" />
              내 메모리 목록
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
          {isLoading ? (
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
                총 {memories.length}개의 메모리
              </p>

              {/* Scope별 그룹 */}
              {Object.entries(groupedMemories).map(([scope, items]) => (
                <div key={scope} className="space-y-2">
                  <h2 className="text-sm font-medium text-foreground-secondary flex items-center gap-2">
                    <Tag className="h-4 w-4" />
                    {scopeLabel[scope] || scope} ({items.length})
                  </h2>

                  <div className="space-y-2">
                    {items.map((memoryResult) => {
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
                                {sourceInfo?.chat_room_name && (
                                  <span className="px-1.5 py-0.5 rounded bg-background-secondary text-accent">
                                    {sourceInfo.chat_room_name}
                                  </span>
                                )}
                                {sourceInfo?.project_name && (
                                  <span className="px-1.5 py-0.5 rounded bg-background-secondary text-accent">
                                    {sourceInfo.project_name}
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
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
