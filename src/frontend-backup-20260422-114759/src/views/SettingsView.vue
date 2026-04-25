<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NButton, NTag, NRadioGroup, NRadio, NSpace, NAlert } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import client from '@/api/client'

const auth = useAuthStore()

const tasteTags = ref<string[]>([])
const budget = ref('适中')
const saving = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const budgetOptions = ['经济', '适中', '宽裕']

const allTasteTags = [
  '文艺', '咖啡', '美食', '自然', '历史',
  '夜生活', '购物', '亲子', '浪漫', '探险',
  '漫步', '拍照', '品尝', '独行', '情侣',
]

onMounted(async () => {
  try {
    const response = await client.get('/auth/me')
    const tags = JSON.parse(response.data.taste_tags_default || '[]')
    tasteTags.value = Array.isArray(tags) ? tags : []
    budget.value = response.data.budget_default || '适中'
  } catch (e) {
    console.error('Failed to load profile', e)
  }
})

function toggleTag(tag: string) {
  const idx = tasteTags.value.indexOf(tag)
  if (idx >= 0) {
    tasteTags.value.splice(idx, 1)
  } else {
    tasteTags.value.push(tag)
  }
}

async function save() {
  saving.value = true
  message.value = ''
  try {
    await client.put('/auth/profile', {
      taste_tags_default: JSON.stringify(tasteTags.value),
      budget_default: budget.value,
    })
    await auth.fetchUser()
    message.value = '保存成功！'
    messageType.value = 'success'
  } catch (e) {
    message.value = '保存失败，请重试'
    messageType.value = 'error'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div style="max-width: 600px; margin: 0 auto; padding: 2rem 1rem">
    <h2 style="margin-bottom: 0.5rem">品味标签</h2>
    <p style="color: var(--color-warm-text-muted); font-size: 0.875rem; margin-bottom: 1rem">选择你喜欢的旅行风格</p>
    <n-space>
      <n-tag
        v-for="tag in allTasteTags"
        :key="tag"
        :type="tasteTags.includes(tag) ? 'warning' : 'default'"
        style="cursor: pointer"
        @click="toggleTag(tag)"
      >
        {{ tag }}
      </n-tag>
    </n-space>

    <h2 style="margin-top: 2rem; margin-bottom: 0.5rem">预算偏好</h2>
    <n-radio-group v-model:value="budget" name="budget">
      <n-space>
        <n-radio v-for="opt in budgetOptions" :key="opt" :value="opt">{{ opt }}</n-radio>
      </n-space>
    </n-radio-group>

    <n-alert v-if="message" :type="messageType" style="margin-top: 1.5rem; margin-bottom: 1rem">
      {{ message }}
    </n-alert>

    <n-button type="primary" block :loading="saving" style="margin-top: 1.5rem" @click="save">
      保存设置
    </n-button>
  </div>
</template>
