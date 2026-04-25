<template>
  <n-drawer :show="show" placement="right" :width="460" @update:show="$emit('update:show', $event)">
    <n-drawer-content v-if="poi" :title="poi.name" closable>
      <div class="detail-panel">
        <img v-if="poi.cover_image_url" :src="poi.cover_image_url" :alt="poi.name" class="detail-image" />
        <div class="detail-badges">
          <span class="badge">{{ poi.district || '热门片区' }}</span>
          <span class="badge">{{ poi.category }}</span>
          <span class="badge accent">{{ poi.is_free ? '免票' : '需购票' }}</span>
        </div>
        <div class="detail-section intro-section">
          <div class="section-title">景点介绍</div>
          <div class="section-body">{{ poi.description || '这里可以接入 LLM 生成的景点详细介绍。' }}</div>
        </div>
        <div class="detail-section" v-if="poi.suggested_route">
          <div class="section-title">推荐玩法</div>
          <div class="section-body">{{ poi.suggested_route }}</div>
        </div>
        <div class="detail-section">
          <div class="section-title">建议时长</div>
          <div class="section-body">{{ formatDuration(poi.suggested_duration_minutes) }}</div>
        </div>
        <a v-if="poi.ticket_url" class="ticket-btn" :href="poi.ticket_url" target="_blank" rel="noopener noreferrer">跳转购票</a>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { NDrawer, NDrawerContent } from 'naive-ui'
import type { CandidatePoiData } from '../types/itinerary'

defineProps<{
  show: boolean
  poi: CandidatePoiData | null
}>()

defineEmits<{
  'update:show': [value: boolean]
}>()

function formatDuration(minutes?: number | null) {
  if (!minutes) return '约 2 小时'
  if (minutes < 60) return `${minutes} 分钟`
  const hours = Math.round((minutes / 60) * 10) / 10
  return `约 ${hours} 小时`
}
</script>

<style scoped>
.detail-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.detail-image {
  width: 100%;
  aspect-ratio: 1.08;
  object-fit: cover;
  border-radius: 18px;
  background: #eef1f6;
}
.detail-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.badge {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f4f5f9;
  color: #5f6675;
  font-size: 12px;
  font-weight: 600;
}
.badge.accent {
  color: #7a60d2;
}
.detail-section {
  padding: 14px 16px;
  border: 1px solid #ebe5f8;
  border-radius: 16px;
  background: #fcfbff;
}
.intro-section {
  background: linear-gradient(180deg, #fbf8ff 0%, #f8f4ff 100%);
}
.section-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #9096a5;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.section-body {
  font-size: 14px;
  line-height: 1.8;
  color: #616877;
}
.ticket-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #a78bfa 0%, #8f79db 100%);
  color: #fff;
  text-decoration: none;
  font-weight: 700;
}
</style>
