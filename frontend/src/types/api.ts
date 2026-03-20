export type AttackType =
  | 'prompt_injection'
  | 'jailbreak'
  | 'gcg'
  | 'auto_dan'
  | 'deep_inception'
  | 'many_shot'
  | 'role_play'
  | 'encoding_attack'
  | 'goat'
  | 'crescendo'
  | 'tap'
  | 'pair'
  | 'rag_attack'
  | 'code_attack';

export type DefenseType =
  | 'input_filter'
  | 'output_filter'
  | 'system_prompt_hardening'
  | 'adversarial_training'
  | 'perplexity_filter'
  | 'keyword_detection';

export type AttackResult = 'success' | 'failure' | 'partial' | 'error';

export interface AttackPayload {
  attack_type: AttackType;
  prompt: string;
  target_behavior: string;
  metadata?: Record<string, unknown>;
}

export interface AttackOutcome {
  result: AttackResult;
  original_prompt: string;
  adversarial_prompt: string;
  model_response: string;
  iterations: number;
  success_score: number;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface DefenseResult {
  is_malicious: boolean;
  confidence: number;
  detected_patterns: string[];
  sanitized_input?: string;
  metadata?: Record<string, unknown>;
}

export interface AttackRequest {
  prompt: string;
  target_behavior: string;
  attack_type: AttackType;
  model: string;
  max_iterations?: number;
}

export interface DefenseRequest {
  input_text: string;
  defense_types?: DefenseType[];
}

export interface ScanRequest {
  text: string;
  scan_type: 'input' | 'output';
}

export interface BenchmarkRequest {
  dataset: string;
  attack_type: AttackType;
  model: string;
  max_cases: number;
}

export interface EvaluationReport {
  total_attacks: number;
  successful_attacks: number;
  failed_attacks: number;
  attack_success_rate: number;
  defense_success_rate: number;
  avg_iterations: number;
  detailed_results: AttackOutcome[];
  timestamp: string;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
}

export interface AttackTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  result?: unknown;
  error?: string;
}

export interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: Record<string, unknown>;
}

export interface User {
  username: string;
  email?: string;
  full_name?: string;
  scopes: string[];
  disabled?: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface GatewayResult {
  decision: 'allow' | 'block' | 'sanitize' | 'review';
  confidence: number;
  reason: string;
  matched_rules: string[];
  sanitized_input?: string;
}

export interface LLMEndpoint {
  name: string;
  provider: string;
  model: string;
  base_url?: string;
  weight: number;
  status: 'healthy' | 'degraded' | 'unhealthy';
}

export interface GatewayStats {
  total_endpoints: number;
  available_endpoints: number;
  strategy: string;
  endpoints: Record<string, LLMEndpoint>;
}
