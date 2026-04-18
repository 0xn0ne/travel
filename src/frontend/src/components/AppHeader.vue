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
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--color-warm-border);
  background: var(--color-warm-surface);
}
.logo {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-coral);
  text-decoration: none;
}
.header-nav {
  display: flex;
  gap: 1.5rem;
}
.header-nav a {
  color: var(--color-warm-text-muted);
  text-decoration: none;
  font-size: 0.875rem;
}
.header-nav a:hover {
  color: var(--color-coral-dark);
}
</style>
