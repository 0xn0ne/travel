import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useSSE, useSSEGet, type PipelineEvent } from '../composables/useSSE'
import type {
  AdjustmentPreview,
  CandidatePoiData,
  CandidatePoiRequestPayload,
  CandidatePoiResponseData,
  ChatMessage,
  DayData,
  GenerateFromPoisPayload,
  ItineraryData,
  POIVisitData,
} from '../types/itinerary'

export const useItineraryStore = defineStore('itinerary', () => {
  const currentItinerary = ref<Record<string, unknown> | null>(null)
  const itineraryId = ref<string | null>(null)
  const events = ref<PipelineEvent[]>([])
  const stage = ref<string>('idle')
  const stageMessage = ref('')
  const homeFlowStage = ref<'input' | 'candidate_selection' | 'generating' | 'result'>('input')
  const isGenerating = ref(false)
  const isLoadingCandidates = ref(false)
  const error = ref<string | null>(null)
  const candidateError = ref<string | null>(null)
  const lastUserInput = ref<string>('')
  const candidateTripContext = ref<CandidatePoiResponseData | null>(null)
  const candidatePois = ref<CandidatePoiData[]>([])
  const selectedCandidatePoiIds = ref<string[]>([])
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

  function attachSSE(sse: ReturnType<typeof useSSE>, resolveDone?: () => void) {
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
  }

  function generate(userInput: string, scenarioId?: string, group?: string): Promise<void> {
    cleanup()
    lastUserInput.value = userInput
    isGenerating.value = true
    homeFlowStage.value = 'generating'
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
    attachSSE(sse, resolveDone ?? undefined)

    return donePromise.then(() => {
      if (!error.value) {
        homeFlowStage.value = 'result'
      }
    })
  }

  async function loadCandidatePois(payload: CandidatePoiRequestPayload): Promise<void> {
    candidateError.value = null
    error.value = null
    isLoadingCandidates.value = true
    stage.value = 'idle'
    stageMessage.value = ''
    homeFlowStage.value = 'input'
    currentItinerary.value = null
    itineraryId.value = null

    try {
      const res = await fetch('/api/poi-candidates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      console.log('[candidate-pois] status', res.status, res.headers.get('content-type'))
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const text = await res.text()
      console.log('[candidate-pois] raw', text.slice(0, 500))
      const json = JSON.parse(text) as CandidatePoiResponseData
      console.log('[candidate-pois] response', json)
      candidateTripContext.value = json
      candidatePois.value = json.candidates || []
      selectedCandidatePoiIds.value = (json.candidates || []).slice(0, Math.min(6, json.candidates.length)).map(item => item.id)
      lastUserInput.value = json.user_input
      homeFlowStage.value = 'candidate_selection'
      isLoadingCandidates.value = false
      console.log('[candidate-pois] state', {
        count: candidatePois.value.length,
        selected: selectedCandidatePoiIds.value.length,
        homeFlowStage: homeFlowStage.value,
        isLoadingCandidates: isLoadingCandidates.value,
      })
    } catch (e) {
      candidateError.value = e instanceof Error ? e.message : String(e)
      throw e
    } finally {
      if (isLoadingCandidates.value) {
        isLoadingCandidates.value = false
      }
    }
  }

  function toggleCandidatePoi(id: string) {
    const exists = selectedCandidatePoiIds.value.includes(id)
    selectedCandidatePoiIds.value = exists
      ? selectedCandidatePoiIds.value.filter(item => item !== id)
      : [...selectedCandidatePoiIds.value, id]
  }

  function setSelectedCandidatePois(ids: string[]) {
    selectedCandidatePoiIds.value = ids
  }

  async function generateFromSelectedPois(payload?: Partial<GenerateFromPoisPayload>): Promise<void> {
    if (!candidateTripContext.value) {
      throw new Error('Missing candidate trip context')
    }

    const selectedPois = candidatePois.value.filter(item => selectedCandidatePoiIds.value.includes(item.id))
    if (selectedPois.length === 0) {
      throw new Error('Please select at least one POI')
    }

    cleanup()
    isGenerating.value = true
    error.value = null
    events.value = []
    stage.value = 'generation'
    stageMessage.value = ''
    homeFlowStage.value = 'generating'

    let resolveDone: (() => void) | null = null
    const donePromise = new Promise<void>((resolve) => { resolveDone = resolve })

    const sse = useSSE('/api/generate-from-pois', {
      user_input: payload?.user_input || candidateTripContext.value.user_input,
      selected_pois: payload?.selected_pois || selectedPois,
      city: payload?.city || candidateTripContext.value.city,
      trip_days: payload?.trip_days || candidateTripContext.value.trip_days,
      scenario_id: payload?.scenario_id,
      group: payload?.group,
    })
    attachSSE(sse, resolveDone ?? undefined)

    return donePromise.then(() => {
      if (!error.value) {
        homeFlowStage.value = 'result'
      }
    })
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

  function resetCandidateSelection() {
    candidateTripContext.value = null
    candidatePois.value = []
    selectedCandidatePoiIds.value = []
    candidateError.value = null
    homeFlowStage.value = 'input'
  }

  function $reset() {
    cleanup()
    currentItinerary.value = null
    itineraryId.value = null
    events.value = []
    stage.value = 'idle'
    stageMessage.value = ''
    homeFlowStage.value = 'input'
    error.value = null
    candidateError.value = null
    isGenerating.value = false
    isLoadingCandidates.value = false
    lastUserInput.value = ''
    candidateTripContext.value = null
    candidatePois.value = []
    selectedCandidatePoiIds.value = []
    previewChanges.value = null
    adjustHistory.value = []
    isAdjusting.value = false
  }

  const currentMessage = computed(() => {
    const e = events.value[events.value.length - 1]
    return e?.message || ''
  })

  const selectedCandidatePois = computed(() =>
    candidatePois.value.filter(item => selectedCandidatePoiIds.value.includes(item.id)),
  )

  return {
    currentItinerary,
    itineraryId,
    events,
    stage,
    stageMessage,
    homeFlowStage,
    isGenerating,
    isLoadingCandidates,
    error,
    candidateError,
    currentMessage,
    lastUserInput,
    candidateTripContext,
    candidatePois,
    selectedCandidatePoiIds,
    selectedCandidatePois,
    previewChanges,
    adjustHistory,
    isAdjusting,
    generate,
    loadCandidatePois,
    toggleCandidatePoi,
    setSelectedCandidatePois,
    generateFromSelectedPois,
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
    resetCandidateSelection,
    $reset,
  }
})
