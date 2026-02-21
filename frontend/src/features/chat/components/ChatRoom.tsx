import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Users, Settings, Trash2, Plus, Wifi, WifiOff, LogOut, Book } from 'lucide-react'
import { Button, Tooltip } from '@/components/ui'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { MembersPanel } from './MembersPanel'
import { ContextSourcesModal } from './ContextSourcesModal'
import { LoadingScreen } from '@/components/common/Loading'
import { EmptyState } from '@/components/common/EmptyState'
import { useChatRoom, useMessages, useSendMessage, useChatRooms, useDeleteChatRoom, useRemoveChatRoomMember } from '../hooks/useChat'
import { useAuthStore } from '@/features/auth/store/authStore'
import { useUIStore } from '@/stores/uiStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { uploadDocument, linkDocumentToRoom } from '@/features/document/api/documentApi'
import { cn } from '@/lib/utils'
import { useQueryClient } from '@tanstack/react-query'

export function ChatRoom() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user, token } = useAuthStore()
  const { setCreateRoomModalOpen } = useUIStore()
  
  const [isSending, setIsSending] = useState(false)
  const [typingUsers, setTypingUsers] = useState<string[]>([])
  const [showMembersPanel, setShowMembersPanel] = useState(false)
  const [showContextModal, setShowContextModal] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string | null>(null)

  const { data: chatRooms = [] } = useChatRooms()
  const { data: room, isLoading: roomLoading } = useChatRoom(roomId)
  const { data: messages = [], isLoading: messagesLoading } = useMessages(roomId)
  const sendMessageMutation = useSendMessage(roomId || '')
  const deleteRoomMutation = useDeleteChatRoom()
  const removeMemberMutation = useRemoveChatRoomMember()

  // WebSocket 연결
  const effectiveToken = token || localStorage.getItem('access_token') || 'dev-token'
  
  const handleWebSocketMessage = useCallback((msg: unknown) => {
    const message = msg as { type: string; data: { user_name?: string; user_id?: string } }
    if (message.type === 'typing:start') {
      setTypingUsers(prev => {
        if (prev.includes(message.data.user_name || '')) return prev
        return [...prev, message.data.user_name || '']
      })
    } else if (message.type === 'typing:stop') {
      setTypingUsers(prev => prev.filter(u => u !== message.data.user_name))
    }
  }, [])

  const { isConnected, sendMessage: wsSendMessage, startTyping, stopTyping } = useWebSocket({
    roomId: roomId || '',
    token: effectiveToken,
    onMessage: handleWebSocketMessage,
  })

  const handleTyping = useCallback(() => {
    if (isConnected) {
      startTyping()
    }
  }, [isConnected, startTyping])

  const handleContextSave = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['chat', 'room', roomId] })
  }, [queryClient, roomId])

  const handleDeleteRoom = useCallback(async () => {
    if (!roomId) return
    if (!confirm('이 대화방을 삭제하시겠습니까? 모든 메시지가 삭제됩니다.')) return
    try {
      await deleteRoomMutation.mutateAsync(roomId)
      navigate('/chat')
    } catch (error) {
      console.error('대화방 삭제 실패:', error)
    }
  }, [roomId, deleteRoomMutation, navigate])

  const handleLeaveRoom = useCallback(async () => {
    if (!roomId || !user) return
    if (!confirm('이 대화방에서 나가시겠습니까?')) return
    try {
      await removeMemberMutation.mutateAsync({ roomId, userId: user.id })
      navigate('/chat')
    } catch (error) {
      console.error('대화방 나가기 실패:', error)
    }
  }, [roomId, user, removeMemberMutation, navigate])

  const handleSend = useCallback(async (content: string) => {
    if (!content.trim() || isSending) return

    stopTyping()

    if (isConnected) {
      wsSendMessage(content)
      return
    }

    setIsSending(true)
    try {
      await sendMessageMutation.mutateAsync({ content })
    } catch (error) {
      console.error('메시지 전송 실패:', error)
    } finally {
      setIsSending(false)
    }
  }, [isSending, stopTyping, isConnected, wsSendMessage, sendMessageMutation])

  const handleFileUpload = useCallback(async (files: FileList) => {
    if (!roomId) return

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      setUploadStatus(`${file.name} 업로드 중...`)
      try {
        const doc = await uploadDocument(file, roomId)
        await linkDocumentToRoom(doc.id, roomId)
        setUploadStatus(`${file.name} 업로드 완료`)
      } catch (error) {
        console.error('파일 업로드 실패:', error)
        setUploadStatus(`${file.name} 업로드 실패`)
      }
    }

    setTimeout(() => setUploadStatus(null), 3000)
  }, [roomId])

  if (!roomId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <EmptyState
          title="대화방을 선택하세요"
          description={chatRooms.length === 0 ? '새 대화방을 만들어 대화를 시작하세요' : '왼쪽 사이드바에서 대화방을 선택하세요'}
          action={
            chatRooms.length === 0 && (
              <Button onClick={() => setCreateRoomModalOpen(true)}>
                <Plus className="h-4 w-4 mr-1" />
                새 대화방 만들기
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
          title="대화방을 찾을 수 없습니다"
          description="삭제되었거나 접근 권한이 없을 수 있습니다"
          action={<Button variant="secondary" onClick={() => navigate('/chat')}>돌아가기</Button>}
        />
      </div>
    )
  }

  if (room.share_role === 'viewer') {
    return (
      <div className="flex-1 flex items-center justify-center">
        <EmptyState
          title="조회자 권한입니다"
          description="이 대화방은은 메모리만 공유받은 상태입니다. 컨텍스트 소스 설정에서 이 방의 메모리를 활용할 수 있습니다."
          action={<Button variant="secondary" onClick={() => navigate('/chat')}>돌아가기</Button>}
        />
      </div>
    )
  }

  // Context Sources 표시
  const contextSources = room.context_sources?.memory
  const sourceLabels: string[] = []
  if (contextSources?.include_this_room !== false) {
    sourceLabels.push('이 대화방')
  }
  if (contextSources?.other_chat_rooms?.length) {
    sourceLabels.push(`다른방(${contextSources.other_chat_rooms.length})`)
  }
  if (sourceLabels.length === 0) {
    sourceLabels.push('이 대화방')
  }

  return (
    <div className="flex flex-col h-full bg-background">
      <header className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h1 className="font-semibold text-lg truncate">{room.name}</h1>
            <span className="px-2 py-0.5 text-xs rounded-full bg-background-secondary text-foreground-secondary shrink-0">
              개인
            </span>
            <Tooltip content={isConnected ? '실시간 연결됨' : '오프라인 (폴링 모드)'} side="bottom">
              <span className={cn(
                'flex items-center gap-1 px-2 py-0.5 text-xs rounded-full shrink-0',
                isConnected ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
              )}>
                {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                {isConnected ? '실시간' : '폴링'}
              </span>
            </Tooltip>
          </div>
          {/* Context Sources - 클릭하면 설정 모달 열기 */}
          <button
            onClick={() => setShowContextModal(true)}
            className="text-xs text-foreground-muted mt-1 hover:text-accent transition-colors text-left"
          >
            📦 메모리 소스: {sourceLabels.join(', ')} <span className="text-accent">(변경)</span>
          </button>
        </div>
        
        <div className="flex items-center gap-1 shrink-0">
          <Tooltip content="Agent 연동 가이드" side="bottom">
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => window.open('/docs/agent-integration-guide.html', '_blank')}
            >
              <Book className="h-4 w-4" />
            </Button>
          </Tooltip>
          <Tooltip content="멤버 관리" side="bottom">
            <Button variant="ghost" size="icon" onClick={() => setShowMembersPanel(true)}>
              <Users className="h-4 w-4" />
            </Button>
          </Tooltip>
          <Tooltip content="메모리 소스 설정" side="bottom">
            <Button variant="ghost" size="icon" onClick={() => setShowContextModal(true)}>
              <Settings className="h-4 w-4" />
            </Button>
          </Tooltip>
          {user?.id === room.owner_id ? (
            <Tooltip content="대화방 삭제" side="bottom">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleDeleteRoom}
                className="text-foreground-muted hover:text-error"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </Tooltip>
          ) : (
            <Tooltip content="대화방 나가기" side="bottom">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLeaveRoom}
                className="text-foreground-muted hover:text-error"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </Tooltip>
          )}
        </div>
      </header>

      <MessageList
        messages={messages}
        currentUserId={user?.id || 'dev-user-001'}
        isLoading={messagesLoading}
        isTyping={isSending || typingUsers.length > 0}
        typingUsers={typingUsers}
      />

      {uploadStatus && (
        <div className="px-4 py-2 text-xs text-foreground-secondary bg-background-secondary border-t border-border">
          {uploadStatus}
        </div>
      )}

      <MessageInput
        onSend={handleSend}
        onFileUpload={handleFileUpload}
        disabled={isSending}
        onTyping={handleTyping}
      />

      {/* Members Panel */}
      <MembersPanel
        roomId={roomId}
        open={showMembersPanel}
        onClose={() => setShowMembersPanel(false)}
      />

      {/* Context Sources Modal */}
      <ContextSourcesModal
        room={room}
        open={showContextModal}
        onClose={() => setShowContextModal(false)}
        onSave={handleContextSave}
      />
    </div>
  )
}
