// API 응답 타입
export interface ApiResponse<T> {
  success: boolean
  data: T
  error: string | null
}

// 페이지네이션
export interface PaginationParams {
  limit?: number
  offset?: number
}

// 사용자
export interface User {
  id: string
  name: string
  email: string
  department_id?: string
  created_at: string
  updated_at: string
}

// 부서
export interface Department {
  id: string
  name: string
  description?: string
  created_at: string
}

// 프로젝트
export interface Project {
  id: string
  name: string
  description?: string
  department_id?: string
  created_at: string
  updated_at: string
}

// 채팅방
export interface ChatRoom {
  id: string
  name: string
  room_type: 'personal' | 'project' | 'department'
  owner_id: string
  project_id?: string
  department_id?: string
  context_sources?: ContextSources
  created_at: string
  updated_at?: string
}

export interface ContextSources {
  memory?: {
    include_this_room?: boolean
    other_chat_rooms?: string[]
    include_personal?: boolean
    projects?: string[]
    departments?: string[]
  }
  rag?: {
    collections?: string[]
    filters?: Record<string, unknown>
  }
}

// 채팅방 멤버
export interface ChatRoomMember {
  id: string
  chat_room_id: string
  user_id: string
  user_name?: string
  user_email?: string
  role: 'owner' | 'admin' | 'member'
  joined_at: string
}

// 메시지
export interface Message {
  id: string
  chat_room_id: string
  user_id: string
  user_name?: string
  role: 'user' | 'assistant'
  content: string
  mentions?: string[]
  created_at: string
}

// 메모리
export interface Memory {
  id: string
  content: string
  scope: 'personal' | 'chatroom' | 'project' | 'department'
  owner_id: string
  project_id?: string
  department_id?: string
  chat_room_id?: string
  category?: string
  importance?: 'high' | 'medium' | 'low'
  created_at: string
  updated_at: string
}

export interface MemorySearchResult {
  memory: Memory
  score: number
}
