<template>
  <div class="home-view">
    <div class="split-layout">
      <!-- LEFT PANEL - Preference Selection -->
      <div class="left-panel">
        <div class="left-scroll">
          <!-- Brand -->
          <div class="panel-brand">
            <h1 class="brand-title">拾途</h1>
            <p class="brand-subtitle">像本地朋友一样帮你规划旅行</p>
          </div>

          <!-- ① 地点 -->
          <div class="section-label">想去哪儿</div>
          <div class="pref-card">
            <div class="location-input-row">
              <input
                v-model="locationInput"
                class="location-input"
                placeholder="输入地点，如：上海"
                @keydown.enter.prevent="addLocation"
              />
              <button class="add-location-btn" @click="addLocation">添加</button>
            </div>
            <div class="location-tags" v-if="locations.length > 0">
              <span
                v-for="loc in locations"
                :key="loc"
                class="location-tag"
              >
                {{ loc }}
                <span class="location-remove" @click="removeLocation(loc)">×</span>
              </span>
            </div>
            <div class="location-hint" v-if="locations.length === 0">
              输入地点后按回车或点击「添加」，可添加多个目的地
            </div>
          </div>

          <!-- ② 行程日期 -->
          <div class="section-label">行程日期</div>
          <div class="pref-card">
            <div class="date-range-picker">
              <n-date-picker
                v-model:value="dateRange"
                type="daterange"
                clearable
                :is-date-disabled="isDateDisabled"
                placeholder="选择出发和返回日期"
                start-placeholder="出发日期"
                end-placeholder="返回日期"
                format="MM月dd日"
                style="width: 100%"
                :locale="zhCN"
                @update:value="onDateRangeChange"
              />
            </div>
            <div v-if="tripDays > 0" class="trip-days-badge">
              共 {{ tripDays }} 天
            </div>

            <!-- 天气预告 -->
            <div v-if="weatherLoading" class="weather-loading">
              <span class="weather-spinner"></span>
              <span>正在获取天气...</span>
            </div>
            <div v-else-if="weatherData.length > 0" class="weather-section">
              <div class="weather-header">
                <span class="weather-title">🌤️ 行程天气</span>
                <span class="weather-city">{{ dateRangeCity }}</span>
              </div>
              <div class="weather-days">
                <div
                  v-for="(day, idx) in weatherData"
                  :key="idx"
                  class="weather-day-card"
                >
                  <div class="weather-date">{{ day.date }}</div>
                  <div class="weather-icon">{{ day.icon }}</div>
                  <div class="weather-temp">{{ day.tempMax }}° / {{ day.tempMin }}°</div>
                  <div class="weather-desc">{{ day.desc }}</div>
                </div>
              </div>
            </div>
            <div v-else-if="dateRange && !weatherLoading" class="weather-empty">
              选择地点后可查看天气预报
            </div>
          </div>

          <!-- ③ 旅行偏好 -->
          <div class="section-label">旅行偏好</div>
          <div class="pref-card">
            <div class="pref-sub-label">人流偏好</div>
            <div class="tag-container" style="margin-bottom: 12px;">
              <span
                v-for="c in crowdPrefs"
                :key="c.value"
                class="tag teal"
                :class="{ selected: selectedCrowd === c.value }"
                @click="selectedCrowd = c.value"
              >{{ c.label }}</span>
            </div>

            <div class="pref-sub-label">旅行风格（可多选）</div>
            <div class="tag-container">
              <span
                v-for="t in sortedStyles"
                :key="t.value"
                class="tag"
                :class="{ selected: selectedStyles.includes(t.value) }"
                @click="toggleTag(selectedStyles, t.value)"
              >{{ t.label }}</span>
            </div>
          </div>

          <!-- ④ 预算区间 -->
          <div class="section-label">人均预算</div>
          <div class="pref-card">
            <div class="tag-container">
              <span
                v-for="b in budgets"
                :key="b.value"
                class="tag amber"
                :class="{ selected: selectedBudget === b.value }"
                @click="selectedBudget = b.value"
              >{{ b.label }}</span>
            </div>
          </div>

          <!-- ⑤ 补充信息 -->
          <div class="section-label">补充信息</div>
          <div class="pref-card">
            <textarea
              v-model="extraInfo"
              class="custom-input"
              placeholder="还有什么想告诉我们的？
比如：带老人/小孩、有宠物、想拍照出片、不能走太多路……"
              rows="3"
            ></textarea>
          </div>

          <!-- 发起规划 -->
          <button
            class="generate-btn"
            :disabled="store.isGenerating || locations.length === 0"
            @click="handleGenerate"
          >
            <span v-if="store.isGenerating" class="btn-loading">✦</span>
            ⚡ 开始规划
          </button>

          <div class="generate-hint" v-if="locations.length === 0">
            请先添加至少一个目的地
          </div>
        </div>
      </div>

      <!-- RIGHT PANEL - Content -->
      <div class="right-panel">
        <!-- Step Bar -->
        <div class="step-bar">
          <div class="step" :class="{ active: currentStep === 1, done: currentStep > 1 }">
            <span class="step-num">①</span> 填写偏好
          </div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: currentStep === 2, done: currentStep > 2 }">
            <span class="step-num">②</span> 生成行程
          </div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: currentStep === 3 }">
            <span class="step-num">③</span> 查看结果
          </div>
        </div>

        <div class="right-scroll">
          <!-- Empty State Hint -->
          <div v-if="!store.isGenerating && store.stage === 'idle' && !store.currentItinerary?.days" class="empty-hint">
            <div class="empty-icon">🗺️</div>
            <p class="empty-title">告诉我想去哪儿</p>
            <p class="empty-sub">在左侧添加目的地和偏好，AI 为你生成专属行程</p>
            <div class="empty-examples">
              <span class="example-chip" @click="fillLocation('上海')">上海</span>
              <span class="example-chip" @click="fillLocation('成都')">成都</span>
              <span class="example-chip" @click="fillLocation('杭州')">杭州</span>
              <span class="example-chip" @click="fillLocation('北京')">北京</span>
              <span class="example-chip" @click="fillLocation('大理')">大理</span>
              <span class="example-chip" @click="fillLocation('大阪')">大阪</span>
            </div>
          </div>

          <!-- Stage Progress -->
          <StageProgress
            v-if="store.isGenerating || store.stage !== 'idle'"
            :current-stage="store.stage"
            :message="store.stageMessage"
          />

          <!-- Itinerary Timeline -->
          <ItineraryTimeline v-if="store.currentItinerary?.days" :days="(store.currentItinerary as any).days" />

          <!-- Error Banner -->
          <div v-if="store.error" class="error-banner">
            <n-alert type="warning" :title="store.error" />
            <n-button size="small" type="primary" style="margin-top: 8px" @click="handleRetry">重试</n-button>
          </div>
        </div>

        <!-- Chat Input Bar -->
        <div class="chat-input-bar">
          <div class="chat-input-inner">
            <n-input
              v-model:value="chatInput"
              type="textarea"
              placeholder="想调整行程？比如「换个更有氛围的」「少走一点路」"
              :autosize="{ minRows: 1, maxRows: 3 }"
              @keydown.enter.exact.prevent="handleChatSend"
            />
            <button class="chat-send-btn" @click="handleChatSend" :disabled="!chatInput.trim()">
              ↑
            </button>
          </div>
          <div class="chat-hints">
            <span class="hint-chip" @click="fillChatHint(0)">🍽️ 换个地方吃饭</span>
            <span class="hint-chip" @click="fillChatHint(1)">📍 不想去这里了</span>
            <span class="hint-chip" @click="fillChatHint(2)">☀️ 加一个上午行程</span>
            <span class="hint-chip" @click="fillChatHint(3)">🚶 轻松一点</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { NInput, NButton, NAlert, NDatePicker, zhCN } from 'naive-ui'
import { useItineraryStore } from '../stores/itinerary'
import StageProgress from '../components/StageProgress.vue'
import ItineraryTimeline from '../components/ItineraryTimeline.vue'

const store = useItineraryStore()
const router = useRouter()
const chatInput = ref('')
const currentStep = ref(1)

// --- 地点 ---
const locationInput = ref('')
const locations = ref<string[]>([])

function addLocation() {
  const val = locationInput.value.trim()
  if (val && !locations.value.includes(val)) {
    locations.value.push(val)
    locationInput.value = ''
  }
}

function removeLocation(loc: string) {
  locations.value = locations.value.filter(l => l !== loc)
}

function fillLocation(loc: string) {
  if (!locations.value.includes(loc)) {
    locations.value.push(loc)
  }
}

// --- 行程日期 ---
const dateRange = ref<[number, number] | null>(null)
const weatherData = ref<any[]>([])
const weatherLoading = ref(false)
const dateRangeCity = ref('')

const tripDays = computed(() => {
  if (!dateRange.value) return 0
  const [start, end] = dateRange.value
  return Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
})

function isDateDisabled(timestamp: number) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return timestamp < today.getTime()
}

async function onDateRangeChange(val: [number, number] | null) {
  dateRange.value = val
  weatherData.value = []
  if (val && locations.value.length > 0) {
    await fetchWeather()
  }
}

// 城市中文名到坐标的映射
const CITY_COORDS: Record<string, [number, number]> = {
  '上海': [31.2304, 121.4737],
  '北京': [39.9042, 116.4074],
  '杭州': [30.2741, 120.1551],
  '成都': [30.5728, 104.0668],
  '深圳': [22.5431, 114.0579],
  '广州': [23.1291, 113.2644],
  '南京': [32.0603, 118.7969],
  '西安': [34.3416, 108.9398],
  '苏州': [31.2989, 120.5853],
  '重庆': [29.4316, 106.9123],
  '厦门': [24.4798, 118.0894],
  '青岛': [36.0671, 120.3826],
  '长沙': [28.2282, 112.9388],
  '武汉': [30.5928, 114.3055],
  '天津': [39.3434, 117.3616],
  '大连': [38.9144, 121.6147],
  '哈尔滨': [45.8038, 126.5340],
  '郑州': [34.7466, 113.6253],
  '济南': [36.6512, 117.1205],
  '昆明': [25.0406, 102.7129],
  '大理': [25.6069, 100.2676],
  '丽江': [26.8721, 100.2299],
  '三亚': [18.2528, 109.5119],
  '大阪': [34.6937, 135.5023],
  '京都': [35.0116, 135.7681],
  '东京': [35.6762, 139.6503],
  '曼谷': [13.7563, 100.5018],
  '首尔': [37.5665, 126.9780],
  '巴黎': [48.8566, 2.3522],
  '伦敦': [51.5074, -0.1278],
  '纽约': [40.7128, -74.0060],
}

function getWeatherIcon(code: number): string {
  if (code === 0) return '☀️'
  if (code <= 3) return '⛅'
  if (code <= 49) return '🌫️'
  if (code <= 59) return '🌦️'
  if (code <= 69) return '🌧️'
  if (code <= 79) return '❄️'
  if (code <= 99) return '⛈️'
  return '🌡️'
}

function getWeatherDesc(code: number): string {
  if (code === 0) return '晴'
  if (code === 1) return '大致晴朗'
  if (code === 2) return '局部多云'
  if (code === 3) return '阴天'
  if (code <= 49) return '雾'
  if (code <= 59) return '毛毛雨'
  if (code <= 69) return '降雨'
  if (code <= 79) return '降雪'
  if (code <= 99) return '雷暴'
  return '天气'
}

async function fetchWeather() {
  if (!dateRange.value || locations.value.length === 0) return

  weatherLoading.value = true
  const [start, end] = dateRange.value

  // 优先用第一个城市
  const city = locations.value[0]
  dateRangeCity.value = city

  // 找坐标
  let lat = CITY_COORDS[city]?.[0]
  let lon = CITY_COORDS[city]?.[1]

  // 如果没有预存坐标，尝试用 geocoding API 获取
  if (!lat) {
    try {
      const geoRes = await fetch(
        `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1`
      )
      const geoData = await geoRes.json()
      if (geoData.results?.[0]) {
        lat = geoData.results[0].latitude
        lon = geoData.results[0].longitude
      }
    } catch {}
  }

  if (!lat || !lon) {
    weatherLoading.value = false
    return
  }

  // Open-Meteo 天气 API
  const startDate = new Date(start).toISOString().split('T')[0]
  const endDate = new Date(end).toISOString().split('T')[0]

  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=weather_code,temperature_2m_max,temperature_2m_min&start_date=${startDate}&end_date=${endDate}&timezone=Asia%2FShanghai`
    const resp = await fetch(url)
    const data = await resp.json()

    if (data.daily) {
      const days = data.daily
      weatherData.value = days.time.map((date: string, i: number) => {
        const d = new Date(date)
        const month = d.getMonth() + 1
        const day = d.getDate()
        const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
        return {
          date: `${month}/${day} ${weekday}`,
          icon: getWeatherIcon(days.weather_code[i]),
          tempMax: Math.round(days.temperature_2m_max[i]),
          tempMin: Math.round(days.temperature_2m_min[i]),
          desc: getWeatherDesc(days.weather_code[i]),
        }
      })
    }
  } catch (e) {
    console.error('天气获取失败', e)
  }

  weatherLoading.value = false
}

// --- 喜好偏好 ---
const travelStyles = [
  { value: 'food_shopping', label: '🛍️ 美食购物' },
  { value: 'nature', label: '🌿 自然风光' },
  { value: 'culture', label: '🏛️ 历史人文' },
  { value: 'landmark', label: '📍 经典打卡' },
  { value: 'hidden', label: '💎 宝藏小店' },
  { value: 'art', label: '🎨 艺术展览' },
  { value: 'photo', label: '📸 拍照打卡' },
  { value: 'romantic', label: '🎠 约会浪漫' },
  { value: 'local', label: '🗺️ 本地人推荐' },
  { value: 'cafe', label: '☕ 咖啡下午茶' },
  { value: 'senior', label: '🧓 长辈出行' },
]

// 按字数排序：4字在前，5字在后
const sortedStyles = computed(() =>
  [...travelStyles].sort((a, b) => {
    const ca = a.label.replace(/[^\u4e00-\u9fa5]/g, '').length
    const cb = b.label.replace(/[^\u4e00-\u9fa5]/g, '').length
    return ca - cb
  })
)
const selectedStyles = ref<string[]>(['food_shopping', 'culture'])

const crowdPrefs = [
  { value: 'quiet', label: '🌿 人少清静' },
  { value: 'moderate', label: '🎵 热闹适中' },
  { value: 'lively', label: '🔥 人山人海' },
]
const selectedCrowd = ref('moderate')

// --- 预算区间 ---
const budgets = [
  { value: 'low', label: '💰 50以下' },
  { value: 'avg', label: '💰 50-200' },
  { value: 'high', label: '💎 200-500' },
  { value: 'luxury', label: '👑 500+' },
]
const selectedBudget = ref('avg')

// --- 补充信息 ---
const extraInfo = ref('')

// --- 工具函数 ---
function toggleTag(arr: string[], val: string) {
  const idx = arr.indexOf(val)
  if (idx === -1) arr.push(val)
  else arr.splice(idx, 1)
}

// --- 生成行程 ---
const canGenerate = computed(() => locations.value.length > 0 && !store.isGenerating)

async function handleGenerate() {
  if (!canGenerate.value) return
  currentStep.value = 2

  // 拼接用户输入
  const styleLabels = travelStyles.filter(t => selectedStyles.value.includes(t.value)).map(t => t.label).join('、')
  const crowdLabel = crowdPrefs.find(c => c.value === selectedCrowd.value)?.label || ''
  const budgetLabel = budgets.find(b => b.value === selectedBudget.value)?.label || ''

  // 日期范围
  let durationStr = ''
  if (dateRange.value) {
    const [start, end] = dateRange.value
    const fmt = (ts: number) => {
      const d = new Date(ts)
      return `${d.getMonth() + 1}月${d.getDate()}日`
    }
    durationStr = `${fmt(start)} - ${fmt(end)}，共${tripDays.value}天`
  }

  const parts: string[] = [
    `目的地：${locations.value.join('、')}`,
  ]
  if (durationStr) parts.push(`行程日期：${durationStr}`)
  if (styleLabels) parts.push(`喜好：${styleLabels}`)
  if (crowdLabel) parts.push(`人流偏好：${crowdLabel}`)
  if (budgetLabel) parts.push(`预算：${budgetLabel}`)

  // 加入天气信息
  if (weatherData.value.length > 0) {
    const weatherSummary = weatherData.value
      .map(d => `${d.date.replace(' ', ' ')} ${d.icon}${d.desc} ${d.tempMin}°-${d.tempMax}°`)
      .join('、')
    parts.push(`天气预报：${weatherSummary}`)
  }

  if (extraInfo.value.trim()) {
    parts.push(`补充：${extraInfo.value.trim()}`)
  }

  const fullInput = parts.join('；')
  console.log('[HomeView] 生成输入:', fullInput)
  await store.generate(fullInput)

  if (store.itineraryId && !store.error) {
    currentStep.value = 3
    router.push(`/itinerary/${store.itineraryId}`)
  }
}

// --- 聊天调整 ---
const chatHints = ['换个地方吃饭', '不想去这里了', '加一个上午行程', '轻松一点']

function fillChatHint(i: number) {
  chatInput.value = chatHints[i] || ''
}

async function handleChatSend() {
  const text = chatInput.value.trim()
  if (!text) return
  chatInput.value = ''
  await store.adjust(store.itineraryId || '', text)
}

async function handleRetry() {
  await store.retry()
  if (store.itineraryId && !store.error) {
    router.push(`/itinerary/${store.itineraryId}`)
  }
}

onUnmounted(() => {
  store.abort()
})
</script>

<style scoped>
.home-view {
  height: calc(100vh - 60px);
  overflow: hidden;
}

/* ===== SPLIT LAYOUT (智行风格) ===== */
.split-layout {
  display: flex;
  height: 100%;
}

/* ===== LEFT PANEL ===== */
.left-panel {
  width: 340px;
  flex-shrink: 0;
  background: var(--color-warm-surface);
  border-right: 1px solid var(--color-warm-border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.left-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px 18px;
}

/* Brand */
.panel-brand {
  text-align: center;
  padding: 10px 0 20px;
  border-bottom: 1px solid var(--color-warm-border);
  margin-bottom: 20px;
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-coral);
  margin: 0;
}

.brand-subtitle {
  font-size: 12px;
  color: var(--color-warm-text-muted);
  margin: 4px 0 0;
}

/* Section Label */
.section-label {
  font-size: 11px;
  color: var(--color-coral);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-label::before {
  content: '▸';
  font-size: 10px;
}

/* Preference Card */
.pref-card {
  background: white;
  border: 1px solid var(--color-warm-border);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-card);
}

/* Tag Container */
.tag-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 5px 12px;
  border: 1px solid var(--color-warm-border);
  border-radius: 20px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-warm-text-muted);
  background: var(--color-sand-light);
  user-select: none;
}

.tag:hover {
  border-color: var(--color-coral);
  color: var(--color-coral);
  background: var(--color-coral-light);
}

.tag.selected {
  background: rgba(255, 107, 107, 0.12);
  border-color: var(--color-coral);
  color: var(--color-coral);
  box-shadow: 0 0 8px rgba(255, 107, 107, 0.15);
}

/* Tag - Teal */
.tag.teal {
  border-color: rgba(78, 205, 196, 0.3);
  color: var(--color-warm-text-muted);
  background: var(--color-sand-light);
}

.tag.teal:hover {
  border-color: var(--color-ocean);
  color: var(--color-ocean-dark);
  background: rgba(78, 205, 196, 0.1);
}

.tag.teal.selected {
  border-color: var(--color-ocean);
  color: var(--color-ocean-dark);
  background: rgba(78, 205, 196, 0.12);
  box-shadow: 0 0 8px rgba(78, 205, 196, 0.15);
}

/* Tag - Amber */
.tag.amber {
  border-color: rgba(245, 158, 11, 0.3);
  color: var(--color-warm-text-muted);
  background: var(--color-sand-light);
}

.tag.amber:hover {
  border-color: var(--color-warm-amber);
  color: var(--color-warm-amber);
  background: rgba(245, 158, 11, 0.1);
}

.tag.amber.selected {
  border-color: var(--color-warm-amber);
  color: var(--color-warm-amber);
  background: rgba(245, 158, 11, 0.12);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.15);
}

/* ===== 地点输入 ===== */
.location-input-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.location-input {
  flex: 1;
  padding: 8px 12px;
  border: 1.5px solid var(--color-warm-border);
  border-radius: 10px;
  font-size: 13px;
  color: var(--color-warm-text);
  background: var(--color-sand-light);
  outline: none;
  transition: border-color 0.2s;
}

.location-input:focus {
  border-color: var(--color-coral);
}

.location-input::placeholder {
  color: var(--color-warm-text-muted);
  font-size: 12px;
}

.add-location-btn {
  padding: 8px 14px;
  background: var(--color-coral);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.add-location-btn:hover {
  background: var(--color-coral-dark);
  transform: translateY(-1px);
}

.location-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.location-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 20px;
  font-size: 12px;
  color: var(--color-coral);
}

.location-remove {
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.location-remove:hover {
  opacity: 1;
}

.location-hint {
  font-size: 11px;
  color: var(--color-warm-text-muted);
  margin-top: 6px;
}

/* ===== 日期范围选择 ===== */
.date-range-picker {
  margin-bottom: 10px;
}

.date-range-picker :deep(.n-input) {
  border-radius: 10px;
}

.trip-days-badge {
  display: inline-block;
  padding: 4px 14px;
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 20px;
  font-size: 12px;
  color: var(--color-coral);
  font-weight: 600;
  margin-bottom: 12px;
}

/* ===== 天气 ===== */
.weather-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-warm-text-muted);
  padding: 8px 0;
}

.weather-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-warm-border);
  border-top-color: var(--color-coral);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

.weather-empty {
  font-size: 12px;
  color: var(--color-warm-text-muted);
  padding: 6px 0;
}

.weather-section {
  margin-top: 12px;
  border-top: 1px solid var(--color-warm-border);
  padding-top: 12px;
}

.weather-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.weather-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-warm-text);
}

.weather-city {
  font-size: 11px;
  color: var(--color-warm-text-muted);
}

.weather-days {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: thin;
}

.weather-days::-webkit-scrollbar {
  height: 3px;
}

.weather-days::-webkit-scrollbar-thumb {
  background: var(--color-warm-border);
  border-radius: 2px;
}

.weather-day-card {
  flex-shrink: 0;
  min-width: 60px;
  background: #f8f6ff;
  border: 1px solid #ede8ff;
  border-radius: 10px;
  padding: 8px 6px;
  text-align: center;
}

.weather-date {
  font-size: 10px;
  color: #888;
  margin-bottom: 4px;
  white-space: nowrap;
}

.weather-icon {
  font-size: 20px;
  margin-bottom: 2px;
}

.weather-temp {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-warm-text);
}

.weather-desc {
  font-size: 10px;
  color: #888;
  margin-top: 2px;
}

/* ===== 喜好子标签 ===== */
.pref-sub-label {
  font-size: 11px;
  color: var(--color-warm-text-muted);
  margin-bottom: 8px;
  font-weight: 500;
}

/* Custom Input */
.custom-input {
  width: 100%;
  min-height: 80px;
  background: var(--color-sand-light);
  border: 1.5px solid var(--color-warm-border);
  border-radius: 12px;
  padding: 12px 14px;
  color: var(--color-warm-text);
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
  line-height: 1.65;
}

.custom-input:focus {
  border-color: var(--color-coral);
}

.custom-input::placeholder {
  color: var(--color-warm-text-muted);
  font-size: 12px;
}

/* Generate Button */
.generate-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, var(--color-coral), var(--color-coral-dark));
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.25s;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.generate-hint {
  text-align: center;
  font-size: 11px;
  color: var(--color-warm-text-muted);
  margin-top: 8px;
}

.btn-loading {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===== RIGHT PANEL ===== */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-warm-bg);
}

/* Step Bar */
.step-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--color-warm-border);
  background: rgba(255, 255, 255, 0.7);
  flex-shrink: 0;
}

.step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--color-warm-border);
  color: var(--color-warm-text-muted);
  transition: all 0.3s;
  font-weight: 500;
  background: white;
}

.step.active {
  border-color: var(--color-coral);
  color: var(--color-coral);
  background: rgba(255, 107, 107, 0.1);
  font-weight: 700;
}

.step.done {
  border-color: var(--color-ocean);
  color: var(--color-ocean-dark);
  background: rgba(78, 205, 196, 0.1);
}

.step-num {
  font-size: 11px;
}

.step-arrow {
  font-size: 11px;
  color: var(--color-warm-text-muted);
}

/* Right Scroll */
.right-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Empty State */
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-warm-text);
  margin-bottom: 8px;
}

.empty-sub {
  font-size: 14px;
  color: var(--color-warm-text-muted);
  margin-bottom: 28px;
  line-height: 1.6;
}

.empty-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.example-chip {
  padding: 8px 18px;
  background: white;
  border: 1.5px solid var(--color-warm-border);
  border-radius: 24px;
  font-size: 13px;
  color: var(--color-warm-text);
  cursor: pointer;
  transition: all 0.2s;
}

.example-chip:hover {
  border-color: var(--color-coral);
  color: var(--color-coral);
  background: rgba(255, 107, 107, 0.08);
  transform: translateY(-1px);
}

/* Error Banner */
.error-banner {
  margin-top: 16px;
}

/* ===== CHAT INPUT BAR ===== */
.chat-input-bar {
  flex-shrink: 0;
  border-top: 1px solid var(--color-warm-border);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  padding: 12px 20px 16px;
}

.chat-input-inner {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-bottom: 10px;
}

.chat-input-inner :deep(.n-input) {
  flex: 1;
}

.chat-send-btn {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, var(--color-coral), var(--color-coral-dark));
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.25);
}

.chat-send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 6px 18px rgba(255, 107, 107, 0.35);
}

.chat-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.chat-hints {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hint-chip {
  font-size: 12px;
  padding: 5px 12px;
  background: var(--color-sand-light);
  border: 1px solid var(--color-warm-border);
  border-radius: 20px;
  color: var(--color-warm-text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.hint-chip:hover {
  border-color: var(--color-coral);
  color: var(--color-coral);
  background: rgba(255, 107, 107, 0.1);
}

/* Responsive */
@media (max-width: 1024px) {
  .left-panel {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .split-layout {
    flex-direction: column;
  }

  .left-panel {
    width: 100%;
    max-height: 50vh;
    border-right: none;
    border-bottom: 1px solid var(--color-warm-border);
  }
}
</style>
