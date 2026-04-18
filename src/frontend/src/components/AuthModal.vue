<script setup lang="ts">
import { ref, watch } from 'vue'
import { NModal, NForm, NFormItem, NInput, NButton, NSpace } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const isOpen = ref(false)
const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const emit = defineEmits<{
  (e: 'success'): void
}>()

watch(isOpen, (val) => {
  if (val) {
    email.value = ''
    password.value = ''
    error.value = ''
    mode.value = 'login'
  }
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(email.value, password.value)
    } else {
      await auth.register(email.value, password.value)
    }
    isOpen.value = false
    emit('success')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}

function openLogin() {
  mode.value = 'login'
  isOpen.value = true
}

function openRegister() {
  mode.value = 'register'
  isOpen.value = true
}

defineExpose({ openLogin, openRegister })
</script>

<template>
  <n-modal v-model:show="isOpen" preset="card" :title="mode === 'login' ? '登录' : '注册'" style="max-width: 400px">
    <n-form @submit.prevent="submit">
      <n-form-item label="邮箱">
        <n-input v-model:value="email" type="text" required placeholder="your@email.com" inputmode="email" />
      </n-form-item>
      <n-form-item label="密码">
        <n-input v-model:value="password" type="password" required placeholder="至少6位" :minlength="6" show-password-on="click" />
      </n-form-item>
      <div v-if="error" style="color: var(--color-coral); margin-bottom: 1rem; font-size: 0.875rem">{{ error }}</div>
      <n-button type="primary" block :loading="loading" attr-type="submit">
        {{ mode === 'login' ? '登录' : '注册' }}
      </n-button>
    </n-form>
    <template #footer>
      <n-space justify="center" style="font-size: 0.875rem">
        <template v-if="mode === 'login'">
          没有账号？<n-button text type="primary" @click="mode = 'register'">立即注册</n-button>
        </template>
        <template v-else>
          已有账号？<n-button text type="primary" @click="mode = 'login'">立即登录</n-button>
        </template>
      </n-space>
    </template>
  </n-modal>
</template>
