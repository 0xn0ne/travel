<template>
  <div v-if="!store.isOpen" class="chat-bubble" @click="store.toggleOpen()" aria-label="打开聊天">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  </div>
  <div v-else class="chat-panel">
    <div class="chat-header">
      <span class="chat-title">拾途助手</span>
      <div class="chat-header-actions">
        <button class="chat-icon-btn" @click="store.clearSession()" title="新对话">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </button>
        <button class="chat-icon-btn" @click="store.toggleOpen()" title="关闭">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
    <div ref="messageListRef" class="chat-messages">
      <div
        v-for="msg in store.lastMessages"
        :key="msg.id"
        :class="['chat-message', `chat-message--${msg.role}`]"
      >
        <div v-if="msg.role === 'user'" class="chat-bubble-user">{{ msg.content }}</div>
        <div v-else class="chat-bubble-assistant">{{ msg.content }}</div>
      </div>
      <div v-if="store.toolMessage" class="chat-tool-msg">{{ store.toolMessage }}</div>
      <div v-if="store.isLoading && !store.toolMessage" class="chat-typing">
        <span></span><span></span><span></span>
      </div>
    </div>
    <div class="chat-input-area">
      <input
        v-model="inputText"
        class="chat-input"
        placeholder="问我任何旅行问题..."
        :disabled="store.isLoading"
        @keydown.enter="handleSend"
      />
      <button class="chat-send-btn" :disabled="!inputText.trim() || store.isLoading" @click="handleSend">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useChat } from '@/composables/useChat'

const store = useChatStore()
const { sendMessage } = useChat()
const inputText = ref('')
const messageListRef = ref<HTMLElement | null>(null)

function handleSend() {
  const msg = inputText.value.trim()
  if (!msg || store.isLoading) return
  inputText.value = ''
  sendMessage(msg)
}

watch(() => store.messages.length, async () => {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTo({ top: messageListRef.value.scrollHeight, behavior: 'smooth' })
  }
})
</script>

<style scoped>
.chat-bubble {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #FF6B6B;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(255, 107, 107, 0.3);
  transition: transform 0.2s;
  z-index: 1000;
}
.chat-bubble:hover { transform: scale(1.1); }

.chat-panel {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 380px;
  height: 520px;
  border-radius: 16px;
  background: #FFFAF5;
  border: 1px solid #E8D5C4;
  box-shadow: 0 8px 32px rgba(45, 32, 22, 0.15);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #E8D5C4;
  background: #FF6B6B;
  color: white;
}
.chat-title { font-weight: 600; font-size: 15px; }
.chat-header-actions { display: flex; gap: 8px; }
.chat-icon-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
}
.chat-icon-btn:hover { background: rgba(255,255,255,0.2); }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.chat-message { display: flex; }
.chat-message--user { justify-content: flex-end; }
.chat-message--assistant { justify-content: flex-start; }

.chat-bubble-user {
  background: #FF6B6B;
  color: white;
  border-radius: 12px 12px 4px 12px;
  padding: 8px 12px;
  max-width: 80%;
  word-break: break-word;
  font-size: 14px;
}
.chat-bubble-assistant {
  background: white;
  color: #2D2016;
  border-radius: 12px 12px 12px 4px;
  padding: 8px 12px;
  max-width: 80%;
  border: 1px solid #E8D5C4;
  word-break: break-word;
  font-size: 14px;
}

.chat-tool-msg {
  color: #6B5B4E;
  font-style: italic;
  font-size: 12px;
  padding: 4px 12px;
  text-align: center;
}

.chat-typing {
  display: flex;
  gap: 4px;
  padding: 4px 12px;
}
.chat-typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #E8D5C4;
  animation: typing-bounce 1.4s infinite ease-in-out;
}
.chat-typing span:nth-child(2) { animation-delay: 0.2s; }
.chat-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #E8D5C4;
  background: #FFFAF5;
}
.chat-input {
  flex: 1;
  border: 1px solid #E8D5C4;
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 14px;
  outline: none;
  background: #FFF8F0;
  color: #2D2016;
}
.chat-input:focus { border-color: #FF6B6B; }
.chat-input::placeholder { color: #6B5B4E; }
.chat-input:disabled { opacity: 0.6; }

.chat-send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #FF6B6B;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.chat-send-btn:hover:not(:disabled) { background: #E55A5A; }
.chat-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
