<template>
  <div class="main-layout">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside width="260px" class="sidebar">
        <div class="sidebar-header">
          <h2 class="app-title">
            <el-icon><Reading /></el-icon>
            Research Agent
          </h2>
          <el-button 
            type="primary" 
            @click="handleNewSession"
            :icon="Plus"
            round
          >
            新对话
          </el-button>
        </div>
        
        <!-- 会话列表 -->
        <SessionList />
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <el-header class="main-header">
          <div class="header-content">
            <h3 v-if="currentSession">
              {{ currentSession.title }}
            </h3>
            <h3 v-else>请选择一个对话或创建新对话</h3>
          </div>
        </el-header>
        
        <el-main class="main-content">
          <slot />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { Plus, Reading } from '@element-plus/icons-vue';
import SessionList from '@/components/Chat/SessionList.vue';
import { useChatStore } from '@/stores/chat';
import { storeToRefs } from 'pinia';

const chatStore = useChatStore();
const { currentSession } = storeToRefs(chatStore);

const handleNewSession = async () => {
  await chatStore.createSession();
};
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.layout-container {
  height: 100%;
}

.sidebar {
  background-color: #f8f9fa;
  border-right: 1px solid #e9ecef;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  margin-bottom: 20px;
}

.app-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  color: #2c3e50;
}

.app-title .el-icon {
  color: #409eff;
}

.main-header {
  background-color: white;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  padding: 0 24px;
}

.header-content h3 {
  margin: 0;
  color: #2c3e50;
}

.main-content {
  padding: 0;
  background-color: #f8f9fa;
}
</style>