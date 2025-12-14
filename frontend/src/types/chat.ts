// src/types/chat.ts

export interface ChatMessage {
  id?: number;
  session_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_calls?: ToolCall[];
  tool_results?: ToolResult[];
  created_at?: string;
  is_streaming?: boolean;
}

export interface ToolCall {
  id?: string;
  name: string;
  args: Record<string, any>;
}

export interface ToolResult {
  tool_call_id: string;
  result: string;
}

export interface ChatSession {
  id: number;
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  messages?: ChatMessage[];
}

export interface ChatRequest {
  session_id?: string;
  message: string;
  stream?: boolean;
}

export interface ChatResponse {
  session_id: string;
  message: ChatMessage;
  is_complete: boolean;
}

export interface ChatStreamChunk {
  content: string;
  is_final: boolean;
  tool_calls?: ToolCall[];
}

// 流式连接相关类型
export interface StreamCallbacks {
  onMessage?: (data: any) => void;
  onError?: (error: any) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface StreamConnection {
  close: () => void;
}