<template>
  <MainLayout>
    <RouterView />
  </MainLayout>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import MainLayout from '@/components/Layout/MainLayout.vue';
import { useChatStore } from '@/stores/chat';

const chatStore = useChatStore();

onMounted(async () => {
  // 加载会话列表
  await chatStore.loadSessions();
  
  // 如果没有会话，创建默认会话
  if (!chatStore.hasSessions) {
    await chatStore.createSession('欢迎使用研究助手');
  }
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100vh;
  overflow: hidden;
}
</style>