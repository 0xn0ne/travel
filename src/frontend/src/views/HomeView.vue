<template>
  <div class="home-view">
    <!-- Hero section with warm gradient -->
    <div class="hero">
      <h1 class="app-title">拾途</h1>
      <p class="app-subtitle">品味行程生成器 —— 像本地朋友一样帮你规划旅行</p>
    </div>

    <!-- Journey cards — mini travel invitations -->
    <div class="journey-cards">
      <div
        v-for="(card, idx) in journeyCards"
        :key="idx"
        class="journey-card"
        @click="fillInput(card.text)"
      >
        <div class="card-icon" v-html="card.icon" />
        <p class="card-text">{{ card.text }}</p>
      </div>
    </div>

    <!-- Warm-styled input area -->
    <div class="input-section">
      <n-input
        v-model:value="userInput"
        type="textarea"
        placeholder="说说你想去哪儿玩 ~ 比如：周末想去上海待两天，喜欢安静文艺的地方，独立咖啡馆、老建筑、小众画廊都可以，不要太赶"
        :rows="3"
        maxlength="500"
        show-count
        :disabled="store.isGenerating"
        @keydown.ctrl.enter="handleGenerate"
      />
      <div class="actions">
        <button
          class="generate-btn"
          :disabled="store.isGenerating || !userInput.trim()"
          @click="handleGenerate"
        >
          <span v-if="store.isGenerating" class="btn-loading">✦</span>
          开始规划
        </button>
      </div>
    </div>

    <StageProgress
      v-if="store.isGenerating || store.stage !== 'idle'"
      :current-stage="store.stage"
      :message="store.stageMessage"
    />

    <ItineraryTimeline v-if="store.currentItinerary?.days" :days="(store.currentItinerary as any).days" />

    <div v-if="store.error" class="error-banner">
      <n-alert type="warning" :title="store.error" />
      <n-button size="small" type="primary" style="margin-top: 8px" @click="handleRetry">重试</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { NInput, NButton, NAlert } from 'naive-ui'
import { useItineraryStore } from '../stores/itinerary'
import StageProgress from '../components/StageProgress.vue'
import ItineraryTimeline from '../components/ItineraryTimeline.vue'

const store = useItineraryStore()
const router = useRouter()
const userInput = ref('')

const journeyCards = [
  {
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor"/></svg>',
    text: '周末想去上海逛逛，喜欢文艺咖啡馆和小众书店',
  },
  {
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>',
    text: '成都三日游，想体验地道川菜和茶馆文化',
  },
  {
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><path d="M18 8h1a4 4 0 010 8h-1M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8zM6 1v3M10 1v3M14 1v3"/></svg>',
    text: '杭州浪漫周末，喜欢西湖和有格调的餐厅',
  },
  {
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><path d="M8 3l4 8 5-6 5 15H2L8 3z"/></svg>',
    text: '带父母逛北京，要轻松不累的经典路线',
  },
]

function fillInput(text: string) {
  userInput.value = text
}

async function handleGenerate() {
  if (!userInput.value.trim()) return
  const input = userInput.value
  userInput.value = ''
  await store.generate(input)
  if (store.itineraryId && !store.error) {
    router.push(`/itinerary/${store.itineraryId}`)
  }
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
  max-width: 680px;
  margin: 0 auto;
  padding: 0 16px 24px;
}

/* Hero — full-width gradient background */
.hero {
  text-align: center;
  padding: 60px 24px 40px;
  margin: 0 -16px;
  background: linear-gradient(135deg, var(--color-sand) 0%, var(--color-ocean-light) 100%);
}

.app-title {
  font-size: 48px;
  font-weight: 700;
  color: var(--color-warm-text);
  margin: 0;
}

.app-subtitle {
  font-size: 16px;
  color: var(--color-warm-text-muted);
  margin-top: 8px;
}

/* Journey cards — responsive grid */
.journey-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  max-width: 960px;
  margin: -20px auto 24px;
  padding: 0 16px;
}

.journey-card {
  background: white;
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 20px;
  cursor: pointer;
  transition: var(--transition-smooth);
}

.journey-card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.card-icon {
  color: var(--color-coral);
  width: 24px;
  height: 24px;
  margin-bottom: 12px;
}

.card-icon :deep(svg) {
  display: block;
  width: 24px;
  height: 24px;
}

.card-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-warm-text);
  margin: 0;
}

/* Input area — warm restyle */
.input-section {
  margin-bottom: 20px;
  background: var(--color-warm-surface);
  border-radius: 12px;
  padding: 16px;
  border: 2px solid var(--color-warm-border);
  transition: border-color 0.2s ease;
}

.input-section:focus-within {
  border-color: var(--color-coral);
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.generate-btn {
  min-height: 44px;
  padding: 0 28px;
  background: var(--color-coral);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-smooth);
  display: flex;
  align-items: center;
  gap: 6px;
}

.generate-btn:hover:not(:disabled) {
  background: var(--color-coral-dark);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-loading {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-banner { margin-top: 16px; }

/* Responsive */
@media (max-width: 1024px) {
  .journey-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .hero {
    padding: 40px 16px 32px;
  }
  .app-title {
    font-size: 32px;
  }
  .app-subtitle {
    font-size: 14px;
  }
  .journey-cards {
    grid-template-columns: 1fr;
    margin-top: -16px;
  }
}
</style>
