<template>
  <div class="stage-progress">
    <div class="steps-track">
      <div
        v-for="(step, idx) in steps"
        :key="step.key"
        class="step-item"
        :class="{
          'step-done': step.status === 'done',
          'step-active': step.status === 'active',
          'step-pending': step.status === 'pending',
        }"
      >
        <div v-if="idx > 0" class="step-line" :class="{ 'line-done': step.status !== 'pending' }" />
        <div class="step-circle">
          <span v-if="step.status === 'done'" class="step-check">✓</span>
          <span v-else-if="step.status === 'active'" class="step-spin">✦</span>
          <span v-else class="step-num">{{ idx + 1 }}</span>
        </div>
        <div class="step-label">{{ step.label }}</div>
      </div>
    </div>

    <Transition name="fade" mode="out-in">
      <div v-if="currentMessage" :key="currentMessage" class="progress-detail">
        <div class="detail-icon" :class="detailIconClass">{{ detailIcon }}</div>
        <div class="detail-text">
          <span class="detail-main">{{ currentMessage }}</span>
          <span v-if="subMessage" class="detail-sub">{{ subMessage }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  currentStage: string
  message?: string
  city?: string
}>()

const ALL_STAGES = ['intent', 'prefilter', 'generation', 'validation', 'complete']

const STAGE_LABELS: Record<string, string> = {
  intent: '理解需求',
  prefilter: '筛选地点',
  generation: '生成行程',
  validation: '验证路线',
  complete: '完成',
}

const STAGE_ICONS: Record<string, string> = {
  intent: '🔍',
  prefilter: '📍',
  generation: '🧭',
  validation: '✅',
  complete: '🎉',
}

const steps = computed(() => {
  return ALL_STAGES.map((key, idx) => {
    const currentIdx = ALL_STAGES.indexOf(props.currentStage)
    let status: 'done' | 'active' | 'pending' = 'pending'
    if (currentIdx > idx) status = 'done'
    else if (currentIdx === idx) status = 'active'
    return { key, label: STAGE_LABELS[key], status }
  })
})

const currentMessage = computed(() => {
  const msg = props.message || ''
  if (msg.includes('|')) {
    return msg.split('|')[0].trim()
  }
  return msg
})

const subMessage = computed(() => {
  const msg = props.message || ''
  if (msg.includes('|')) {
    return msg.split('|').slice(1).join('').trim()
  }
  return ''
})

const detailIcon = computed(() => STAGE_ICONS[props.currentStage] || '⏳')

const detailIconClass = computed(() => {
  if (props.currentStage === 'complete') return 'icon-done'
  if (props.currentStage === 'intent') return 'icon-intent'
  if (props.currentStage === 'prefilter') return 'icon-prefilter'
  if (props.currentStage === 'generation') return 'icon-generation'
  if (props.currentStage === 'validation') return 'icon-validation'
  return ''
})
</script>

<style scoped>
.stage-progress {
  padding: 10px 0 18px;
}

.steps-track {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  margin-bottom: 18px;
  position: relative;
  padding: 12px 18px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid #1f1f1f;
  box-shadow: 0 14px 28px rgba(108, 124, 240, 0.08);
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 110px;
  position: relative;
}

.step-line {
  position: absolute;
  top: 18px;
  right: 50%;
  width: 100%;
  height: 4px;
  background: #ddd9d2;
  border-radius: 999px;
  transition: background 0.3s ease;
}

.step-line.line-done {
  background: #8ed1c2;
}

.step-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid #8faecc;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #889BB2;
  transition: all 0.25s ease;
  z-index: 1;
  position: relative;
  box-shadow: 0 8px 16px rgba(108, 124, 240, 0.08);
}

.step-done .step-circle {
  background: #98afd0;
  border-color: #8faecc;
  color: white;
  box-shadow: 0 12px 20px rgba(108, 124, 240, 0.18);
}

.step-active .step-circle {
  background: #f7c8a0;
  color: #667B95;
  box-shadow: 0 0 0 7px rgba(247, 200, 160, 0.22);
}

.step-check {
  font-size: 15px;
  font-weight: 900;
}

.step-spin {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.step-num {
  font-weight: 800;
  font-size: 12px;
}

.step-label {
  font-size: 11px;
  color: #90a5bc;
  margin-top: 8px;
  text-align: center;
  white-space: nowrap;
  transition: color 0.25s ease;
  font-weight: 800;
}

.step-active .step-label {
  color: #7f99b6;
}

.step-done .step-label {
  color: #8aa6be;
}

.progress-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f4ef 100%);
  border: 2px solid #1f1f1f;
  border-radius: 24px;
  box-shadow: 0 14px 28px rgba(108, 124, 240, 0.08);
}

.detail-icon {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: rgba(255, 255, 255, 0.92);
  border: 2px solid #1f1f1f;
}

.detail-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.detail-main {
  font-size: 14px;
  font-weight: 900;
  color: #7a94b1;
}

.detail-sub {
  font-size: 12px;
  color: #9cb0c5;
}

.icon-done { background: #e9edff; }
.icon-intent { background: #ffffff; }
.icon-prefilter { background: #f7f4ef; }
.icon-generation { background: #eef1ff; }
.icon-validation { background: #eef8f5; }

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
