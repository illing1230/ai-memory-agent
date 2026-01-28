import { useEffect, useRef, useCallback, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { chatKeys } from '@/features/chat/hooks/useChat'

type MessageHandler = (data: unknown) => void

interface WebSocketMessage {
  type: string
  data: unknown
}

interface UseWebSocketOptions {
  roomId: string
  token: string
  onMessage?: MessageHandler
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

interface UseWebSocketReturn {
  isConnected: boolean
  send: (type: string, data: unknown) => void
  sendMessage: (content: string) => void
  startTyping: () => void
  stopTyping: () => void
}

export function useWebSocket({
  roomId,
  token,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
}: UseWebSocketOptions): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const [isConnected, setIsConnected] = useState(false)
  const queryClient = useQueryClient()

  // WebSocket URL 생성
  const getWsUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}/ws/chat/${roomId}?token=${token}`
  }, [roomId, token])

  // 연결 함수
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const ws = new WebSocket(getWsUrl())

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
      onConnect?.()
    }

    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason)
      setIsConnected(false)
      onDisconnect?.()

      // 재연결 시도 (비정상 종료 시)
      if (event.code !== 1000 && event.code !== 4001) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 3000)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      onError?.(error)
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        handleMessage(message)
        onMessage?.(message)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    wsRef.current = ws
  }, [getWsUrl, onConnect, onDisconnect, onError, onMessage])

  // 메시지 처리
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'message:new':
        // 새 메시지를 쿼리 캐시에 추가
        queryClient.setQueryData(
          chatKeys.messages(roomId),
          (old: unknown[] | undefined) => {
            if (!old) return [message.data]
            // 중복 체크
            const exists = old.some((m: { id?: string }) => m.id === (message.data as { id?: string }).id)
            if (exists) return old
            return [...old, message.data]
          }
        )
        break

      case 'member:join':
      case 'member:leave':
        // 멤버 목록 갱신
        queryClient.invalidateQueries({ queryKey: chatKeys.members(roomId) })
        break

      case 'memory:extracted':
        // 메모리 추출 알림 (토스트 등으로 표시)
        console.log('Memory extracted:', message.data)
        break

      case 'room:info':
        // 채팅방 정보 (접속자 목록 등)
        console.log('Room info:', message.data)
        break

      case 'pong':
        // 핑 응답
        break
    }
  }, [queryClient, roomId])

  // 메시지 전송
  const send = useCallback((type: string, data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }))
    }
  }, [])

  // 채팅 메시지 전송
  const sendMessage = useCallback((content: string) => {
    send('message:send', { content })
  }, [send])

  // 타이핑 시작
  const startTyping = useCallback(() => {
    send('typing:start', {})
  }, [send])

  // 타이핑 종료
  const stopTyping = useCallback(() => {
    send('typing:stop', {})
  }, [send])

  // 연결/해제
  useEffect(() => {
    if (roomId && token) {
      connect()
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted')
        wsRef.current = null
      }
    }
  }, [connect, roomId, token])

  // 핑 전송 (30초마다)
  useEffect(() => {
    if (!isConnected) return

    const pingInterval = setInterval(() => {
      send('ping', {})
    }, 30000)

    return () => clearInterval(pingInterval)
  }, [isConnected, send])

  return {
    isConnected,
    send,
    sendMessage,
    startTyping,
    stopTyping,
  }
}
