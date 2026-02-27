import { useState } from 'react'
import { Bot, Activity, Clock, ChevronDown, ChevronRight } from 'lucide-react'
import { Loading } from '@/components/common/Loading'
import { Button } from '@/components/ui'
import { useAgentDashboard, useAdminAgentApiLogs } from '../hooks/useAdmin'
import { cn } from '@/lib/utils'

export function AgentDashboardTab() {
  const { data: dashboard, isLoading: dashboardLoading } = useAgentDashboard()
  const { data: logsData } = useAdminAgentApiLogs({ limit: 20, offset: 0 })
  
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null)
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null)

  if (dashboardLoading) {
    return <div className="flex justify-center py-12"><Loading size="lg" /></div>
  }

  if (!dashboard) return null

  const cards = [
    { 
      label: '전체 인스턴스', 
      value: dashboard.total_instances || 0, 
      icon: Bot, 
      color: 'text-accent' 
    },
    { 
      label: '전체 데이터', 
      value: (dashboard.total_memories || 0) + (dashboard.total_messages || 0), 
      icon: Activity, 
      color: 'text-info' 
    },
    { 
      label: '활성 인스턴스', 
      value: dashboard.active_instances || 0, 
      icon: Activity, 
      color: 'text-success' 
    },
    { 
      label: '메모리 수', 
      value: dashboard.total_memories || 0, 
      icon: Bot, 
      color: 'text-warning' 
    },
  ]

  return (
    <div className="space-y-8">
      {/* Statistics Cards */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Agent 통계</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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

      {/* Agent Instances */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Agent 인스턴스 목록</h2>
        <div className="card">
          {dashboard.top_agents && dashboard.top_agents.length > 0 ? (
            <div className="divide-y divide-border">
              {dashboard.top_agents.map((agent) => (
                <div key={agent.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setExpandedAgent(expandedAgent === agent.id ? null : agent.id)}
                        className="p-1 hover:bg-background-hover rounded"
                      >
                        {expandedAgent === agent.id ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                      <Bot className="h-5 w-5 text-accent" />
                      <div>
                        <h3 className="font-medium">{agent.name}</h3>
                        <p className="text-sm text-foreground-secondary">
                          메모리: {agent.memory_count}개
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-sm text-foreground-secondary">
                        <Clock className="h-3 w-3" />
                        {agent.last_active ? new Date(agent.last_active).toLocaleString() : '활동 없음'}
                      </div>
                    </div>
                  </div>
                  
                  {expandedAgent === agent.id && (
                    <div className="mt-4 pl-8 border-l-2 border-border ml-2">
                      <div className="space-y-2">
                        <p className="text-sm"><strong>ID:</strong> {agent.id}</p>
                        <p className="text-sm"><strong>메모리 개수:</strong> {agent.memory_count}</p>
                        <p className="text-sm"><strong>마지막 활동:</strong> {agent.last_active ? new Date(agent.last_active).toLocaleString() : '없음'}</p>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => setSelectedInstance(selectedInstance === agent.id ? null : agent.id)}
                        >
                          {selectedInstance === agent.id ? 'API 로그 숨기기' : 'API 로그 보기'}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-foreground-secondary">
              <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>활성 Agent 인스턴스가 없습니다</p>
            </div>
          )}
        </div>
      </div>

      {/* API Logs */}
      <div>
        <h2 className="text-lg font-semibold mb-4">API 로그</h2>
        <div className="card">
          {logsData?.logs && logsData.logs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-3">시간</th>
                    <th className="text-left p-3">인스턴스</th>
                    <th className="text-left p-3">메서드</th>
                    <th className="text-left p-3">경로</th>
                    <th className="text-center p-3">상태</th>
                  </tr>
                </thead>
                <tbody>
                  {logsData.logs
                    .filter(log => !selectedInstance || log.agent_instance_id === selectedInstance)
                    .map((log, index) => (
                    <tr key={index} className="border-b border-border/50">
                      <td className="p-3 text-sm">
                        {new Date(log.created_at || log.timestamp).toLocaleString()}
                      </td>
                      <td className="p-3 text-sm font-mono">
                        {log.agent_instance_name || log.agent_instance_id?.substring(0, 8) || 'Unknown'}
                      </td>
                      <td className="p-3">
                        <span className={cn(
                          'px-2 py-1 rounded text-xs font-medium',
                          log.method === 'POST' ? 'bg-accent/10 text-accent' :
                          log.method === 'GET' ? 'bg-success/10 text-success' :
                          log.method === 'PUT' ? 'bg-warning/10 text-warning' :
                          log.method === 'DELETE' ? 'bg-error/10 text-error' :
                          'bg-background-secondary text-foreground-secondary'
                        )}>
                          {log.method || 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="p-3 text-sm font-mono">{log.path || log.endpoint}</td>
                      <td className="p-3 text-center">
                        <span className={cn(
                          'px-2 py-1 rounded text-xs font-medium',
                          (log.status_code || log.response_status) >= 200 && (log.status_code || log.response_status) < 300 
                            ? 'bg-success/10 text-success' :
                          (log.status_code || log.response_status) >= 400 
                            ? 'bg-error/10 text-error' :
                          'bg-background-secondary text-foreground-secondary'
                        )}>
                          {log.status_code || log.response_status || 'Unknown'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-foreground-secondary">
              <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>API 로그가 없습니다</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}