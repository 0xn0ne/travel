<template>
  <div class="stage-progress">
    <!-- Warm gradient progress bar -->
    <div class="progress-track">
      <div
        class="progress-fill"
        :class="{ complete: isComplete }"
        :style="{ width: progressPercent + '%' }"
      />
    </div>

    <!-- Travel-themed stage message -->
    <Transition name="fade" mode="out-in">
      <p class="stage-message" :class="{ 'message-complete': isComplete }" :key="currentStage">
        {{ currentMessage }}
      </p>
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

const stages = ['intent', 'prefilter', 'generation', 'validation', 'complete']

const getStageMessage = (stage: string, city?: string): string => {
  const messages: Record<string, string> = {
    intent: `正在理解你的${city ? city + '之旅' : '旅行'}需求...`,
    prefilter: `在${city || ''}寻找有趣的地方...`,
    generation: `为你规划${city ? city + '的' : ''}精彩行程...`,
    validation: '验证路线和时间的合理性...',
    complete: `你的${city ? city + '之旅' : '旅程'}准备好了！`,
  }
  return messages[stage] || messages.intent
}

const currentMessage = computed(() => props.message || getStageMessage(props.currentStage, props.city))

const progressPercent = computed(() => {
  const idx = stages.indexOf(props.currentStage)
  if (idx < 0) return 10
  return [10, 30, 60, 85, 100][idx] || 10
})

const isComplete = computed(() => props.currentStage === 'complete')
</script>

<style scoped>
.stage-progress {
  display: flex;
  flex-direction: column;
  padding: 16px 0;
}

/* Progress bar track */
.progress-track {
  width: 100%;
  height: 8px;
  background: var(--color-sand);
  border-radius: 4px;
  overflow: hidden;
}

/* Progress bar fill — warm gradient */
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-sand) 0%, var(--color-coral) 50%, var(--color-ocean) 100%);
  border-radius: 4px;
  transition: width 0.5s ease;
}

/* Shimmer animation while in progress */
.progress-fill:not(.complete) {
  animation: shimmer 2s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

/* Stage message */
.stage-message {
  font-size: 14px;
  color: var(--color-warm-text-muted);
  margin: 10px 0 0;
  text-align: center;
  min-height: 20px;
}

.stage-message.message-complete {
  color: var(--color-ocean);
  font-weight: 600;
}

/* Fade transition for message changes */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
