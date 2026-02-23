import { useCallback, useState } from 'react'
import { Upload, FileText, X, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui'
import { useUploadDocument } from '../hooks/useDocument'

interface DocumentUploadProps {
  chatRoomId?: string
  onSuccess?: () => void
}

export function DocumentUpload({ chatRoomId, onSuccess }: DocumentUploadProps) {
  const [dragOver, setDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const uploadMutation = useUploadDocument()

  const acceptedTypes = ['.pdf', '.txt', '.pptx']
  const acceptedMimeTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']

  const isValidFile = (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    return acceptedTypes.includes(ext) || acceptedMimeTypes.includes(file.type)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file && isValidFile(file)) {
      setSelectedFile(file)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && isValidFile(file)) {
      setSelectedFile(file)
    }
    e.target.value = ''
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    try {
      await uploadMutation.mutateAsync({ file: selectedFile, chatRoomId })
      setSelectedFile(null)
      onSuccess?.()
    } catch {
      // error handled by mutation
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer
          ${dragOver ? 'border-accent bg-accent/5' : 'border-border hover:border-accent/50'}
        `}
        onClick={() => document.getElementById('doc-file-input')?.click()}
      >
        <Upload className="h-8 w-8 mx-auto mb-2 text-foreground-muted" />
        <p className="text-sm text-foreground-secondary">
          파일을 드래그하거나 클릭하여 업로드
        </p>
        <p className="text-xs text-foreground-muted mt-1">PDF, TXT, PPTX (최대 50MB)</p>
        <input
          id="doc-file-input"
          type="file"
          accept=".pdf,.txt,.pptx"
          className="hidden"
          onChange={handleFileSelect}
        />
      </div>

      {selectedFile && (
        <div className="flex items-center gap-2 p-3 bg-background-secondary rounded-lg">
          <FileText className="h-5 w-5 text-accent shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{selectedFile.name}</p>
            <p className="text-xs text-foreground-muted">{formatSize(selectedFile.size)}</p>
          </div>
          <Button variant="ghost" size="icon-sm" onClick={() => setSelectedFile(null)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {selectedFile && (
        <Button
          className="w-full"
          onClick={handleUpload}
          disabled={uploadMutation.isPending}
        >
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              업로드 중...
            </>
          ) : (
            '업로드'
          )}
        </Button>
      )}

      {uploadMutation.isError && (
        <p className="text-sm text-red-500">
          업로드 실패: {uploadMutation.error?.message || '알 수 없는 오류'}
        </p>
      )}

      {uploadMutation.isSuccess && (
        <p className="text-sm text-green-500">업로드 완료!</p>
      )}
    </div>
  )
}
