import { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui'
import { MessageItem } from './MessageItem'
import { TypingIndicator } from '@/components/common/Loading'
import { EmptyState } from '@/components/common/EmptyState'
import { MessageSquare } from 'lucide-react'
import type { Message } from '@/types'

interface MessageListProps {
  messages: Message[]
  currentUserId: string
  isTyping?: boolean
  isLoading?: boolean
  typingUsers?: string[]
}

export function MessageList({ 
  messages, 
  currentUserId, 
  isTyping = false, 
  isLoading = false,
  typingUsers = [],
}: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages.length])

  if (!isLoading && messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <EmptyState
          icon={MessageSquare}
          title="대화를 시작해보세요"
          description="@ai를 멘션하거나 /로 명령어를 입력할 수 있습니다"
        />
      </div>
    )
  }

  const typingText = typingUsers.length > 0
    ? `${typingUsers.join(', ')}님이 입력 중...`
    : 'AI가 응답 중...'

  return (
    <ScrollArea className="flex-1">
      <div ref={scrollRef} className="py-4">
        {messages.map((message) => (
          <MessageItem
            key={message.id}
            message={message}
            isOwnMessage={message.user_id === currentUserId}
          />
        ))}
        
        {isTyping && (
          <div className="px-4 py-2">
            <div className="flex items-center gap-2 text-sm text-foreground-secondary">
              <TypingIndicator />
              <span>{typingText}</span>
            </div>
          </div>
        )}
        
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}
