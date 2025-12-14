<template>
  <div :class="['message-bubble', message.role]">
    <div class="message-header">
      <div class="avatar">
        <el-icon v-if="message.role === 'user'"><UserFilled /></el-icon>
        <el-icon v-else><ChatRound /></el-icon>
      </div>
      <div class="message-info">
        <span class="role">
          {{ roleText }}
        </span>
        <span class="time" v-if="message.created_at">
          {{ formatTime(message.created_at) }}
        </span>
      </div>
    </div>
    
    <div class="message-content">
      <!-- 工具调用显示 -->
      <div v-if="message.tool_calls && message.tool_calls.length > 0" class="tool-calls">
        <div v-for="(toolCall, idx) in message.tool_calls" :key="idx" class="tool-call">
          <el-tag type="info" size="small">
            <el-icon><Tools /></el-icon>
            {{ toolCall.name }}
          </el-tag>
          <div class="tool-args">
            <pre>{{ JSON.stringify(toolCall.args, null, 2) }}</pre>
          </div>
        </div>
      </div>
      
      <!-- 消息内容 -->
      <div class="content-text" v-html="formattedContent"></div>
      
      <!-- 加载动画 -->
      <div v-if="isLast && message.is_streaming" class="typing-indicator">
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { UserFilled, ChatRound, Tools } from '@element-plus/icons-vue';
import type { ChatMessage } from '@/types/chat';

interface Props {
  message: ChatMessage & { is_streaming?: boolean };
  isLast?: boolean;
}

const props = defineProps<Props>();

const roleText = computed(() => {
  switch (props.message.role) {
    case 'user': return '你';
    case 'assistant': return '研究助手';
    case 'system': return '系统';
    case 'tool': return '工具';
    default: return props.message.role;
  }
});

const formatTime = (timeString: string) => {
  try {
    return new Date(timeString).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return '';
  }
};

const formattedContent = computed(() => {
  const content = props.message.content;
  // 简单的Markdown样式转换
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
});
</script>

<style scoped>
/* 样式保持不变 */
.message-bubble {
  margin-bottom: 16px;
}

.message-bubble.user {
  text-align: right;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.message-bubble.user .message-header {
  justify-content: flex-end;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #e9ecef;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
}

.message-bubble.user .avatar {
  margin-right: 0;
  margin-left: 12px;
  background-color: #e3f2fd;
  color: #2196f3;
}

.message-bubble.assistant .avatar {
  background-color: #f3e5f5;
  color: #9c27b0;
}

.message-info {
  display: flex;
  flex-direction: column;
}

.message-bubble.user .message-info {
  align-items: flex-end;
}

.role {
  font-weight: 500;
  color: #2c3e50;
  font-size: 14px;
}

.time {
  font-size: 12px;
  color: #6c757d;
  margin-top: 2px;
}

.message-content {
  max-width: 100%;
}

.message-bubble.assistant .message-content {
  text-align: left;
}

.message-bubble.user .message-content {
  text-align: right;
}

.content-text {
  display: inline-block;
  padding: 12px 16px;
  border-radius: 18px;
  max-width: 80%;
  word-break: break-word;
  line-height: 1.5;
  text-align: left;
}

.message-bubble.assistant .content-text {
  background-color: white;
  border: 1px solid #e9ecef;
  border-top-left-radius: 4px;
}

.message-bubble.user .content-text {
  background-color: #2196f3;
  color: white;
  border-top-right-radius: 4px;
}

.content-text :deep(strong) {
  font-weight: 600;
}

.content-text :deep(em) {
  font-style: italic;
}

.content-text :deep(code) {
  background-color: #f8f9fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9em;
}

.tool-calls {
  margin-bottom: 12px;
}

.tool-call {
  margin-bottom: 8px;
}

.tool-call .el-tag {
  margin-bottom: 4px;
}

.tool-call .el-tag .el-icon {
  margin-right: 4px;
}

.tool-args pre {
  margin: 0;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.typing-indicator {
  margin-top: 8px;
}

.typing-dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #adb5bd;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>