import { useState } from 'react';
import { Bot, Key, Trash2, RefreshCw, Copy, Check, X, Edit2, Power, PowerOff } from 'lucide-react';
import { Button, ScrollArea } from '@/components/ui';
import { Loading } from '@/components/common/Loading';
import { EmptyState } from '@/components/common/EmptyState';
import { agentApi, type AgentInstance } from '../api/agentApi';
import { formatDate } from '@/lib/utils';

export function MyAgentInstances() {
  const [instances, setInstances] = useState<AgentInstance[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInstance, setSelectedInstance] = useState<AgentInstance | null>(null);
  const [editingInstance, setEditingInstance] = useState<AgentInstance | null>(null);
  const [editName, setEditName] = useState('');
  const [showApiKey, setShowApiKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const loadInstances = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await agentApi.listAgentInstances();
      setInstances(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Agent Instance를 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyApiKey = (apiKey: string) => {
    navigator.clipboard.writeText(apiKey);
    setCopiedKey(apiKey);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleRegenerateApiKey = async (instanceId: string) => {
    if (!confirm('API Key를 재발급하시겠습니까? 이전 API Key는 더 이상 사용할 수 없습니다.')) {
      return;
    }

    try {
      setIsRegenerating(true);
      const result = await agentApi.regenerateApiKey(instanceId);
      setInstances(instances.map(inst => 
        inst.id === instanceId ? { ...inst, api_key: result.api_key } : inst
      ));
      alert('API Key가 재발급되었습니다.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'API Key 재발급 실패');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleDeleteInstance = async (instanceId: string) => {
    if (!confirm('이 Agent Instance를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
      return;
    }

    try {
      setIsDeleting(true);
      await agentApi.deleteAgentInstance(instanceId);
      setInstances(instances.filter(inst => inst.id !== instanceId));
      setSelectedInstance(null);
      alert('Agent Instance가 삭제되었습니다.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Agent Instance 삭제 실패');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleUpdateInstance = async () => {
    if (!editingInstance || !editName.trim()) return;

    try {
      setIsUpdating(true);
      const updated = await agentApi.updateAgentInstance(editingInstance.id, {
        name: editName.trim(),
      });
      setInstances(instances.map(inst => 
        inst.id === editingInstance.id ? updated : inst
      ));
      setEditingInstance(null);
      setEditName('');
      alert('Agent Instance가 수정되었습니다.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Agent Instance 수정 실패');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleToggleStatus = async (instance: AgentInstance) => {
    const newStatus = instance.status === 'active' ? 'inactive' : 'active';
    const confirmMsg = newStatus === 'active' 
      ? '이 Agent Instance를 활성화하시겠습니까?'
      : '이 Agent Instance를 비활성화하시겠습니까?';
    
    if (!confirm(confirmMsg)) return;

    try {
      await agentApi.updateAgentInstance(instance.id, { status: newStatus });
      setInstances(instances.map(inst => 
        inst.id === instance.id ? { ...inst, status: newStatus } : inst
      ));
    } catch (err) {
      alert(err instanceof Error ? err.message : '상태 변경 실패');
    }
  };

  useState(() => {
    loadInstances();
  });

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <Bot className="h-5 w-5 text-accent" />
              내 Agent Instances
            </h1>
            <p className="text-sm text-foreground-secondary mt-1">
              내 Agent Instance를 관리하고 API Key를 확인하세요
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={loadInstances}
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
              title="Agent Instance를 불러오는 중 오류가 발생했습니다"
              description={error}
              action={
                <Button variant="secondary" size="sm" onClick={loadInstances}>
                  다시 시도
                </Button>
              }
            />
          ) : instances.length === 0 ? (
            <EmptyState
              icon={Bot}
              title="생성된 Agent Instance가 없습니다"
              description="Agent Marketplace에서 Agent Type을 선택하여 Instance를 생성하세요"
            />
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-foreground-secondary">
                총 {instances.length}개의 Agent Instance
              </p>

              <div className="space-y-3">
                {instances.map((instance) => (
                  <div
                    key={instance.id}
                    className="card p-4 hover:shadow-medium transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-foreground">
                            {instance.name}
                          </h3>
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs ${
                              instance.status === 'active'
                                ? 'bg-success/10 text-success'
                                : 'bg-foreground-muted/10 text-foreground-muted'
                            }`}
                          >
                            {instance.status === 'active' ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <p className="text-xs text-foreground-secondary">
                          ID: {instance.id}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleToggleStatus(instance)}
                          title={instance.status === 'active' ? '비활성화' : '활성화'}
                        >
                          {instance.status === 'active' ? (
                            <PowerOff className="h-4 w-4" />
                          ) : (
                            <Power className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => {
                            setEditingInstance(instance);
                            setEditName(instance.name);
                          }}
                          title="이름 수정"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => setSelectedInstance(instance)}
                          title="API Key 보기"
                        >
                          <Key className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleDeleteInstance(instance.id)}
                          title="삭제"
                          disabled={isDeleting}
                        >
                          <Trash2 className="h-4 w-4 text-error" />
                        </Button>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-border">
                      <span className="text-xs text-foreground-tertiary">
                        {formatDate(instance.created_at)}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedInstance(instance)}
                      >
                        <Key className="h-4 w-4 mr-1" />
                        API Key
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* API Key Modal */}
      {selectedInstance && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">API Key</h2>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => {
                  setSelectedInstance(null);
                  setShowApiKey(null);
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Instance
                </label>
                <p className="font-medium text-foreground">{selectedInstance.name}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  API Key
                </label>
                <div className="flex gap-2">
                  <input
                    type={showApiKey === selectedInstance.id ? 'text' : 'password'}
                    value={selectedInstance.api_key}
                    readOnly
                    className="flex-1 px-3 py-2 rounded-lg border border-border bg-background-secondary text-foreground font-mono text-sm"
                  />
                  <Button
                    variant="secondary"
                    size="icon-sm"
                    onClick={() => setShowApiKey(
                      showApiKey === selectedInstance.id ? null : selectedInstance.id
                    )}
                  >
                    {showApiKey === selectedInstance.id ? (
                      <X className="h-4 w-4" />
                    ) : (
                      <Check className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant="secondary"
                    size="icon-sm"
                    onClick={() => handleCopyApiKey(selectedInstance.api_key)}
                  >
                    {copiedKey === selectedInstance.api_key ? (
                      <Check className="h-4 w-4 text-success" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={() => {
                    setSelectedInstance(null);
                    setShowApiKey(null);
                  }}
                >
                  닫기
                </Button>
                <Button
                  className="flex-1"
                  onClick={() => handleRegenerateApiKey(selectedInstance.id)}
                  disabled={isRegenerating}
                >
                  {isRegenerating ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      재발급 중...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2" />
                      재발급
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Name Modal */}
      {editingInstance && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">이름 수정</h2>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => {
                  setEditingInstance(null);
                  setEditName('');
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Instance 이름 *
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="Agent Instance 이름"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={() => {
                    setEditingInstance(null);
                    setEditName('');
                  }}
                >
                  취소
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleUpdateInstance}
                  disabled={!editName.trim() || isUpdating}
                >
                  {isUpdating ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      저장 중...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      저장
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
