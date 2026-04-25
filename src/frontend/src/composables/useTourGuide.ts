import { useTourGuideStore } from '@/stores/tourGuide'

export function useTourGuide() {
  const store = useTourGuideStore()
  let aborted = false

  async function analyze() {
    if (store.isStreaming) return
    aborted = false

    const text = store.observations.join(' ').trim()
    if (!text) return

    const history = store.messages
      .filter(m => m.content && !m.isStreaming)
      .slice(-8)
      .map(m => ({ role: m.role, content: m.content }))

    store.addUserMessage(text)
    store.setStreaming(true)
    store.setToolStatus('正在分析...')
    store.updateStreamingText('')

    const guideMsgId = store.addGuideMessage('', true)

    try {
      const response = await fetch('/api/tour-guide/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          observations: store.observations,
          profile: store.profile,
          session_id: store.sessionId,
          history,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = (response.body as ReadableStream).getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        if (aborted) break
        const { done, value } = await reader.read()
        if (done) break

        const decoded = decoder.decode(value ?? new Uint8Array(), { stream: true })
        buffer += decoded
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) {
            continue
          }
          try {
            const raw = line.slice(6)
            if (!raw) continue
            const data = JSON.parse(raw)

            const eventData = data.data as Record<string, unknown> | undefined
            if (data.event_type === 'tour_thinking') {
              store.setToolStatus((eventData?.message as string) || '思考中...')
            } else if (data.event_type === 'tour_text') {
              const chunk = (eventData?.text as string) || ''
              if (chunk) {
                store.updateStreamingText(store.streamingText + chunk)
              }
            } else if (data.event_type === 'tour_done') {
              store.updateGuideMessage(guideMsgId, { content: store.streamingText, isStreaming: false })
              store.setToolStatus(null)
            } else if (data.event_type === 'tour_error') {
              store.setToolStatus(null)
              store.updateGuideMessage(guideMsgId, {
                content: (eventData?.message as string) || '发生错误，请稍后再试',
                isStreaming: false,
              })
            }
          } catch {
            // skip malformed lines
          }
        }
      }

      if (!aborted) {
        store.updateGuideMessage(guideMsgId, { content: store.streamingText, isStreaming: false })
        store.setToolStatus(null)
      }
    } catch (e) {
      store.setToolStatus(null)
      store.updateGuideMessage(guideMsgId, { content: '发生错误，请稍后再试', isStreaming: false })
      store.updateStreamingText('')
    } finally {
      // Ensure guide message has content if still empty
      const guideMsg = store.messages.find(m => m.id === guideMsgId)
      if (guideMsg && !guideMsg.content) {
        store.updateGuideMessage(guideMsgId, { content: store.streamingText })
      }
      store.updateGuideMessage(guideMsgId, { isStreaming: false })
      store.setStreaming(false)
      store.setToolStatus(null)
      store.updateStreamingText('')
    }
  }

  function abort() {
    aborted = true
    store.setStreaming(false)
    store.setToolStatus(null)
    store.updateStreamingText('')
  }

  return { analyze, abort }
}
