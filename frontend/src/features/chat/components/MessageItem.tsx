import { cn } from '@/lib/utils'
import { Avatar } from '@/components/ui'
import { formatTime } from '@/lib/utils'
import { Bot } from 'lucide-react'
import type { Message } from '@/types'

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
      </div>
    </div>
  )
}

function MessageContent({ content, isAssistant }: { content: string; isAssistant: boolean }) {
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

  if (isAssistant) {
    const lines = content.split('\n')
    return (
      <div className="space-y-1 whitespace-pre-wrap break-words">
        {lines.map((line, i) => (
          <div key={i}>{highlightMentions(line)}</div>
        ))}
      </div>
    )
  }

  return (
    <div className="whitespace-pre-wrap break-words">
      {content.startsWith('/') ? highlightCommands(content) : highlightMentions(content)}
    </div>
  )
}
