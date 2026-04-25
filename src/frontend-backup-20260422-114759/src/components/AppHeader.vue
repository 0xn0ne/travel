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
  padding: 0.9rem 1.5rem;
  border-bottom: 1px solid #e7e8ee;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(12px);
}

.logo {
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #2f2f33;
  text-decoration: none;
}

.header-nav {
  display: flex;
  gap: 1.5rem;
}

.header-nav a {
  color: #7f8493;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: color 0.2s ease;
}

.header-nav a:hover {
  color: #8f79db;
}
</style>
