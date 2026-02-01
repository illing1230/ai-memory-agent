import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getDocuments,
  getDocument,
  uploadDocument,
  deleteDocument,
  linkDocumentToRoom,
  unlinkDocumentFromRoom,
} from '../api/documentApi'

const documentKeys = {
  all: ['documents'] as const,
  list: (chatRoomId?: string) => [...documentKeys.all, 'list', chatRoomId] as const,
  detail: (docId: string) => [...documentKeys.all, 'detail', docId] as const,
}

export function useDocuments(chatRoomId?: string) {
  return useQuery({
    queryKey: documentKeys.list(chatRoomId),
    queryFn: () => getDocuments(chatRoomId),
  })
}

export function useDocument(docId: string) {
  return useQuery({
    queryKey: documentKeys.detail(docId),
    queryFn: () => getDocument(docId),
    enabled: !!docId,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, chatRoomId }: { file: File; chatRoomId?: string }) =>
      uploadDocument(file, chatRoomId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (docId: string) => deleteDocument(docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })
}

export function useLinkDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, roomId }: { docId: string; roomId: string }) =>
      linkDocumentToRoom(docId, roomId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })
}

export function useUnlinkDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ docId, roomId }: { docId: string; roomId: string }) =>
      unlinkDocumentFromRoom(docId, roomId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })
}
