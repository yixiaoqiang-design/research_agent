import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API 调用接口定义
export interface ChatRequest {
  session_id?: string;
  message: string;
  stream?: boolean;
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

export interface ChatMessage {
  id?: number;
  session_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_calls?: any[];
  tool_results?: any;
  created_at?: string;
}

export interface StreamCallbacks {
  onMessage?: (data: any) => void;
  onError?: (error: any) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface StreamConnection {
  close: () => void;
}

class ApiClient {
  private client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // ====================== 聊天会话相关 ======================

  /**
   * 创建新的聊天会话
   * @param title 会话标题
   * @returns 会话信息
   */
  async createSession(title: string = '新对话'): Promise<any> {
    const response = await this.client.post('/api/chat/sessions', { title });
    return response.data;
  }

  /**
   * 获取所有聊天会话
   * @returns 会话列表
   */
  async getSessions(): Promise<any> {
    const response = await this.client.get('/api/chat/sessions');
    return response.data;
  }

  /**
   * 获取特定会话
   * @param sessionId 会话ID
   * @returns 会话信息
   */
  async getSession(sessionId: string): Promise<any> {
    const response = await this.client.get(`/api/chat/sessions/${sessionId}`);
    return response.data;
  }

  /**
   * 删除会话
   * @param sessionId 会话ID
   */
  async deleteSession(sessionId: string): Promise<void> {
    await this.client.delete(`/api/chat/sessions/${sessionId}`);
  }

  /**
   * 获取会话的所有消息
   * @param sessionId 会话ID
   * @returns 消息列表
   */
  async getSessionMessages(sessionId: string): Promise<any> {
    const response = await this.client.get(`/api/chat/sessions/${sessionId}/messages`);
    return response.data;
  }

  // ====================== 消息相关 ======================

  /**
   * 发送消息（非流式）
   * @param data 消息数据
   * @returns 响应结果
   */
  async sendMessage(data: ChatRequest): Promise<any> {
    const response = await this.client.post('/api/chat/message', data);
    return response.data;
  }

  // ====================== 流式连接（使用 fetch API） ======================

  /**
   * 创建流式连接（POST 请求）
   * @param data 请求数据
   * @param callbacks 回调函数
   * @returns 可关闭的连接对象
   */
  createStreamConnection(
    data: { 
      session_id?: string; 
      message: string;
    }, 
    callbacks: StreamCallbacks = {}
  ): StreamConnection {
    const url = `${API_BASE_URL}/api/chat/stream`;
    const requestData = {
      session_id: data.session_id,
      message: data.message,
      stream: true
    };

    const controller = new AbortController();
    const signal = controller.signal;
    
    let isActive = true;
    let isComplete = false;

    // 使用 fetch 发送 POST 请求
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
      signal,
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP 错误! 状态码: ${response.status} ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error('浏览器不支持 ReadableStream');
        }

        // 连接成功建立
        console.log('流式连接已建立');
        callbacks.onOpen?.();

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        // 处理流式数据
        const processStream = async (): Promise<void> => {
          try {
            while (isActive) {
              const { done, value } = await reader.read();
              
              if (done) {
                console.log('流式传输完成');
                isComplete = true;
                callbacks.onClose?.();
                break;
              }

              // 解码数据并添加到缓冲区
              buffer += decoder.decode(value, { stream: true });
              
              // 按行分割处理 SSE 格式
              const lines = buffer.split('\n');
              buffer = lines.pop() || ''; // 保留未完成的行
              
              for (const line of lines) {
                if (!isActive) break;
                
                if (line.startsWith('data: ')) {
                  const dataLine = line.substring(6).trim();
                  
                  // 忽略空行和结束标记
                  if (dataLine === '' || dataLine === '[DONE]') {
                    if (dataLine === '[DONE]') {
                      console.log('接收到结束标记 [DONE]');
                      isComplete = true;
                      callbacks.onClose?.();
                    }
                    continue;
                  }
                  
                  try {
                    const parsedData = JSON.parse(dataLine);
                    callbacks.onMessage?.(parsedData);
                  } catch (error) {
                    console.error('解析 SSE 数据失败:', error, '原始数据:', dataLine);
                    
                    // 如果解析失败，尝试发送原始内容
                    if (dataLine) {
                      callbacks.onMessage?.({
                        content: dataLine,
                        is_final: false
                      });
                    }
                  }
                }
              }
            }
          } catch (error) {
            if (error.name === 'AbortError') {
              console.log('流式请求被主动中断');
              if (!isComplete) {
                callbacks.onClose?.();
              }
            } else if (isActive) {
              console.error('读取流数据时发生错误:', error);
              callbacks.onError?.(error);
            }
          } finally {
            isActive = false;
          }
        };

        processStream();
      })
      .catch(error => {
        if (isActive) {
          console.error('发送流式请求失败:', error);
          callbacks.onError?.(error);
        }
      });

    return {
      close: () => {
        if (!isActive) return;
        isActive = false;
        console.log('手动关闭流式连接');
        controller.abort();
        if (!isComplete) {
          callbacks.onClose?.();
        }
      }
    };
  }

  /**
   * 发送流式消息（简化接口）
   * @param data 消息数据
   * @returns 流式连接对象
   */
  sendStreamMessage(data: { 
    session_id?: string; 
    message: string;
  }): StreamConnection {
    return this.createStreamConnection(data);
  }

  // ====================== 辅助方法 ======================

  /**
   * 检查 API 健康状态
   * @returns 健康状态
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch (error) {
      console.error('API 健康检查失败:', error);
      return false;
    }
  }

  /**
   * 设置认证令牌
   * @param token 认证令牌
   */
  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  /**
   * 移除认证令牌
   */
  removeAuthToken(): void {
    delete this.client.defaults.headers.common['Authorization'];
  }
}

// 创建并导出单例实例
export const apiClient = new ApiClient();

// 为了方便使用，也导出一些常用类型
export type { AxiosInstance } from 'axios';

// 导出一些常用的 API 调用函数
export const chatApi = {
  // 会话管理
  createSession: (title: string = '新对话') => apiClient.createSession(title),
  getSessions: () => apiClient.getSessions(),
  getSession: (sessionId: string) => apiClient.getSession(sessionId),
  deleteSession: (sessionId: string) => apiClient.deleteSession(sessionId),
  getSessionMessages: (sessionId: string) => apiClient.getSessionMessages(sessionId),
  
  // 消息发送
  sendMessage: (data: ChatRequest) => apiClient.sendMessage(data),
  sendStreamMessage: (data: { session_id?: string; message: string }) => apiClient.sendStreamMessage(data),
  
  // 辅助功能
  healthCheck: () => apiClient.healthCheck(),
};

export default apiClient;