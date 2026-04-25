<template>
  <div class="hand-drawn-map">
    <div class="map-header">
      <div class="map-kicker">路线预览</div>
      <div class="map-title">{{ title || '旅行地图' }}</div>
      <div class="map-subtitle">{{ currentDayTitle }}</div>
      <div class="day-info">
        <span class="info-item" v-if="currentDayWeather">
          {{ currentDayWeather }}
        </span>
        <span class="info-item" v-if="currentDayDuration">
          预计游玩 {{ currentDayDuration }} 小时
        </span>
        <span class="info-item weather-considered" v-if="hasWeather">
          已考虑近期天气
        </span>
      </div>
    </div>

    <div class="day-pagination">
      <button
        class="page-btn prev-btn"
        :disabled="currentDayIndex === 0"
        @click="prevDay"
      >
        上一天
      </button>
      <div class="day-indicator">
        Day {{ currentDayIndex + 1 }} / {{ days.length }}
      </div>
      <button
        class="page-btn next-btn"
        :disabled="currentDayIndex === days.length - 1"
        @click="nextDay"
      >
        下一天
      </button>
    </div>

    <div class="map-canvas" ref="canvasContainer">
      <svg class="route-svg" :viewBox="`0 0 ${canvasWidth} ${canvasHeight}`" preserveAspectRatio="xMidYMid meet">
        <path
          v-for="(path, idx) in routePaths"
          :key="`path-${idx}`"
          :d="path"
          class="route-path"
          :style="{ stroke: getPathColor(idx) }"
        />
      </svg>

      <div class="deco-cloud" style="top: 20px; left: 50px;">☁️</div>
      <div class="deco-cloud" style="top: 40px; right: 80px; animation-delay: 2s;">☁️</div>
      <div class="deco-tree" style="bottom: 50px; left: 100px;">🌳</div>

      <div
        v-for="(poi, idx) in mappedPois"
        :key="`poi-${idx}`"
        class="poi-marker"
        :class="{ highlighted: highlightedId === poi.poi_id }"
        :style="{ top: `${poi.y}px`, left: `${poi.x}px` }"
        @click="handlePoiClick(poi)"
      >
        <div class="poi-number">{{ idx + 1 }}</div>
        <div class="poi-icon">{{ poi.emoji }}</div>
        <div class="poi-label">{{ poi.name }}</div>
        <div class="poi-time">{{ poi.time_slot }}</div>
      </div>
    </div>

    <div class="legend">
      <div class="legend-title">路线说明</div>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-line"></div>
          <span>游览路线</span>
        </div>
        <div class="legend-item">
          <span>时间节点</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import type { DayData, POIVisitData } from '../types/itinerary'

const props = defineProps<{
  days: DayData[]
  title?: string
  subtitle?: string
  highlightedId?: string | number | null
}>()

const emit = defineEmits<{
  poiClick: [poi: POIVisitData]
}>()

const canvasContainer = ref<HTMLElement | null>(null)
const canvasWidth = ref(800)
const canvasHeight = ref(600)
const currentDayIndex = ref(0)

const currentDayTitle = computed(() => {
  const day = props.days[currentDayIndex.value]
  return day?.date || `第 ${currentDayIndex.value + 1} 天`
})

const currentDayWeather = computed(() => {
  const day = props.days[currentDayIndex.value]
  return day?.weather || ''
})

const currentDayDuration = computed(() => {
  const pois = currentDayPois.value
  if (pois.length === 0) return 0

  let totalMinutes = 0
  pois.forEach(poi => {
    totalMinutes += poi.duration_minutes || 0
  })

  return (totalMinutes / 60).toFixed(1)
})

const hasWeather = computed(() => {
  return currentDayWeather.value && currentDayWeather.value.length > 0
})

function prevDay() {
  if (currentDayIndex.value > 0) {
    currentDayIndex.value--
  }
}

function nextDay() {
  if (currentDayIndex.value < props.days.length - 1) {
    currentDayIndex.value++
  }
}

interface MappedPOI extends POIVisitData {
  x: number
  y: number
  emoji: string
  lat: number
  lng: number
}

function getPoiEmoji(poi: POIVisitData): string {
  const name = poi.name || ''
  const vibe = poi.vibe_description || ''
  const text = (name + vibe).toLowerCase()

  if (text.includes('站') || text.includes('机场')) return '🚄'
  if (text.includes('湖') || text.includes('江') || text.includes('海')) return '🌊'
  if (text.includes('寺') || text.includes('庙') || text.includes('塔')) return '🏛️'
  if (text.includes('餐') || text.includes('食') || text.includes('馆')) return '🥟'
  if (text.includes('咖啡')) return '☕'
  if (text.includes('公园') || text.includes('山') || text.includes('林')) return '🌿'
  if (text.includes('街') || text.includes('路')) return '🗺️'
  if (text.includes('博物馆') || text.includes('展览')) return '🏛️'
  return '📍'
}

const currentDayPois = computed(() => {
  const day = props.days[currentDayIndex.value]
  return day?.pois || []
})

function parseTimeToHours(timeSlot: string): number {
  const match = timeSlot.match(/(\d{1,2}):(\d{2})/)
  if (match) {
    return parseInt(match[1]) + parseInt(match[2]) / 60
  }
  return 0
}

function sortPoisByTime(pois: POIVisitData[]): POIVisitData[] {
  return [...pois].sort((a, b) => {
    return parseTimeToHours(a.time_slot) - parseTimeToHours(b.time_slot)
  })
}

function optimizeRoute(pois: POIVisitData[]): POIVisitData[] {
  if (pois.length <= 2) return pois

  const result: POIVisitData[] = []
  const remaining = [...pois]
  const getCoord = (p: POIVisitData) => ({
    lat: (p as any).latitude || 30.25,
    lng: (p as any).longitude || 120.16
  })

  result.push(remaining.shift()!)

  while (remaining.length > 0) {
    const last = result[result.length - 1]
    const lastCoord = getCoord(last)

    let nearestIdx = 0
    let nearestDist = Infinity

    for (let i = 0; i < remaining.length; i++) {
      const coord = getCoord(remaining[i])
      const dist = Math.sqrt(
        Math.pow(coord.lat - lastCoord.lat, 2) +
        Math.pow(coord.lng - lastCoord.lng, 2)
      )
      if (dist < nearestDist) {
        nearestDist = dist
        nearestIdx = i
      }
    }

    result.push(remaining.splice(nearestIdx, 1)[0])
  }

  return result
}

const orderedPois = computed(() => {
  const pois = currentDayPois.value
  if (pois.length === 0) return []

  const timeSorted = sortPoisByTime(pois)
  return optimizeRoute(timeSorted)
})

const mappedPois = computed<MappedPOI[]>(() => {
  if (orderedPois.value.length === 0) return []

  const pois = orderedPois.value
  const n = pois.length
  const padding = 60
  const mapWidth = canvasWidth.value - padding * 2
  const mapHeight = canvasHeight.value - padding * 2
  const centerX = canvasWidth.value / 2

  return pois.map((poi, idx) => {
    let x: number
    let y: number

    if (n === 1) {
      x = centerX
      y = canvasHeight.value / 2
    } else if (n === 2) {
      const spread = Math.min(mapWidth * 0.22, 120)
      x = idx === 0 ? centerX - spread : centerX + spread
      y = canvasHeight.value / 2
    } else {
      const row = Math.floor(idx / 2)
      const isLeft = idx % 2 === 0
      const rowCount = Math.ceil(n / 2)
      const rowHeight = mapHeight / rowCount
      const progress = rowCount === 1 ? 0.5 : row / (rowCount - 1)
      const spread = Math.min(80 + progress * (mapWidth * 0.18), mapWidth * 0.32)
      const verticalOffset = isLeft ? -8 : 8

      x = centerX + (isLeft ? -spread : spread)
      y = padding + row * rowHeight + rowHeight / 2 + verticalOffset

      if (idx === n - 1 && n % 2 === 1) {
        x = centerX
        y -= 6
      }
    }

    return {
      ...poi,
      x,
      y,
      lat: (poi as any).latitude || 30.25,
      lng: (poi as any).longitude || 120.16,
      emoji: getPoiEmoji(poi)
    }
  })
})

const routePaths = computed(() => {
  if (mappedPois.value.length < 2) return []

  const paths: string[] = []

  for (let i = 0; i < mappedPois.value.length - 1; i++) {
    const start = mappedPois.value[i]
    const end = mappedPois.value[i + 1]
    const dx = end.x - start.x
    const dy = end.y - start.y
    const distance = Math.sqrt(dx * dx + dy * dy)
    const offset = distance * 0.12
    const direction = i % 2 === 0 ? 1 : -1
    const cx1 = start.x + dx * 0.3
    const cy1 = start.y + dy * 0.3 + offset * direction
    const cx2 = start.x + dx * 0.7
    const cy2 = start.y + dy * 0.7 - offset * direction

    const path = `M ${start.x},${start.y} C ${cx1},${cy1} ${cx2},${cy2} ${end.x},${end.y}`
    paths.push(path)
  }

  return paths
})

function getPathColor(idx: number): string {
  const colors = ['#7BA8E0', '#6C8CD5', '#5B8FD9']
  return colors[idx % colors.length]
}

function handlePoiClick(poi: MappedPOI) {
  emit('poiClick', poi)
}

onMounted(() => {
  if (canvasContainer.value) {
    canvasWidth.value = canvasContainer.value.clientWidth
    canvasHeight.value = Math.min(400, canvasContainer.value.clientWidth * 0.7)
  }
})
</script>

<style scoped>
.hand-drawn-map {
  width: 100%;
}

.map-header {
  text-align: center;
  margin-bottom: 14px;
  padding: 8px 6px 0;
}

.map-kicker {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #958fa4;
  margin-bottom: 8px;
}

.map-title {
  font-size: 28px;
  font-weight: 800;
  color: #2f3542;
  margin-bottom: 6px;
}

.map-subtitle {
  font-size: 13px;
  color: #8e95a4;
}

.day-info {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 14px;
  font-size: 13px;
  flex-wrap: wrap;
}

.info-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #666d7c;
  background: #EDF4FC;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid #DCE4F5;
}

.weather-considered {
  background: #eef8ef;
  border-color: #cae7cd;
  color: #437452;
}

.day-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0 16px;
  gap: 10px;
}

.page-btn,
.day-indicator {
  min-height: 40px;
  padding: 0 16px;
  background: #fff;
  border: 1px solid #e6e9f0;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 700;
  color: #5c6472;
}

.page-btn {
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: #C5DEFF;
  background: #EDF4FC;
  color: #FF9F6B;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.day-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.map-canvas {
  position: relative;
  width: 100%;
  max-width: 760px;
  height: 400px;
  margin: 0 auto;
  background: linear-gradient(135deg, #EDF4FC 0%, #EAF3FF 100%);
  border-radius: 24px;
  border: 1px solid #DCE4F5;
  overflow: hidden;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
}

.route-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.route-path {
  fill: none;
  stroke-width: 3;
  stroke-dasharray: 8, 5;
  stroke-linecap: round;
  animation: dash 30s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -1000;
  }
}

.deco-cloud {
  position: absolute;
  font-size: 28px;
  opacity: 0.22;
  animation: float 6s ease-in-out infinite;
  pointer-events: none;
  z-index: 0;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.deco-tree {
  position: absolute;
  font-size: 22px;
  opacity: 0.28;
  pointer-events: none;
  z-index: 0;
}

.poi-marker {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
  cursor: pointer;
  transition: transform 0.25s ease;
  transform: translate(-50%, -50%);
}

.poi-number {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: #6C8CD5;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  border: 2px solid white;
  box-shadow: 0 8px 16px rgba(139, 92, 246, 0.18);
}

.poi-marker:hover {
  transform: translate(-50%, -50%) scale(1.06);
}

.poi-marker.highlighted {
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.12); }
}

.poi-icon {
  width: 44px;
  height: 44px;
  background: #fff;
  border: 2px solid #6C8CD5;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 10px 22px rgba(139, 92, 246, 0.16);
  position: relative;
}

.poi-label {
  margin-top: 12px;
  background: rgba(255,255,255,0.94);
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #2d3340;
  box-shadow: 0 8px 18px rgba(35,38,47,0.08);
  white-space: nowrap;
  border: 1px solid #DCE4F5;
}

.poi-time {
  font-size: 10px;
  color: #FF9F6B;
  margin-top: 6px;
  background: rgba(255,255,255,0.9);
  padding: 3px 8px;
  border-radius: 999px;
  border: 1px solid #DCE4F5;
}

.legend {
  margin-top: 16px;
  padding: 14px 16px;
  background: #EDF4FC;
  border-radius: 18px;
  border: 1px solid #DCE4F5;
}

.legend-title {
  font-weight: 700;
  color: #FF9F6B;
  margin-bottom: 10px;
  font-size: 14px;
}

.legend-items {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666d7c;
}

.legend-line {
  width: 30px;
  height: 3px;
  background: #DCE9FF;
  border-radius: 2px;
}

@media (max-width: 768px) {
  .map-title {
    font-size: 22px;
  }

  .map-canvas {
    height: 400px;
  }

  .poi-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .poi-label {
    font-size: 11px;
    padding: 4px 8px;
  }
}
</style>
