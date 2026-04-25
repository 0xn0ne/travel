<template>
  <div class="stage-progress">
    <!-- 5步进度指示器 -->
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
        <!-- 连接线（第一个之后） -->
        <div v-if="idx > 0" class="step-line" :class="{ 'line-done': step.status !== 'pending' }" />

        <!-- 圆形图标 -->
        <div class="step-circle">
          <span v-if="step.status === 'done'" class="step-check">✓</span>
          <span v-else-if="step.status === 'active'" class="step-spin">✦</span>
          <span v-else class="step-num">{{ idx + 1 }}</span>
        </div>

        <!-- 阶段名称 -->
        <div class="step-label">{{ step.label }}</div>
      </div>
    </div>

    <!-- 详细进度消息 -->
    <Transition name="fade" mode="out-in">
      <div class="progress-detail" :key="currentMessage" v-if="currentMessage">
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
  generation: '✈️',
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

// 从 message 中解析主消息和子消息
const currentMessage = computed(() => {
  const msg = props.message || ''
  // 如果有子消息格式 "主消息 | 子消息"
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
  padding: 20px 0 16px;
}

/* ===== 5步进度条 ===== */
.steps-track {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  margin-bottom: 24px;
  position: relative;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 90px;
  position: relative;
}

.step-line {
  position: absolute;
  top: 14px;
  right: 50%;
  width: 100%;
  height: 2px;
  background: var(--color-warm-border);
  transition: background 0.3s;
}

.step-line.line-done {
  background: var(--color-coral);
}

.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--color-warm-border);
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--color-warm-text-muted);
  transition: all 0.3s;
  z-index: 1;
  position: relative;
}

.step-done .step-circle {
  background: var(--color-coral);
  border-color: var(--color-coral);
  color: white;
}

.step-active .step-circle {
  background: white;
  border-color: var(--color-coral);
  color: var(--color-coral);
  box-shadow: 0 0 0 4px rgba(255, 107, 107, 0.15);
}

.step-check {
  font-size: 14px;
  font-weight: bold;
}

.step-spin {
  display: inline-block;
  animation: spin 1s linear infinite;
  color: var(--color-coral);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.step-num {
  font-weight: 600;
  font-size: 12px;
}

.step-label {
  font-size: 11px;
  color: var(--color-warm-text-muted);
  margin-top: 6px;
  text-align: center;
  white-space: nowrap;
  transition: color 0.3s;
}

.step-active .step-label {
  color: var(--color-coral);
  font-weight: 600;
}

.step-done .step-label {
  color: var(--color-ocean-dark);
}

/* ===== 详细消息 ===== */
.progress-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 20px;
  background: rgba(255, 107, 107, 0.05);
  border: 1px solid rgba(255, 107, 107, 0.1);
  border-radius: 12px;
  max-width: 480px;
  margin: 0 auto;
}

.detail-icon {
  font-size: 20px;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-main {
  font-size: 14px;
  color: var(--color-warm-text);
  font-weight: 500;
}

.detail-sub {
  font-size: 12px;
  color: var(--color-warm-text-muted);
}

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
