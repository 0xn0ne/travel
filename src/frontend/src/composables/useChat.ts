import { useSSE } from './useSSE'
import { useChatStore } from '@/stores/chat'

export function useChat() {
  const store = useChatStore()

  async function sendMessage(message: string) {
    store.addUserMessage(message)
    store.isLoading = true

    try {
      const sse = useSSE('/api/chat', {
        message,
        session_id: store.sessionId,
      })

      await sse.start()

      for (const event of sse.events.value) {
        if (event.event_type === 'tool_executing' && event.message) {
          store.setToolMessage(event.message)
        } else if (event.event_type === 'tool_completed') {
          store.setToolMessage(null)
        } else if (event.event_type === 'chat_text') {
          const text = (event.data as Record<string, unknown>)?.text as string ?? event.message ?? ''
          if (text) {
            store.addAssistantMessage(text, false)
          }
        }
      }
    } finally {
      store.isLoading = false
      store.setToolMessage(null)
    }
  }

  return { sendMessage }
}
