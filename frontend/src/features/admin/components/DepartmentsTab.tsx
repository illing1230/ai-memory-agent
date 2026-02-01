import { Building2 } from 'lucide-react'
import { Loading } from '@/components/common/Loading'
import { useAdminDepartments } from '../hooks/useAdmin'
import { formatDate } from '@/lib/utils'

export function DepartmentsTab() {
  const { data: departments, isLoading } = useAdminDepartments()

  if (isLoading) {
    return <div className="flex justify-center py-12"><Loading size="lg" /></div>
  }

  if (!departments || departments.length === 0) {
    return <p className="text-foreground-secondary py-4">부서가 없습니다.</p>
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-foreground-secondary mb-3">총 {departments.length}개</p>
      <div className="grid gap-3">
        {departments.map((dept) => (
          <div key={dept.id} className="card p-4 flex items-center gap-4">
            <div className="p-2 rounded-lg bg-background-secondary text-accent">
              <Building2 className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium">{dept.name}</p>
              {dept.description && (
                <p className="text-sm text-foreground-secondary truncate">{dept.description}</p>
              )}
            </div>
            <div className="text-right shrink-0">
              <p className="text-lg font-bold">{dept.member_count}</p>
              <p className="text-xs text-foreground-tertiary">멤버</p>
            </div>
            <div className="text-xs text-foreground-tertiary shrink-0">
              {dept.created_at ? formatDate(dept.created_at) : ''}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
