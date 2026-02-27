import { useState } from 'react'
import { Shield, LayoutDashboard, MessageSquare, Brain, BarChart3, Radio, Bot } from 'lucide-react'
import { Button, ScrollArea } from '@/components/ui'
import { cn } from '@/lib/utils'
import { DashboardTab } from './DashboardTab'
import { KnowledgeDashboardTab } from './KnowledgeDashboardTab'
import { ChatRoomsTab } from './ChatRoomsTab'
import { MemoriesTab } from './MemoriesTab'
import { MchatTab } from './MchatTab'
import { AgentDashboardTab } from './AgentDashboardTab'

type TabId = 'dashboard' | 'knowledge' | 'agent' | 'chatrooms' | 'memories' | 'mchat'

const tabs: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: 'dashboard', label: '대시보드', icon: LayoutDashboard },
  { id: 'knowledge', label: '지식 대시보드', icon: BarChart3 },
  { id: 'agent', label: 'Agent', icon: Bot },
  { id: 'chatrooms', label: '대화방', icon: MessageSquare },
  { id: 'memories', label: '메모리', icon: Brain },
  { id: 'mchat', label: 'Mchat', icon: Radio },
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
          {activeTab === 'knowledge' && <KnowledgeDashboardTab />}
          {activeTab === 'agent' && <AgentDashboardTab />}
          {activeTab === 'chatrooms' && <ChatRoomsTab />}
          {activeTab === 'memories' && <MemoriesTab />}
          {activeTab === 'mchat' && <MchatTab />}
        </div>
      </ScrollArea>
    </div>
  )
}
