/**
 * Galaxy TypeScript 类型定义
 * =========================
 * 
 * 前后端共享的类型定义
 */

// ============================================================================
// 系统类型
// ============================================================================

export interface SystemInfo {
  name: string;
  version: string;
  description: string;
  ascii: string;
  features: SystemFeatures;
  nodes: number;
  code_lines: number;
  timestamp: string;
}

export interface SystemFeatures {
  ai_driven: boolean;
  multi_device: boolean;
  autonomous_learning: boolean;
  visual_understanding: boolean;
  self_programming: boolean;
  digital_twin: boolean;
}

// ============================================================================
// 设备类型
// ============================================================================

export type DevicePlatform = 'android' | 'windows' | 'macos' | 'linux' | 'ios' | 'tablet';

export type DeviceStatus = 'online' | 'offline' | 'busy' | 'idle' | 'error';

export interface Device {
  device_id: string;
  platform: DevicePlatform;
  name: string;
  status: DeviceStatus;
  capabilities: string[];
  registered_at: string;
}

export interface DeviceRegisterRequest {
  device_id: string;
  device_type: DevicePlatform;
  device_name: string;
}

// ============================================================================
// Agent 类型
// ============================================================================

export type TaskComplexity = 'low' | 'medium' | 'high' | 'critical';

export type AgentState = 'created' | 'running' | 'completed' | 'failed';

export interface Agent {
  agent_id: string;
  name: string;
  task: string;
  task_type: string;
  state: AgentState;
  complexity: TaskComplexity;
  llm_provider: string;
  device_id: string;
  target_device_id: string;
}

// ============================================================================
// LLM 类型
// ============================================================================

export interface LLMProvider {
  provider: string;
  model: string;
  speed_score: number;
  quality_score: number;
  available: boolean;
}

// ============================================================================
// 孪生模型类型
// ============================================================================

export type CouplingMode = 'tight' | 'loose' | 'decoupled';

export interface AgentTwin {
  twin_id: string;
  agent_id: string;
  coupling_mode: CouplingMode;
  snapshot: Record<string, any>;
  behavior_history: BehaviorRecord[];
}

export interface BehaviorRecord {
  timestamp: string;
  update: Record<string, any>;
}

// ============================================================================
// 聊天类型
// ============================================================================

export interface ChatRequest {
  message: string;
  device_id?: string;
}

export interface ChatResponse {
  response: string;
  agent?: {
    id: string;
    llm: string;
  };
  executed?: boolean;
  timestamp: string;
}

// ============================================================================
// WebSocket 类型
// ============================================================================

export interface WSMessage {
  type: 'ping' | 'pong' | 'chat' | 'chat_response' | 'status_update';
  content?: string;
  data?: any;
}

// ============================================================================
// API 响应类型
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// ============================================================================
// 多设备操作类型
// ============================================================================

export interface DeviceCommand {
  device_id: string;
  action: DeviceAction;
  params: Record<string, any>;
}

export type DeviceAction = 
  | 'click'
  | 'input'
  | 'scroll'
  | 'screenshot'
  | 'open_app'
  | 'press_key';

export interface ParallelExecuteRequest {
  commands: DeviceCommand[];
}

export interface ParallelExecuteResponse {
  success: boolean;
  results: Record<string, any>;
}
