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
  role?: string
  department_id?: string
  created_at?: string
  updated_at?: string
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

// 대화방
export interface ChatRoom {
  id: string
  name: string
  room_type: 'personal'
  owner_id: string
  member_role?: 'owner' | 'admin' | 'member' | 'viewer'
  share_role?: 'viewer' | 'member' | null
  context_sources?: ContextSources
  created_at: string
  updated_at?: string
}

export interface ContextSources {
  memory?: {
    include_this_room?: boolean
    other_chat_rooms?: string[]

    agent_instances?: string[]
  }
  rag?: {
    collections?: string[]
    filters?: Record<string, unknown>
  }
}

// 대화방 멤버
export interface ChatRoomMember {
  id: string
  chat_room_id: string
  user_id: string
  user_name?: string
  user_email?: string
  role: 'owner' | 'admin' | 'member'
  joined_at: string
}

// 소스 참조 정보
export interface MessageSource {
  documents?: Array<{
    document_id: string
    document_name: string
    content: string
    score: number
    slide_number?: number
    slide_image_url?: string
  }>
  memories?: Array<{
    memory_id: string
    content: string
    scope: string
    score: number
    source_name: string
  }>
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
  sources?: MessageSource
  created_at: string
}

// 메모리
export interface Memory {
  id: string
  content: string
  scope: 'personal' | 'chatroom' | 'agent'
  owner_id: string
  chat_room_id?: string
  category?: string
  importance?: 'high' | 'medium' | 'low'
  metadata?: {
    source?: string
    agent_instance_id?: string
    [key: string]: unknown
  }
  created_at: string
  updated_at: string
}

export interface MemoryListResult {
  memory: Memory
  source_info?: {
    owner_name?: string
    chat_room_name?: string
    agent_instance_name?: string
  }
}

export interface MemorySearchResult {
  memory: Memory
  score: number
  source_info?: {
    owner_name?: string
    chat_room_name?: string
    agent_instance_name?: string
  }
}

// 관리자 타입
export interface DashboardStats {
  total_users: number
  total_chat_rooms: number
  total_memories: number
  total_messages: number
  total_departments: number
  total_projects: number
}

export interface AdminUser {
  id: string
  name: string
  email: string
  role: string
  department_id?: string
  department_name?: string
  created_at?: string
}

export interface AdminChatRoom {
  id: string
  name: string
  room_type: string
  owner_id: string
  owner_name?: string
  member_count: number
  message_count: number
  created_at?: string
}

export interface AdminDepartment {
  id: string
  name: string
  description?: string
  member_count: number
  created_at?: string
}

export interface AdminProject {
  id: string
  name: string
  description?: string
  department_id?: string
  department_name?: string
  member_count: number
  created_at?: string
}

export interface AdminMemory {
  id: string
  content: string
  scope: string
  owner_id: string
  owner_name?: string
  category?: string
  importance?: string
  created_at?: string
}

export interface PaginatedMemories {
  items: AdminMemory[]
  total: number
  limit: number
  offset: number
}

// 문서
export interface Document {
  id: string
  name: string
  file_type: 'pdf' | 'txt' | 'pptx'
  file_size: number
  owner_id: string
  chat_room_id?: string
  status: 'processing' | 'completed' | 'failed'
  chunk_count: number
  created_at: string
}

export interface DocumentChunk {
  id: string
  document_id: string
  content: string
  chunk_index: number
  vector_id?: string
  slide_number?: number
  slide_image_url?: string
}

export interface DocumentDetail extends Document {
  chunks: DocumentChunk[]
}

export interface DocumentLink {
  document_id: string
  chat_room_id: string
  linked_at: string
}

// 지식 대시보드
export interface MemoryStats {
  total: number
  active: number
  superseded: number
  by_scope: Record<string, number>
  by_category: Record<string, number>
  by_importance: Record<string, number>
  recent_7d: number
  recent_30d: number
}

export interface HotTopic {
  entity_name: string
  entity_type: string
  mention_count: number
}

export interface StaleKnowledge {
  no_access_30d: number
  no_access_60d: number
  no_access_90d: number
  low_importance_stale: number
}

export interface UserContribution {
  user_id: string
  user_name: string
  memories_created: number
  memories_accessed: number
}

export interface DocumentStats {
  total: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  total_chunks: number
}

export interface KnowledgeDashboard {
  memory_stats: MemoryStats
  hot_topics: HotTopic[]
  stale_knowledge: StaleKnowledge
  contributions: UserContribution[]
  document_stats: DocumentStats
}

// Mchat 타입
export interface MchatStatus {
  status: 'connected' | 'disconnected' | 'disabled'
  connected: boolean
  bot_user_id: string | null
  base_url: string | null
  last_error: string | null
  stats: {
    messages_received: number
    messages_responded: number
    memories_extracted: number
    errors: number
  }
}

export interface MchatChannel {
  id: string
  mchat_channel_id: string
  mchat_channel_name: string | null
  mchat_team_id: string | null
  agent_room_id: string
  agent_room_name: string | null
  sync_enabled: boolean
  created_at: string
}

export interface MchatUser {
  id: string
  mchat_user_id: string
  mchat_username: string | null
  agent_user_id: string
  agent_user_name: string | null
  agent_user_email: string | null
  created_at: string
}
