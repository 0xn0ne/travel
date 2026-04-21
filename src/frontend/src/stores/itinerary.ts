import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useSSE, useSSEGet, type PipelineEvent } from '../composables/useSSE'
import type { AdjustmentPreview, ChatMessage, DayData, ItineraryData, POIVisitData } from '../types/itinerary'

export const useItineraryStore = defineStore('itinerary', () => {
  const currentItinerary = ref<Record<string, unknown> | null>(null)
  const itineraryId = ref<string | null>(null)
  const events = ref<PipelineEvent[]>([])
  const stage = ref<string>('idle')
  const stageMessage = ref('')
  const isGenerating = ref(false)
  const error = ref<string | null>(null)
  const lastUserInput = ref<string>('')
  const previewChanges = ref<AdjustmentPreview | null>(null)
  const adjustHistory = ref<ChatMessage[]>([])
  const isAdjusting = ref<boolean>(false)

  let currentSSE: ReturnType<typeof useSSE> | null = null
  let cleanupFns: Array<() => void> = []

  function cleanup() {
    cleanupFns.forEach((fn) => fn())
    cleanupFns = []
    if (currentSSE) {
      currentSSE.abort()
      currentSSE = null
    }
  }

  function updateFromEvent(event: PipelineEvent) {
    events.value.push(event)
    stage.value = event.stage
    if (event.message) {
      stageMessage.value = event.message
    }
    // Extract itinerary_id from top-level event field
    if ((event as any).itinerary_id && typeof (event as any).itinerary_id === 'string') {
      itineraryId.value = (event as any).itinerary_id
      console.log('[DEBUG] itinerary_id extracted:', itineraryId.value)
    }
    if (event.data) {
      const d = event.data
      if ('updated_itinerary' in d && d.updated_itinerary && typeof d.updated_itinerary === 'object') {
        currentItinerary.value = d.updated_itinerary as Record<string, unknown>
      } else if ('itinerary' in d && d.itinerary && typeof d.itinerary === 'object') {
        currentItinerary.value = d.itinerary as Record<string, unknown>
      } else if ('title' in d) {
        currentItinerary.value = d
      }
    }
  }

  function generate(userInput: string, scenarioId?: string, group?: string): Promise<void> {
    cleanup()
    lastUserInput.value = userInput
    isGenerating.value = true
    error.value = null
    events.value = []
    stage.value = 'intent'
    stageMessage.value = ''

    let resolveDone: (() => void) | null = null
    const donePromise = new Promise<void>((resolve) => { resolveDone = resolve })

    const sse = useSSE('/api/generate', {
      user_input: userInput,
      scenario_id: scenarioId,
      group,
    })
    currentSSE = sse

    let lastProcessedIndex = 0

    const stopEventsWatch = watch(
      () => sse.events.value.length,
      (newLen) => {
        for (let i = lastProcessedIndex; i < newLen; i++) {
          updateFromEvent(sse.events.value[i])
        }
        lastProcessedIndex = newLen
      },
    )

    const stopErrorWatch = watch(sse.error, (err) => {
      if (err) {
        error.value = err
        isGenerating.value = false
        cleanup()
        resolveDone?.()
      }
    })

    const stopDoneWatch = watch(sse.done, (d) => {
      if (d) {
        isGenerating.value = false
        cleanup()
        resolveDone?.()
      }
    })

    cleanupFns = [stopEventsWatch, stopErrorWatch, stopDoneWatch]
    sse.start()

    return donePromise
  }

  function retry(): Promise<void> {
    if (lastUserInput.value) {
      return generate(lastUserInput.value)
    }
    return Promise.resolve()
  }

  function reconnect(id: string) {
    cleanup()
    isGenerating.value = true
    error.value = null
    events.value = []
    stage.value = 'reconnect'
    stageMessage.value = '正在恢复行程...'

    const sse = useSSEGet(`/api/itinerary/stream?itinerary_id=${id}`)
    currentSSE = sse

    let lastProcessedIndex = 0

    const stopEventsWatch = watch(
      () => sse.events.value.length,
      (newLen) => {
        for (let i = lastProcessedIndex; i < newLen; i++) {
          updateFromEvent(sse.events.value[i])
        }
        lastProcessedIndex = newLen
      },
    )

    const stopErrorWatch = watch(sse.error, (err) => {
      if (err) {
        error.value = err
        isGenerating.value = false
        cleanup()
      }
    })

    const stopDoneWatch = watch(sse.done, (d) => {
      if (d) {
        isGenerating.value = false
        cleanup()
      }
    })

    cleanupFns = [stopEventsWatch, stopErrorWatch, stopDoneWatch]
    sse.start()
  }

  function abort() {
    if (currentSSE) {
      cleanup()
      isGenerating.value = false
    }
  }

  async function adjust(itineraryId: string, text: string) {
    cleanup()
    adjustHistory.value.push({ role: 'user', text })
    isAdjusting.value = true
    error.value = null

    const history = adjustHistory.value
    const sse = useSSE('/api/itinerary/adjust', {
      itinerary_id: itineraryId,
      adjustment_text: text,
      conversation_history: history.map((m) => ({ role: m.role, content: m.text })),
    })
    currentSSE = sse

    let lastProcessedIndex = 0

    const stopEventsWatch = watch(
      () => sse.events.value.length,
      (newLen) => {
        for (let i = lastProcessedIndex; i < newLen; i++) {
          const event = sse.events.value[i]
          if (event.event_type === 'adjust_preview' && event.data) {
            previewChanges.value = event.data as unknown as AdjustmentPreview
            if (event.message) {
              adjustHistory.value.push({ role: 'assistant', text: event.message })
            }
          } else {
            updateFromEvent(event)
          }
          if (
            event.event_type === 'adjust_response' &&
            event.message
          ) {
            adjustHistory.value.push({ role: 'assistant', text: event.message })
          }
        }
        lastProcessedIndex = newLen
      },
    )

    const stopErrorWatch = watch(sse.error, (err) => {
      if (err) {
        error.value = err
        isAdjusting.value = false
        cleanup()
      }
    })

    const stopDoneWatch = watch(sse.done, (d) => {
      if (d) {
        isAdjusting.value = false
        cleanup()
      }
    })

    cleanupFns = [stopEventsWatch, stopErrorWatch, stopDoneWatch]
    sse.start()
  }

  async function confirmAdjustment(itId: string) {
    try {
      const res = await fetch('/api/itinerary/adjust/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ itinerary_id: itId, confirmed: true }),
      })
      if (res.ok) {
        const json = await res.json()
        if (json.itinerary && typeof json.itinerary === 'object') {
          currentItinerary.value = json.itinerary as Record<string, unknown>
        }
      }
      previewChanges.value = null
    } catch (e) {
      error.value = String(e)
    }
  }

  function cancelAdjustment() {
    previewChanges.value = null
  }

  async function saveItinerary(itId: string, data: ItineraryData): Promise<void> {
    const res = await fetch(`/api/itinerary/${itId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ itinerary: data }),
    })
    if (!res.ok) {
      throw new Error(`Failed to save itinerary: ${res.status}`)
    }
  }

  async function deletePoi(dayNumber: number, poiId: string): Promise<void> {
    const itinerary = currentItinerary.value as ItineraryData | null
    if (!itinerary || !itineraryId.value) return

    const day = itinerary.days.find((d: DayData) => d.day_number === dayNumber)
    if (!day) return

    day.pois = day.pois.filter((p: POIVisitData) => p.poi_id !== poiId)
    currentItinerary.value = { ...itinerary }

    await saveItinerary(itineraryId.value, itinerary)
  }

  async function insertPoi(
    dayNumber: number,
    position: 'before' | 'after',
    anchorPoiId: string,
    newPoi: POIVisitData,
  ): Promise<void> {
    const itinerary = currentItinerary.value as ItineraryData | null
    if (!itinerary || !itineraryId.value) return

    const day = itinerary.days.find((d: DayData) => d.day_number === dayNumber)
    if (!day) return

    const anchorIndex = day.pois.findIndex((p: POIVisitData) => p.poi_id === anchorPoiId)
    if (anchorIndex === -1) return

    const insertIndex = position === 'before' ? anchorIndex : anchorIndex + 1
    day.pois.splice(insertIndex, 0, newPoi)
    currentItinerary.value = { ...itinerary }

    await saveItinerary(itineraryId.value, itinerary)
  }

  async function submitFeedback(itId: string, rating: string, comment?: string): Promise<boolean> {
    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ itinerary_id: itId, rating, comment }),
      })
      return res.ok
    } catch (e) {
      error.value = String(e)
      return false
    }
  }

  function $reset() {
    cleanup()
    currentItinerary.value = null
    itineraryId.value = null
    events.value = []
    stage.value = 'idle'
    stageMessage.value = ''
    error.value = null
    isGenerating.value = false
    lastUserInput.value = ''
    previewChanges.value = null
    adjustHistory.value = []
    isAdjusting.value = false
  }

  const currentMessage = computed(() => {
    const e = events.value[events.value.length - 1]
    return e?.message || ''
  })

  return {
    currentItinerary,
    itineraryId,
    events,
    stage,
    stageMessage,
    isGenerating,
    error,
    currentMessage,
    lastUserInput,
    previewChanges,
    adjustHistory,
    isAdjusting,
    generate,
    retry,
    reconnect,
    abort,
    adjust,
    confirmAdjustment,
    cancelAdjustment,
    submitFeedback,
    deletePoi,
    insertPoi,
    saveItinerary,
    $reset,
  }
})
