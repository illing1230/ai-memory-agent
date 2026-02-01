import { useState } from 'react'
import { FileText, Trash2, Eye, Loader2 } from 'lucide-react'
import { Button, Tooltip } from '@/components/ui'
import { useDocuments, useDeleteDocument } from '../hooks/useDocument'
import { DocumentUpload } from './DocumentUpload'
import type { Document } from '@/types'

export function DocumentPage() {
  const { data: documents = [], isLoading } = useDocuments()
  const deleteMutation = useDeleteDocument()
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null)

  const handleDelete = async (docId: string) => {
    if (!confirm('이 문서를 삭제하시겠습니까?')) return
    await deleteMutation.mutateAsync(docId)
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const statusLabel = (status: string) => {
    switch (status) {
      case 'completed': return { text: '완료', className: 'text-green-500' }
      case 'processing': return { text: '처리 중', className: 'text-yellow-500' }
      case 'failed': return { text: '실패', className: 'text-red-500' }
      default: return { text: status, className: 'text-foreground-muted' }
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-border px-6 py-4">
        <h1 className="text-lg font-semibold">문서 관리</h1>
        <p className="text-sm text-foreground-muted mt-1">
          PDF, TXT 파일을 업로드하여 채팅방에서 AI 컨텍스트로 활용할 수 있습니다.
        </p>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Upload Section */}
        <div className="max-w-lg">
          <h2 className="text-sm font-semibold mb-3">문서 업로드</h2>
          <DocumentUpload />
        </div>

        {/* Document List */}
        <div>
          <h2 className="text-sm font-semibold mb-3">
            내 문서 {documents.length > 0 && `(${documents.length})`}
          </h2>

          {isLoading ? (
            <div className="flex items-center gap-2 text-foreground-muted py-8 justify-center">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">로딩 중...</span>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12 text-foreground-muted">
              <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">업로드된 문서가 없습니다</p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc: Document) => {
                const status = statusLabel(doc.status)
                return (
                  <div
                    key={doc.id}
                    className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-background-hover transition-colors"
                  >
                    <FileText className="h-5 w-5 text-accent shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{doc.name}</p>
                      <div className="flex items-center gap-2 text-xs text-foreground-muted">
                        <span>{doc.file_type.toUpperCase()}</span>
                        <span>·</span>
                        <span>{formatSize(doc.file_size)}</span>
                        <span>·</span>
                        <span className={status.className}>{status.text}</span>
                        {doc.chunk_count > 0 && (
                          <>
                            <span>·</span>
                            <span>{doc.chunk_count} chunks</span>
                          </>
                        )}
                        <span>·</span>
                        <span>{formatDate(doc.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Tooltip content="삭제">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleDelete(doc.id)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </Tooltip>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
