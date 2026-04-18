<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NGrid, NGi, NButton, NEmpty, NSpin } from 'naive-ui'
import client from '@/api/client'

const router = useRouter()
const itineraries = ref<Array<{
  id: string
  city: string
  title: string
  date: string
  poi_count: number | null
}>>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const response = await client.get('/itineraries')
    itineraries.value = response.data
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
})

function viewItinerary(id: string) {
  router.push({ name: 'itinerary', params: { id } })
}
</script>

<template>
  <div style="max-width: 800px; margin: 0 auto; padding: 2rem 1rem">
    <h2 style="margin-bottom: 1.5rem">我的行程</h2>

    <n-spin :show="loading">
      <n-empty v-if="!loading && error" description="加载失败" />
      <n-empty v-else-if="!loading && itineraries.length === 0" description="还没有行程记录">
        <template #extra>
          <n-button type="primary" @click="router.push('/')">开始规划</n-button>
        </template>
      </n-empty>
      <n-grid v-else :cols="2" :x-gap="16" :y-gap="16" responsive="screen">
        <n-gi v-for="item in itineraries" :key="item.id">
          <n-card hoverable style="cursor: pointer" @click="viewItinerary(item.id)">
            <div style="font-size: 0.75rem; color: var(--color-coral); margin-bottom: 0.5rem">{{ item.city }}</div>
            <div style="font-size: 1.125rem; font-weight: 600; margin-bottom: 0.75rem">{{ item.title }}</div>
            <div style="display: flex; justify-content: space-between; font-size: 0.875rem; color: var(--color-warm-text-muted)">
              <span>{{ item.date }}</span>
              <span v-if="item.poi_count">{{ item.poi_count }}个地点</span>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>