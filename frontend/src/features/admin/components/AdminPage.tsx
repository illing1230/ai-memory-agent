import { useState } from 'react'
import { Shield, LayoutDashboard, Users, Building2, Briefcase, MessageSquare, Brain } from 'lucide-react'
import { Button, ScrollArea } from '@/components/ui'
import { cn } from '@/lib/utils'
import { DashboardTab } from './DashboardTab'
import { UsersTab } from './UsersTab'
import { DepartmentsTab } from './DepartmentsTab'
import { ProjectsTab } from './ProjectsTab'
import { ChatRoomsTab } from './ChatRoomsTab'
import { MemoriesTab } from './MemoriesTab'

type TabId = 'dashboard' | 'users' | 'departments' | 'projects' | 'chatrooms' | 'memories'

const tabs: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: 'dashboard', label: '대시보드', icon: LayoutDashboard },
  { id: 'users', label: '사용자', icon: Users },
  { id: 'departments', label: '부서', icon: Building2 },
  { id: 'projects', label: '프로젝트', icon: Briefcase },
  { id: 'chatrooms', label: '대화방', icon: MessageSquare },
  { id: 'memories', label: '메모리', icon: Brain },
]

export function AdminPage() {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard')

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <h1 className="text-xl font-semibold flex items-center gap-2">
          <Shield className="h-5 w-5 text-accent" />
          관리자 페이지
        </h1>
        <p className="text-sm text-foreground-secondary mt-1">
          시스템 전체를 관리하고 모니터링합니다
        </p>
      </header>

      {/* Tab Navigation */}
      <div className="border-b border-border px-6">
        <div className="flex gap-1 -mb-px overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
                activeTab === tab.id
                  ? 'border-accent text-accent'
                  : 'border-transparent text-foreground-secondary hover:text-foreground hover:border-border'
              )}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <ScrollArea className="flex-1">
        <div className="px-6 py-4">
          {activeTab === 'dashboard' && <DashboardTab />}
          {activeTab === 'users' && <UsersTab />}
          {activeTab === 'departments' && <DepartmentsTab />}
          {activeTab === 'projects' && <ProjectsTab />}
          {activeTab === 'chatrooms' && <ChatRoomsTab />}
          {activeTab === 'memories' && <MemoriesTab />}
        </div>
      </ScrollArea>
    </div>
  )
}
