<template>
  <div class="hand-drawn-map">
    <div class="map-header">
      <div class="map-title">{{ title || '旅行地图' }}</div>
      <div class="map-subtitle">{{ subtitle }}</div>
    </div>

    <div class="map-canvas" ref="canvasContainer">
      <svg class="route-svg" :viewBox="`0 0 ${canvasWidth} ${canvasHeight}`" preserveAspectRatio="xMidYMid meet">
        <!-- 绘制路线 -->
        <path
          v-for="(path, idx) in routePaths"
          :key="`path-${idx}`"
          :d="path"
          class="route-path"
          :style="{ stroke: getPathColor(idx) }"
        />
      </svg>

      <!-- 装饰元素 -->
      <div class="deco-cloud" style="top: 20px; left: 50px;">☁️</div>
      <div class="deco-cloud" style="top: 40px; right: 80px; animation-delay: 2s;">☁️</div>
      <div class="deco-tree" style="bottom: 50px; left: 100px;">🌳</div>

      <!-- POI 标记点 -->
      <div
        v-for="(poi, idx) in mappedPois"
        :key="`poi-${idx}`"
        class="poi-marker"
        :class="{ highlighted: highlightedId === poi.poi_id }"
        :style="{ top: `${poi.y}px`, left: `${poi.x}px` }"
        @click="handlePoiClick(poi)"
      >
        <div class="poi-icon">{{ poi.emoji }}</div>
        <div class="poi-label">{{ poi.name }}</div>
        <div class="poi-time">{{ poi.time_slot }}</div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="legend">
      <div class="legend-title">📍 路线说明</div>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-line"></div>
          <span>游览路线</span>
        </div>
        <div class="legend-item">
          <span style="color: #FF9999;">⏰ 游玩时间</span>
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

interface MappedPOI extends POIVisitData {
  x: number
  y: number
  emoji: string
  lat: number
  lng: number
}

// 获取POI的emoji
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

// 将所有POI展平并获取坐标
const allPois = computed(() => {
  const pois: POIVisitData[] = []
  props.days.forEach(day => {
    if (day.pois) {
      pois.push(...day.pois)
    }
  })
  return pois
})

// 映射POI到画布坐标
const mappedPois = computed<MappedPOI[]>(() => {
  if (allPois.value.length === 0) return []

  // 提取所有经纬度
  const coords = allPois.value.map(poi => ({
    lat: (poi as any).latitude || 30.25, // 默认杭州坐标
    lng: (poi as any).longitude || 120.16,
    poi
  }))

  // 计算边界
  const lats = coords.map(c => c.lat)
  const lngs = coords.map(c => c.lng)
  const minLat = Math.min(...lats)
  const maxLat = Math.max(...lats)
  const minLng = Math.min(...lngs)
  const maxLng = Math.max(...lngs)

  // 添加边距
  const padding = 80
  const mapWidth = canvasWidth.value - padding * 2
  const mapHeight = canvasHeight.value - padding * 2

  // 映射到画布坐标（注意：纬度越大越靠北，y坐标越小）
  return coords.map(({ lat, lng, poi }) => {
    const x = padding + ((lng - minLng) / (maxLng - minLng || 1)) * mapWidth
    const y = padding + ((maxLat - lat) / (maxLat - minLat || 1)) * mapHeight

    return {
      ...poi,
      x,
      y,
      lat,
      lng,
      emoji: getPoiEmoji(poi)
    }
  })
})

// 生成路线路径
const routePaths = computed(() => {
  if (mappedPois.value.length < 2) return []

  const paths: string[] = []

  for (let i = 0; i < mappedPois.value.length - 1; i++) {
    const start = mappedPois.value[i]
    const end = mappedPois.value[i + 1]

    // 使用贝塞尔曲线连接两点，让路线更自然
    const dx = end.x - start.x
    const dy = end.y - start.y
    const distance = Math.sqrt(dx * dx + dy * dy)

    // 控制点偏移（让曲线更自然）
    const offset = distance * 0.2
    const cx1 = start.x + dx * 0.3 + offset * (Math.random() - 0.5)
    const cy1 = start.y + dy * 0.3 + offset * (Math.random() - 0.5)
    const cx2 = start.x + dx * 0.7 + offset * (Math.random() - 0.5)
    const cy2 = start.y + dy * 0.7 + offset * (Math.random() - 0.5)

    const path = `M ${start.x},${start.y} C ${cx1},${cy1} ${cx2},${cy2} ${end.x},${end.y}`
    paths.push(path)
  }

  return paths
})

function getPathColor(idx: number): string {
  const colors = ['#FFB5B5', '#FFA0A0', '#FF8E8E']
  return colors[idx % colors.length]
}

function handlePoiClick(poi: MappedPOI) {
  emit('poiClick', poi)
}

onMounted(() => {
  if (canvasContainer.value) {
    canvasWidth.value = canvasContainer.value.clientWidth
    canvasHeight.value = Math.min(600, canvasContainer.value.clientWidth * 0.75)
  }
})
</script>

<style scoped>
.hand-drawn-map {
  width: 100%;
}

.map-header {
  text-align: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px dashed #FFB5B5;
}

.map-title {
  font-family: 'Ma Shan Zheng', cursive, 'PingFang SC', sans-serif;
  font-size: 28px;
  color: #FF6B6B;
  margin-bottom: 8px;
}

.map-subtitle {
  font-size: 13px;
  color: #999;
}

.map-canvas {
  position: relative;
  width: 100%;
  height: 600px;
  background: linear-gradient(135deg, #FFF9F5 0%, #FFF5F0 100%);
  border-radius: 16px;
  border: 2px solid #FFE0D0;
  overflow: hidden;
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
  font-size: 30px;
  opacity: 0.3;
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
  font-size: 24px;
  opacity: 0.4;
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
  transition: transform 0.3s;
  transform: translate(-50%, -50%);
}

.poi-marker:hover {
  transform: translate(-50%, -50%) scale(1.1);
}

.poi-marker.highlighted {
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.15); }
}

.poi-icon {
  width: 50px;
  height: 50px;
  background: white;
  border: 3px solid #FF8E8E;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
  position: relative;
}

.poi-icon::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 8px solid #FF8E8E;
}

.poi-label {
  margin-top: 12px;
  background: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: #2d2d2d;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  white-space: nowrap;
  border: 2px solid #FFD0D0;
}

.poi-time {
  font-size: 10px;
  color: #FF9999;
  margin-top: 4px;
  background: #FFF5F5;
  padding: 2px 8px;
  border-radius: 10px;
}

.legend {
  margin-top: 20px;
  padding: 15px;
  background: #FFF9F5;
  border-radius: 12px;
  border: 1px dashed #FFB5B5;
}

.legend-title {
  font-weight: 600;
  color: #FF6B6B;
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
  color: #666;
}

.legend-line {
  width: 30px;
  height: 3px;
  background: #FFB5B5;
  border-radius: 2px;
}

@media (max-width: 768px) {
  .map-canvas {
    height: 400px;
  }

  .map-title {
    font-size: 22px;
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
