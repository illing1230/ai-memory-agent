import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Avatar } from '@/components/ui'
import { formatTime } from '@/lib/utils'
import { Bot, ChevronRight, FileText, Brain, Image } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message, MessageSource } from '@/types'

interface MessageItemProps {
  message: Message
  isOwnMessage?: boolean
}

export function MessageItem({ message, isOwnMessage = false }: MessageItemProps) {
  const isAssistant = message.role === 'assistant'

  return (
    <div
      className={cn(
        'group flex gap-3 px-4 py-2',
        'hover:bg-background-hover transition-colors',
        isOwnMessage && !isAssistant && 'flex-row-reverse'
      )}
    >
      <div className="shrink-0">
        {isAssistant ? (
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white">
            <Bot className="h-4 w-4" />
          </div>
        ) : (
          <Avatar
            alt={message.user_name || 'User'}
            fallback={message.user_name?.charAt(0) || 'U'}
            size="md"
          />
        )}
      </div>

      <div className={cn('flex-1 min-w-0', isOwnMessage && !isAssistant && 'text-right')}>
        <div className={cn('flex items-center gap-2 mb-1', isOwnMessage && !isAssistant && 'flex-row-reverse')}>
          <span className="font-medium text-sm text-foreground">
            {isAssistant ? 'AI' : message.user_name || '사용자'}
          </span>
          <span className="text-xs text-foreground-muted">{formatTime(message.created_at)}</span>
        </div>

        <div className={cn('inline-block max-w-[85%] text-sm', isAssistant && 'bg-background-secondary rounded-lg px-3 py-2')}>
          <MessageContent content={message.content} isAssistant={isAssistant} />
        </div>

        {isAssistant && message.sources && <SourcePanel sources={message.sources} />}
      </div>
    </div>
  )
}

function SourcePanel({ sources }: { sources: MessageSource }) {
  const [isOpen, setIsOpen] = useState(false)

  const docCount = sources.documents?.length ?? 0
  const memCount = sources.memories?.length ?? 0
  const totalCount = docCount + memCount

  if (totalCount === 0) return null

  const parts: string[] = []
  if (docCount > 0) parts.push(`문서 ${docCount}`)
  if (memCount > 0) parts.push(`메모리 ${memCount}`)
  const summary = parts.join(', ')

  return (
    <div className="mt-2 max-w-[85%]">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1 text-xs text-foreground-muted hover:text-foreground transition-colors"
      >
        <ChevronRight
          className={cn('h-3 w-3 transition-transform', isOpen && 'rotate-90')}
        />
        <span>참조 소스 ({summary})</span>
      </button>

      {isOpen && (
        <div className="mt-1 pl-4 space-y-1 text-xs text-foreground-secondary">
          {sources.documents?.map((doc) => (
            <div key={`${doc.document_id}-${doc.slide_number ?? ''}`} className="flex items-start gap-1.5">
              {doc.slide_image_url ? (
                <Image className="h-3 w-3 mt-0.5 shrink-0 text-accent" />
              ) : (
                <FileText className="h-3 w-3 mt-0.5 shrink-0 text-accent" />
              )}
              <div className="min-w-0">
                <span className="font-medium">{doc.document_name}</span>
                {doc.slide_number && (
                  <span className="text-foreground-muted ml-1">슬라이드 {doc.slide_number}</span>
                )}
                <span className="text-foreground-muted ml-1">({Math.round(doc.score * 100)}%)</span>
                {doc.slide_image_url && (
                  <a
                    href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}${doc.slide_image_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block mt-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <img
                      src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}${doc.slide_image_url}`}
                      alt={`슬라이드 ${doc.slide_number}`}
                      className="w-48 rounded border border-border hover:opacity-80 transition-opacity"
                    />
                  </a>
                )}
                {!doc.slide_image_url && (
                  <p className="text-foreground-muted truncate">{doc.content}</p>
                )}
              </div>
            </div>
          ))}
          {sources.memories?.map((mem) => (
            <div key={mem.memory_id} className="flex items-start gap-1.5">
              <Brain className="h-3 w-3 mt-0.5 shrink-0 text-purple-500" />
              <div className="min-w-0">
                <span className="font-medium">{mem.source_name}</span>
                <span className="text-foreground-muted ml-1">({Math.round(mem.score * 100)}%)</span>
                <p className="text-foreground-muted truncate">{mem.content}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function MessageContent({ content, isAssistant }: { content: string; isAssistant: boolean }) {
  // AI 응답은 마크다운으로 렌더링
  if (isAssistant) {
    return (
      <div className="prose prose-sm dark:prose-invert max-w-none break-words">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // 커스텀 스타일링
            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
            ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
            li: ({ children }) => <li className="mb-1">{children}</li>,
            code: ({ className, children, ...props }) => {
              const isInline = !className
              return isInline ? (
                <code className="px-1 py-0.5 rounded bg-background-tertiary text-accent font-mono text-xs" {...props}>
                  {children}
                </code>
              ) : (
                <code className={cn("block p-2 rounded bg-background-tertiary overflow-x-auto text-xs", className)} {...props}>
                  {children}
                </code>
              )
            },
            pre: ({ children }) => (
              <pre className="mb-2 rounded bg-background-tertiary overflow-x-auto">
                {children}
              </pre>
            ),
            a: ({ href, children }) => (
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                {children}
              </a>
            ),
            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
            em: ({ children }) => <em className="italic">{children}</em>,
            h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
            h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
            h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 border-accent pl-3 italic text-foreground-secondary mb-2">
                {children}
              </blockquote>
            ),
            table: ({ children }) => (
              <div className="overflow-x-auto mb-2">
                <table className="min-w-full border-collapse border border-border text-xs">
                  {children}
                </table>
              </div>
            ),
            th: ({ children }) => (
              <th className="border border-border bg-background-secondary px-2 py-1 text-left font-semibold">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="border border-border px-2 py-1">{children}</td>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    )
  }

  // 사용자 메시지는 멘션/커맨드 하이라이팅
  const highlightMentions = (text: string) => {
    const parts = text.split(/(@\w+)/g)
    return parts.map((part, i) => {
      if (part.match(/^@\w+$/)) {
        return (
          <span key={i} className="px-1 py-0.5 rounded bg-accent-muted text-accent font-medium">
            {part}
          </span>
        )
      }
      return part
    })
  }

  const highlightCommands = (text: string) => {
    if (text.startsWith('/')) {
      const match = text.match(/^(\/\w+)/)
      if (match) {
        return (
          <>
            <span className="font-mono text-accent">{match[1]}</span>
            {text.slice(match[1].length)}
          </>
        )
      }
    }
    return text
  }

  return (
    <div className="whitespace-pre-wrap break-words">
      {content.startsWith('/') ? highlightCommands(content) : highlightMentions(content)}
    </div>
  )
}
