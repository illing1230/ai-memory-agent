import { useState } from 'react';
import { Bot, Plus, Trash2, RefreshCw, Edit2, X, Check, Globe, Lock } from 'lucide-react';
import { Button, ScrollArea } from '@/components/ui';
import { Loading } from '@/components/common/Loading';
import { EmptyState } from '@/components/common/EmptyState';
import { agentApi, type AgentType } from '../api/agentApi';
import { formatDate } from '@/lib/utils';

export function AgentTypeManagement() {
  const [agentTypes, setAgentTypes] = useState<AgentType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editingType, setEditingType] = useState<AgentType | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    version: '1.0.0',
    capabilities: '',
    public_scope: 'private' as 'private' | 'project' | 'department' | 'public',
  });

  const loadAgentTypes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        setError('로그인이 필요합니다.');
        return;
      }
      const data = await agentApi.listAgentTypes({ developer_id: userId });
      setAgentTypes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Agent Type을 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      alert('이름을 입력해주세요.');
      return;
    }

    // 인증 확인
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      alert('로그인이 필요합니다.');
      return;
    }

    try {
      setIsCreating(true);
      await agentApi.createAgentType({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        version: formData.version,
        capabilities: formData.capabilities
          .split(',')
          .map(c => c.trim())
          .filter(c => c),
        public_scope: formData.public_scope,
      });
      setFormData({
        name: '',
        description: '',
        version: '1.0.0',
        capabilities: '',
        public_scope: 'private',
      });
      setIsCreating(false);
      await loadAgentTypes();
      alert('Agent가 생성되었습니다.');
    } catch (err) {
      setIsCreating(false);
      alert(err instanceof Error ? err.message : 'Agent Type 생성 실패');
    }
  };

  const handleUpdate = async () => {
    if (!editingType || !formData.name.trim()) return;

    try {
      await agentApi.updateAgentType(editingType.id, {
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        version: formData.version,
        capabilities: formData.capabilities
          .split(',')
          .map(c => c.trim())
          .filter(c => c),
        public_scope: formData.public_scope,
      });
      setEditingType(null);
      setFormData({
        name: '',
        description: '',
        version: '1.0.0',
        capabilities: '',
        public_scope: 'private',
      });
      await loadAgentTypes();
      alert('Agent가 수정되었습니다.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Agent Type 수정 실패');
    }
  };

  const handleDelete = async (agentTypeId: string) => {
    if (!confirm('이 Agent Type을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
      return;
    }

    try {
      await agentApi.deleteAgentType(agentTypeId);
      await loadAgentTypes();
      alert('Agent 삭제되었습니다.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Agent Type 삭제 실패');
    }
  };

  const openCreateForm = () => {
    setEditingType(null);
    setFormData({
      name: '',
      description: '',
      version: '1.0.0',
      capabilities: '',
      public_scope: 'private',
    });
    setIsCreating(true);
  };

  const openEditForm = (agentType: AgentType) => {
    setEditingType(agentType);
    setFormData({
      name: agentType.name,
      description: agentType.description || '',
      version: agentType.version,
      capabilities: agentType.capabilities?.join(', ') || '',
      public_scope: agentType.public_scope,
    });
    setIsCreating(true);
  };

  const closeForm = () => {
    setIsCreating(false);
    setEditingType(null);
    setFormData({
      name: '',
      description: '',
      version: '1.0.0',
      capabilities: '',
      public_scope: 'private',
    });
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
              Agent 등록
            </h1>
            <p className="text-sm text-foreground-secondary mt-1">
              내 Agent Type을 생성하고 관리하세요
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={loadAgentTypes}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
            <Button size="sm" onClick={openCreateForm}>
              <Plus className="h-4 w-4 mr-1" />
              Agent 등록
            </Button>
          </div>
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
              title="생성된 Agent가 없습니다"
              description="새로운 Agent Type을 생성하여 시작하세요"
              action={
                <Button size="sm" onClick={openCreateForm}>
                  <Plus className="h-4 w-4 mr-1" />
                  Agent 등록
                </Button>
              }
            />
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-foreground-secondary">
                총 {agentTypes.length}개의 Agent Type
              </p>

              <div className="space-y-3">
                {agentTypes.map((agentType) => (
                  <div
                    key={agentType.id}
                    className="card p-4 hover:shadow-medium transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-foreground">
                            {agentType.name}
                          </h3>
                          <span className="text-xs text-foreground-secondary">
                            v{agentType.version}
                          </span>
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
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs ${
                              agentType.status === 'active'
                                ? 'bg-success/10 text-success'
                                : 'bg-foreground-muted/10 text-foreground-muted'
                            }`}
                          >
                            {agentType.status}
                          </span>
                        </div>
                        <p className="text-xs text-foreground-secondary">
                          ID: {agentType.id}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => openEditForm(agentType)}
                          title="수정"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleDelete(agentType.id)}
                          title="삭제"
                        >
                          <Trash2 className="h-4 w-4 text-error" />
                        </Button>
                      </div>
                    </div>

                    {agentType.description && (
                      <p className="text-sm text-foreground-secondary mb-3">
                        {agentType.description}
                      </p>
                    )}

                    {agentType.capabilities && agentType.capabilities.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {agentType.capabilities.map((capability) => (
                          <span
                            key={capability}
                            className="px-2 py-0.5 rounded text-xs bg-background-secondary text-foreground-tertiary"
                          >
                            {capability}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-3 border-t border-border">
                      <span className="text-xs text-foreground-tertiary">
                        {formatDate(agentType.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Create/Edit Modal */}
      {isCreating && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">
                {editingType ? 'Agent registration' : 'Agent registration'}
              </h2>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={closeForm}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  이름 *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Agent Type 이름"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  설명
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Agent Type 설명"
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-accent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  버전
                </label>
                <input
                  type="text"
                  value={formData.version}
                  onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                  placeholder="1.0.0"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  기능 (쉼표로 구분)
                </label>
                <input
                  type="text"
                  value={formData.capabilities}
                  onChange={(e) => setFormData({ ...formData, capabilities: e.target.value })}
                  placeholder="memory, message, log"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  공개 범위
                </label>
                <select
                  value={formData.public_scope}
                  onChange={(e) => setFormData({ ...formData, public_scope: e.target.value as 'private' | 'project' | 'department' | 'public' })}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="private">비공개</option>
                  <option value="project">프로젝트</option>
                  <option value="department">부서</option>
                  <option value="public">전체</option>
                </select>
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={closeForm}
                >
                  취소
                </Button>
                <Button
                  className="flex-1"
                  onClick={editingType ? handleUpdate : handleCreate}
                  disabled={!formData.name.trim()}
                >
                  {editingType ? (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      수정
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4 mr-2" />
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
