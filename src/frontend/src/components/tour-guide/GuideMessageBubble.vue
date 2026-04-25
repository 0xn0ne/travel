<template>
  <div v-if="message.role === 'user'" class="bubble-user">
    {{ message.content }}
  </div>
  <div v-else class="bubble-guide">
    {{ message.content }}
  </div>
</template>

<script setup lang="ts">
interface GuideMessage {
  id: string
  role: 'user' | 'guide'
  content: string
  timestamp: string
  isStreaming?: boolean
}

defineProps<{
  message: GuideMessage
}>()
</script>

<style scoped>
.bubble-user {
  background: #FF6B6B;
  color: white;
  border-radius: 12px 12px 4px 12px;
  padding: 10px 14px;
  max-width: 85%;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.5;
}

.bubble-guide {
  background: #FFF8F0;
  color: #2D2016;
  border-radius: 12px 12px 12px 4px;
  padding: 10px 14px;
  max-width: 85%;
  border: 1px solid #E8D5C4;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}
</style>