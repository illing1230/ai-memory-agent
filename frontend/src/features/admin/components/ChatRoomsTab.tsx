import { MessageSquare, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui'
import { Loading } from '@/components/common/Loading'
import { useAdminChatRooms, useDeleteAdminChatRoom } from '../hooks/useAdmin'
import { formatDate } from '@/lib/utils'

const roomTypeLabel: Record<string, string> = {
  personal: '개인',
  project: '프로젝트',
  department: '부서',
}

export function ChatRoomsTab() {
  const { data: rooms, isLoading } = useAdminChatRooms()
  const deleteRoom = useDeleteAdminChatRoom()

  if (isLoading) {
    return <div className="flex justify-center py-12"><Loading size="lg" /></div>
  }

  if (!rooms || rooms.length === 0) {
    return <p className="text-foreground-secondary py-4">채팅방이 없습니다.</p>
  }

  const handleDelete = (roomId: string, roomName: string) => {
    if (confirm(`"${roomName}" 채팅방을 삭제하시겠습니까?`)) {
      deleteRoom.mutate(roomId)
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-foreground-secondary mb-3">총 {rooms.length}개</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-foreground-secondary">
              <th className="py-2 px-3 font-medium">이름</th>
              <th className="py-2 px-3 font-medium">유형</th>
              <th className="py-2 px-3 font-medium">소유자</th>
              <th className="py-2 px-3 font-medium">멤버</th>
              <th className="py-2 px-3 font-medium">메시지</th>
              <th className="py-2 px-3 font-medium">생성일</th>
              <th className="py-2 px-3 font-medium">액션</th>
            </tr>
          </thead>
          <tbody>
            {rooms.map((room) => (
              <tr key={room.id} className="border-b border-border/50 hover:bg-background-hover">
                <td className="py-2 px-3 flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-foreground-muted shrink-0" />
                  {room.name}
                </td>
                <td className="py-2 px-3">
                  <span className="px-1.5 py-0.5 rounded bg-background-secondary text-xs">
                    {roomTypeLabel[room.room_type] || room.room_type}
                  </span>
                </td>
                <td className="py-2 px-3 text-foreground-secondary">{room.owner_name || '-'}</td>
                <td className="py-2 px-3">{room.member_count}</td>
                <td className="py-2 px-3">{room.message_count}</td>
                <td className="py-2 px-3 text-foreground-tertiary">
                  {room.created_at ? formatDate(room.created_at) : '-'}
                </td>
                <td className="py-2 px-3">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    className="text-foreground-muted hover:text-error"
                    onClick={() => handleDelete(room.id, room.name)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
