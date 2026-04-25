<script setup lang="ts">
import { NButton } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const emit = defineEmits<{
  (e: 'open-login'): void
}>()

function handleAuth() {
  if (auth.isAuthenticated) {
    auth.logout()
  } else {
    emit('open-login')
  }
}
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="logo">拾途</router-link>
    </div>
    <nav class="header-nav">
      <router-link v-if="auth.isAuthenticated" to="/my-itineraries">我的行程</router-link>
      <router-link v-if="auth.isAuthenticated" to="/settings">设置</router-link>
    </nav>
    <div class="header-right">
      <n-button size="small" @click="handleAuth">
        {{ auth.isAuthenticated ? '退出' : '登录' }}
      </n-button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem 0.5rem;
  background: #eef6ff;
}

.logo {
  display: inline-flex;
  align-items: center;
  padding: 10px 18px;
  border: 1.5px solid #c7dbef;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 8px 18px rgba(108, 140, 213, 0.08);
  font-size: 1.5rem;
  font-weight: 400;
  letter-spacing: 0.04em;
  line-height: 1;
  color: #2f4f6f;
  text-decoration: none;
  font-family: var(--font-ui-display);
}

.header-nav {
  display: flex;
  gap: 1rem;
}

.header-nav a {
  color: #7f9bb6;
  text-decoration: none;
  font-size: 0.92rem;
  font-weight: 700;
  font-family: var(--font-ui-rounded);
  transition: opacity 0.2s ease;
}

.header-nav a:hover {
  opacity: 0.75;
}

.header-right :deep(.n-button) {
  border: none;
  border-radius: 999px;
  background: #6c8cd5;
  color: #fff;
  box-shadow: 0 8px 18px rgba(108, 140, 213, 0.2);
  font-weight: 700;
  padding: 0 16px;
}
</style>
