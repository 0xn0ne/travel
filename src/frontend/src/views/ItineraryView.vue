<template>
  <div class="itinerary-view">
    <div v-if="loading" class="loading-skeleton">
      <div class="skeleton-header">
        <n-skeleton text :width="200" />
        <n-skeleton text :width="300" />
      </div>
      <div v-for="d in 2" :key="d" class="skeleton-day">
        <n-skeleton text :width="120" />
        <n-skeleton text :repeat="4" />
        <n-skeleton text :width="180" />
      </div>
    </div>

    <div v-else-if="notFound" class="not-found">
      <n-result status="404" title="行程不存在" description="该行程可能已被删除或链接有误">
        <template #footer>
          <n-button type="primary" @click="router.push('/')">返回首页</n-button>
        </template>
      </n-result>
    </div>

    <div v-else-if="error && !store.currentItinerary" class="error-section">
      <n-alert type="warning" :title="error" />
      <n-button size="small" type="primary" style="margin-top: 8px" @click="loadItinerary">重试</n-button>
    </div>

    <div v-else-if="store.isGenerating" class="generating">
      <StageProgress :current-stage="store.stage" :message="store.stageMessage" />
      <div class="skeleton-timeline">
        <div v-for="d in 3" :key="d" class="skeleton-day">
          <n-skeleton text :width="100" />
          <n-skeleton text :repeat="3" />
          <n-skeleton text :width="180" />
        </div>
      </div>
    </div>

    <div v-else-if="store.currentItinerary" class="itinerary-content">
      <div class="itinerary-header">
        <div class="header-row">
          <h1 class="title">{{ (store.currentItinerary as any).title }}</h1>
          <ShareButton :itinerary-id="getItineraryId()" />
        </div>
        <p class="summary">{{ (store.currentItinerary as any).summary }}</p>
      </div>

      <DayRouteSelector
        :days="displayDays"
        :selected-day="activeDay"
        @select="setActiveDay"
      />

      <div class="split-layout">
        <div class="split-left">
          <ItineraryTimeline
            :days="filteredDays"
            :preview-mode="store.previewChanges !== null"
            :preview-changes="store.previewChanges?.changes ?? null"
            :highlight-poi-id="highlightPoiId"
            @action="handlePoiAction"
            @poi-click="handleTimelinePoiClick"
          />
        </div>
        <div class="split-right">
          <MapView
            :days="filteredDays"
            :active-day="null"
            :highlight-poi-id="highlightPoiId"
            :height="'100%'"
            @marker-click="handleMapMarkerClick"
          />
        </div>
      </div>

      <StageProgress
        v-if="store.isAdjusting"
        :current-stage="store.stage"
        :message="store.stageMessage"
      />

      <div v-if="store.previewChanges" class="preview-actions">
        <div class="preview-actions-inner">
          <n-button type="primary" class="touch-target" @click="handleConfirm" :loading="store.isAdjusting">
            确认修改
          </n-button>
          <n-button class="touch-target" @click="store.cancelAdjustment()">取消</n-button>
        </div>
      </div>

      <FeedbackWidget v-if="!store.isAdjusting && !store.previewChanges" :itinerary-id="getItineraryId()" />

      <div v-if="store.adjustHistory.length > 0" class="chat-history">
        <div
          v-for="(msg, idx) in store.adjustHistory"
          :key="idx"
          class="chat-bubble"
          :class="msg.role === 'user' ? 'bubble-user' : 'bubble-assistant'"
        >
          <div class="bubble-content">{{ msg.text }}</div>
        </div>
      </div>

      <div v-if="store.error && store.isAdjusting === false" class="error-section">
        <n-alert type="warning" :title="store.error" />
      </div>

      <div class="chat-input-bar">
        <div class="chat-input-inner">
          <n-input
            v-model:value="adjustText"
            type="textarea"
            placeholder="想调整行程？比如「第二天的咖啡馆换成更有氛围的」"
            :autosize="{ minRows: 1, maxRows: 4 }"
            @keydown.enter.exact.prevent="handleSendAdjust"
          />
          <n-button
            type="primary"
            :loading="store.isAdjusting"
            :disabled="!adjustText.trim() || store.isGenerating"
            class="send-btn"
            @click="handleSendAdjust"
          >
            发送
          </n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NSkeleton, NResult, NButton, NAlert, NInput } from 'naive-ui'
import ItineraryTimeline from '../components/ItineraryTimeline.vue'
import StageProgress from '../components/StageProgress.vue'
import FeedbackWidget from '../components/FeedbackWidget.vue'
import MapView from '../components/MapView.vue'
import DayRouteSelector from '../components/DayRouteSelector.vue'
import ShareButton from '../components/ShareButton.vue'
import { useItineraryStore } from '../stores/itinerary'
import type { POIVisitData, DayData } from '../types/itinerary'

const route = useRoute()
const router = useRouter()
const store = useItineraryStore()

const loading = ref(true)
const error = ref<string | null>(null)
const notFound = ref(false)
const adjustText = ref('')
const activeDay = ref<number | null>(null)
const highlightPoiId = ref<string | number | null>(null)

let clearHighlightTimer: ReturnType<typeof setTimeout> | null = null

function getItineraryId(): string {
  return route.params.id as string
}

async function loadItinerary() {
  loading.value = true
  error.value = null
  notFound.value = false

  try {
    const id = getItineraryId()
    const res = await fetch(`/api/itinerary/${id}`)
    if (res.status === 404) {
      loading.value = false
      notFound.value = true
      return
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    if (data.itinerary) {
      store.currentItinerary = data.itinerary
    } else {
      store.currentItinerary = data
    }
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
}

const displayDays = computed<DayData[]>(() => {
  if (store.previewChanges?.updated_itinerary) {
    return (store.previewChanges.updated_itinerary as any).days as DayData[] || []
  }
  return (store.currentItinerary as any)?.days as DayData[] || []
})

const filteredDays = computed<DayData[]>(() => {
  if (activeDay.value === null) return displayDays.value
  return displayDays.value.filter((d) => d.day_number === activeDay.value)
})

function setActiveDay(dayNumber: number) {
  if (activeDay.value === dayNumber) {
    activeDay.value = null
  } else {
    activeDay.value = dayNumber
  }
}

function handleTimelinePoiClick(poiId: string | number) {
  highlightPoiId.value = poiId
  scheduleClearHighlight()
}

function handleMapMarkerClick(poiId: string | number) {
  highlightPoiId.value = poiId
  scheduleClearHighlight()

  const el = document.querySelector(`[data-poi-id="${poiId}"]`) as HTMLElement
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

function scheduleClearHighlight() {
  if (clearHighlightTimer) clearTimeout(clearHighlightTimer)
  clearHighlightTimer = setTimeout(() => {
    highlightPoiId.value = null
  }, 3000)
}

function findDayNumber(poiName: string): number {
  const days = (store.currentItinerary as any)?.days as DayData[] | undefined
  if (!days) return 1
  for (const day of days) {
    if (day.pois?.some((p) => p.name === poiName)) {
      return day.day_number
    }
  }
  return 1
}

function handlePoiAction(type: string, poi: POIVisitData) {
  const dayNum = findDayNumber(poi.name)
  switch (type) {
    case 'delete':
      if (poi.poi_id) {
        store.deletePoi(dayNum, poi.poi_id)
      }
      break
    case 'insert_before':
      adjustText.value = `请在第${dayNum}天${poi.name}前面插入一个新的体验`
      nextTick(() => {
        const el = document.querySelector('.chat-input-bar textarea') as HTMLElement
        el?.focus()
      })
      break
    case 'insert_after':
      adjustText.value = `请在第${dayNum}天${poi.name}后面插入一个新的体验`
      nextTick(() => {
        const el = document.querySelector('.chat-input-bar textarea') as HTMLElement
        el?.focus()
      })
      break
    case 'replace':
      store.adjust(getItineraryId(), `请替换第${dayNum}天的${poi.name}`)
      nextTick(() => window.scrollTo({ top: 0, behavior: 'smooth' }))
      break
  }
}

function handleSendAdjust() {
  const text = adjustText.value.trim()
  if (!text || store.isAdjusting) return
  adjustText.value = ''
  store.adjust(getItineraryId(), text)
}

async function handleConfirm() {
  await store.confirmAdjustment(getItineraryId())
  await loadItinerary()
}

onMounted(loadItinerary)

onUnmounted(() => {
  store.abort()
  if (clearHighlightTimer) clearTimeout(clearHighlightTimer)
})
</script>

<style scoped>
.itinerary-view {
  min-height: 60vh;
}

.loading-skeleton {
  max-width: 720px;
  margin: 0 auto;
  padding: 20px 16px;
}
.skeleton-header {
  margin-bottom: 24px;
}
.skeleton-header :deep(.n-skeleton) {
  margin-bottom: 8px;
}
.skeleton-day {
  margin-bottom: 24px;
}

.not-found {
  padding: 60px 0;
  text-align: center;
}

.error-section {
  padding: 16px 0;
}

.generating {
  max-width: 720px;
  margin: 0 auto;
  padding: 20px 16px;
}
.skeleton-timeline {
  margin-top: 20px;
}

.itinerary-content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 16px 100px;
}

.itinerary-header {
  margin-bottom: 16px;
}
.header-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-warm-text);
  margin: 0 0 8px;
}
.summary {
  font-size: 15px;
  color: var(--color-warm-text-muted);
  margin: 0;
}

.split-layout {
  display: flex;
  gap: 16px;
  min-height: 500px;
}
.split-left {
  flex: 1;
  min-width: 0;
}
.split-right {
  flex: 1;
  min-width: 0;
  position: sticky;
  top: 16px;
  align-self: flex-start;
  height: 500px;
}

.preview-actions {
  margin: 16px 0;
}
.preview-actions-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
@media (min-width: 768px) {
  .preview-actions-inner {
    flex-direction: row;
  }
}

.chat-history {
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.chat-bubble {
  display: flex;
}
.bubble-user {
  justify-content: flex-end;
}
.bubble-assistant {
  justify-content: flex-start;
}
.bubble-content {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.bubble-user .bubble-content {
  background: var(--color-coral);
  color: white;
  border-bottom-right-radius: 4px;
}
.bubble-assistant .bubble-content {
  background: var(--color-warm-surface);
  color: var(--color-warm-text);
  border-bottom-left-radius: 4px;
}

.chat-input-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-warm-bg);
  border-top: 1px solid var(--color-warm-border);
  padding: 12px 16px;
  z-index: 100;
}
.chat-input-inner {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 8px;
}
.chat-input-inner :deep(.n-input) {
  flex: 1;
}
.send-btn {
  flex-shrink: 0;
  height: 44px;
  min-width: 44px;
}
.touch-target {
  min-height: 44px;
  min-width: 44px;
}

@media (max-width: 768px) {
  .itinerary-content {
    padding: 16px 12px 100px;
  }
  .title {
    font-size: 20px;
  }
  .split-layout {
    flex-direction: column;
  }
  .split-right {
    position: static;
    height: 300px;
    order: -1;
  }
}
</style>
