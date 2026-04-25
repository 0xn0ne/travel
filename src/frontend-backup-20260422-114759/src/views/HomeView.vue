<template>
  <div class="home-view">
    <div class="split-layout">
      <div class="left-panel">
        <div class="left-scroll">
          <div class="panel-brand">
            <h1 class="brand-title">拾途</h1>
            <p class="brand-subtitle">像本地朋友一样帮你规划旅行</p>
          </div>

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
              <span v-for="loc in locations" :key="loc" class="location-tag">
                {{ loc }}
                <span class="location-remove" @click="removeLocation(loc)">×</span>
              </span>
            </div>

          </div>

          <div class="section-label">行程日期</div>
          <div class="pref-card">
            <div class="date-range-picker">
              <n-date-picker
                v-model:value="dateRange"
                type="daterange"
                clearable
                :actions="['clear', 'confirm']"
                :is-date-disabled="isDateDisabled"
                placeholder="选择出发和返回日期"
                start-placeholder="出发日期"
                end-placeholder="返回日期"
                format="MM月dd日"
                style="width: 100%"
                :first-day-of-week="0"
                @update:value="onDateRangeChange"
              />
            </div>
            <div v-if="tripDays > 0" class="trip-days-badge">共 {{ tripDays }} 天</div>

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
                <div v-for="(day, idx) in weatherData" :key="idx" class="weather-day-card">
                  <div class="weather-date">{{ day.date }}</div>
                  <div class="weather-icon">{{ day.icon }}</div>
                  <div class="weather-temp">{{ day.tempMax }}° / {{ day.tempMin }}°</div>
                  <div class="weather-desc">{{ day.desc }}</div>
                </div>
              </div>
            </div>
            <div v-else-if="dateRange && !weatherLoading" class="weather-empty">选择地点后可查看天气预报</div>
          </div>

          <div class="section-label">旅行偏好</div>
          <div class="pref-card">
            <div class="pref-sub-label">人流偏好</div>
            <div class="tag-container style-tag-grid" style="margin-bottom: 12px;">
              <span
                v-for="c in crowdPrefs"
                :key="c.value"
                class="tag teal style-tag"
                :class="{ selected: selectedCrowd === c.value }"
                @click="selectedCrowd = c.value"
              >{{ c.label }}</span>
            </div>

            <div class="pref-sub-label">旅行风格（可多选）</div>
            <div class="tag-container style-tag-grid">
              <span
                v-for="t in sortedStyles"
                :key="t.value"
                class="tag style-tag"
                :class="{ selected: selectedStyles.includes(t.value) }"
                @click="toggleTag(selectedStyles, t.value)"
              >{{ t.label }}</span>
            </div>
          </div>

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

          <button
            class="generate-btn"
            :disabled="store.isGenerating || store.isLoadingCandidates || locations.length === 0"
            @click="handleGenerate"
          >
            <span v-if="store.isGenerating || store.isLoadingCandidates" class="btn-loading">✦</span>
            {{ store.homeFlowStage === 'candidate_selection' ? '重新匹配景点' : '⚡ 开始规划' }}
          </button>

          <div class="generate-hint" v-if="locations.length === 0">请先添加至少一个目的地</div>
        </div>
      </div>

      <div class="right-panel">
        <div class="step-bar">
          <div class="step" :class="{ active: currentStep === 1, done: currentStep > 1 }"><span class="step-num">①</span> 填写偏好</div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: currentStep === 2, done: currentStep > 2 }"><span class="step-num">②</span> 选择景点</div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: currentStep === 3, done: currentStep > 3 }"><span class="step-num">③</span> 生成行程</div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: currentStep === 4 }"><span class="step-num">④</span> 查看结果</div>
        </div>

        <div class="right-scroll">
          <div v-if="showEmptyState" class="empty-hint">
            <div class="empty-icon">🗺️</div>
            <p class="empty-title">告诉我想去哪儿</p>
            <p class="empty-sub">在左侧添加目的地和偏好，先为你匹配候选景点，再生成专属行程</p>
            <div class="empty-examples">
              <span class="example-chip" @click="fillLocation('北京')">北京</span>
              <span class="example-chip" @click="fillLocation('上海')">上海</span>
              <span class="example-chip" @click="fillLocation('福州')">福州</span>
              <span class="example-chip" @click="fillLocation('厦门')">厦门</span>
              <span class="example-chip" @click="fillLocation('成都')">成都</span>
              <span class="example-chip" @click="fillLocation('重庆')">重庆</span>
            </div>
          </div>

          <StageProgress
            v-if="store.isLoadingCandidates || store.homeFlowStage === 'generating' || store.isGenerating"
            :current-stage="store.isLoadingCandidates ? 'prefilter' : store.stage"
            :message="store.isLoadingCandidates ? '正在匹配候选景点' : store.stageMessage"
          />

          <div v-if="store.homeFlowStage === 'candidate_selection'" class="candidate-stage-anchor">
            已匹配 {{ store.candidatePois.length }} 个候选景点，请向下查看并选择。
          </div>

          <div
            v-if="store.homeFlowStage === 'candidate_selection'"
            ref="candidateStageRef"
            class="candidate-stage"
          >
            <div class="candidate-stage-head">
              <div>
                <div class="candidate-kicker">候选景点</div>
                <h2 class="candidate-title">先挑你真正想去的点</h2>
                <p class="candidate-sub">已为 {{ store.candidateTripContext?.city }} 匹配 {{ store.candidatePois.length }} 个候选景点，默认帮你勾选了一部分，可继续调整。</p>
              </div>
              <div class="candidate-summary">已选 {{ store.selectedCandidatePoiIds.length }} / {{ store.candidatePois.length }}</div>
            </div>

            <div v-if="store.candidateError" class="error-banner">
              <n-alert type="warning" :title="store.candidateError" />
            </div>

            <div
              v-else-if="store.homeFlowStage === 'candidate_selection' && store.candidatePois.length === 0"
              class="candidate-debug-card"
            >
              已进入候选景点阶段，但当前没有可展示的景点。
            </div>

            <PoiCandidateGrid
              :pois="store.candidatePois"
              :selected-ids="store.selectedCandidatePoiIds"
              @toggle="store.toggleCandidatePoi"
              @detail="openCandidateDetail"
            />

            <div class="candidate-footer">
              <div class="candidate-footer-copy">勾选后会仅基于这些景点生成路线，并尽量按区域聚合安排行程。</div>
              <button class="generate-btn candidate-confirm-btn" :disabled="store.selectedCandidatePoiIds.length === 0 || store.isGenerating" @click="handleGenerateFromSelectedPois">
                基于已选景点生成行程
              </button>
            </div>
          </div>

          <ItineraryTimeline v-if="store.currentItinerary?.days" :days="(store.currentItinerary as any).days" />

          <div v-if="store.error" class="error-banner">
            <n-alert type="warning" :title="store.error" />
            <n-button size="small" type="primary" style="margin-top: 8px" @click="handleRetry">重试</n-button>
          </div>
        </div>

        <div class="chat-input-bar">
          <div class="chat-input-inner">
            <n-input
              v-model:value="chatInput"
              type="textarea"
              placeholder="想调整行程？比如「换个更有氛围的」「少走一点路」"
              :autosize="{ minRows: 1, maxRows: 3 }"
              @keydown.enter.exact.prevent="handleChatSend"
            />
            <button class="chat-send-btn" @click="handleChatSend" :disabled="!chatInput.trim()">↑</button>
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

    <PoiDetailDrawer v-model:show="candidateDetailVisible" :poi="activeCandidatePoi" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NInput, NButton, NAlert, NDatePicker } from 'naive-ui'
import { useItineraryStore } from '../stores/itinerary'
import StageProgress from '../components/StageProgress.vue'
import ItineraryTimeline from '../components/ItineraryTimeline.vue'
import PoiCandidateGrid from '../components/PoiCandidateGrid.vue'
import PoiDetailDrawer from '../components/PoiDetailDrawer.vue'
import type { CandidatePoiData, CandidatePoiRequestPayload } from '../types/itinerary'

const store = useItineraryStore()
const router = useRouter()
const chatInput = ref('')
const candidateStageRef = ref<HTMLElement | null>(null)
const candidateDetailVisible = ref(false)
const activeCandidatePoi = ref<CandidatePoiData | null>(null)

const currentStep = computed(() => {
  if (store.homeFlowStage === 'result') return 4
  if (store.homeFlowStage === 'generating') return 3
  if (store.homeFlowStage === 'candidate_selection') return 2
  return 1
})

const showEmptyState = computed(() => !store.isGenerating && !store.isLoadingCandidates && store.homeFlowStage === 'input' && store.stage === 'idle' && !store.currentItinerary?.days)

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
  const city = locations.value[0]
  dateRangeCity.value = city
  let lat = CITY_COORDS[city]?.[0]
  let lon = CITY_COORDS[city]?.[1]

  if (!lat) {
    try {
      const geoRes = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1`)
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

const sortedStyles = computed(() => [...travelStyles].sort((a, b) => a.label.replace(/[^\u4e00-\u9fa5]/g, '').length - b.label.replace(/[^\u4e00-\u9fa5]/g, '').length))
const selectedStyles = ref<string[]>(['food_shopping', 'culture'])

const crowdPrefs = [
  { value: 'quiet', label: '🌿 人少清静' },
  { value: 'moderate', label: '🎵 热闹适中' },
  { value: 'lively', label: '🔥 人山人海' },
]
const selectedCrowd = ref('moderate')

const budgets = [
  { value: 'low', label: '💰 50以下' },
  { value: 'avg', label: '💰 50-200' },
  { value: 'high', label: '💎 200-500' },
  { value: 'luxury', label: '👑 500+' },
]
const selectedBudget = ref('avg')
const extraInfo = ref('')

function toggleTag(arr: string[], val: string) {
  const idx = arr.indexOf(val)
  if (idx === -1) arr.push(val)
  else arr.splice(idx, 1)
}

const canGenerate = computed(() => locations.value.length > 0 && !store.isGenerating && !store.isLoadingCandidates)

async function handleGenerate() {
  if (!canGenerate.value) return

  const normalizedDateRange = Array.isArray(dateRange.value)
    && dateRange.value.every(value => typeof value === 'number' && Number.isFinite(value))
    ? dateRange.value.map(value => Math.trunc(value))
    : undefined

  const payload: CandidatePoiRequestPayload = {
    destinations: locations.value,
    date_range: normalizedDateRange,
    trip_days: tripDays.value || undefined,
    styles: selectedStyles.value,
    crowd_preference: selectedCrowd.value,
    budget: selectedBudget.value,
    extra_info: extraInfo.value.trim() || undefined,
  }

  console.log('[candidate-pois] payload', payload)

  try {
    await store.loadCandidatePois(payload)
  } catch (e) {
    console.error('候选景点匹配失败', e)
    if (e instanceof Error) {
      console.error('候选景点匹配失败详情', e.message)
    }
  }
}

async function handleGenerateFromSelectedPois() {
  try {
    await store.generateFromSelectedPois()
    if (store.itineraryId && !store.error) {
      router.push(`/itinerary/${store.itineraryId}`)
    }
  } catch (e) {
    console.error('生成行程失败', e)
  }
}

function openCandidateDetail(poi: CandidatePoiData) {
  activeCandidatePoi.value = poi
  candidateDetailVisible.value = true
}

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

watch(
  () => store.homeFlowStage,
  async (stage) => {
    if (stage !== 'candidate_selection') return
    await nextTick()
    candidateStageRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  },
)

onUnmounted(() => {
  store.abort()
})
</script>

<style scoped>
.home-view {
  height: calc(100vh - 60px);
  overflow: hidden;
  background: linear-gradient(180deg, #f3f4f9 0%, #eceef4 100%);
}
.split-layout {
  display: flex;
  height: 100%;
  gap: 14px;
  padding: 14px;
}
.left-panel {
  width: 344px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(252, 251, 255, 0.96) 0%, rgba(247, 245, 252, 0.96) 100%);
  border: 1px solid #e1e3ec;
  border-radius: 24px;
  box-shadow: 0 10px 24px rgba(31, 35, 52, 0.045);
}
.left-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 22px 18px 24px;
}
.panel-brand {
  padding: 2px 2px 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid #eceef3;
}
.brand-title {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.035em;
  color: #26272b;
  margin: 0;
}
.brand-subtitle {
  font-size: 13px;
  line-height: 1.65;
  color: #7e8290;
  margin: 6px 0 0;
}
.section-label {
  font-size: 11px;
  color: #959bab;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin: 0 0 10px 2px;
  font-weight: 700;
}
.pref-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e4e7ef;
  border-radius: 16px;
  padding: 18px;
  margin-bottom: 14px;
}
.pref-sub-label {
  font-size: 13px;
  line-height: 1.5;
  color: #6f7482;
  margin-bottom: 9px;
  font-weight: 600;
}
.tag-container,
.style-tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.style-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  width: calc((100% - 16px) / 3);
  min-width: 0;
  padding-left: 10px;
  padding-right: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tag,
.tag.teal,
.tag.amber {
  padding: 7px 13px;
  border: 1px solid #e5e7ee;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
  cursor: pointer;
  transition: all 0.18s ease;
  color: #6f7482;
  background: #ffffff;
  user-select: none;
}
.tag.selected,
.tag.teal.selected,
.tag.amber.selected {
  background: linear-gradient(135deg, #9d8ae1 0%, #8573c8 100%);
  border-color: #9685db;
  color: #ffffff;
  box-shadow: 0 4px 10px rgba(133, 115, 200, 0.12);
}
.location-input-row {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}
.location-input,
.custom-input {
  width: 100%;
  background: #ffffff;
  border: 1px solid #e5e7ee;
  border-radius: 14px;
  color: #333333;
  outline: none;
  font-size: 14px;
  font-family: inherit;
}
.location-input {
  flex: 1;
  padding: 10px 12px;
}
.custom-input {
  min-height: 92px;
  padding: 12px 14px;
  resize: vertical;
  line-height: 1.65;
}
.location-hint,
.generate-hint,
.weather-empty,
.weather-loading,
.weather-city,
.hint-chip,
:deep(.n-input__placeholder),
:deep(.n-base-selection-placeholder) {
  color: #858b99;
  font-size: 14px;
}
.add-location-btn {
  padding: 10px 15px;
  background: linear-gradient(135deg, #a78bfa 0%, #8f79db 100%);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.location-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.location-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 11px;
  background: #f4f5f8;
  border: 1px solid #e5e7ee;
  border-radius: 999px;
  font-size: 12px;
  color: #555b68;
}
.location-remove {
  cursor: pointer;
  font-size: 14px;
}
.date-range-picker { margin-bottom: 12px; }
.date-range-picker :deep(.n-input),
.chat-input-inner :deep(.n-input) { border-radius: 14px; }
.date-range-picker :deep(.n-input__input-el),
.date-range-picker :deep(.n-base-selection-input__content),
.date-range-picker :deep(.n-base-selection-label) {
  font-size: 14px;
  color: #333333;
}
.date-range-picker :deep(.n-date-panel-weekdays__item) {
  color: #6f7482;
  font-size: 12px;
  font-weight: 600;
}
.trip-days-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  background: #f4f5f8;
  border: 1px solid #e5e7ee;
  border-radius: 999px;
  font-size: 12px;
  color: #5d6470;
  font-weight: 600;
  margin-bottom: 12px;
}
.weather-section {
  margin-top: 14px;
  background: linear-gradient(180deg, #f5f6fb 0%, #f0f2f8 100%);
  border: 1px solid #e3e6ef;
  border-radius: 14px;
  padding: 14px;
}
.weather-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.weather-title { font-size: 13px; font-weight: 600; color: #474b57; }
.weather-days {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 4px;
  scroll-snap-type: x proximity;
  -webkit-overflow-scrolling: touch;
}
.weather-days::-webkit-scrollbar {
  height: 6px;
}
.weather-days::-webkit-scrollbar-thumb {
  background: rgba(167, 139, 250, 0.24);
  border-radius: 999px;
}
.weather-day-card {
  flex: 0 0 96px;
  padding: 10px;
  background: rgba(255,255,255,0.68);
  border-radius: 12px;
  text-align: center;
  scroll-snap-align: start;
}
.weather-date,
.weather-desc { font-size: 11px; }
.weather-icon { font-size: 20px; margin-bottom: 2px; }
.weather-temp { font-size: 12px; font-weight: 600; color: #454954; }
.generate-btn {
  width: 100%;
  padding: 15px 16px;
  margin-top: 4px;
  background: linear-gradient(135deg, #a78bfa 0%, #8f79db 100%);
  border: none;
  border-radius: 11px;
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 10px 20px rgba(167, 139, 250, 0.18);
}
.generate-btn:disabled,
.chat-send-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-loading { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(245, 246, 251, 0.96) 0%, rgba(239, 241, 247, 0.96) 100%);
  border: 1px solid #e1e4ec;
  border-radius: 24px;
  box-shadow: 0 10px 24px rgba(31, 35, 52, 0.035);
}
.step-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 18px 24px 14px;
  border-bottom: 1px solid #e6e9f0;
  background: rgba(250, 250, 252, 0.72);
}
.step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid #e4e6ee;
  color: #7b8190;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.9);
}
.step.active { border-color: #d7dbe6; color: #59606f; background: #eef1f5; }
.step.done { border-color: #dde0ea; color: #6d7381; background: #f8f9fc; }
.step-num { font-size: 12px; }
.right-scroll { flex: 1; overflow-y: auto; padding: 28px; }
.empty-hint {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 58px 32px;
  text-align: center;
  background: #fcfbff;
  border: 1px solid #eee8f7;
  border-radius: 28px;
}
.empty-icon {
  width: 70px;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  margin-bottom: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
}
.empty-title {
  font-size: 30px;
  line-height: 1.14;
  font-weight: 700;
  letter-spacing: -0.04em;
  color: #343846;
  margin-bottom: 12px;
}
.empty-sub {
  max-width: 480px;
  font-size: 14px;
  color: #6f7584;
  margin-bottom: 24px;
  line-height: 1.75;
}
.empty-examples { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; max-width: 520px; }
.example-chip {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid #d9dde6;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #5d6474;
  cursor: pointer;
}
.candidate-stage-anchor {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f7f4ff 0%, #f2edff 100%);
  border: 1px solid #e5ddfb;
  color: #6957bd;
  font-size: 14px;
  font-weight: 700;
}
.candidate-stage {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.candidate-stage-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}
.candidate-kicker {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #9399a8;
  font-weight: 700;
  margin-bottom: 8px;
}
.candidate-title {
  margin: 0;
  font-size: 28px;
  line-height: 1.1;
  color: #2f3440;
}
.candidate-sub {
  margin: 10px 0 0;
  color: #6f7585;
  line-height: 1.7;
  font-size: 14px;
  max-width: 680px;
}
.candidate-summary {
  padding: 8px 14px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #e3e6ee;
  color: #6957bd;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}
.candidate-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 20px;
  background: rgba(255,255,255,0.82);
  border: 1px solid #e5e8f0;
}
.candidate-footer-copy {
  font-size: 14px;
  line-height: 1.7;
  color: #6e7483;
}
.candidate-confirm-btn {
  width: auto;
  min-width: 240px;
  margin-top: 0;
}
.candidate-debug-card {
  padding: 18px 20px;
  border-radius: 18px;
  background: rgba(255,255,255,0.88);
  border: 1px solid #e5e8f0;
  color: #5e6573;
  font-size: 14px;
}
.error-banner { margin-top: 16px; }
.chat-input-bar {
  border-top: 1px solid #e5e8f0;
  background: rgba(250, 251, 253, 0.92);
  padding: 16px 24px 18px;
}
.chat-input-inner { display: flex; gap: 12px; align-items: flex-end; }
.chat-send-btn {
  width: 42px;
  height: 42px;
  border: none;
  border-radius: 11px;
  background: linear-gradient(135deg, #a78bfa 0%, #8f79db 100%);
  color: #fff;
  font-size: 18px;
  cursor: pointer;
}
.chat-hints { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.hint-chip {
  padding: 7px 11px;
  background: #fff;
  border: 1px solid #e3e6ee;
  border-radius: 999px;
  cursor: pointer;
}
@media (max-width: 1200px) {
  .candidate-stage-head,
  .candidate-footer { flex-direction: column; align-items: flex-start; }
  .candidate-confirm-btn { width: 100%; }
}
@media (max-width: 1024px) {
  .split-layout { flex-direction: column; }
  .left-panel { width: 100%; }
  .style-tag { width: calc((100% - 8px) / 2); }
}
</style>
