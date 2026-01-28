import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Users, Settings, MoreHorizontal, Plus, Wifi, WifiOff } from 'lucide-react'
import { Button, Tooltip } from '@/components/ui'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { LoadingScreen } from '@/components/common/Loading'
import { EmptyState } from '@/components/common/EmptyState'
import { useChatRoom, useMessages, useSendMessage, useChatRooms } from '../hooks/useChat'
import { useAuthStore } from '@/features/auth/store/authStore'
import { useUIStore } from '@/stores/uiStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { cn } from '@/lib/utils'

export function ChatRoom() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  const { user, token } = useAuthStore()
  const { setCreateRoomModalOpen } = useUIStore()
  
  const [isSending, setIsSending] = useState(false)
  const [typingUsers, setTypingUsers] = useState<string[]>([])

  const { data: chatRooms = [] } = useChatRooms()
  const { data: room, isLoading: roomLoading } = useChatRoom(roomId)
  const { data: messages = [], isLoading: messagesLoading } = useMessages(roomId)
  const sendMessageMutation = useSendMessage(roomId || '')

  // WebSocket 연결 (토큰이 있을 때만)
  const effectiveToken = token || localStorage.getItem('access_token') || 'dev-token'
  
  const { isConnected, sendMessage: wsSendMessage, startTyping, stopTyping } = useWebSocket({
    roomId: roomId || '',
    token: effectiveToken,
    onMessage: useCallback((msg: unknown) => {
      const message = msg as { type: string; data: { user_name?: string; user_id?: string } }
      // 타이핑 인디케이터 처리
      if (message.type === 'typing:start') {
        setTypingUsers(prev => {
          if (prev.includes(message.data.user_name || '')) return prev
          return [...prev, message.data.user_name || '']
        })
      } else if (message.type === 'typing:stop') {
        setTypingUsers(prev => prev.filter(u => u !== message.data.user_name))
      }
    }, []),
  })

  if (!roomId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <EmptyState
          title="채팅방을 선택하세요"
          description={chatRooms.length === 0 ? '새 채팅방을 만들어 대화를 시작하세요' : '왼쪽 사이드바에서 채팅방을 선택하세요'}
          action={
            chatRooms.length === 0 && (
              <Button onClick={() => setCreateRoomModalOpen(true)}>
                <Plus className="h-4 w-4 mr-1" />
                새 채팅방 만들기
              </Button>
            )
          }
        />
      </div>
    )
  }

  if (roomLoading) {
    return <LoadingScreen />
  }

  if (!room) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <EmptyState
          title="채팅방을 찾을 수 없습니다"
          description="삭제되었거나 접근 권한이 없을 수 있습니다"
          action={<Button variant="secondary" onClick={() => navigate('/chat')}>돌아가기</Button>}
        />
      </div>
    )
  }

  const handleSend = async (content: string) => {
    if (!content.trim() || isSending) return
    
    stopTyping()
    
    // WebSocket으로 전송 시도
    if (isConnected) {
      wsSendMessage(content)
      return
    }
    
    // 폴백: REST API 사용
    setIsSending(true)
    try {
      await sendMessageMutation.mutateAsync({ content })
    } catch (error) {
      console.error('메시지 전송 실패:', error)
    } finally {
      setIsSending(false)
    }
  }

  const handleTyping = useCallback(() => {
    if (isConnected) {
      startTyping()
    }
  }, [isConnected, startTyping])

  return (
    <div className="flex flex-col h-full bg-background">
      <header className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-3">
          <h1 className="font-semibold text-lg">{room.name}</h1>
          <span className="px-2 py-0.5 text-xs rounded-full bg-background-secondary text-foreground-secondary">
            {room.room_type === 'personal' ? '개인' : room.room_type === 'project' ? '프로젝트' : '부서'}
          </span>
          {/* 연결 상태 표시 */}
          <Tooltip content={isConnected ? '실시간 연결됨' : '오프라인 (폴링 모드)'} side="bottom">
            <span className={cn(
              'flex items-center gap-1 px-2 py-0.5 text-xs rounded-full',
              isConnected ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
            )}>
              {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
              {isConnected ? '실시간' : '폴링'}
            </span>
          </Tooltip>
        </div>
        
        <div className="flex items-center gap-1">
          <Tooltip content="멤버" side="bottom">
            <Button variant="ghost" size="icon"><Users className="h-4 w-4" /></Button>
          </Tooltip>
          <Tooltip content="설정" side="bottom">
            <Button variant="ghost" size="icon"><Settings className="h-4 w-4" /></Button>
          </Tooltip>
          <Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button>
        </div>
      </header>

      <MessageList
        messages={messages}
        currentUserId={user?.id || 'dev-user-001'}
        isLoading={messagesLoading}
        isTyping={isSending || typingUsers.length > 0}
        typingUsers={typingUsers}
      />

      <MessageInput 
        onSend={handleSend} 
        disabled={isSending}
        onTyping={handleTyping}
      />
    </div>
  )
}
