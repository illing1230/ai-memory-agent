import { useState } from 'react'
import { Brain, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui'
import { Loading } from '@/components/common/Loading'
import { useAdminMemories, useDeleteAdminMemory } from '../hooks/useAdmin'
import { formatDate, cn } from '@/lib/utils'

const PAGE_SIZE = 20

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

export function MemoriesTab() {
  const [page, setPage] = useState(0)
  const offset = page * PAGE_SIZE
  const { data, isLoading } = useAdminMemories(PAGE_SIZE, offset)
  const deleteMemory = useDeleteAdminMemory()

  if (isLoading && !data) {
    return <div className="flex justify-center py-12"><Loading size="lg" /></div>
  }

  if (!data || data.items.length === 0) {
    return <p className="text-foreground-secondary py-4">메모리가 없습니다.</p>
  }

  const totalPages = Math.ceil(data.total / PAGE_SIZE)

  const handleDelete = (memoryId: string) => {
    if (confirm('이 메모리를 삭제하시겠습니까?')) {
      deleteMemory.mutate(memoryId)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-foreground-secondary">
          총 {data.total}개 중 {offset + 1}-{Math.min(offset + PAGE_SIZE, data.total)}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
            이전
          </Button>
          <span className="text-sm text-foreground-secondary px-2">
            {page + 1} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            다음
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        {data.items.map((memory) => (
          <div key={memory.id} className="card p-3 hover:shadow-medium transition-shadow">
            <div className="flex items-start gap-3">
              <Brain className="h-4 w-4 mt-0.5 text-foreground-muted shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-foreground">
                  {memory.content.length > 120 ? memory.content.slice(0, 120) + '...' : memory.content}
                </p>
                <div className="flex items-center gap-2 mt-2 text-xs text-foreground-tertiary flex-wrap">
                  <span className="px-1.5 py-0.5 rounded bg-background-secondary">
                    {scopeLabel[memory.scope] || memory.scope}
                  </span>
                  {memory.owner_name && (
                    <span>{memory.owner_name}</span>
                  )}
                  {memory.category && (
                    <span className="px-1.5 py-0.5 rounded bg-background-secondary">{memory.category}</span>
                  )}
                  {memory.importance && (
                    <span className={cn('px-1.5 py-0.5 rounded', importanceColor[memory.importance])}>
                      {memory.importance === 'high' ? '높음' : memory.importance === 'medium' ? '중간' : '낮음'}
                    </span>
                  )}
                  {memory.created_at && (
                    <span>{formatDate(memory.created_at)}</span>
                  )}
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
        ))}
      </div>

      {/* Bottom pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
            이전
          </Button>
          <span className="flex items-center text-sm text-foreground-secondary px-2">
            {page + 1} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            다음
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
