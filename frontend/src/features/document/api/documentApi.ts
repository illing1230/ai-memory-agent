import { get, del, post } from '@/lib/api'
import type { Document, DocumentDetail, DocumentLink } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

export async function getDocuments(chatRoomId?: string): Promise<Document[]> {
  return get<Document[]>('/documents', chatRoomId ? { chat_room_id: chatRoomId } : undefined)
}

export async function getDocument(docId: string): Promise<DocumentDetail> {
  return get<DocumentDetail>(`/documents/${docId}`)
}

export async function uploadDocument(file: File, chatRoomId?: string): Promise<Document> {
  const formData = new FormData()
  formData.append('file', file)
  if (chatRoomId) {
    formData.append('chat_room_id', chatRoomId)
  }

  const token = localStorage.getItem('access_token')
  const userId = localStorage.getItem('user_id')

  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (userId) headers['X-User-ID'] = userId

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!response.ok) {
    let errorData: unknown
    try {
      errorData = await response.json()
    } catch {
      errorData = null
    }
    const message =
      errorData && typeof errorData === 'object' && 'detail' in errorData
        ? String((errorData as { detail: unknown }).detail)
        : `HTTP ${response.status}: ${response.statusText}`
    throw new Error(message)
  }

  return response.json()
}

export async function deleteDocument(docId: string): Promise<void> {
  return del(`/documents/${docId}`)
}

export async function linkDocumentToRoom(docId: string, roomId: string): Promise<DocumentLink> {
  return post<DocumentLink>(`/documents/${docId}/link/${roomId}`)
}

export async function unlinkDocumentFromRoom(docId: string, roomId: string): Promise<void> {
  return del(`/documents/${docId}/link/${roomId}`)
}

export interface DocumentSearchResult {
  content: string
  score: number
  document_name: string
  document_id: string
  chunk_index: number
  file_type: string
  slide_number?: number
  slide_image_url?: string
}

export async function searchDocuments(query: string, limit: number = 10): Promise<DocumentSearchResult[]> {
  return get<DocumentSearchResult[]>('/documents/search', { query, limit })
}

export function getSlideImageUrl(docId: string, slideNumber: number): string {
  return `${API_BASE_URL}/documents/${docId}/slides/${slideNumber}`
}
