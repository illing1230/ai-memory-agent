import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, MessageSquare, Briefcase, Building2 } from 'lucide-react'
import { Button, Input } from '@/components/ui'
import { useCreateChatRoom } from '@/features/chat/hooks/useChat'
import { cn } from '@/lib/utils'

interface CreateRoomModalProps {
  open: boolean
  onClose: () => void
}

type RoomType = 'personal' | 'project' | 'department'

export function CreateRoomModal({ open, onClose }: CreateRoomModalProps) {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [roomType, setRoomType] = useState<RoomType>('personal')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const createRoom = useCreateChatRoom()

  if (!open) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || isSubmitting) return

    setIsSubmitting(true)
    try {
      const room = await createRoom.mutateAsync({ name: name.trim(), room_type: roomType })
      onClose()
      setName('')
      setRoomType('personal')
      navigate(`/chat/${room.id}`)
    } catch (error) {
      console.error('채팅방 생성 실패:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const roomTypes: { type: RoomType; label: string; icon: React.ElementType; desc: string }[] = [
    { type: 'personal', label: '개인', icon: MessageSquare, desc: '나만 사용하는 채팅방' },
    { type: 'project', label: '프로젝트', icon: Briefcase, desc: '프로젝트 팀원과 공유' },
    { type: 'department', label: '부서', icon: Building2, desc: '부서 전체와 공유' },
  ]

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40 animate-fade-in" onClick={onClose} />

      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div className="bg-background rounded-xl shadow-popup w-full max-w-md animate-scale-in" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between px-6 py-4 border-b border-border">
            <h2 className="text-lg font-semibold">새 채팅방 만들기</h2>
            <Button variant="ghost" size="icon-sm" onClick={onClose}><X className="h-4 w-4" /></Button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">채팅방 이름</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="예: 품질검사팀 회의" autoFocus />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">유형 선택</label>
              <div className="grid grid-cols-3 gap-2">
                {roomTypes.map(({ type, label, icon: Icon, desc }) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setRoomType(type)}
                    className={cn(
                      'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
                      'hover:border-accent hover:bg-accent-muted',
                      roomType === type ? 'border-accent bg-accent-muted' : 'border-border'
                    )}
                  >
                    <Icon className={cn('h-6 w-6', roomType === type ? 'text-accent' : 'text-foreground-secondary')} />
                    <span className={cn('text-sm font-medium', roomType === type ? 'text-accent' : 'text-foreground')}>{label}</span>
                    <span className="text-xs text-foreground-tertiary text-center">{desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="ghost" onClick={onClose}>취소</Button>
              <Button type="submit" disabled={!name.trim() || isSubmitting}>
                {isSubmitting ? '생성 중...' : '만들기'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
