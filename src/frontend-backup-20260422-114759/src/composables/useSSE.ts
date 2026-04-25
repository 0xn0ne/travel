import { ref } from 'vue'

export interface PipelineEvent {
  stage: string
  status: string
  message?: string
  data?: Record<string, unknown>
  timestamp: string
  event_type?: string
  itinerary_id?: string
}

export interface SSEConnection {
  events: import('vue').Ref<PipelineEvent[]>
  error: import('vue').Ref<string | null>
  done: import('vue').Ref<boolean>
  start: () => void
  abort: () => void
}

export function useSSE(url: string, body: Record<string, unknown>): SSEConnection {
  const events = ref<PipelineEvent[]>([])
  const error = ref<string | null>(null)
  const done = ref(false)
  let aborted = false
  let buffer = ''

  async function start() {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!response.ok) {
        error.value = `HTTP ${response.status}`
        return
      }
      const reader = (response.body as ReadableStream).getReader()
      const decoder = new TextDecoder()
      while (true) {
        const { done: streamDone, value } = await reader.read()
        if (streamDone || aborted) break
        buffer += decoder.decode(value ?? new Uint8Array(), { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            events.value.push(JSON.parse(line.slice(6)))
          } catch {
            // skip malformed lines
          }
        }
        const last = events.value[events.value.length - 1]
        if (last?.event_type === 'done' || last?.event_type === 'error' || last?.event_type === 'adjust_done' || last?.event_type === 'adjust_error') break
      }
    } catch (e) {
      error.value = String(e)
    } finally {
      done.value = true
    }
  }

  function abort() {
    aborted = true
  }

  return { events, error, done, start, abort }
}

export function useSSEGet(url: string): SSEConnection {
  const events = ref<PipelineEvent[]>([])
  const error = ref<string | null>(null)
  const done = ref(false)
  let aborted = false
  let buffer = ''

  async function start() {
    try {
      const response = await fetch(url)
      if (!response.ok) {
        error.value = `HTTP ${response.status}`
        return
      }
      const reader = (response.body as ReadableStream).getReader()
      const decoder = new TextDecoder()
      while (true) {
        const { done: streamDone, value } = await reader.read()
        if (streamDone || aborted) break
        buffer += decoder.decode(value ?? new Uint8Array(), { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            events.value.push(JSON.parse(line.slice(6)))
          } catch {
            // skip malformed lines
          }
        }
        const last = events.value[events.value.length - 1]
        if (last?.event_type === 'done' || last?.event_type === 'error' || last?.event_type === 'adjust_done' || last?.event_type === 'adjust_error') break
      }
    } catch (e) {
      error.value = String(e)
    } finally {
      done.value = true
    }
  }

  function abort() {
    aborted = true
  }

  return { events, error, done, start, abort }
}
