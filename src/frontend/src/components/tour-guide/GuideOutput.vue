<template>
  <div class="guide-output-card">
    <div class="guide-header">
      <span class="guide-title">导游推荐</span>
      <span v-if="store.isStreaming" class="streaming-indicator">
        <span class="pulse-dot"></span>
        分析中
      </span>
      <span v-else-if="store.toolStatus" class="status-text">
        {{ store.toolStatus }}
      </span>
    </div>

    <div ref="scrollRef" class="messages-area">
      <div v-if="store.messages.length === 0" class="welcome-msg">
        告诉我你看到了什么，我来给你推荐 👀
      </div>

      <div
        v-for="msg in store.messages"
        :key="msg.id"
        :class="['message-wrapper', `message-wrapper--${msg.role}`]"
      >
        <GuideMessageBubble :message="msg" />
      </div>

      <div v-if="store.isStreaming && store.streamingText" class="streaming-text">
        {{ store.streamingText }}<span class="cursor">|</span>
      </div>

      <div v-if="store.isStreaming && !store.streamingText" class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useTourGuideStore } from '@/stores/tourGuide'
import GuideMessageBubble from './GuideMessageBubble.vue'

const store = useTourGuideStore()
const scrollRef = ref<HTMLElement | null>(null)

watch(() => store.messages.length, async () => {
  await nextTick()
  if (scrollRef.value) {
    scrollRef.value.scrollTo({ top: scrollRef.value.scrollHeight, behavior: 'smooth' })
  }
})

watch(() => store.streamingText, async () => {
  await nextTick()
  if (scrollRef.value) {
    scrollRef.value.scrollTo({ top: scrollRef.value.scrollHeight, behavior: 'smooth' })
  }
})
</script>

<style scoped>
.guide-output-card {
  background: #FFFFFF;
  border: 1px solid #E8D5C4;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(45, 32, 22, 0.08);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 104px);
  overflow: hidden;
}

.guide-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid #E8D5C4;
  flex-shrink: 0;
}

.guide-title {
  font-weight: 600;
  font-size: 15px;
  color: #2D2016;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #4ECDC4;
  font-size: 12px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4ECDC4;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.status-text {
  color: #6B5B4E;
  font-size: 12px;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome-msg {
  text-align: center;
  color: #6B5B4E;
  font-size: 14px;
  padding: 40px 20px;
}

.message-wrapper {
  display: flex;
}

.message-wrapper--user {
  justify-content: flex-end;
}

.message-wrapper--guide {
  justify-content: flex-start;
}

.streaming-text {
  color: #2D2016;
  font-size: 14px;
  line-height: 1.6;
  padding: 0 4px;
  word-break: break-word;
}

.cursor {
  display: inline-block;
  animation: blink 0.8s infinite;
  color: #FF6B6B;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #E8D5C4;
  animation: typing-bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
</style>