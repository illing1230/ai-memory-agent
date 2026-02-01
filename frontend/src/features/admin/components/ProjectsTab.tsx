import { Briefcase } from 'lucide-react'
import { Loading } from '@/components/common/Loading'
import { useAdminProjects } from '../hooks/useAdmin'
import { formatDate } from '@/lib/utils'

export function ProjectsTab() {
  const { data: projects, isLoading } = useAdminProjects()

  if (isLoading) {
    return <div className="flex justify-center py-12"><Loading size="lg" /></div>
  }

  if (!projects || projects.length === 0) {
    return <p className="text-foreground-secondary py-4">프로젝트가 없습니다.</p>
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-foreground-secondary mb-3">총 {projects.length}개</p>
      <div className="grid gap-3">
        {projects.map((project) => (
          <div key={project.id} className="card p-4 flex items-center gap-4">
            <div className="p-2 rounded-lg bg-background-secondary text-success">
              <Briefcase className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium">{project.name}</p>
              <div className="flex items-center gap-2 text-sm text-foreground-secondary">
                {project.description && <span className="truncate">{project.description}</span>}
                {project.department_name && (
                  <span className="px-1.5 py-0.5 rounded bg-background-secondary text-xs shrink-0">
                    {project.department_name}
                  </span>
                )}
              </div>
            </div>
            <div className="text-right shrink-0">
              <p className="text-lg font-bold">{project.member_count}</p>
              <p className="text-xs text-foreground-tertiary">멤버</p>
            </div>
            <div className="text-xs text-foreground-tertiary shrink-0">
              {project.created_at ? formatDate(project.created_at) : ''}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
