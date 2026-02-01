import { Trash2, Shield, ShieldOff } from 'lucide-react'
import { Button } from '@/components/ui'
import { Loading } from '@/components/common/Loading'
import { useAdminUsers, useUpdateUserRole, useDeleteAdminUser } from '../hooks/useAdmin'
import { useAuthStore } from '@/features/auth/store/authStore'
import { formatDate } from '@/lib/utils'

export function UsersTab() {
  const { data: users, isLoading } = useAdminUsers()
  const updateRole = useUpdateUserRole()
  const deleteUser = useDeleteAdminUser()
  const currentUser = useAuthStore((s) => s.user)

  if (isLoading) {
    return <div className="flex justify-center py-12"><Loading size="lg" /></div>
  }

  if (!users || users.length === 0) {
    return <p className="text-foreground-secondary py-4">사용자가 없습니다.</p>
  }

  const handleToggleRole = (userId: string, currentRole: string) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin'
    if (confirm(`역할을 '${newRole}'(으)로 변경하시겠습니까?`)) {
      updateRole.mutate({ userId, role: newRole })
    }
  }

  const handleDelete = (userId: string, userName: string) => {
    if (confirm(`"${userName}" 사용자를 삭제하시겠습니까?`)) {
      deleteUser.mutate(userId)
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-foreground-secondary mb-3">총 {users.length}명</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-foreground-secondary">
              <th className="py-2 px-3 font-medium">이름</th>
              <th className="py-2 px-3 font-medium">이메일</th>
              <th className="py-2 px-3 font-medium">역할</th>
              <th className="py-2 px-3 font-medium">부서</th>
              <th className="py-2 px-3 font-medium">가입일</th>
              <th className="py-2 px-3 font-medium">액션</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => {
              const isMe = user.id === currentUser?.id
              return (
                <tr key={user.id} className="border-b border-border/50 hover:bg-background-hover">
                  <td className="py-2 px-3">
                    {user.name}
                    {isMe && <span className="ml-1 text-xs text-accent">(나)</span>}
                  </td>
                  <td className="py-2 px-3 text-foreground-secondary">{user.email}</td>
                  <td className="py-2 px-3">
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                      user.role === 'admin' ? 'bg-accent/10 text-accent' : 'bg-background-secondary text-foreground-secondary'
                    }`}>
                      {user.role === 'admin' ? '관리자' : '일반'}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-foreground-secondary">{user.department_name || '-'}</td>
                  <td className="py-2 px-3 text-foreground-tertiary">
                    {user.created_at ? formatDate(user.created_at) : '-'}
                  </td>
                  <td className="py-2 px-3">
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title={user.role === 'admin' ? '일반으로 변경' : '관리자로 변경'}
                        onClick={() => handleToggleRole(user.id, user.role)}
                        disabled={isMe}
                      >
                        {user.role === 'admin' ? (
                          <ShieldOff className="h-4 w-4 text-warning" />
                        ) : (
                          <Shield className="h-4 w-4 text-accent" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-foreground-muted hover:text-error"
                        onClick={() => handleDelete(user.id, user.name)}
                        disabled={isMe}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
