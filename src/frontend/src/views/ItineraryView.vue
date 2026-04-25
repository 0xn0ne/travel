<template>
  <div class="itinerary-view">
    <div v-if="loading" class="loading-skeleton state-card">
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

    <div v-else-if="notFound" class="not-found state-card">
      <n-result status="404" title="行程不存在" description="该行程可能已被删除或链接有误">
        <template #footer>
          <n-button type="primary" @click="router.push('/j')">返回首页</n-button>
        </template>
      </n-result>
    </div>

    <div v-else-if="error && !store.currentItinerary" class="error-section state-card">
      <n-alert type="warning" :title="error" />
      <n-button size="small" type="primary" style="margin-top: 8px" @click="loadItinerary">重试</n-button>
    </div>

    <div v-else-if="store.isGenerating" class="generating state-card">
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
      <div class="itinerary-header hero-card">
        <div class="header-copy">
          <div class="header-kicker">你的旅行行程</div>
          <div class="header-row">
            <h1 class="title">{{ (store.currentItinerary as any).title }}</h1>
            <ShareButton :itinerary-id="getItineraryId()" />
          </div>
          <p class="summary">{{ (store.currentItinerary as any).summary }}</p>
        </div>
        <div class="header-meta">
          <div class="meta-chip">{{ formatDateRange() || '已生成路线' }}</div>
          <div v-if="formatWalkingDistance()" class="meta-chip muted">{{ formatWalkingDistance() }}</div>
        </div>
      </div>


      <div class="view-toggle toggle-card">
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'diary' }"
          @click="viewMode = 'diary'"
        >
          手帐视图
        </button>
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'map' }"
          @click="viewMode = 'map'"
        >
          地图视图
        </button>
      </div>

      <!-- 视图切换按钮 -->
      <div class="view-toggle">
        <n-button
          :type="viewMode === 'diary' ? 'primary' : 'default'"
          size="small"
          @click="viewMode = 'diary'"
        >
          📖 手帐风格
        </n-button>
        <n-button
          :type="viewMode === 'map' ? 'primary' : 'default'"
          size="small"
          @click="viewMode = 'map'"
        >
          🗺️ 手绘地图
        </n-button>
      </div>

      <div class="split-layout">
        <div class="split-left panel-card">
          <div class="timeline-toolbar">
            <div>
              <div class="toolbar-kicker">行程管理</div>
              <span class="toolbar-title">行程景点</span>
            </div>
            <button class="add-btn" @click="timelineRef?.openAddDialog()">
              <span>+</span> 新增景点
            </button>
          </div>

          <ItineraryTimeline
            ref="timelineRef"
            :days="displayDays"
            :preview-mode="store.previewChanges !== null"
            :highlight-poi-id="highlightPoiId"
            @poi-click="handleTimelinePoiClick"
            @toggle="handleToggle"
            @update-day="handleUpdateDay"
          />
        </div>
        <div class="split-right">
          <DiaryRoute
            v-if="viewMode === 'diary'"
            :days="displayDays"
            :title="(store.currentItinerary as any)?.title || '旅行手帐'"
            :date-range="formatDateRange()"
            :people-count="peopleCount"
            :total-distance="formatWalkingDistance()"
            :weather="itineraryWeather"
            :taste-tags="itineraryTags"
            :highlighted-id="highlightPoiId"
            @poi-click="handleDiaryPoiClick"
          />
          <HandDrawnMap
            v-else
            :days="displayDays"
            :title="(store.currentItinerary as any)?.title || '旅行地图'"
            :subtitle="formatDateRange()"
            :highlighted-id="highlightPoiId"
            @poi-click="handleDiaryPoiClick"
          />
        </div>
      </div>

      <div class="progress-inline" v-if="store.isAdjusting">
        <StageProgress
          :current-stage="store.stage"
          :message="store.stageMessage"
        />
      </div>

      <div v-if="store.previewChanges" class="preview-actions panel-card">
        <div class="preview-actions-inner">
          <n-button type="primary" class="touch-target" @click="handleConfirm" :loading="store.isAdjusting">
            确认修改
          </n-button>
          <n-button class="touch-target" @click="store.cancelAdjustment()">取消</n-button>
        </div>
      </div>

      <FeedbackWidget v-if="!store.isAdjusting && !store.previewChanges" :itinerary-id="getItineraryId()" />

      <div v-if="store.adjustHistory.length > 0" class="chat-history panel-card">
        <div
          v-for="(msg, idx) in store.adjustHistory"
          :key="idx"
          class="chat-bubble"
          :class="msg.role === 'user' ? 'bubble-user' : 'bubble-assistant'"
        >
          <div class="bubble-content">{{ msg.text }}</div>
        </div>
      </div>

      <div v-if="store.error && store.isAdjusting === false" class="error-section panel-card">
        <n-alert type="warning" :title="store.error" />
      </div>

      <div class="chat-input-bar">
        <div class="chat-input-shell">
          <div class="chat-input-copy">
            <div class="chat-kicker">继续微调</div>
            <div class="chat-title">告诉我你还想怎么改这份路线</div>
          </div>
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
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NSkeleton, NResult, NButton, NAlert, NInput } from 'naive-ui'
import ItineraryTimeline from '../components/ItineraryTimeline.vue'
import StageProgress from '../components/StageProgress.vue'
import FeedbackWidget from '../components/FeedbackWidget.vue'
import DiaryRoute from '../components/DiaryRoute.vue'
import HandDrawnMap from '../components/HandDrawnMap.vue'
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
const highlightPoiId = ref<string | number | null>(null)
const viewMode = ref<'diary' | 'map'>('map')

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
    console.log('[DEBUG] Loading itinerary:', id)
    const res = await fetch(`/api/itinerary/${id}`)
    console.log('[DEBUG] Response status:', res.status)
    if (res.status === 404) {
      console.log('[DEBUG] Itinerary not found')
      loading.value = false
      notFound.value = true
      return
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    console.log('[DEBUG] Itinerary data loaded:', data)
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


function handleTimelinePoiClick(poiId: string | number) {
  highlightPoiId.value = poiId
  scheduleClearHighlight()
}

function scheduleClearHighlight() {
  if (clearHighlightTimer) clearTimeout(clearHighlightTimer)
  clearHighlightTimer = setTimeout(() => {
    highlightPoiId.value = null
  }, 3000)
}

function handleDiaryPoiClick(poi: POIVisitData) {
  const id = poi.poi_id
  if (id) {
    highlightPoiId.value = id
    scheduleClearHighlight()
    const el = document.querySelector(`[data-poi-id="${id}"]`) as HTMLElement
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

function formatDateRange(): string {
  const days = (store.currentItinerary as any)?.days as DayData[] || []
  if (days.length === 0) return ''
  return `${days.length}天${days.length - 1}晚`
}

function peopleCount(): string {
  return '2人'
}

function formatWalkingDistance(): string {
  const total = (store.currentItinerary as any)?.total_walking_minutes
  if (!total) return ''
  const km = (total * 0.75 / 1000).toFixed(1)
  return `约${km}km`
}

function itineraryWeather(): string {
  return ''
}

function itineraryTags(): string[] {
  return []
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

/* Reserved for future POI action handling:
function handlePoiAction(type: string, poi: POIVisitData) {
  const dayNum = findDayNumber(poi.name)
  switch (type) {
    case 'delete':
      if (poi.poi_id) { store.deletePoi(dayNum, poi.poi_id) }
      break
    case 'insert_before':
      adjustText.value = `请在第${dayNum}天${poi.name}前面插入一个新的体验`
      nextTick(() => { const el = document.querySelector('.chat-input-bar textarea') as HTMLElement; el?.focus() })
      break
    case 'insert_after':
      adjustText.value = `请在第${dayNum}天${poi.name}后面插入一个新的体验`
      nextTick(() => { const el = document.querySelector('.chat-input-bar textarea') as HTMLElement; el?.focus() })
      break
    case 'replace':
      store.adjust(getItineraryId(), `请替换第${dayNum}天的${poi.name}`)
      nextTick(() => window.scrollTo({ top: 0, behavior: 'smooth' }))
      break
  }
}
*/

function handleUpdateDay(updatedDay: DayData) {
  const itinerary = store.currentItinerary as any
  if (!itinerary?.days) return
  const dayIndex = itinerary.days.findIndex((d: DayData) => d.day_number === updatedDay.day_number)
  if (dayIndex === -1) return
  itinerary.days = itinerary.days.map((d: DayData, i: number) =>
    i === dayIndex ? { ...d, pois: updatedDay.pois } : d
  )
  store.currentItinerary = { ...itinerary }
}

function handleToggle() {
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
  min-height: 100vh;
  padding: 28px 0 140px;
  background: var(--bg-main);
  background-image:
    radial-gradient(rgba(158, 190, 219, 0.1) 1px, transparent 1px),
    radial-gradient(rgba(255, 255, 255, 0.65) 1px, transparent 1px);
  background-position: 0 0, 14px 14px;
  background-size: 26px 26px, 26px 26px;
}

.state-card,
.hero-card,
.selector-card,
.toggle-card,
.panel-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(108, 140, 213, 0.18);
  border-radius: 22px;
  box-shadow: 0 10px 28px rgba(108, 140, 213, 0.08);
  backdrop-filter: blur(12px);
}

.loading-skeleton,
.generating,
.error-section,
.not-found {
  max-width: 760px;
  margin: 0 auto;
  padding: 24px 20px;
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
  text-align: center;
}

.itinerary-content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 16px;
}

.itinerary-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 28px;
  margin-bottom: 16px;
}

.header-copy {
  min-width: 0;
}

.header-kicker,
.toolbar-kicker,
.chat-kicker {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--type-muted);
  margin-bottom: 8px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title {
  font-size: 34px;
  line-height: 1.15;
  font-weight: 800;
  color: var(--type-title);
  margin: 0;
}

.summary {
  font-size: 15px;
  line-height: 1.7;
  color: var(--type-muted);
  margin: 12px 0 0;
  max-width: 760px;
}

.header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  background: var(--accent-orange);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.meta-chip.muted {
  background: var(--paper-2);
  color: var(--type-muted);
}

.selector-card,
.toggle-card {
  margin-bottom: 16px;
}

.selector-card {
  padding: 6px;
}

.view-toggle {
  display: inline-flex;
  gap: 8px;
  padding: 8px;
}

.toggle-btn {
  min-height: 42px;
  padding: 0 16px;
  border: 0;
  border-radius: 14px;
  background: transparent;
  color: var(--type-muted);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: var(--font-ui-rounded);
}

.toggle-btn.active {
  background: var(--accent-orange);
  color: #fff;
  box-shadow: 0 12px 24px rgba(255, 159, 107, 0.25);
}

.toggle-btn:not(.active):hover {
  background: var(--paper-2);
  color: var(--type-title);
}

.view-toggle {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin: 16px 0;
}

.split-layout {
  display: flex;
  gap: 18px;
  align-items: flex-start;
}

.split-left,
.split-right {
  min-width: 0;
}

.split-left {
  flex: 1;
  padding: 18px;
}

.split-right {
  flex: 1;
  padding: 18px;
  position: sticky;
  top: 16px;
  margin-left: auto;
}

.timeline-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
}

.toolbar-title {
  display: block;
  font-size: 20px;
  font-weight: 800;
  color: var(--type-title);
}

.add-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  color: var(--type-body);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: var(--font-ui-rounded);
}

.add-btn:hover {
  border-color: var(--accent-orange);
  background: rgba(255, 159, 107, 0.08);
  color: var(--accent-orange);
}

.preview-card-shell :deep(.diary-view),
.preview-card-shell :deep(.hand-drawn-map) {
  background: transparent;
}

.progress-inline,
.preview-actions,
.chat-history,
.error-section {
  margin-top: 16px;
}

.preview-actions {
  padding: 18px;
}

.preview-actions-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-history {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
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
  max-width: min(80%, 720px);
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-user .bubble-content {
  background: var(--accent-orange);
  color: #fff;
  border-bottom-right-radius: 8px;
}

.bubble-assistant .bubble-content {
  background: var(--paper-2);
  color: var(--type-body);
  border: 1px solid rgba(108, 140, 213, 0.15);
  border-bottom-left-radius: 8px;
}

.chat-input-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  padding: 14px 16px 18px;
  background: linear-gradient(180deg, rgba(213, 235, 250, 0) 0%, rgba(213, 235, 250, 0.82) 28%, rgba(213, 235, 250, 0.98) 100%);
  backdrop-filter: blur(10px);
}

.chat-input-shell {
  max-width: 1280px;
  margin: 0 auto;
  padding: 16px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(108, 140, 213, 0.18);
  border-radius: 22px;
  box-shadow: 0 18px 40px rgba(108, 140, 213, 0.12);
}

.chat-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--type-title);
  margin-bottom: 12px;
}

.chat-input-inner {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.chat-input-inner :deep(.n-input) {
  flex: 1;
}

.send-btn {
  flex-shrink: 0;
  min-width: 72px;
  height: 44px;
}

.touch-target {
  min-height: 44px;
  min-width: 44px;
}

@media (min-width: 768px) {
  .preview-actions-inner {
    flex-direction: row;
  }
}

@media (max-width: 960px) {
  .itinerary-header {
    flex-direction: column;
  }

  .header-meta {
    justify-content: flex-start;
  }

  .split-layout {
    flex-direction: column;
  }

  .split-right {
    position: static;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .itinerary-view {
    padding-top: 16px;
  }

  .itinerary-content {
    padding: 0 12px;
  }

  .itinerary-header,
  .split-left,
  .split-right,
  .chat-input-shell {
    padding: 18px;
  }

  .title {
    font-size: 26px;
  }

  .header-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .view-toggle {
    display: flex;
    width: 100%;
  }

  .toggle-btn {
    flex: 1;
  }
}
</style>
