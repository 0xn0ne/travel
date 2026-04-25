<template>
  <div class="tour-guide-view">
    <div class="tour-guide-grid">
      <div class="tour-left">
        <ObservationInput ref="obsInputRef" />
        <UserProfilePanel />
        <button
          class="analyze-btn"
          :disabled="store.observations.length === 0 || store.isStreaming"
          @click="handleAnalyze"
        >
          <svg v-if="!store.isStreaming" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
          <span v-if="store.isStreaming" class="btn-spinner"></span>
          {{ store.isStreaming ? '分析中...' : '让导游分析' }}
        </button>
      </div>
      <div class="tour-right">
        <GuideOutput />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useTourGuideStore } from '@/stores/tourGuide'
import { useTourGuide } from '@/composables/useTourGuide'
import ObservationInput from '@/components/tour-guide/ObservationInput.vue'
import UserProfilePanel from '@/components/tour-guide/UserProfilePanel.vue'
import GuideOutput from '@/components/tour-guide/GuideOutput.vue'

const store = useTourGuideStore()
const { analyze } = useTourGuide()
const obsInputRef = ref()

function handleAnalyze() {
  obsInputRef.value?.flushInput()
  if (store.observations.length === 0 || store.isStreaming) return
  analyze()
}
</script>

<style scoped>
.tour-guide-view {
  min-height: calc(100vh - 64px);
  background: #FFFAF5;
  padding: 20px;
}

.tour-guide-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.tour-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tour-right {
  min-height: 0;
}

.analyze-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 20px;
  border: none;
  border-radius: 14px;
  background: #FF6B6B;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(255, 107, 107, 0.3);
}

.analyze-btn:hover:not(:disabled) {
  background: #E55A5A;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
}

.analyze-btn:active:not(:disabled) {
  transform: translateY(0);
}

.analyze-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .tour-guide-grid {
    grid-template-columns: 1fr;
  }

  .tour-guide-view {
    padding: 12px;
  }

  .analyze-btn {
    position: sticky;
    bottom: 12px;
    z-index: 10;
  }
}
</style>
