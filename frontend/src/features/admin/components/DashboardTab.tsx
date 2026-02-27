import { useState } from 'react'
import { Users, MessageSquare, Brain, Building2, Briefcase, MessagesSquare, Edit2, Trash2, Save, X } from 'lucide-react'
import { Loading } from '@/components/common/Loading'
import { Button, Input, Textarea, Select } from '@/components/ui'
import { 
  useDashboardStats, 
  useAdminDepartments, 
  useAdminProjects,
  useUpdateDepartment,
  useDeleteDepartment,
  useUpdateProject,
  useDeleteProject
} from '../hooks/useAdmin'

export function DashboardTab() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: departments = [], isLoading: deptLoading } = useAdminDepartments()
  const { data: projects = [], isLoading: projectsLoading } = useAdminProjects()
  
  const updateDepartmentMutation = useUpdateDepartment()
  const deleteDepartmentMutation = useDeleteDepartment()
  const updateProjectMutation = useUpdateProject()
  const deleteProjectMutation = useDeleteProject()

  const [editingDept, setEditingDept] = useState<string | null>(null)
  const [editingProject, setEditingProject] = useState<string | null>(null)
  const [deptForm, setDeptForm] = useState({ name: '', description: '' })
  const [projectForm, setProjectForm] = useState({ name: '', description: '', department_id: '' })

  if (statsLoading || deptLoading || projectsLoading) {
    return <div className="flex justify-center py-12"><Loading size="lg" /></div>
  }

  if (!stats) return null

  const cards = [
    { label: '사용자', value: stats.total_users, icon: Users, color: 'text-accent' },
    { label: '대화방', value: stats.total_chat_rooms, icon: MessageSquare, color: 'text-success' },
    { label: '메모리', value: stats.total_memories, icon: Brain, color: 'text-warning' },
    { label: '메시지', value: stats.total_messages, icon: MessagesSquare, color: 'text-info' },
    { label: '부서', value: stats.total_departments, icon: Building2, color: 'text-error' },
    { label: '프로젝트', value: stats.total_projects, icon: Briefcase, color: 'text-accent' },
  ]

  const handleEditDept = (dept: any) => {
    setEditingDept(dept.id)
    setDeptForm({ name: dept.name, description: dept.description || '' })
  }

  const handleSaveDept = async (deptId: string) => {
    try {
      await updateDepartmentMutation.mutateAsync({
        departmentId: deptId,
        data: deptForm
      })
      setEditingDept(null)
    } catch (error) {
      console.error('부서 수정 실패:', error)
    }
  }

  const handleDeleteDept = async (deptId: string) => {
    if (confirm('정말 이 부서를 삭제하시겠습니까? 소속 사용자들의 부서가 해제됩니다.')) {
      try {
        await deleteDepartmentMutation.mutateAsync(deptId)
      } catch (error) {
        console.error('부서 삭제 실패:', error)
      }
    }
  }

  const handleEditProject = (project: any) => {
    setEditingProject(project.id)
    setProjectForm({ 
      name: project.name, 
      description: project.description || '', 
      department_id: project.department_id || '' 
    })
  }

  const handleSaveProject = async (projectId: string) => {
    try {
      await updateProjectMutation.mutateAsync({
        projectId: projectId,
        data: projectForm
      })
      setEditingProject(null)
    } catch (error) {
      console.error('프로젝트 수정 실패:', error)
    }
  }

  const handleDeleteProject = async (projectId: string) => {
    if (confirm('정말 이 프로젝트를 삭제하시겠습니까? 모든 프로젝트 멤버가 제거됩니다.')) {
      try {
        await deleteProjectMutation.mutateAsync(projectId)
      } catch (error) {
        console.error('프로젝트 삭제 실패:', error)
      }
    }
  }

  return (
    <div className="space-y-8">
      {/* Statistics Cards */}
      <div>
        <h2 className="text-lg font-semibold mb-4">시스템 현황</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {cards.map((card) => (
            <div key={card.label} className="card p-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg bg-background-secondary ${card.color}`}>
                  <card.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{card.value}</p>
                  <p className="text-sm text-foreground-secondary">{card.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Departments Section */}
      <div>
        <h2 className="text-lg font-semibold mb-4">부서 관리</h2>
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3">부서명</th>
                  <th className="text-left p-3">설명</th>
                  <th className="text-center p-3">멤버 수</th>
                  <th className="text-center p-3">액션</th>
                </tr>
              </thead>
              <tbody>
                {departments.map((dept) => (
                  <tr key={dept.id} className="border-b border-border/50">
                    <td className="p-3">
                      {editingDept === dept.id ? (
                        <Input
                          value={deptForm.name}
                          onChange={(e) => setDeptForm(prev => ({ ...prev, name: e.target.value }))}
                          className="max-w-40"
                        />
                      ) : (
                        <span className="font-medium">{dept.name}</span>
                      )}
                    </td>
                    <td className="p-3">
                      {editingDept === dept.id ? (
                        <Textarea
                          value={deptForm.description}
                          onChange={(e) => setDeptForm(prev => ({ ...prev, description: e.target.value }))}
                          className="max-w-60"
                          rows={2}
                        />
                      ) : (
                        <span className="text-foreground-secondary">{dept.description || '설명 없음'}</span>
                      )}
                    </td>
                    <td className="p-3 text-center">{dept.member_count}</td>
                    <td className="p-3">
                      <div className="flex justify-center gap-1">
                        {editingDept === dept.id ? (
                          <>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              onClick={() => handleSaveDept(dept.id)}
                              disabled={updateDepartmentMutation.isPending}
                            >
                              <Save className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              onClick={() => setEditingDept(null)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              onClick={() => handleEditDept(dept)}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              onClick={() => handleDeleteDept(dept.id)}
                              disabled={deleteDepartmentMutation.isPending}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Projects Section */}
      <div>
        <h2 className="text-lg font-semibold mb-4">프로젝트 관리</h2>
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3">프로젝트명</th>
                  <th className="text-left p-3">설명</th>
                  <th className="text-left p-3">부서</th>
                  <th className="text-center p-3">멤버 수</th>
                  <th className="text-center p-3">액션</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project) => (
                  <tr key={project.id} className="border-b border-border/50">
                    <td className="p-3">
                      {editingProject === project.id ? (
                        <Input
                          value={projectForm.name}
                          onChange={(e) => setProjectForm(prev => ({ ...prev, name: e.target.value }))}
                          className="max-w-40"
                        />
                      ) : (
                        <span className="font-medium">{project.name}</span>
                      )}
                    </td>
                    <td className="p-3">
                      {editingProject === project.id ? (
                        <Textarea
                          value={projectForm.description}
                          onChange={(e) => setProjectForm(prev => ({ ...prev, description: e.target.value }))}
                          className="max-w-60"
                          rows={2}
                        />
                      ) : (
                        <span className="text-foreground-secondary">{project.description || '설명 없음'}</span>
                      )}
                    </td>
                    <td className="p-3">
                      {editingProject === project.id ? (
                        <Select
                          value={projectForm.department_id}
                          onValueChange={(value) => setProjectForm(prev => ({ ...prev, department_id: value }))}
                        >
                          <option value="">부서 없음</option>
                          {departments.map((dept) => (
                            <option key={dept.id} value={dept.id}>{dept.name}</option>
                          ))}
                        </Select>
                      ) : (
                        <span className="text-foreground-secondary">{project.department_name || '부서 없음'}</span>
                      )}
                    </td>
                    <td className="p-3 text-center">{project.member_count}</td>
                    <td className="p-3">
                      <div className="flex justify-center gap-1">
                        {editingProject === project.id ? (
                          <>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              onClick={() => handleSaveProject(project.id)}
                              disabled={updateProjectMutation.isPending}
                            >
                              <Save className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              onClick={() => setEditingProject(null)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              onClick={() => handleEditProject(project)}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              onClick={() => handleDeleteProject(project.id)}
                              disabled={deleteProjectMutation.isPending}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
