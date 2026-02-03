import { useState } from 'react';
import { Bot, Plus, ExternalLink, Check, X, RefreshCw, Globe, Lock } from 'lucide-react';
import { Button, ScrollArea } from '@/components/ui';
import { Loading } from '@/components/common/Loading';
import { EmptyState } from '@/components/common/EmptyState';
import { agentApi, type AgentType } from '../api/agentApi';
import { formatDate } from '@/lib/utils';

export function AgentMarketplace() {
  const [agentTypes, setAgentTypes] = useState<AgentType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentType | null>(null);
  const [newInstanceName, setNewInstanceName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const loadAgentTypes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await agentApi.listAgentTypes({ status: 'active' });
      setAgentTypes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Agent Type을 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateInstance = async () => {
    if (!selectedAgent || !newInstanceName.trim()) return;

    try {
      setIsCreating(true);
      await agentApi.createAgentInstance({
        agent_type_id: selectedAgent.id,
        name: newInstanceName.trim(),
      });
      setSelectedAgent(null);
      setNewInstanceName('');
      alert('Agent Instance가 생성되었습니다. API Key를 확인하세요.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Agent Instance 생성 실패');
    } finally {
      setIsCreating(false);
    }
  };

  useState(() => {
    loadAgentTypes();
  });

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <Bot className="h-5 w-5 text-accent" />
              Agent Marketplace
            </h1>
            <p className="text-sm text-foreground-secondary mt-1">
              공개된 Agent Type을 탐색하고 내 Agent Instance를 생성하세요
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={loadAgentTypes}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
        </div>
      </header>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="px-6 py-4">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loading size="lg" />
            </div>
          ) : error ? (
            <EmptyState
              icon={Bot}
              title="Agent Type을 불러오는 중 오류가 발생했습니다"
              description={error}
              action={
                <Button variant="secondary" size="sm" onClick={loadAgentTypes}>
                  다시 시도
                </Button>
              }
            />
          ) : agentTypes.length === 0 ? (
            <EmptyState
              icon={Bot}
              title="공개된 Agent가가 없습니다"
              description="현재 사용 가능한 공개 Agent가가 없습니다"
            />
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-foreground-secondary">
                총 {agentTypes.length}개의 Agent Type
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {agentTypes.map((agentType) => (
                  <div
                    key={agentType.id}
                    className="card p-4 hover:shadow-medium transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="font-semibold text-foreground mb-1">
                          {agentType.name}
                        </h3>
                        <p className="text-xs text-foreground-secondary">
                          v{agentType.version}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs flex items-center gap-1 ${
                            agentType.public_scope === 'public'
                              ? 'bg-success/10 text-success'
                              : agentType.public_scope === 'project'
                              ? 'bg-info/10 text-info'
                              : agentType.public_scope === 'department'
                              ? 'bg-warning/10 text-warning'
                              : 'bg-foreground-muted/10 text-foreground-muted'
                          }`}
                        >
                          {agentType.public_scope === 'public' ? (
                            <>
                              <Globe className="h-3 w-3" />
                              전체
                            </>
                          ) : agentType.public_scope === 'project' ? (
                            <>
                              <Globe className="h-3 w-3" />
                              프로젝트
                            </>
                          ) : agentType.public_scope === 'department' ? (
                            <>
                              <Globe className="h-3 w-3" />
                              부서
                            </>
                          ) : (
                            <>
                              <Lock className="h-3 w-3" />
                              비공개
                            </>
                          )}
                        </span>
                        <span className="px-2 py-1 rounded-full text-xs bg-success/10 text-success">
                          Active
                        </span>
                      </div>
                    </div>

                    {agentType.description && (
                      <p className="text-sm text-foreground-secondary mb-3 line-clamp-2">
                        {agentType.description}
                      </p>
                    )}

                    {agentType.capabilities && agentType.capabilities.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {agentType.capabilities.slice(0, 3).map((capability) => (
                          <span
                            key={capability}
                            className="px-2 py-0.5 rounded text-xs bg-background-secondary text-foreground-tertiary"
                          >
                            {capability}
                          </span>
                        ))}
                        {agentType.capabilities.length > 3 && (
                          <span className="px-2 py-0.5 rounded text-xs bg-background-secondary text-foreground-tertiary">
                            +{agentType.capabilities.length - 3}
                          </span>
                        )}
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-3 border-t border-border">
                      <span className="text-xs text-foreground-tertiary">
                        {formatDate(agentType.created_at)}
                      </span>
                      <Button
                        size="sm"
                        onClick={() => setSelectedAgent(agentType)}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Instance 생성
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Create Instance Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Agent Instance 생성</h2>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => {
                  setSelectedAgent(null);
                  setNewInstanceName('');
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Agent Type
                </label>
                <div className="p-3 bg-background-secondary rounded-lg">
                  <p className="font-medium text-foreground">{selectedAgent.name}</p>
                  <p className="text-sm text-foreground-secondary">
                    {selectedAgent.description || '설명 없음'}
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Instance 이름 *
                </label>
                <input
                  type="text"
                  value={newInstanceName}
                  onChange={(e) => setNewInstanceName(e.target.value)}
                  placeholder="내 Agent Instance 이름"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={() => {
                    setSelectedAgent(null);
                    setNewInstanceName('');
                  }}
                >
                  취소
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleCreateInstance}
                  disabled={!newInstanceName.trim() || isCreating}
                >
                  {isCreating ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      생성 중...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      생성
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
