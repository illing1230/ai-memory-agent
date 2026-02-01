import { useState, useMemo } from 'react'
import { Search, Filter, Trash2, Brain, Clock, Tag } from 'lucide-react'
import { Button, Input, ScrollArea } from '@/components/ui'
import { Loading } from '@/components/common/Loading'
import { EmptyState } from '@/components/common/EmptyState'
import { useMemorySearch, useDeleteMemory } from '../hooks/useMemory'
import { formatDate, cn } from '@/lib/utils'
import type { MemorySearchResult } from '@/types'

type ScopeFilter = 'all' | 'personal' | 'chatroom' | 'project' | 'department'

export function MemorySearch() {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>('all')

  const handleQueryChange = (value: string) => {
    setQuery(value)
    setTimeout(() => setDebouncedQuery(value), 300)
  }

  const { data: searchResults, isLoading, isError, error } = useMemorySearch({ query: debouncedQuery, limit: 20 })
  const deleteMemory = useDeleteMemory()

  const filteredResults = useMemo(() => {
    if (!searchResults) return []
    if (scopeFilter === 'all') return searchResults
    return searchResults.filter((r) => r.memory.scope === scopeFilter)
  }, [searchResults, scopeFilter])

  const handleDelete = async (memoryId: string) => {
    if (confirm('이 메모리를 삭제하시겠습니까?')) {
      await deleteMemory.mutateAsync(memoryId)
    }
  }

  return (
    <div className="flex flex-col h-full bg-background">
      <header className="border-b border-border px-6 py-4">
        <h1 className="text-xl font-semibold flex items-center gap-2">
          <Brain className="h-5 w-5 text-accent" />
          메모리 검색
        </h1>
        <p className="text-sm text-foreground-secondary mt-1">저장된 메모리에서 정보를 검색하세요</p>
      </header>

      <div className="border-b border-border px-6 py-4 space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
          <Input
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            placeholder="검색어를 입력하세요..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-foreground-muted" />
          <span className="text-sm text-foreground-secondary">범위:</span>
          <div className="flex gap-1">
            {(['all', 'personal', 'chatroom', 'project', 'department'] as ScopeFilter[]).map((scope) => (
              <Button
                key={scope}
                variant={scopeFilter === scope ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setScopeFilter(scope)}
                className="text-xs"
              >
                {scope === 'all' && '전체'}
                {scope === 'personal' && '개인'}
                {scope === 'chatroom' && '채팅방'}
                {scope === 'project' && '프로젝트'}
                {scope === 'department' && '부서'}
              </Button>
            ))}
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="px-6 py-4">
          {!debouncedQuery ? (
            <EmptyState icon={Search} title="검색어를 입력하세요" description="2글자 이상 입력하면 검색이 시작됩니다" />
          ) : isLoading ? (
            <div className="flex justify-center py-8"><Loading size="lg" /></div>
          ) : isError ? (
            <EmptyState icon={Brain} title="검색 중 오류가 발생했습니다" description={(error as Error)?.message || '잠시 후 다시 시도해주세요'} />
          ) : filteredResults.length === 0 ? (
            <EmptyState icon={Brain} title="검색 결과가 없습니다" description={`"${debouncedQuery}"와 관련된 메모리를 찾을 수 없습니다`} />
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-foreground-secondary">{filteredResults.length}개의 결과</p>
              {filteredResults.map((result) => (
                <MemoryCard key={result.memory.id} result={result} onDelete={() => handleDelete(result.memory.id)} />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

interface MemoryCardProps {
  result: MemorySearchResult
  onDelete: () => void
}

function MemoryCard({ result, onDelete }: MemoryCardProps) {
  const { memory, score } = result
  const scopeLabel: Record<string, string> = { personal: '개인', chatroom: '채팅방', project: '프로젝트', department: '부서' }

  return (
    <div className="group card p-4 hover:shadow-medium transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-foreground leading-relaxed">{memory.content}</p>
          <div className="flex items-center gap-3 mt-3 text-xs text-foreground-tertiary">
            <span className="flex items-center gap-1">
              <Tag className="h-3 w-3" />
              {scopeLabel[memory.scope] || memory.scope}
            </span>
            {memory.category && (
              <span className="px-1.5 py-0.5 rounded bg-background-secondary">{memory.category}</span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDate(memory.created_at)}
            </span>
            <span className={cn('font-medium', score >= 0.8 ? 'text-success' : score >= 0.6 ? 'text-warning' : 'text-foreground-tertiary')}>
              유사도 {Math.round(score * 100)}%
            </span>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          className="opacity-0 group-hover:opacity-100 text-foreground-muted hover:text-error"
          onClick={onDelete}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
