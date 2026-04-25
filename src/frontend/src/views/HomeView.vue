<template>
  <div class="home-view">
    <div class="split-layout">
      <aside class="left-panel">
        <div class="left-scroll">
          <div class="panel-brand">
            <h1 class="brand-title">拾途</h1>
            <p class="brand-subtitle">像一只贴心小狗，陪伴你挑景点、辨路线、做攻略。</p>
          </div>

          <div class="pref-card pastel-blue primary-pref-card">
            <div class="section-label section-label-inline">想去哪儿</div>
            <div class="location-input-row">
              <input
                v-model="locationInput"
                class="location-input"
                placeholder="输入地点，如：上海"
                @keydown.enter.prevent="addLocation"
              />
              <button class="add-location-btn" @click="addLocation">添加</button>
            </div>
            <div v-if="locations.length > 0" class="location-tags">
              <span v-for="loc in locations" :key="loc" class="location-tag">
                {{ loc }}
                <span class="location-remove" @click="locations = []">×</span>
              </span>
            </div>
          </div>

          <div class="pref-card pastel-yellow secondary-pref-card">
            <div class="section-label section-label-inline">行程日期</div>
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
            <div v-if="tripDays > 0" class="trip-days-badge">🗓️ 共 {{ tripDays }} 天</div>

            <div v-if="weatherLoading" class="weather-loading">
              <span class="weather-spinner"></span>
              <span>正在帮你看看天气...</span>
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

          <div class="pref-card pastel-pink crowd-pref-card">
            <div class="section-label section-label-inline">人流偏好</div>
            <div class="tag-container crowd-grid">
              <span
                v-for="c in crowdPrefs"
                :key="c.value"
                class="tag teal style-tag crowd-pill"
                :class="{ selected: selectedCrowd === c.value }"
                @click="selectedCrowd = c.value"
              >{{ c.label }}</span>
            </div>
          </div>

          <div class="left-secondary-stack">
            <div class="section-label section-label-secondary">旅行风格</div>
            <div class="pref-card pref-card-secondary pastel-mint secondary-pref-card">
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

            <div class="section-label section-label-secondary">人均预算</div>
            <div class="pref-card pref-card-secondary pastel-mint secondary-pref-card">
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

            <div class="section-label section-label-secondary">补充信息</div>
            <div class="pref-card pref-card-secondary pastel-peach secondary-pref-card">
              <textarea
                v-model="extraInfo"
                class="custom-input"
                placeholder="还有什么想告诉我们的？
比如：带老人/小孩、有宠物、想拍照出片、不能走太多路……"
                rows="4"
              ></textarea>
            </div>

            <button
              class="generate-btn"
              :disabled="store.isGenerating || store.isLoadingCandidates || locations.length === 0"
              @click="handleGenerate"
            >
              <span v-if="store.isGenerating || store.isLoadingCandidates" class="btn-loading">✦</span>
              {{ store.homeFlowStage === 'candidate_selection' ? '重新匹配景点' : '开始规划' }}
            </button>

            <div v-if="locations.length === 0" class="generate-hint"></div>
          </div>
        </div>
      </aside>

      <section class="right-panel">
        <div class="step-bar">
          <div class="step" :class="{ active: currentStep === 1, done: currentStep > 1 }"><span class="step-num">①</span> 填愿望</div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: currentStep === 2, done: currentStep > 2 }"><span class="step-num">②</span> 挑景点</div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: currentStep === 3, done: currentStep > 3 }"><span class="step-num">③</span> 拼路线</div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: currentStep === 4 }"><span class="step-num">④</span> 看结果</div>
        </div>

        <div class="right-scroll">
          <div v-if="showEmptyState" class="hero-card">
            <div class="hero-copy">
              <h2 class="hero-title">让小狗搭子帮你规划旅行叭</h2>
              <p class="hero-sub">输入目的地、日期和偏好，我会先帮你挑一批值得去的地方，再一起生成路线。</p>
              <div class="hero-actions">
                <button class="hero-primary" @click="fillLocation('上海')">从上海开始</button>
                <button class="hero-secondary" @click="fillLocation('杭州')">换个城市试试</button>
              </div>
              <div class="empty-examples">
                <span class="example-chip" @click="fillLocation('北京')">北京</span>
                <span class="example-chip" @click="fillLocation('上海')">上海</span>
                <span class="example-chip" @click="fillLocation('福州')">福州</span>
                <span class="example-chip" @click="fillLocation('厦门')">厦门</span>
                <span class="example-chip" @click="fillLocation('成都')">成都</span>
                <span class="example-chip" @click="fillLocation('重庆')">重庆</span>
              </div>
            </div>
            <div class="hero-illustration" aria-hidden="true">
              <div class="hero-art-frame">
                <img
                  class="hero-mascot"
                  src="/imgs/177101776915152_.pic-removebg-preview.png"
                  alt="小狗旅行搭子"
                />
              </div>
            </div>
          </div>

          <div v-else-if="store.homeFlowStage === 'input'" class="guide-card">
            <div class="guide-copy">
              <h3 class="guide-title">把愿望告诉我，我来把路线拼顺。</h3>
              <p class="guide-sub">先在左边填地点和日期，再补一点偏好；我会按你想要的节奏挑景点、看天气、排出一条更轻松的路线。</p>
              <div class="guide-points">
                <div class="guide-point">
                  <span class="guide-point-icon">🧳</span>
                  <span>先写城市和日期</span>
                </div>
                <div class="guide-point">
                  <span class="guide-point-icon">🎨</span>
                  <span>选喜欢的旅行风格</span>
                </div>
                <div class="guide-point">
                  <span class="guide-point-icon">🐾</span>
                  <span>我来给你候选景点</span>
                </div>
              </div>
            </div>
            <div class="guide-illustration" aria-hidden="true">
              <div class="guide-scene-card">
                <img
                  class="guide-mascot"
                  src="/imgs/176801776846821_.pic-removebg-preview.png"
                  alt="小狗旅行搭子"
                />
              </div>
            </div>
          </div>

          <StageProgress
            v-if="store.isLoadingCandidates || store.homeFlowStage === 'generating' || store.isGenerating"
            :current-stage="store.isLoadingCandidates ? 'prefilter' : store.stage"
            :message="store.isLoadingCandidates ? '正在帮你嗅探候选景点' : store.stageMessage"
          />

          <div v-if="store.homeFlowStage === 'candidate_selection'" class="candidate-stage-anchor">
            🐾 已匹配 {{ store.candidatePois.length }} 个候选景点，请继续往下挑选喜欢的卡片。
          </div>

          <div
            v-if="store.homeFlowStage === 'candidate_selection'"
            ref="candidateStageRef"
            class="candidate-stage"
          >
            <div class="candidate-stage-head">
              <div>
                <div class="candidate-kicker">候选景点贴纸墙</div>
                <h2 class="candidate-title">先挑你真正想去的点</h2>
                <p class="candidate-sub">已为 {{ store.candidateTripContext?.city }} 匹配 {{ store.candidatePois.length }} 个候选景点，默认帮你勾选了一部分，你也可以自己慢慢挑。</p>
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
                🐕 基于已选景点生成行程
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
          <div class="chat-input-row">
            <img
              class="chat-mascot-inline"
              src="/imgs/IMG_0084-removebg-preview.png"
              alt="小狗搭子"
            />
            <textarea
              v-model="chatInput"
              class="chat-text-input"
              placeholder="想调整行程？比如「换个更有氛围的」「少走一点路」"
              rows="1"
              @keydown.enter.exact.prevent="handleChatSend"
            ></textarea>
            <button class="chat-send-btn" @click="handleChatSend" :disabled="!chatInput.trim()">↑</button>
          </div>
          <div class="chat-hints">
            <span class="hint-chip" @click="fillChatHint(0)">换个地方吃饭</span>
            <span class="hint-chip" @click="fillChatHint(1)">不想去这里了</span>
            <span class="hint-chip" @click="fillChatHint(2)">加一个上午行程</span>
            <span class="hint-chip" @click="fillChatHint(3)">轻松一点</span>
          </div>
        </div>
      </section>
    </div>

    <PoiDetailDrawer v-model:show="candidateDetailVisible" :poi="activeCandidatePoi" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NAlert, NDatePicker } from 'naive-ui'
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
  { value: 'landmark', label: '经典必去' },
  { value: 'hidden', label: '宝藏小店' },
  { value: 'nature', label: '自然风光' },
  { value: 'culture', label: '历史人文' },
  { value: 'photo', label: '拍照打卡' },
  { value: 'art', label: '艺术展览' },
  { value: 'cafe', label: '咖啡饮品' },
  { value: 'food_shopping', label: '美食购物' },
  { value: 'romantic', label: '约会浪漫' },
  { value: 'senior', label: '长辈出行' },
]

const sortedStyles = computed(() => [...travelStyles].sort((a, b) => a.label.replace(/[^\u4e00-\u9fa5]/g, '').length - b.label.replace(/[^\u4e00-\u9fa5]/g, '').length))
const selectedStyles = ref<string[]>(['food_shopping', 'culture'])

const crowdPrefs = [
  { value: 'quiet', label: '人少清静' },
  { value: 'moderate', label: '热闹适中' },
  { value: 'lively', label: '人山人海' },
]
const selectedCrowd = ref('moderate')

const budgets = [
  { value: 'low', label: '50以下' },
  { value: 'avg', label: '50-200' },
  { value: 'high', label: '200-500' },
  { value: 'luxury', label: '500+' },
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
.brand-title,
.hero-title,
.guide-title,
.candidate-title {
  font-family: 'ZCoolHappy', sans-serif;
  font-weight: 400;
  letter-spacing: 0.04em;
  color: var(--type-title);
}

.home-view {
  position: relative;
  height: calc(100vh - 64px);
  overflow: hidden;
  background-color: var(--bg-main);
  color: var(--text-body);
  background-image:
    radial-gradient(rgba(158, 190, 219, 0.1) 1px, transparent 1px),
    radial-gradient(rgba(255, 255, 255, 0.65) 1px, transparent 1px);
  background-position: 0 0, 14px 14px;
  background-size: 26px 26px, 26px 26px;
}

.wish-card-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.location-input-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
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
  gap: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-main);
  font-weight: 700;
}

.location-remove {
  cursor: pointer;
  font-size: 16px;
  font-weight: 900;
  line-height: 1;
  color: var(--text-soft);
}

.step-arrow {
  font-weight: 700;
  color: var(--text-soft);
  font-size: 14px;
  flex-shrink: 0;
}

.step-num {
  font-weight: 700;
}

.candidate-stage-head,
.weather-header,
.candidate-footer,
.chat-input-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.weather-title {
  color: var(--type-title-soft);
  font-size: 12px;
  font-weight: 700;
}

.weather-days {
  margin-top: 12px;
  display: flex;
  overflow-x: auto;
  gap: 10px;
}

.weather-date,
.weather-desc {
  font-size: 12px;
  color: var(--text-body);
}

.weather-icon {
  font-size: 24px;
  margin: 8px 0 4px;
}

.weather-temp {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
}

.weather-loading,
.weather-empty {
  padding: 10px 0 2px;
}

.weather-spinner,
.btn-loading {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.date-range-picker {
  margin-bottom: 12px;
}

.trip-days-badge {
  margin-bottom: 12px;
}

.split-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  height: 100%;
  gap: 24px;
  padding: 24px;
}

.left-panel,
.right-panel {
  min-height: 0;
}

.left-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.72);
  border-radius: 28px;
  backdrop-filter: blur(12px);
}

.left-scroll,
.right-scroll {
  min-height: 0;
  overflow-y: auto;
  position: relative;
  z-index: 1;
}

.left-scroll {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.panel-brand,
.pref-card {
  background: rgba(255, 255, 255, 0.82);
  border: none;
  border-radius: var(--card-radius);
}

.hero-card,
.guide-card,
.candidate-stage,
.candidate-stage-anchor,
.chat-input-bar,
.candidate-debug-card {
  background: rgba(255, 255, 255, 0.96);
  border: none;
  border-radius: var(--card-radius);
}

.panel-brand {
  margin-bottom: 0;
  padding: 20px 20px 18px;
  background: rgba(255, 255, 255, 0.40);
  border: none;
}

.left-secondary-stack {
  display: grid;
  gap: 0;
}

.left-secondary-stack-hidden {
  display: none;
}

.primary-pref-card,
.crowd-pref-card {
  margin-bottom: 0;
}

.secondary-pref-card {
  margin-bottom: 12px;
}

.brand-title {
  font-size: 28px;
  line-height: 1.1;
  margin: 0;
}

.brand-subtitle,
.location-input,
.custom-input,
.pref-sub-label,
.tag,
.tag.teal,
.tag.amber,
.hero-sub,
.guide-sub,
.candidate-sub,
.candidate-footer-copy,
.generate-hint,
.location-hint,
.weather-empty,
.weather-loading,
.weather-city,
.section-label,
.wish-sub,
.guide-point,
.weather-date,
.weather-desc,
.weather-temp,
.step,
.location-remove,
:deep(.n-input__input-el),
:deep(.n-input__textarea-el),
:deep(.n-input__placeholder),
:deep(.n-base-selection-placeholder),
:deep(.n-base-selection-label) {
  font-family: var(--font-ui-rounded);
}

.brand-subtitle {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--type-body);
}

.section-label {
  font-size: 14px;
  color: var(--type-muted);
  margin: 24px 0 8px 8px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.section-label-inline {
  margin: 0 0 10px;
  padding-left: 2px;
}

.section-label-secondary {
  margin-top: 18px;
  color: var(--type-muted);
}

.section-label:first-child,
.section-label:nth-of-type(2) {
  margin-top: 0;
}

.pref-card {
  padding: 16px;
  margin-bottom: 14px;
}

.pref-card-secondary {
  background: rgba(255, 255, 255, 0.40);
  border: none;
  box-shadow: none;
}

.pastel-blue,
.pastel-yellow {
  background: rgba(255, 255, 255, 0.48);
  border: none;
  box-shadow: none;
}

.pastel-pink {
  background: rgba(255, 255, 255, 0.42);
  border: none;
  box-shadow: none;
}

.pastel-mint {
  background: rgba(255, 255, 255, 0.44);
  border: none;
  box-shadow: none;
}

.pastel-peach {
  background: rgba(255, 255, 255, 0.46);
  border: none;
  box-shadow: none;
}

.pref-sub-label {
  font-size: 13px;
  line-height: 1.5;
  color: var(--type-title-soft);
  margin-bottom: 10px;
  font-weight: 600;
}

.tag-container,
.style-tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.style-tag-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.crowd-grid {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  margin-bottom: 0;
}

.crowd-grid-stack {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.crowd-pill {
  justify-content: center;
  border-radius: 18px;
  min-height: 38px;
  padding: 8px 14px;
}

.style-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  min-height: 44px;
  padding: 9px 12px;
  text-align: center;
  line-height: 1.35;
  word-break: break-word;
}

.tag,
.tag.teal,
.tag.amber {
  border: none;
  border-radius: 18px;
  font-weight: 500;
  padding: 7px 15px;
  font-size: 13px;
  color: var(--type-chip);
  background: var(--paper-2);
  transition: background-color 0.2s ease, color 0.2s ease;
}

.tag:hover,
.example-chip:hover,
.hint-chip:hover {
  transform: none;
  background-color: var(--paper-2);
  opacity: 0.8;
}

.tag.selected,
.tag.teal.selected,
.tag.amber.selected {
  background: var(--accent-orange);
  color: #fff;
  font-weight: 800;
  opacity: 1;
}

.hint-chip {
  border: none;
  border-radius: 999px;
  font-weight: 600;
  font-size: 14px;
  color: var(--type-chip);
  background: rgba(255, 255, 255, 0.85);
  padding: 9px 20px;
}

.example-chip {
  border: none;
  border-radius: 999px;
  font-weight: 600;
  font-size: 16px;
  color: var(--type-chip);
  background: rgba(255, 255, 255, 0.85);
  padding: 8px 18px;
}

.location-tag,
.trip-days-badge,
.candidate-summary,
.hero-decor,
.candidate-kicker {
  border: none;
  border-radius: 999px;
  font-weight: 600;
  font-size: 12px;
  color: var(--type-chip);
  background: rgba(255, 255, 255, 0.85);
  padding: 6px 14px;
}

.location-input,
.custom-input {
  width: 100%;
  background: var(--paper-2);
  border: none;
  border-radius: 18px;
  color: var(--type-body);
  font-size: 14px;
  box-shadow: none;
  transition: border-color 0.2s ease;
}

.location-input {
  width: 100%;
  padding: 10px 14px;
  outline: none;
  margin-bottom: 12px;
}

.custom-input {
  padding: 12px 14px;
  resize: vertical;
  line-height: 1.7;
  min-height: 128px;
}

.date-range-picker :deep(.n-input),
.chat-input-inner :deep(.n-input),
.date-range-picker :deep(.n-base-selection),
.chat-input-inner :deep(.n-input-wrapper) {
  background: var(--paper-2);
  border: none;
  border-radius: 18px;
  color: var(--type-body);
  font-size: 15px;
  box-shadow: none;
  flex: 1;
}

.add-location-btn {
  cursor: pointer;
  transition: transform 0.2s ease;
  border: none;
  border-radius: 10px;
  background: var(--accent-orange);
  color: #fff;
  padding: 0 14px;
  height: 40px;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.generate-btn,
.hero-primary,
.hero-secondary,
.chat-send-btn {
  cursor: pointer;
  transition: transform 0.2s ease;
  border: none;
  border-radius: 20px;
}

.add-location-btn:hover,
.generate-btn:hover,
.hero-primary:hover,
.hero-secondary:hover,
.chat-send-btn:hover {
  transform: translateY(-1px);
}

.generate-btn,
.hero-primary,
.chat-send-btn {
  background: var(--accent-orange);
  color: #fff;
}

.hero-secondary {
  background: var(--paper-2);
  color: var(--type-chip);
}

.generate-btn {
  width: 100%;
  min-height: 56px;
  padding: 0 20px;
  border-radius: 999px;
  font-size: 17px;
  font-weight: 700;
  margin-top: 6px;
}

.generate-btn:disabled,
.chat-send-btn:disabled,
.add-location-btn:disabled,
.hero-primary:disabled,
.hero-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.generate-hint,
.location-hint,
.weather-empty,
.weather-loading,
.weather-city,
:deep(.n-input__placeholder),
:deep(.n-base-selection-placeholder) {
  color: var(--type-muted);
  font-size: 15px;
}

:deep(.n-input__input-el),
:deep(.n-input__textarea-el),
:deep(.n-base-selection-label) {
  color: var(--type-body);
}

.weather-section {
  background: rgba(255, 255, 255, 0.50);
  border: none;
  border-radius: 22px;
  padding: 14px;
}

.weather-day-card {
  background: rgba(255, 255, 255, 0.70);
  border: none;
  border-radius: 18px;
  padding: 10px;
}

.right-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: visible;
  position: relative;
}

.step-bar {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  margin-bottom: 18px;
  align-self: stretch;
  background: rgba(255, 255, 255, 0.82);
  border: none;
  border-radius: 24px;
  backdrop-filter: blur(8px);
  box-shadow: none;
}

.step {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 16px;
  color: var(--type-muted);
  font-size: 16px;
  font-weight: 600;
  border: 2px solid transparent;
}

.hero-card,
.guide-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 400px;
  gap: 24px;
  padding: 24px;
  min-height: 520px;
  background: rgba(255, 255, 255, 0.90);
  border: none;
  border-radius: var(--card-radius);
  backdrop-filter: blur(12px);
}

.hero-copy,
.guide-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.hero-title,
.guide-title,
.candidate-title {
  text-wrap: balance;
}

.hero-title {
  font-size: clamp(38px, 4.5vw, 54px);
  line-height: 1.16;
  margin: 0;
}

.guide-title {
  font-size: clamp(28px, 3vw, 36px);
  line-height: 1.2;
  margin: 12px 0 0;
}

.hero-sub,
.guide-sub,
.candidate-sub,
.candidate-footer-copy {
  color: var(--type-body);
  font-size: 14px;
  line-height: 1.85;
}

.hero-sub,
.guide-sub {
  font-size: 15px;
  line-height: 1.9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  margin-top: 18px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 24px 0 0;
}

.empty-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.hero-primary,
.hero-secondary {
  min-height: 48px;
  padding: 0 20px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 700;
}

.guide-points {
  display: grid;
  gap: 12px;
  margin-top: 22px;
}

.guide-point {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.50);
  border: none;
  color: var(--type-body);
  font-size: 14px;
  font-weight: 600;
}

.guide-point-icon {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.70);
  border: none;
  flex-shrink: 0;
}

.hero-illustration,
.guide-illustration {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  border-radius: 24px;
  overflow: visible;
  align-self: stretch;
}

.hero-art-frame,
.guide-scene-card {
  position: relative;
  width: 100%;
  flex: 1;
  border-radius: 24px;
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero-mascot,
.guide-mascot {
  width: 100%;
  max-width: 440px;
  object-fit: contain;
  display: block;
  position: relative;
  z-index: 1;
}

.hero-decor {
  position: absolute;
  z-index: 2;
  padding: 7px 14px;
  background: rgba(255, 255, 255, 0.90);
  border: none;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: var(--type-chip);
  white-space: nowrap;
}

.hero-decor-a { left: 10px; bottom: 18px; }
.candidate-stage-anchor {
  margin-bottom: 14px;
  padding: 16px 18px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
  background: var(--bg-main);
}

.candidate-stage {
  padding: 24px;
}

.candidate-title {
  margin: 0;
  font-size: 30px;
}

.candidate-summary {
  flex-shrink: 0;
  padding: 8px 14px;
  font-size: 13px;
}

.candidate-confirm-btn {
  width: auto;
  min-width: 260px;
}

.chat-input-bar {
  margin-top: 18px;
  padding: 20px 14px;
  background: rgba(255, 255, 255, 0.88);
  border: none;
  border-radius: 20px;
  backdrop-filter: blur(8px);
  overflow: visible;
}

.chat-mascot {
  width: 48px;
  height: 48px;
  object-fit: contain;
  border-radius: 50%;
  flex-shrink: 0;
}

.chat-input-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: flex-start;
}

.chat-mascot-inline {
  position: absolute;
  left: -40px;
  top: 50%;
  transform: translateY(-50%);
  width: 272px;
  height: 272px;
  object-fit: contain;
  pointer-events: none;
  z-index: 2;
}

.chat-text-input {
  flex: 1;
  background: var(--paper-2);
  border: none;
  border-radius: 18px;
  color: var(--type-body);
  font-size: 14px;
  font-family: var(--font-ui-rounded);
  box-shadow: none;
  padding: 10px 52px 10px 14px;
  outline: none;
  resize: none;
  line-height: 1.5;
  min-height: 42px;
  max-height: 80px;
  overflow-y: auto;
  margin-left: 48px;
  margin-right: 155px;
  margin-top: 62px;
}

.chat-send-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 700;
}

.chat-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 20px;
}

:deep(.n-alert) {
  border-radius: 18px;
}

:deep(.n-button) {
  border-radius: 14px;
}

@media (max-width: 1180px) {
  .split-layout {
    grid-template-columns: 1fr;
    height: auto;
    overflow-y: auto;
  }

  .home-view {
    height: auto;
    min-height: calc(100vh - 60px);
  }

  .left-panel,
  .right-panel,
  .left-scroll,
  .right-scroll {
    overflow: visible;
  }

  .hero-card,
  .guide-card {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .split-layout {
    padding: 12px;
    gap: 12px;
  }

  .left-scroll {
    padding: 14px;
  }

  .brand-title {
    font-size: 32px;
  }

  .hero-title {
    font-size: 36px;
  }

  .style-tag-grid {
    grid-template-columns: 1fr;
  }

  .candidate-stage-head,
  .candidate-footer,
  .chat-input-inner {
    flex-direction: column;
    align-items: stretch;
  }

  .candidate-confirm-btn {
    width: 100%;
    min-width: 0;
  }
}
</style>
