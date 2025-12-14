<template>
  <div class="session-list">
    <el-scrollbar height="calc(100vh - 120px)">
      <div 
        v-for="session in sessions" 
        :key="session.session_id"
        :class="['session-item', { active: isActive(session.session_id) }]"
        @click="handleSelectSession(session.session_id)"
      >
        <div class="session-content">
          <el-icon class="session-icon">
            <ChatDotRound />
          </el-icon>
          <div class="session-info">
            <div class="session-title">
              {{ session.title }}
            </div>
            <div class="session-time">
              {{ formatTime(session.updated_at) }}
            </div>
          </div>
        </div>
        
        <el-dropdown 
          trigger="click" 
          @command="handleCommand($event, session.session_id)"
          v-if="isActive(session.session_id)"
        >
          <el-icon class="session-actions">
            <MoreFilled />
          </el-icon>
          
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="delete">
                <el-icon><Delete /></el-icon>
                删除
              </el-dropdown-item>
              <el-dropdown-item command="rename">
                <el-icon><Edit /></el-icon>
                重命名
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      
      <div v-if="sessions.length === 0" class="empty-sessions">
        <el-icon><ChatLineRound /></el-icon>
        <p>暂无对话记录</p>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { 
  ChatDotRound, 
  MoreFilled, 
  Delete, 
  Edit,
  ChatLineRound 
} from '@element-plus/icons-vue';
import { useChatStore } from '@/stores/chat';
import { storeToRefs } from 'pinia';
import { ElMessage, ElMessageBox } from 'element-plus';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

const chatStore = useChatStore();
const { sessions, currentSessionId } = storeToRefs(chatStore);

const isActive = (sessionId: string) => {
  return currentSessionId.value === sessionId;
};

const formatTime = (timeString: string) => {
  try {
    return formatDistanceToNow(new Date(timeString), { 
      addSuffix: true,
      locale: zhCN 
    });
  } catch (error) {
    return '未知时间';
  }
};

const handleSelectSession = async (sessionId: string) => {
  await chatStore.switchSession(sessionId);
};

const handleCommand = async (command: string, sessionId: string) => {
  if (command === 'delete') {
    try {
      await ElMessageBox.confirm(
        '确定要删除这个对话吗？删除后无法恢复。',
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      );
      
      await chatStore.deleteSession(sessionId);
      ElMessage.success('删除成功');
    } catch (error) {
      // 用户取消删除
    }
  } else if (command === 'rename') {
    try {
      const { value: newTitle } = await ElMessageBox.prompt(
        '请输入新的对话标题',
        '重命名',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputValue: sessions.value.find(s => s.session_id === sessionId)?.title,
        }
      );
      
      if (newTitle && newTitle.trim()) {
        // 这里可以添加更新会话标题的API调用
        const session = sessions.value.find(s => s.session_id === sessionId);
        if (session) {
          session.title = newTitle.trim();
        }
        ElMessage.success('重命名成功');
      }
    } catch (error) {
      // 用户取消重命名
    }
  }
};
</script>

<style scoped>
.session-list {
  flex: 1;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.session-item:hover {
  background-color: #e9ecef;
}

.session-item.active {
  background-color: #e3f2fd;
  border-color: #2196f3;
}

.session-content {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.session-icon {
  margin-right: 12px;
  color: #6c757d;
  flex-shrink: 0;
}

.session-item.active .session-icon {
  color: #2196f3;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: #6c757d;
}

.session-actions {
  color: #6c757d;
  padding: 4px;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.empty-sessions {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
}

.empty-sessions .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #adb5bd;
}

.empty-sessions p {
  margin: 0;
  font-size: 14px;
}
</style>