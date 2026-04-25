<template>
  <div ref="mapContainer" class="map-view" :style="{ height: typeof height === 'number' ? `${height}px` : height }">
    <div v-if="loading" class="map-loading">
      <n-spin size="medium" />
      <span class="loading-text">加载地图中...</span>
    </div>
    <div v-if="loadError" class="map-error">
      <n-result status="500" title="地图加载失败" description="请检查网络连接后重试" size="small">
        <template #footer>
          <n-button size="small" @click="initMap">重试</n-button>
        </template>
      </n-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { NSpin, NResult, NButton } from 'naive-ui'
import AMapLoader from '@amap/amap-jsapi-loader'
import type { DayData, POIVisitData } from '../types/itinerary'

interface MarkerInfo {
  marker: any
  poiId: string | number
  poi: POIVisitData
}

interface PolylineInfo {
  polyline: any
  dayNumber: number
}

const props = defineProps<{
  days: DayData[]
  activeDay: number | null
  highlightPoiId: string | number | null
  height?: number | string
}>()

const emit = defineEmits<{
  markerClick: [poiId: string | number]
}>()

const mapContainer = ref<HTMLElement>()
const loading = ref(true)
const loadError = ref(false)

let map: any = null
let AMap: any = null
let markers: MarkerInfo[] = []
let polylines: PolylineInfo[] = []
let infoWindow: any = null

// Day route colors (hex values for AMap)
const DAY_COLORS: Record<number, string> = {
  1: '#3B82F6', // Day 1 blue
  2: '#10B981', // Day 2 green
  3: '#F59E0B', // Day 3 orange
}

// Tier badge colors
const TIER_COLORS: Record<number, string> = {
  1: '#F0A020', // Gold
  2: '#B5A89A', // Silver
  3: '#CD7F32', // Bronze
}

const TIER_SYMBOLS: Record<number, string> = {
  1: '★',
  2: '○',
  3: '◇',
}

async function initMap() {
  loading.value = true
  loadError.value = false

  try {
    // Fetch Amap key from backend
    const keyRes = await fetch('/api/config/amap-key')
    if (!keyRes.ok) throw new Error('Failed to load map config')
    const { key } = await keyRes.json()

    // Load AMap JS API
    AMap = await AMapLoader.load({
      key,
      version: '2.0',
    })

    // Initialize map
    map = new AMap.Map(mapContainer.value, {
      zoom: 13,
      center: [120.1551, 30.2741], // Default to Hangzhou (will be overridden)
    })

    infoWindow = new AMap.InfoWindow({
      offset: new AMap.Pixel(0, -30),
      closeWhenClickMap: true,
    })

    loading.value = false

    // Render markers and polylines
    renderMap()
  } catch (e) {
    console.error('Map init error:', e)
    loadError.value = true
    loading.value = false
  }
}

function createMarkerContent(poi: POIVisitData): string {
  const tier = poi.tier || 2
  const symbol = TIER_SYMBOLS[tier]
  const color = TIER_COLORS[tier]
  
  return `
    <div style="
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: ${color};
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: bold;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      border: 2px solid white;
    ">${symbol}</div>
  `
}

function renderMap() {
  if (!map || !AMap) return

  // Clear existing markers and polylines
  clearMarkersAndPolylines()

  const dayToRender = props.activeDay

  props.days.forEach((day) => {
    // Skip days that don't match the active day (unless activeDay is null)
    if (dayToRender !== null && day.day_number !== dayToRender) return

    const dayColor = DAY_COLORS[day.day_number] || DAY_COLORS[1]
    const poisWithCoords: POIVisitData[] = []

    day.pois.forEach((poi, index) => {
      // Skip POIs without coordinates
      if (poi.latitude == null || poi.longitude == null) return

      poisWithCoords.push(poi)

      // Create marker
      const marker = new AMap.Marker({
        position: [poi.longitude, poi.latitude],
        content: createMarkerContent(poi),
        offset: new AMap.Pixel(-14, -14),
        anchor: 'center',
      })

      // Marker click handler
      marker.on('click', () => {
        // Show info window
        infoWindow.setContent(`<div style="padding: 8px; font-weight: 600;">${poi.name}</div>`)
        infoWindow.open(map, [poi.longitude, poi.latitude])
        
        // Emit marker click event
        emit('markerClick', poi.poi_id || index)
      })

      marker.setMap(map)
      markers.push({ marker, poiId: poi.poi_id || index, poi })
    })

    // Draw polylines between consecutive POIs
    for (let i = 0; i < poisWithCoords.length - 1; i++) {
      const current = poisWithCoords[i]
      const next = poisWithCoords[i + 1]

      const polyline = new AMap.Polyline({
        path: [
          [current.longitude, current.latitude],
          [next.longitude, next.latitude],
        ],
        strokeColor: dayColor,
        strokeWeight: 3,
        strokeOpacity: 0.8,
        strokeDasharray: [10, 5], // Dashed line
        showDir: false,
      })

      polyline.setMap(map)
      polylines.push({ polyline, dayNumber: day.day_number })
    }
  })

  // Auto-fit map to show all markers
  if (markers.length > 0) {
    map.setFitView(
      markers.map((m) => m.marker),
      false,
      [60, 60, 60, 60],
      14
    )
  }
}

function clearMarkersAndPolylines() {
  markers.forEach(({ marker }) => {
    marker.setMap(null)
  })
  polylines.forEach(({ polyline }) => {
    polyline.setMap(null)
  })
  markers = []
  polylines = []
  if (infoWindow) {
    infoWindow.close()
  }
}

// Watch for changes in days or active day
watch(
  () => [props.days, props.activeDay],
  () => {
    nextTick(() => {
      renderMap()
    })
  },
  { deep: true }
)

// Watch for highlightPoiId changes (timeline -> map sync)
watch(
  () => props.highlightPoiId,
  (poiId) => {
    if (!poiId || !map) return
    
    const markerInfo = markers.find((m) => m.poiId === poiId)
    if (markerInfo) {
      const { poi } = markerInfo
      // Pan map to center on this marker
      map.setCenter([poi.longitude, poi.latitude])
      
      // Show info window
      infoWindow.setContent(`<div style="padding: 8px; font-weight: 600;">${poi.name}</div>`)
      infoWindow.open(map, [poi.longitude, poi.latitude])
      
      // Animate marker (bounce effect by toggling offset)
      const marker = markerInfo.marker
      const originalOffset = marker.getOffset()
      marker.setOffset(new AMap.Pixel(originalOffset.x, originalOffset.y - 5))
      setTimeout(() => {
        marker.setOffset(originalOffset)
      }, 200)
    }
  }
)

onMounted(initMap)

onUnmounted(() => {
  clearMarkersAndPolylines()
  if (map) {
    map.destroy()
    map = null
  }
})
</script>

<style scoped>
.map-view {
  position: relative;
  width: 100%;
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-warm-surface);
}

.map-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-warm-text-muted);
  background: var(--color-warm-bg);
}

.loading-text {
  font-size: 14px;
}

.map-error {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: var(--color-warm-bg);
}
</style>
