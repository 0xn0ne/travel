<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// POI category definitions
const categories = [
  { key: '景点', amap: '风景名胜', color: '#FF6B6B' },
  { key: '酒店', amap: '住宿服务', color: '#4ECDC4' },
  { key: '餐厅', amap: '餐饮服务', color: '#FFD166' },
  { key: '购物', amap: '购物服务', color: '#A78BFA' },
]

// State
const mapContainer = ref<HTMLDivElement | null>(null)
const searchCity = ref('上海')
const searchCenter = ref<{ lng: number; lat: number } | null>(null)
const searchRadius = ref(0)
const isDrawing = ref(false)
const hasDrawn = ref(false)
const activeTab = ref('景点')
const poisByCategory = ref<Record<string, any[]>>({})
const loadingCategories = ref<Record<string, boolean>>({})
const selectedPoi = ref<any>(null)
const isSearching = ref(false)
const errorMsg = ref('')
const isShootingMode = ref(false)
const isShooting = ref(false)
const shotTarget = ref<{ x: number; y: number } | null>(null)
const shotResult = ref<any>(null)
const shotMessage = ref('')

// Drawing state
const drawPoints = ref<[number, number][]>([])
const drawPreviewPolyline = ref<any>(null)
const completedPolygon = ref<any>(null)

let map: any = null
let markers: any[] = []
const amapKey = '0333fef34c3215f082bf3098f1ef19b1'

function goBack() {
  router.push('/')
}

const activeCategory = computed(() => categories.find(cat => cat.key === activeTab.value) || categories[0])
const currentPois = computed(() => poisByCategory.value[activeTab.value] || [])
const canShoot = computed(() => currentPois.value.length > 0 && !isShooting.value)

onMounted(() => {
  loadAMap()
})

onUnmounted(() => {
  if (map) map.destroy()
})

function loadAMap() {
  if (typeof window.AMap === 'undefined') {
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${amapKey}&plugin=AMap.PolyEditor`
    script.onload = initMap
    document.head.appendChild(script)
  } else {
    initMap()
  }
}

function initMap() {
  if (!mapContainer.value) return
  map = new window.AMap.Map(mapContainer.value, {
    zoom: 12,
    center: [121.4737, 31.2304],
    mapStyle: 'amap://styles/whitesmoke',
  })
}

// ===== Drawing =====

function startDraw() {
  if (!map) return
  clearAll()
  isDrawing.value = true
  errorMsg.value = ''
  drawPoints.value = []
  map.setStatus({ dragEnable: false, touchZoomCenter: false })
  map.on('click', onMapClickForDraw)
}

function onMapClickForDraw(e: any) {
  drawPoints.value.push([e.lnglat.lng, e.lnglat.lat])
  updatePreview()
}

function updatePreview() {
  if (drawPreviewPolyline.value) { map.remove(drawPreviewPolyline.value); drawPreviewPolyline.value = null }
  if (drawPoints.value.length === 0) return
  const pts = drawPoints.value
  // Draw a closed preview: all points + dashed line from last back to first
  const path = [...pts, pts[0]]
  drawPreviewPolyline.value = new window.AMap.Polyline({
    path,
    strokeColor: '#6C8CD5',
    strokeWeight: 2,
    strokeOpacity: 0.7,
    zIndex: 199,
  })
  drawPreviewPolyline.value.setMap(map)
}

function finishDraw() {
  if (!isDrawing.value) return
  if (drawPoints.value.length < 3) {
    errorMsg.value = '请至少点击3个点绘制区域'
    return
  }
  map.off('click', onMapClickForDraw)
  map.setStatus({ dragEnable: true, touchZoomCenter: true })

  // Remove preview
  if (drawPreviewPolyline.value) { map.remove(drawPreviewPolyline.value); drawPreviewPolyline.value = null }

  const pts = drawPoints.value
  const thinned = pts.filter((_, i) => i % 4 === 0 || i === pts.length - 1)
  const first = thinned[0]
  const last = thinned[thinned.length - 1]
  // Smooth only the interior points
  const interior = thinned.length > 2 ? thinned.slice(1, -1) : []
  const smoothed = interior.length > 1 ? chaikinSmooth(interior, 3) : []
  const closed: [number, number][] = [first, ...smoothed, last]

  // Blue shadow fill polygon
  if (completedPolygon.value) map.remove(completedPolygon.value)
  completedPolygon.value = new window.AMap.Polygon({
    path: closed,
    strokeColor: '#6C8CD5',
    strokeWeight: 2,
    fillColor: '#6C8CD5',
    fillOpacity: 0.12,
    zIndex: 198,
  })
  completedPolygon.value.setMap(map)

  // Compute bounding box
  const lngs = closed.map(p => p[0])
  const lats = closed.map(p => p[1])
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs)
  const minLat = Math.min(...lats), maxLat = Math.max(...lats)
  searchCenter.value = { lng: (minLng + maxLng) / 2, lat: (minLat + maxLat) / 2 }
  const dx = (maxLng - minLng) * 111320 * Math.cos((searchCenter.value.lat * Math.PI) / 180)
  const dy = (maxLat - minLat) * 111320
  searchRadius.value = Math.sqrt(dx * dx + dy * dy) * 1.2 * 1000

  drawPoints.value = closed
  hasDrawn.value = true
  isDrawing.value = false
}

function clearAll() {
  if (drawPreviewPolyline.value) { map.remove(drawPreviewPolyline.value); drawPreviewPolyline.value = null }
  if (completedPolygon.value) { map.remove(completedPolygon.value); completedPolygon.value = null }
  drawPoints.value = []
  clearMarkers()
  searchCenter.value = null
  searchRadius.value = 0
  hasDrawn.value = false
  isDrawing.value = false
  resetShooting()
  map.setStatus({ dragEnable: true, touchZoomCenter: true })
  map.off('click', onMapClickForDraw)
}

function clearMarkers() {
  markers.forEach(m => map.remove(m))
  markers = []
}

// ===== POI Search =====

function chaikinSmooth(pts: [number, number][], iterations: number = 2): [number, number][] {
  let result = pts
  for (let k = 0; k < iterations; k++) {
    const next: [number, number][] = []
    for (let i = 0; i < result.length - 1; i++) {
      const [x0, y0] = result[i]
      const [x1, y1] = result[i + 1]
      next.push([x0 * 0.75 + x1 * 0.25, y0 * 0.75 + y1 * 0.25])
      next.push([x0 * 0.25 + x1 * 0.75, y0 * 0.25 + y1 * 0.75])
    }
    result = next
  }
  return result
}

function isPointInPolygon(point: [number, number], polygon: [number, number][]): boolean {
  const [x, y] = point
  let inside = false
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i]
    const [xj, yj] = polygon[j]
    if (((yi > y) !== (yj > y)) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
      inside = !inside
    }
  }
  return inside
}

async function searchPoi(category: { key: string; amap: string; color: string }) {
  if (!searchCenter.value || !searchRadius.value) return
  loadingCategories.value[category.key] = true
  poisByCategory.value[category.key] = []

  const requestBody = {
    keywords: category.amap,
    city: searchCity.value,
    location: `${searchCenter.value.lng},${searchCenter.value.lat}`,
    radius: Math.round(searchRadius.value),
    pageSize: 50,
    pageNum: 1,
  }

  try {
    const res = await fetch('/api/poi/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })
    const data = await res.json()
    if (data.pois) {
      const polygonPath = drawPoints.value
      const filtered = data.pois.filter((poi: any) => {
        if (!poi.location) return false
        const [lng, lat] = poi.location.split(',').map(Number)
        return isPointInPolygon([lng, lat], polygonPath)
      })
      poisByCategory.value[category.key] = filtered
      addMarkers(filtered, category.color)
    }
  } catch {
    errorMsg.value = '搜索失败，请重试'
  } finally {
    loadingCategories.value[category.key] = false
  }
}

function addMarkers(pois: any[], color: string) {
  if (!map) return
  pois.forEach((poi: any) => {
    if (!poi.location) return
    const [lng, lat] = poi.location.split(',').map(Number)
    const marker = new window.AMap.Marker({
      position: [lng, lat],
      icon: new window.AMap.Icon({
        size: new window.AMap.Size(28, 34),
        image: `data:image/svg+xml;base64,${btoa(`<svg xmlns='http://www.w3.org/2000/svg' width='28' height='34' viewBox='0 0 28 34'><path d='M14 0C6.27 0 0 6.27 0 14c0 10.5 14 20 14 20s14-9.5 14-20C28 6.27 21.73 0 14 0z' fill='${encodeURIComponent(color)}'/><circle cx='14' cy='14' r='6' fill='white'/></svg>`)}`,
        imageSize: new window.AMap.Size(28, 34),
      }),
      title: poi.name,
      extData: poi,
    })
    marker.on('click', () => { selectedPoi.value = poi })
    map.add(marker)
    markers.push(marker)
  })
  map.setFitView(markers)
}

function resetShooting() {
  isShootingMode.value = false
  isShooting.value = false
  shotTarget.value = null
  shotResult.value = null
  shotMessage.value = ''
}

function enterShootingMode() {
  if (currentPois.value.length === 0) {
    shotMessage.value = `请先搜索${activeTab.value}`
    return
  }
  isShootingMode.value = true
  shotResult.value = null
  shotTarget.value = null
  shotMessage.value = `瞄准${activeTab.value}，点击靶心随机开枪`
}

function shootRandomPoi() {
  if (!canShoot.value) return
  isShooting.value = true
  shotResult.value = null
  shotTarget.value = {
    x: 18 + Math.random() * 64,
    y: 18 + Math.random() * 54,
  }
  shotMessage.value = '子弹飞行中...'

  window.setTimeout(() => {
    const pois = currentPois.value
    const picked = pois[Math.floor(Math.random() * pois.length)]
    shotResult.value = picked
    selectedPoi.value = picked
    isShooting.value = false
    shotMessage.value = `命中：${picked.name}`
    focusPoi(picked)
  }, 850)
}

function focusPoi(poi: any) {
  if (!map || !poi?.location) return
  const [lng, lat] = poi.location.split(',').map(Number)
  map.setZoomAndCenter(Math.max(map.getZoom?.() || 14, 15), [lng, lat])
}

function switchTab(cat: string) {
  activeTab.value = cat
  resetShooting()
}

function handleSearchAll() {
  if (!hasDrawn.value) {
    errorMsg.value = '请先在地图上绘制范围'
    return
  }
  resetShooting()
  isSearching.value = true
  errorMsg.value = ''
  categories.forEach((cat, i) => {
    setTimeout(() => searchPoi(cat), i * 300)
  })
  setTimeout(() => { isSearching.value = false }, categories.length * 300 + 500)
}
</script>

<template>
  <div class="pmap-view">
    <!-- Header -->
    <div class="pmap-header">
      <button class="pmap-back" @click="goBack">← 返回</button>
      <div class="pmap-title">即兴玩家P人</div>
      <div class="pmap-city">
        <input v-model="searchCity" class="pmap-city-input" placeholder="输入城市" />
      </div>
    </div>

    <div class="pmap-body">
      <!-- Sidebar -->
      <div class="pmap-sidebar">
        <!-- Draw controls -->
        <div class="pmap-draw-section">
          <p class="pmap-hint">在地图上点击多个点绘制自由区域</p>
          <div class="pmap-draw-btns">
            <button class="pmap-btn pmap-btn-primary" @click="startDraw" :disabled="isDrawing">
              {{ isDrawing ? '绘制中...' : '绘制范围' }}
            </button>
            <button class="pmap-btn pmap-btn-finish" @click="finishDraw" :disabled="!isDrawing">
              完成
            </button>
            <button class="pmap-btn pmap-btn-secondary" @click="clearAll" :disabled="!hasDrawn && !isDrawing">
              清除
            </button>
          </div>
          <div v-if="isDrawing && drawPoints.length > 0" class="pmap-draw-hint">
            已点击 {{ drawPoints.length }} 个点{{ drawPoints.length < 3 ? '（至少3个点）' : '，点击"完成"结束绘制' }}
          </div>
          <div v-if="hasDrawn && searchCenter" class="pmap-range-info">
            已绘制 {{ drawPoints.length }} 个顶点的区域
          </div>
        </div>

        <!-- Search all -->
        <button class="pmap-btn pmap-btn-search" @click="handleSearchAll" :disabled="!hasDrawn || isSearching">
          {{ isSearching ? '搜索中...' : '搜索所有类别' }}
        </button>

        <div v-if="errorMsg" class="pmap-error">{{ errorMsg }}</div>

        <div class="pmap-shoot-panel">
          <div>
            <div class="pmap-shoot-title">随机射击模式</div>
            <div class="pmap-shoot-sub">当前分类：{{ activeTab }} · {{ currentPois.length }} 个地点</div>
          </div>
          <button class="pmap-btn pmap-btn-shoot" @click="enterShootingMode" :disabled="currentPois.length === 0 || isShooting">
            {{ isShootingMode ? '重新瞄准' : `射击选${activeTab}` }}
          </button>
          <div v-if="shotMessage" class="pmap-shoot-msg">{{ shotMessage }}</div>
          <div v-if="shotResult" class="pmap-shot-result" @click="selectedPoi = shotResult">
            <span>这次去</span>
            <strong>{{ shotResult.name }}</strong>
          </div>
        </div>

        <!-- Category tabs -->
        <div class="pmap-tabs">
          <button
            v-for="cat in categories"
            :key="cat.key"
            class="pmap-tab"
            :class="{ active: activeTab === cat.key }"
            :style="{ '--cat-color': cat.color }"
            @click="switchTab(cat.key)"
          >
            {{ cat.key }}
            <span class="pmap-tab-count">{{ (poisByCategory[cat.key] || []).length }}</span>
          </button>
        </div>

        <!-- POI list -->
        <div class="pmap-list">
          <div v-if="loadingCategories[activeTab]" class="pmap-loading">加载中...</div>
          <div v-else-if="currentPois.length === 0" class="pmap-empty">暂无数据，请先绘制范围并搜索</div>
          <div
            v-for="poi in currentPois"
            :key="poi.id"
            class="pmap-item"
            :class="{ selected: selectedPoi?.id === poi.id }"
            @click="selectedPoi = poi"
          >
            <div class="pmap-item-name">{{ poi.name }}</div>
            <div class="pmap-item-addr">{{ poi.address || '地址未知' }}</div>
            <div class="pmap-item-score" v-if="poi.biz_ext?.rating">
              ⭐ {{ poi.biz_ext.rating }}
            </div>
          </div>
        </div>
      </div>

      <!-- Map -->
      <div class="pmap-map-wrap">
        <div ref="mapContainer" class="pmap-map"></div>

        <div v-if="isShootingMode" class="pmap-shoot-overlay">
          <div class="pmap-shoot-card">
            <div class="pmap-shoot-kicker">P 人命运枪</div>
            <div class="pmap-shoot-heading">对 {{ activeTab }} 开一枪</div>
            <div class="pmap-target" :style="{ '--cat-color': activeCategory.color }" @click="shootRandomPoi">
              <div class="pmap-target-ring ring-1"></div>
              <div class="pmap-target-ring ring-2"></div>
              <div class="pmap-target-ring ring-3"></div>
              <div class="pmap-crosshair"></div>
              <div
                v-if="shotTarget"
                class="pmap-bullet-hole"
                :class="{ fire: isShooting }"
                :style="{ left: `${shotTarget.x}%`, top: `${shotTarget.y}%` }"
              ></div>
            </div>
            <button class="pmap-trigger" @click="shootRandomPoi" :disabled="!canShoot">
              {{ isShooting ? '砰！' : '开枪随机选一个' }}
            </button>
            <div class="pmap-overlay-msg">{{ shotMessage || `从 ${currentPois.length} 个${activeTab}里随机命中一个` }}</div>
          </div>
        </div>

        <!-- POI detail card -->
        <div v-if="selectedPoi" class="pmap-detail">
          <div class="pmap-detail-name">{{ selectedPoi.name }}</div>
          <div class="pmap-detail-score" v-if="selectedPoi.biz_ext?.rating">
            评分：⭐ {{ selectedPoi.biz_ext.rating }}
          </div>
          <div class="pmap-detail-addr">{{ selectedPoi.address || '地址未知' }}</div>
          <div class="pmap-detail-type" v-if="selectedPoi.type">{{ selectedPoi.type }}</div>
          <button class="pmap-btn-close" @click="selectedPoi = null">×</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pmap-view {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  background-color: var(--bg-main);
  font-family: var(--font-ui-rounded);
}

.pmap-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(108, 140, 213, 0.15);
}

.pmap-back {
  background: none;
  border: none;
  font-size: 16px;
  color: var(--type-muted);
  cursor: pointer;
  font-family: var(--font-ui-rounded);
  padding: 6px 12px;
  border-radius: 999px;
  transition: background 0.2s;
}

.pmap-back:hover {
  background: rgba(108, 140, 213, 0.1);
}

.pmap-title {
  font-size: 20px;
  font-weight: 400;
  color: var(--type-title);
  letter-spacing: 0.04em;
}

.pmap-city {
  margin-left: auto;
}

.pmap-city-input {
  background: var(--paper-2);
  border: none;
  border-radius: 18px;
  padding: 8px 16px;
  font-size: 14px;
  color: var(--type-body);
  font-family: var(--font-ui-rounded);
  outline: none;
  width: 120px;
}

.pmap-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.pmap-sidebar {
  width: 320px;
  min-width: 320px;
  background: rgba(255, 255, 255, 0.90);
  backdrop-filter: blur(12px);
  border-radius: 24px 0 0 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  overflow-y: auto;
}

.pmap-draw-section {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 18px;
  padding: 14px;
}

.pmap-hint {
  font-size: 13px;
  color: var(--type-muted);
  margin: 0 0 10px;
  line-height: 1.5;
}

.pmap-draw-btns {
  display: flex;
  gap: 8px;
}

.pmap-btn {
  flex: 1;
  border: none;
  border-radius: 14px;
  padding: 9px 0;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-ui-rounded);
  transition: opacity 0.2s;
}

.pmap-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pmap-btn-primary {
  background: var(--accent-orange);
  color: #fff;
}

.pmap-btn-finish {
  background: #6C8CD5;
  color: #fff;
}

.pmap-btn-secondary {
  background: var(--paper-2);
  color: var(--type-body);
}

.pmap-btn-search {
  background: #6C8CD5;
  color: #fff;
  border-radius: 14px;
  padding: 11px 0;
  font-size: 15px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  font-family: var(--font-ui-rounded);
  transition: opacity 0.2s;
}

.pmap-btn-search:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pmap-shoot-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(232, 241, 255, 0.9));
  border: 1px solid rgba(108, 140, 213, 0.15);
  border-radius: 18px;
  padding: 14px;
}

.pmap-shoot-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--type-title);
}

.pmap-shoot-sub,
.pmap-shoot-msg {
  font-size: 12px;
  color: var(--type-muted);
  margin-top: 4px;
}

.pmap-btn-shoot {
  background: #111827;
  color: #fff;
  width: 100%;
}

.pmap-shot-result {
  display: flex;
  flex-direction: column;
  gap: 3px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 14px;
  padding: 10px 12px;
  cursor: pointer;
}

.pmap-shot-result span {
  font-size: 11px;
  color: var(--type-muted);
}

.pmap-shot-result strong {
  font-size: 14px;
  color: var(--type-title);
}

.pmap-draw-hint {
  margin-top: 10px;
  font-size: 12px;
  color: #6C8CD5;
  font-weight: 600;
  text-align: center;
}

.pmap-range-info {
  margin-top: 10px;
  font-size: 11px;
  color: var(--type-muted);
  line-height: 1.6;
}

.pmap-error {
  font-size: 13px;
  color: var(--type-body);
  background: rgba(243, 154, 168, 0.15);
  border-radius: 10px;
  padding: 8px 12px;
}

.pmap-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pmap-tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 999px;
  border: none;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.85);
  color: var(--type-muted);
  font-family: var(--font-ui-rounded);
  transition: all 0.2s;
}

.pmap-tab.active {
  background: var(--cat-color);
  color: #fff;
}

.pmap-tab-count {
  background: rgba(0,0,0,0.1);
  border-radius: 999px;
  padding: 1px 6px;
  font-size: 10px;
}

.pmap-tab.active .pmap-tab-count {
  background: rgba(255,255,255,0.25);
}

.pmap-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pmap-loading,
.pmap-empty {
  font-size: 13px;
  color: var(--type-muted);
  text-align: center;
  padding: 20px 0;
}

.pmap-item {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.pmap-item:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateX(2px);
}

.pmap-item.selected {
  border-color: #6C8CD5;
  background: rgba(232, 241, 255, 0.9);
}

.pmap-item-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--type-title);
  margin-bottom: 4px;
}

.pmap-item-addr {
  font-size: 12px;
  color: var(--type-muted);
  line-height: 1.4;
}

.pmap-item-score {
  font-size: 12px;
  color: var(--type-body);
  margin-top: 4px;
}

.pmap-map-wrap {
  flex: 1;
  position: relative;
}

.pmap-map {
  width: 100%;
  height: 100%;
}

.pmap-shoot-overlay {
  position: absolute;
  inset: 0;
  z-index: 8;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.pmap-shoot-card {
  width: 300px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(14px);
  border-radius: 28px;
  padding: 22px;
  box-shadow: 0 18px 48px rgba(17, 24, 39, 0.16);
  text-align: center;
  pointer-events: auto;
}

.pmap-shoot-kicker {
  font-size: 12px;
  letter-spacing: 0.14em;
  color: var(--type-muted);
  margin-bottom: 5px;
}

.pmap-shoot-heading {
  font-size: 22px;
  font-weight: 900;
  color: var(--type-title);
  margin-bottom: 16px;
}

.pmap-target {
  position: relative;
  width: 190px;
  height: 190px;
  margin: 0 auto 16px;
  border-radius: 50%;
  background: radial-gradient(circle, #fff 0 13%, var(--cat-color) 14% 28%, #fff 29% 43%, var(--cat-color) 44% 59%, #fff 60% 100%);
  box-shadow: inset 0 0 0 2px rgba(17, 24, 39, 0.08), 0 12px 30px rgba(17, 24, 39, 0.14);
  cursor: crosshair;
}

.pmap-target-ring,
.pmap-crosshair {
  position: absolute;
  inset: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
}

.pmap-crosshair::before,
.pmap-crosshair::after {
  content: '';
  position: absolute;
  background: rgba(17, 24, 39, 0.55);
}

.pmap-crosshair::before {
  width: 120px;
  height: 1px;
  left: -60px;
  top: 0;
}

.pmap-crosshair::after {
  width: 1px;
  height: 120px;
  left: 0;
  top: -60px;
}

.pmap-bullet-hole {
  position: absolute;
  width: 16px;
  height: 16px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: #111827;
  box-shadow: 0 0 0 6px rgba(17, 24, 39, 0.12);
}

.pmap-bullet-hole.fire {
  animation: pmap-pop 0.45s ease-out;
}

.pmap-trigger {
  width: 100%;
  border: none;
  border-radius: 999px;
  padding: 12px 16px;
  background: #111827;
  color: #fff;
  font-size: 15px;
  font-weight: 900;
  font-family: var(--font-ui-rounded);
  cursor: pointer;
}

.pmap-trigger:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.pmap-overlay-msg {
  min-height: 18px;
  margin-top: 10px;
  font-size: 13px;
  color: var(--type-muted);
}

@keyframes pmap-pop {
  0% { transform: translate(-50%, -50%) scale(0.2); opacity: 0; }
  70% { transform: translate(-50%, -50%) scale(1.25); opacity: 1; }
  100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
}

.pmap-detail {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 260px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 18px;
  box-shadow: 0 8px 24px rgba(108, 140, 213, 0.15);
  z-index: 10;
}

.pmap-detail-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--type-title);
  margin-bottom: 6px;
}

.pmap-detail-score {
  font-size: 13px;
  color: var(--type-body);
  margin-bottom: 4px;
}

.pmap-detail-addr {
  font-size: 12px;
  color: var(--type-muted);
  line-height: 1.5;
  margin-bottom: 4px;
}

.pmap-detail-type {
  font-size: 11px;
  color: var(--type-muted);
  background: var(--paper-2);
  border-radius: 999px;
  padding: 3px 10px;
  display: inline-block;
  margin-top: 6px;
}

.pmap-btn-close {
  position: absolute;
  top: 10px;
  right: 12px;
  background: none;
  border: none;
  font-size: 18px;
  color: var(--type-muted);
  cursor: pointer;
  line-height: 1;
}
</style>
