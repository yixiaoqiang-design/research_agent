import { defineStore } from 'pinia';
import { ref, computed, onUnmounted } from 'vue';
import { apiClient } from '@/utils/api';
import type { ChatMessage, ChatSession } from '@/types/chat';

export const useChatStore = defineStore('chat', () => {
  // ====================== 状态定义 ======================
  
  // 聊天会话列表
  const sessions = ref<ChatSession[]>([]);
  
  // 当前活跃的会话
  const currentSession = ref<ChatSession | null>(null);
  
  // 当前会话的消息列表
  const messages = ref<ChatMessage[]>([]);
  
  // 加载状态（非流式请求）
  const isLoading = ref(false);
  
  // 流式处理状态
  const isStreaming = ref(false);
  
  // 流式内容缓冲
  const streamContent = ref('');
  
  // 当前流式连接
  const streamConnection = ref<ReturnType<typeof apiClient.createStreamConnection> | null>(null);

  // ====================== 计算属性 ======================
  
  /**
   * 当前会话ID
   */
  const currentSessionId = computed(() => currentSession.value?.id || '');
  
  /**
   * 是否有会话
   */
  const hasSessions = computed(() => sessions.value.length > 0);
  
  /**
   * 是否有消息
   */
  const hasMessages = computed(() => messages.value.length > 0);
  
  /**
   * 是否可以发送消息（输入框非空且没有正在处理中的请求）
   */
  const canSendMessage = computed(() => {
    return !isLoading.value && !isStreaming.value;
  });

  // ====================== 会话管理方法 ======================
  
  /**
   * 加载所有会话
   */
  async function loadSessions() {
    try {
      console.log('正在加载会话列表...');
      const data = await apiClient.getSessions();
      sessions.value = data;
      console.log('会话列表加载成功，数量:', sessions.value.length);
      
      // 如果有会话但没有当前会话，选择第一个
      if (sessions.value.length > 0 && !currentSession.value) {
        await switchSession(sessions.value[0].id);
      }
    } catch (error) {
      console.error('加载会话失败:', error);
      throw error;
    }
  }
  
  /**
   * 创建新会话
   * @param title 会话标题
   * @returns 创建的会话
   */
  async function createSession(title?: string) {
    try {
      console.log('正在创建新会话...');
      const session = await apiClient.createSession(title);
      sessions.value.unshift(session);
      await switchSession(session.id);
      console.log('新会话创建成功:', session.id);
      return session;
    } catch (error) {
      console.error('创建会话失败:', error);
      throw error;
    }
  }
  
  /**
   * 切换到指定会话
   * @param sessionId 会话ID
   */
  async function switchSession(sessionId: string) {
    try {
      // 关闭当前流式连接
      closeStreamConnection();
      
      console.log('正在切换到会话:', sessionId);
      const session = await apiClient.getSession(sessionId);
      currentSession.value = session;
      messages.value = session.messages || [];
      streamContent.value = '';
      isStreaming.value = false;
      console.log('会话切换成功，消息数量:', messages.value.length);
    } catch (error) {
      console.error('切换会话失败:', error);
      throw error;
    }
  }
  
  /**
   * 删除会话
   * @param sessionId 会话ID
   */
  async function deleteSession(sessionId: string) {
    try {
      console.log('正在删除会话:', sessionId);
      await apiClient.deleteSession(sessionId);
      
      // 从列表中移除
      sessions.value = sessions.value.filter(s => s.id !== sessionId);
      
      // 如果删除的是当前会话，切换到其他会话
      if (currentSession.value?.id === sessionId) {
        closeStreamConnection();
        currentSession.value = null;
        messages.value = [];
        streamContent.value = '';
        
        // 如果有其他会话，切换到第一个
        if (sessions.value.length > 0) {
          await switchSession(sessions.value[0].id);
        } else {
          // 否则创建新会话
          await createSession();
        }
      }
      
      console.log('会话删除成功');
    } catch (error) {
      console.error('删除会话失败:', error);
      throw error;
    }
  }
  
  /**
   * 重命名会话
   * @param sessionId 会话ID
   * @param newTitle 新标题
   */
  async function renameSession(sessionId: string, newTitle: string) {
    try {
      // 这里需要后端支持重命名API，暂时在前端更新
      const session = sessions.value.find(s => s.id === sessionId);
      if (session) {
        session.title = newTitle;
        if (currentSession.value?.id === sessionId) {
          currentSession.value.title = newTitle;
        }
      }
    } catch (error) {
      console.error('重命名会话失败:', error);
      throw error;
    }
  }

  // ====================== 消息处理方法 ======================
  
  /**
   * 发送消息
   * @param content 消息内容
   * @param useStream 是否使用流式响应
   */
  async function sendMessage(content: string, useStream: boolean = true) {
    if (!content.trim() || !canSendMessage.value) {
      console.warn('消息发送被阻止：内容为空或正在处理中');
      return;
    }

    // 如果没有当前会话，创建新会话
    if (!currentSession.value) {
      console.log('没有当前会话，正在创建新会话...');
      await createSession(content.slice(0, 50));
    }

    // 添加用户消息
    const userMessage: ChatMessage = {
      session_id: currentSessionId.value,
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    };
    
    messages.value.push(userMessage);
    console.log('用户消息已添加');

    if (useStream) {
      // 流式响应
      await sendStreamMessage(content);
    } else {
      // 非流式响应
      await sendRegularMessage(content);
    }
  }
  
  /**
   * 发送非流式消息
   * @param content 消息内容
   */
  async function sendRegularMessage(content: string) {
    isLoading.value = true;
    console.log('开始发送非流式消息...');
    
    try {
      const response = await apiClient.sendMessage({
        session_id: currentSessionId.value,
        message: content,
        stream: false
      });
      
      const assistantMessage: ChatMessage = {
        session_id: currentSessionId.value,
        role: 'assistant',
        content: response.message.content,
        tool_calls: response.message.tool_calls,
        tool_results: response.message.tool_results,
        created_at: new Date().toISOString()
      };
      
      messages.value.push(assistantMessage);
      console.log('非流式消息发送成功');
      
      // 更新会话列表中的会话
      updateSessionAfterMessage();
      
    } catch (error) {
      console.error('发送非流式消息失败:', error);
      
      // 添加错误消息
      const errorMessage: ChatMessage = {
        session_id: currentSessionId.value,
        role: 'assistant',
        content: '抱歉，消息发送失败，请稍后重试。',
        created_at: new Date().toISOString()
      };
      messages.value.push(errorMessage);
    } finally {
      isLoading.value = false;
    }
  }
  
  /**
   * 发送流式消息
   * @param content 消息内容
   */
  async function sendStreamMessage(content: string) {
    // 关闭之前的连接
    closeStreamConnection();
    
    isStreaming.value = true;
    streamContent.value = '';
    console.log('开始发送流式消息...');

    try {
      // 确保有有效的 session_id
      const sessionId = currentSessionId.value;
      if (!sessionId) {
        throw new Error('没有有效的会话ID');
      }

      streamConnection.value = apiClient.createStreamConnection(
        {
          session_id: sessionId,
          message: content
        },
        {
          onOpen: () => {
            console.log('流式连接已建立');
          },
          onMessage: (data) => {
            if (data.content) {
              streamContent.value += data.content;
            }

            if (data.is_final) {
              console.log('流式传输完成');
              
              // 流式传输完成，创建最终消息
              const assistantMessage: ChatMessage = {
                session_id: sessionId,
                role: 'assistant',
                content: streamContent.value,
                tool_calls: data.tool_calls,
                created_at: new Date().toISOString()
              };
              
              messages.value.push(assistantMessage);
              streamContent.value = '';
              isStreaming.value = false;
              
              // 更新会话列表
              updateSessionAfterMessage();
              
              // 关闭连接
              closeStreamConnection();
            }
          },
          onError: (error) => {
            console.error('流式传输错误:', error);
            isStreaming.value = false;
            
            // 只有当不是因为正常关闭导致的错误才显示错误消息
            if (streamConnection.value) {
              const errorMessage: ChatMessage = {
                session_id: sessionId,
                role: 'assistant',
                content: '抱歉，消息传输中断，请稍后重试。',
                created_at: new Date().toISOString()
              };
              messages.value.push(errorMessage);
            }
            
            closeStreamConnection();
          },
          onClose: () => {
            console.log('流式连接已关闭');
            isStreaming.value = false;
            streamConnection.value = null;
          }
        }
      );

      console.log('流式连接已创建');
    } catch (error) {
      console.error('启动流式传输失败:', error);
      isStreaming.value = false;
      
      // 添加错误消息
      const errorMessage: ChatMessage = {
        session_id: currentSessionId.value,
        role: 'assistant',
        content: '抱歉，无法建立流式连接，请稍后重试。',
        created_at: new Date().toISOString()
      };
      messages.value.push(errorMessage);
    }
  }
  
  /**
   * 更新会话的最后更新时间
   */
  function updateSessionAfterMessage() {
    const sessionIndex = sessions.value.findIndex(
      s => s.id === currentSessionId.value
    );
    
    if (sessionIndex !== -1) {
      sessions.value[sessionIndex].updated_at = new Date().toISOString();
      
      // 如果这是第一条消息，根据用户消息内容更新标题
      if (messages.value.length === 2) { // 用户消息 + AI回复
        const userMessage = messages.value.find(m => m.role === 'user');
        if (userMessage && userMessage.content) {
          const newTitle = userMessage.content.slice(0, 50) + 
            (userMessage.content.length > 50 ? '...' : '');
          
          sessions.value[sessionIndex].title = newTitle;
          
          // 同时更新当前会话标题
          if (currentSession.value) {
            currentSession.value.title = newTitle;
          }
        }
      }
    }
  }

  // ====================== 流式连接管理 ======================
  
  /**
   * 关闭当前的流式连接
   */
  function closeStreamConnection() {
    if (streamConnection.value) {
      console.log('正在关闭流式连接...');
      try {
        streamConnection.value.close();
      } catch (error) {
        console.warn('关闭流式连接时发生错误:', error);
      } finally {
        streamConnection.value = null;
        isStreaming.value = false;
      }
    }
  }
  
  /**
   * 清空当前会话（不删除）
   */
  function clearCurrentSession() {
    closeStreamConnection();
    currentSession.value = null;
    messages.value = [];
    streamContent.value = '';
    console.log('当前会话已清空');
  }
  
  /**
   * 清空所有会话（从store中移除，不删除服务器数据）
   */
  function clearAllSessions() {
    closeStreamConnection();
    sessions.value = [];
    currentSession.value = null;
    messages.value = [];
    streamContent.value = '';
    console.log('所有会话已清空');
  }
  
  /**
   * 重新加载当前会话的消息
   */
  async function reloadCurrentSession() {
    if (currentSessionId.value) {
      await switchSession(currentSessionId.value);
    }
  }

  // ====================== 初始化与清理 ======================
  
  /**
   * 初始化聊天store
   */
  async function init() {
    try {
      await loadSessions();
      
      // 如果没有会话，创建默认会话
      if (!hasSessions.value) {
        await createSession('欢迎使用研究助手');
      }
    } catch (error) {
      console.error('初始化聊天store失败:', error);
    }
  }
  
  /**
   * 清理资源（在组件卸载时调用）
   */
  onUnmounted(() => {
    closeStreamConnection();
    console.log('聊天store资源已清理');
  });

  // ====================== 导出 ======================
  return {
    // 状态
    sessions,
    currentSession,
    messages,
    isLoading,
    isStreaming,
    streamContent,
    
    // 计算属性
    currentSessionId,
    hasSessions,
    hasMessages,
    canSendMessage,
    
    // 会话管理方法
    loadSessions,
    createSession,
    switchSession,
    deleteSession,
    renameSession,
    
    // 消息处理方法
    sendMessage,
    sendRegularMessage,
    sendStreamMessage,
    clearCurrentSession,
    clearAllSessions,
    reloadCurrentSession,
    
    // 连接管理
    closeStreamConnection,
    
    // 初始化
    init,
  };
});

// 导出store的类型
export type ChatStore = ReturnType<typeof useChatStore>;
