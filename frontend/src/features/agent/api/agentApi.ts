import { get, post, put, del } from '@/lib/api';

// Agent Type 타입
export interface AgentType {
  id: string;
  name: string;
  description: string | null;
  version: string;
  config_schema: Record<string, any> | null;
  capabilities: string[] | null;
  public_scope: 'private' | 'project' | 'department' | 'public';
  project_id: string | null;
  status: 'active' | 'deprecated';
  developer_id: string;
  created_at: string;
  updated_at: string;
}

// Agent Instance 타입
export interface AgentInstance {
  id: string;
  agent_type_id: string;
  name: string;
  config: Record<string, any> | null;
  webhook_url: string | null;
  api_key: string;
  owner_id: string;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

// Agent Data 타입
export interface AgentData {
  id: string;
  agent_instance_id: string;
  data_type: 'memory' | 'message' | 'log';
  content: string;
  internal_user_id: string;
  external_user_id: string | null;
  metadata: Record<string, any> | null;
  created_at: string;
}

// External User Mapping 타입
export interface ExternalUserMapping {
  id: string;
  agent_instance_id: string;
  external_user_id: string;
  internal_user_id: string;
  external_system_name: string | null;
  created_at: string;
}

// Agent Instance Share 타입
export interface AgentInstanceShare {
  id: string;
  agent_instance_id: string;
  shared_with_user_id: string | null;
  shared_with_project_id: string | null;
  shared_with_department_id: string | null;
  role: 'viewer' | 'member';
  created_at: string;
}

// Agent Type 생성 DTO
export interface CreateAgentTypeDTO {
  name: string;
  description?: string;
  version?: string;
  config_schema?: Record<string, any>;
  capabilities?: string[];
  public_scope?: 'private' | 'project' | 'department' | 'public';
  project_id?: string;
}

// Agent Type 수정 DTO
export interface UpdateAgentTypeDTO {
  name?: string;
  description?: string;
  version?: string;
  config_schema?: Record<string, any>;
  capabilities?: string[];
  public_scope?: 'private' | 'project' | 'department' | 'public';
  project_id?: string;
  status?: 'active' | 'deprecated';
}

// Agent Instance 생성 DTO
export interface CreateAgentInstanceDTO {
  agent_type_id: string;
  name: string;
  config?: Record<string, any>;
  webhook_url?: string;
}

// Agent Instance 수정 DTO
export interface UpdateAgentInstanceDTO {
  name?: string;
  config?: Record<string, any>;
  webhook_url?: string;
  status?: 'active' | 'inactive';
}

// External User Mapping 생성 DTO
export interface CreateExternalUserMappingDTO {
  external_user_id: string;
  internal_user_id: string;
  external_system_name?: string;
}

// Agent Instance Share 생성 DTO
export interface CreateAgentInstanceShareDTO {
  shared_with_user_id?: string;
  shared_with_project_id?: string;
  shared_with_department_id?: string;
  role?: 'viewer' | 'member';
}

// ==================== Agent Type ====================

export const agentApi = {
  // Agent Type 목록 조회
  listAgentTypes: async (params?: {
    developer_id?: string;
    is_public?: boolean;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<AgentType[]> => {
    return get<AgentType[]>('/agent-types', params);
  },

  // Agent Type 조회
  getAgentType: async (agentTypeId: string): Promise<AgentType> => {
    return get<AgentType>(`/agent-types/${agentTypeId}`);
  },

  // Agent Type 생성
  createAgentType: async (data: CreateAgentTypeDTO): Promise<AgentType> => {
    return post<AgentType>('/agent-types', data);
  },

  // Agent Type 수정
  updateAgentType: async (
    agentTypeId: string,
    data: UpdateAgentTypeDTO
  ): Promise<AgentType> => {
    return put<AgentType>(`/agent-types/${agentTypeId}`, data);
  },

  // Agent Type 삭제
  deleteAgentType: async (agentTypeId: string): Promise<void> => {
    return del(`/agent-types/${agentTypeId}`);
  },

  // ==================== Agent Instance ====================

  // Agent Instance 목록 조회
  listAgentInstances: async (params?: {
    agent_type_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<AgentInstance[]> => {
    return get<AgentInstance[]>('/agent-instances', params);
  },

  // Agent Instance 조회
  getAgentInstance: async (instanceId: string): Promise<AgentInstance> => {
    return get<AgentInstance>(`/agent-instances/${instanceId}`);
  },

  // Agent Instance 생성
  createAgentInstance: async (data: CreateAgentInstanceDTO): Promise<AgentInstance> => {
    return post<AgentInstance>('/agent-instances', data);
  },

  // Agent Instance 수정
  updateAgentInstance: async (
    instanceId: string,
    data: UpdateAgentInstanceDTO
  ): Promise<AgentInstance> => {
    return put<AgentInstance>(`/agent-instances/${instanceId}`, data);
  },

  // API Key 재발급
  regenerateApiKey: async (instanceId: string): Promise<{ api_key: string }> => {
    return post<{ api_key: string }>(`/agent-instances/${instanceId}/regenerate-api-key`);
  },

  // Agent Instance 삭제
  deleteAgentInstance: async (instanceId: string): Promise<void> => {
    return del(`/agent-instances/${instanceId}`);
  },

  // ==================== Agent Data ====================

  // Agent 데이터 목록 조회
  listAgentData: async (
    instanceId: string,
    params?: {
      internal_user_id?: string;
      data_type?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<AgentData[]> => {
    return get<AgentData[]>(`/agent-instances/${instanceId}/data`, params);
  },

  // ==================== External User Mapping ====================

  // 외부 사용자 매핑 목록 조회
  listExternalUserMappings: async (
    instanceId: string,
    params?: {
      limit?: number;
      offset?: number;
    }
  ): Promise<ExternalUserMapping[]> => {
    return get<ExternalUserMapping[]>(`/agent-instances/${instanceId}/user-mappings`, params);
  },

  // 외부 사용자 매핑 생성
  createExternalUserMapping: async (
    instanceId: string,
    data: CreateExternalUserMappingDTO
  ): Promise<ExternalUserMapping> => {
    return post<ExternalUserMapping>(`/agent-instances/${instanceId}/user-mappings`, data);
  },

  // 외부 사용자 매핑 삭제
  deleteExternalUserMapping: async (mappingId: string): Promise<void> => {
    return del(`/agent-instances/user-mappings/${mappingId}`);
  },

  // ==================== Agent Instance Share ====================

  // Agent Instance 공유 목록 조회
  listAgentInstanceShares: async (
    instanceId: string,
    params?: {
      limit?: number;
      offset?: number;
    }
  ): Promise<AgentInstanceShare[]> => {
    return get<AgentInstanceShare[]>(`/agent-instances/${instanceId}/shares`, params);
  },

  // Agent Instance 공유 생성
  createAgentInstanceShare: async (
    instanceId: string,
    data: CreateAgentInstanceShareDTO
  ): Promise<AgentInstanceShare> => {
    return post<AgentInstanceShare>(`/agent-instances/${instanceId}/shares`, data);
  },

  // Agent Instance 공유 삭제
  deleteAgentInstanceShare: async (shareId: string): Promise<void> => {
    return del(`/agent-instances/shares/${shareId}`);
  },
};
