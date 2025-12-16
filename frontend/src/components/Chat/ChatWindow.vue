<template>
  <div class="chat-window">
    <!-- 消息列表 -->
    <div ref="messagesContainer" class="messages-container">
      <div class="messages-wrapper">
        <div 
          v-for="(message, index) in messages" 
          :key="message.id || index"
          class="message-wrapper"
        >
          <MessageBubble 
            :message="message"
            :is-last="index === messages.length - 1"
          />
        </div>
        
        <!-- 流式响应显示 -->
        <div v-if="isStreaming && streamContent" class="message-wrapper">
          <MessageBubble 
            :message="{
              session_id: currentSessionId || 'temp',
              role: 'assistant',
              content: streamContent,
              created_at: new Date().toISOString(),
              is_streaming: true
            }"
            :is-last="true"
          />
        </div>
        
        <!-- 空状态 -->
        <div v-if="messages.length === 0 && !isStreaming" class="empty-state">
          <el-icon class="empty-icon"><ChatRound /></el-icon>
          <h3>开始你的学术研究对话</h3>
          <p>我是你的研究助手，可以帮你查找和总结学术论文</p>
          
          <div class="quick-questions">
            <el-button 
              v-for="(question, idx) in quickQuestions" 
              :key="idx"
              @click="sendQuickQuestion(question)"
              type="primary"
              plain
              round
            >
              {{ question }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          :autosize="{ minRows: 3, maxRows: 6 }"
          placeholder="请输入你的研究问题..."
          @keydown.enter.exact.prevent="handleSend"
          resize="none"
        />
        
        <div class="input-actions">
          <div class="tools">
            <el-tooltip content="清空对话" placement="top">
              <el-button 
                :icon="Delete" 
                @click="handleClear"
                :disabled="!hasMessages || !currentSessionId"
              />
            </el-tooltip>
            
            <el-tooltip content="使用流式响应" placement="top">
              <el-switch
                v-model="useStream"
                inline-prompt
                active-text="流式"
                inactive-text="普通"
              />
            </el-tooltip>
          </div>
          
          <el-button 
            type="primary" 
            @click="handleSend"
            :loading="isLoading"
            :disabled="!inputMessage.trim() || isStreaming || !currentSessionId"
            round
          >
            <template #icon>
              <el-icon><Promotion /></el-icon>
            </template>
            发送
          </el-button>
        </div>
      </div>
      
      <div class="input-tips">
        <small>
          <el-icon><InfoFilled /></el-icon>
          我可以帮你：搜索arXiv论文查找文献等，相关内容由 AI 生成，仅供参考。
        </small>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import { 
  Promotion, 
  Delete, 
  InfoFilled,
  ChatRound 
} from '@element-plus/icons-vue';
import { useChatStore } from '@/stores/chat';
import { storeToRefs } from 'pinia';
import MessageBubble from './MessageBubble.vue';

const chatStore = useChatStore();
const {
  messages,
  currentSessionId,
  isLoading,
  isStreaming,
  streamContent
} = storeToRefs(chatStore);

const inputMessage = ref('');
const useStream = ref(true);
const messagesContainer = ref<HTMLElement>();

const hasMessages = computed(() => messages.value.length > 0);

const quickQuestions = [
  '帮我查找关于transformer的最新论文',
  '什么是强化学习？',
  '查找关于神经网络剪枝的文献',
  '总结一下GPT-4的主要贡献'
];

const sendQuickQuestion = (question: string) => {
  inputMessage.value = question;
  handleSend();
};

const handleSend = async () => {
  if (!inputMessage.value.trim() || isLoading.value || isStreaming.value || !currentSessionId.value) {
    return;
  }
  
  const message = inputMessage.value.trim();
  inputMessage.value = '';
  
  await chatStore.sendMessage(message, useStream.value);
  
  // 滚动到底部
  scrollToBottom();
};

const handleClear = () => {
  if (currentSessionId.value) {
    chatStore.deleteSession(currentSessionId.value);
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

// 监听消息变化，自动滚动
watch([messages, streamContent], () => {
  scrollToBottom();
}, { deep: true });
</script>

<style scoped>
/* 样式保持不变 */
.chat-window {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background-color: #fafafa;
}

.messages-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.message-wrapper {
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #6c757d;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 24px;
  color: #dee2e6;
}

.empty-state h3 {
  margin: 0 0 12px 0;
  color: #2c3e50;
}

.empty-state p {
  margin: 0 0 32px 0;
  font-size: 16px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  max-width: 600px;
  margin: 0 auto;
}

.input-area {
  border-top: 1px solid #e9ecef;
  padding: 20px;
  background-color: white;
}

.input-wrapper {
  margin-bottom: 12px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.tools {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-tips {
  text-align: center;
  color: #6c757d;
  font-size: 12px;
}

.input-tips .el-icon {
  margin-right: 4px;
}
</style>
