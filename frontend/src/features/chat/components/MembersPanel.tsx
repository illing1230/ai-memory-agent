import { useState, useEffect } from 'react'
import { X, UserPlus, Crown, Star, User, Trash2, Loader2 } from 'lucide-react'
import { Button, Input, ScrollArea, Avatar } from '@/components/ui'
import { cn } from '@/lib/utils'
import { get, post, del } from '@/lib/api'

interface MembersPanelProps {
  roomId: string
  open: boolean
  onClose: () => void
}

interface Member {
  id: string
  user_id: string
  user_name?: string
  user_email?: string
  role: 'owner' | 'admin' | 'member'
  joined_at: string
}

interface User {
  id: string
  name: string
  email: string
}

export function MembersPanel({ roomId, open, onClose }: MembersPanelProps) {
  const [members, setMembers] = useState<Member[]>([])
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<'member' | 'admin'>('member')
  const [isInviting, setIsInviting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 멤버 목록 로드
  const loadMembers = async () => {
    try {
      const data = await get<Member[]>(`/chat-rooms/${roomId}/members`)
      setMembers(data)
    } catch (e) {
      console.error('멤버 목록 로드 실패:', e)
    }
  }

  // 전체 사용자 목록 로드
  const loadAllUsers = async () => {
    try {
      const data = await get<User[]>('/users')
      setAllUsers(data)
    } catch (e) {
      console.error('사용자 목록 로드 실패:', e)
    }
  }

  useEffect(() => {
    if (open && roomId) {
      setIsLoading(true)
      Promise.all([loadMembers(), loadAllUsers()]).finally(() => setIsLoading(false))
    }
  }, [open, roomId])

  // 초대 가능한 사용자 목록
  const availableUsers = allUsers.filter(
    user => !members.some(m => m.user_id === user.id)
  )

  // 이메일로 사용자 찾기
  const findUserByEmail = (email: string) => {
    return availableUsers.find(u => u.email.toLowerCase() === email.toLowerCase())
  }

  // 멤버 초대
  const handleInvite = async () => {
    if (!inviteEmail.trim()) return
    
    const user = findUserByEmail(inviteEmail)
    if (!user) {
      setError('해당 이메일의 사용자를 찾을 수 없습니다')
      return
    }

    setIsInviting(true)
    setError(null)

    try {
      await post(`/chat-rooms/${roomId}/members`, {
        user_id: user.id,
        role: inviteRole,
      })
      setInviteEmail('')
      await loadMembers()
    } catch (e: unknown) {
      const error = e as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || '초대에 실패했습니다')
    } finally {
      setIsInviting(false)
    }
  }

  // 멤버 제거
  const handleRemove = async (userId: string) => {
    if (!confirm('이 멤버를 제거하시겠습니까?')) return

    try {
      await del(`/chat-rooms/${roomId}/members/${userId}`)
      await loadMembers()
    } catch (e) {
      console.error('멤버 제거 실패:', e)
    }
  }

  if (!open) return null

  const roleIcon = {
    owner: <Crown className="h-4 w-4 text-warning" />,
    admin: <Star className="h-4 w-4 text-accent" />,
    member: <User className="h-4 w-4 text-foreground-tertiary" />,
  }

  const roleLabel = {
    owner: '소유자',
    admin: '관리자',
    member: '멤버',
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 animate-fade-in"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-80 bg-background border-l border-border shadow-lg z-50 animate-slide-up flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="font-semibold">멤버 관리</h2>
          <Button variant="ghost" size="icon-sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Invite Section */}
        <div className="p-4 border-b border-border space-y-3">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <UserPlus className="h-4 w-4" />
            멤버 초대
          </h3>
          
          <div className="space-y-2">
            <Input
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="이메일 입력..."
              list="available-users"
            />
            <datalist id="available-users">
              {availableUsers.map(u => (
                <option key={u.id} value={u.email}>
                  {u.name}
                </option>
              ))}
            </datalist>

            <div className="flex gap-2">
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as 'member' | 'admin')}
                className="flex-1 h-9 px-3 rounded-md border border-border bg-background text-sm"
              >
                <option value="member">멤버</option>
                <option value="admin">관리자</option>
              </select>
              <Button onClick={handleInvite} disabled={isInviting || !inviteEmail.trim()}>
                {isInviting ? <Loader2 className="h-4 w-4 animate-spin" /> : '초대'}
              </Button>
            </div>

            {error && (
              <p className="text-xs text-error">{error}</p>
            )}
          </div>
        </div>

        {/* Member List */}
        <div className="flex-1 overflow-hidden">
          <div className="px-4 py-2 border-b border-border">
            <span className="text-sm text-foreground-secondary">
              {members.length}명의 멤버
            </span>
          </div>

          <ScrollArea className="h-full">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-accent" />
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center gap-3 p-2 rounded-md hover:bg-background-hover group"
                  >
                    <Avatar
                      alt={member.user_name || 'User'}
                      fallback={member.user_name?.charAt(0) || 'U'}
                      size="sm"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">
                          {member.user_name || 'Unknown'}
                        </span>
                        {roleIcon[member.role]}
                      </div>
                      <span className="text-xs text-foreground-muted truncate block">
                        {member.user_email}
                      </span>
                    </div>
                    <span className="text-xs text-foreground-tertiary">
                      {roleLabel[member.role]}
                    </span>
                    {member.role !== 'owner' && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="opacity-0 group-hover:opacity-100 text-foreground-muted hover:text-error"
                        onClick={() => handleRemove(member.user_id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </div>
    </>
  )
}
