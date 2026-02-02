import { get } from '@/lib/api'
import type { Project } from '@/types'

export async function getProjects(): Promise<Project[]> {
  return get<Project[]>('/projects')
}

export async function getProject(projectId: string): Promise<Project> {
  return get<Project>(`/projects/${projectId}`)
}

export async function getUserProjects(userId: string): Promise<Project[]> {
  return get<Project[]>(`/users/${userId}/projects`)
}
