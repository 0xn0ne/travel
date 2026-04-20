import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ChatMsg {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  isStreaming?: boolean
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMsg[]>([])
  const sessionId = ref<string>(crypto.randomUUID())
  const isOpen = ref(false)
  const isLoading = ref(false)
  const toolMessage = ref<string | null>(null)

  const lastMessages = computed(() => messages.value.slice(-20))

  function addUserMessage(content: string) {
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    })
  }

  function addAssistantMessage(content: string, isStreaming = true) {
    const msg: ChatMsg = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content,
      timestamp: new Date().toISOString(),
      isStreaming,
    }
    messages.value.push(msg)
    return msg
  }

  function updateLastAssistantMessage(content: string) {
    const last = messages.value.filter(m => m.role === 'assistant').pop()
    if (last) {
      last.content = content
      last.isStreaming = false
    }
  }

  function setToolMessage(msg: string | null) {
    toolMessage.value = msg
  }

  function toggleOpen() {
    isOpen.value = !isOpen.value
  }

  function clearSession() {
    messages.value = []
    sessionId.value = crypto.randomUUID()
    toolMessage.value = null
  }

  return {
    messages, sessionId, isOpen, isLoading, toolMessage,
    lastMessages,
    addUserMessage, addAssistantMessage, updateLastAssistantMessage,
    setToolMessage, toggleOpen, clearSession,
  }
})
