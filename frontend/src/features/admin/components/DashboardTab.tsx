import { Users, MessageSquare, Brain, Building2, Briefcase, MessagesSquare } from 'lucide-react'
import { Loading } from '@/components/common/Loading'
import { useDashboardStats } from '../hooks/useAdmin'

export function DashboardTab() {
  const { data: stats, isLoading } = useDashboardStats()

  if (isLoading) {
    return <div className="flex justify-center py-12"><Loading size="lg" /></div>
  }

  if (!stats) return null

  const cards = [
    { label: '사용자', value: stats.total_users, icon: Users, color: 'text-accent' },
    { label: '채팅방', value: stats.total_chat_rooms, icon: MessageSquare, color: 'text-success' },
    { label: '메모리', value: stats.total_memories, icon: Brain, color: 'text-warning' },
    { label: '메시지', value: stats.total_messages, icon: MessagesSquare, color: 'text-info' },
    { label: '부서', value: stats.total_departments, icon: Building2, color: 'text-error' },
    { label: '프로젝트', value: stats.total_projects, icon: Briefcase, color: 'text-accent' },
  ]

  return (
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
  )
}
